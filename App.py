from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import time
import threading
import requests
import logging
from typing import Generator
from aws_manager import AWSManager
from config import MAX_ELASTIC_IPS, HEALTH_CHECK_INTERVAL, IP_CHECK_INTERVAL

load_dotenv()

app = Flask(__name__)
CORS(app)
limiter = Limiter(app, key_func=get_remote_address)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stop_allocation = False
aws_manager = None

# Swagger configuration
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "AWS IP Allocation API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Database setup
engine = create_engine(os.getenv('DATABASE_URL'))
SessionLocal = sessionmaker(bind=engine)

def manage_elastic_ips(aws_manager: AWSManager) -> Generator[str, None, None]:
    while not stop_allocation:
        try:
            elastic_ips = aws_manager.get_elastic_ips()
            matched_ips = []

            for ip_data in elastic_ips[:]:
                public_ip, allocation_id = ip_data
                if aws_manager.is_desired_ip(public_ip):
                    if public_ip not in aws_manager.allocated_ips:
                        logger.info(f"Allocated: {public_ip}")
                        yield f"Allocated {public_ip}"
                        aws_manager.allocated_ips[public_ip] = allocation_id
                    matched_ips.append(ip_data)
                    elastic_ips.remove(ip_data)

            # Release excess IPs
            if len(elastic_ips) + len(matched_ips) >= MAX_ELASTIC_IPS:
                for _, allocation_id in elastic_ips:
                    aws_manager.release_ip(allocation_id)
                elastic_ips = []

            # Allocate new IPs if needed
            while len(elastic_ips) + len(matched_ips) < MAX_ELASTIC_IPS:
                public_ip, allocation_id = aws_manager.allocate_ip()
                if aws_manager.is_desired_ip(public_ip):
                    matched_ips.append([public_ip, allocation_id])
                    yield f"Allocated {public_ip}"
                else:
                    elastic_ips.append([public_ip, allocation_id])
                    yield f"Suggested {public_ip}"

            # Release undesired IPs
            for _, allocation_id in elastic_ips:
                aws_manager.release_ip(allocation_id)

            time.sleep(IP_CHECK_INTERVAL)
        except Exception as e:
            logger.error(f"Error in IP management: {e}")
            yield f"Error: {str(e)}"
            time.sleep(5)

@app.route('/allocate-ip', methods=['POST'])
@limiter.limit("5 per minute")
def allocate_ip():
    try:
        global stop_allocation, aws_manager
        stop_allocation = False

        credentials = AWSCredentials(**request.json)
        aws_manager = AWSManager(
            credentials.aws_access_key_id,
            credentials.aws_secret_access_key,
            credentials.region_name,
            SessionLocal
        )
        return Response(manage_elastic_ips(aws_manager), content_type='text/plain')
    except ValueError as e:
        return jsonify({'error': 'Invalid request data', 'details': str(e)}), 400
    except InvalidCredentialsError as e:
        return jsonify({'error': 'Invalid AWS credentials', 'details': str(e)}), 401
    except Exception as e:
        logger.error(f"Error in allocation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stop', methods=['POST'])
def stop_allocation_route():
    global stop_allocation
    stop_allocation = True
    return jsonify({'status': 'PROCESS STOPPED'})

@app.route('/fetch_regions', methods=['GET'])
def fetch_regions():
    session = boto3.session.Session()
    available_regions = session.get_available_regions('ec2')
    regions=[]
    for region in available_regions:
        regions.append(region)
    return regions

@app.route('/allocation-history', methods=['GET'])
def get_allocation_history():
    with SessionLocal() as session:
        history = session.query(IPAllocationHistory).all()
        return jsonify([{
            'ip_address': h.ip_address,
            'allocated_at': h.allocated_at.isoformat(),
            'released_at': h.released_at.isoformat() if h.released_at else None,
            'region': h.region
        } for h in history])

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'BACKEND SERVER FOR AWS TOOL IS STARTED'})

def health_check():
    while True:
        try:
            response = requests.get('https://backend-ip-2.onrender.com')
            logger.info(f'Health check: {response.status_code}')
        except Exception as e:
            logger.error(f'Health check failed: {e}')
        time.sleep(HEALTH_CHECK_INTERVAL)

if __name__ == '__main__':
    threading.Thread(target=health_check, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
