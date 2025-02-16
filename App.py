from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import boto3
import os
import time
import threading
import requests 
app = Flask(__name__)
CORS(app)

stop_allocation = False
allocated_ips = []
desired_ips = [
    '43.204.22','43.204.25', '43.204.24', '43.204.23', '43.204.28', '43.204.30',  
    '43.205.232', '43.205.113', '43.205.207', '43.205.178', '43.205.126', '43.205.124', '43.205.113', 
    '43.205.208', '43.205.191', '43.205.94', '43.205.228', '43.205.210', '43.205.191', '43.205.120', '43.205.238', '43.205.207', '43.205.110', '43.205.121', 
    '43.205.107', '43.205.123', '43.205.92', '43.205.213', '43.205.217', '43.205.130', '43.205.220', '43.205.194', '43.205.178', 
    '43.205.210', '43.205.111', '43.205.215', '43.205.253', '43.205.49', '43.205.52', '43.205.153', '43.205.50', 
    '43.205.94', '43.205.208', '43.205.217', '43.205.142', '43.205.146'
]
my_dict = {}
def manage_elastic_ips(aws_access_key_id,aws_secret_access_key,region_name):
    while not stop_allocation:
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )

        ec2 = session.client('ec2')
        response = ec2.describe_addresses()
        elastic_ips = [[address.get('PublicIp'), address.get('AllocationId')] for address in response.get('Addresses', [])]
        matched_ips = []

        for ip_data in elastic_ips[:]:  
            public_ip = ip_data[0]
            ip_prefix = '.'.join(public_ip.split('.')[:3])
            if ip_prefix in desired_ips:
                if public_ip in my_dict:
                    print("HII")
                else:
                    print(f"Allocated : {public_ip}")
                    yield f"Allocated {public_ip}"
                    my_dict[public_ip]=1
                matched_ips.append(ip_data)  
                elastic_ips.remove(ip_data)

        if len(elastic_ips) + len(matched_ips) >= 5:
            for ip_data in elastic_ips[:]:  
                ec2.release_address(AllocationId=ip_data[1])   
            elastic_ips = []  

        while len(elastic_ips) + len(matched_ips) < 5:
            allocation_response = ec2.allocate_address(Domain='vpc')  # Allocate Elastic IP for VPC
            new_ip_data = [allocation_response.get('PublicIp'), allocation_response.get('AllocationId')]
            public_ip = allocation_response.get('PublicIp')
            ip_prefix = '.'.join(public_ip.split('.')[:3])
            if ip_prefix in desired_ips:
                print(f"Allocated : {allocation_response.get('PublicIp')}")
                yield f"Allocated {allocation_response.get('PublicIp')}"
                matched_ips.append(new_ip_data)  
            else:
                elastic_ips.append(new_ip_data)
                print(f"Suggested : {allocation_response.get('PublicIp')}")
                yield f"Suggested {allocation_response.get('PublicIp')}"
        for ip_data in elastic_ips[:]:  
            ec2.release_address(AllocationId=ip_data[1])   
        elastic_ips = []
        time.sleep(60)



@app.route('/allocate-ip', methods=['POST'])
def allocate_ip():
    
    global stop_allocation
    stop_allocation = False

    data = request.json
    aws_access_key_id = data['aws_access_key_id']
    aws_secret_access_key = data['aws_secret_access_key']
    region_name=data['region_name']
    return Response(manage_elastic_ips(aws_access_key_id,aws_secret_access_key,region_name), content_type='text/plain')

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


@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'BACKEND SERVER FOR AWS TOOL IS STARTED'})



def call_api_every_10_seconds():
        while True:
            # Replace this URL with the API endpoint you want to call
            url = 'https://backend-ip-2.onrender.com'
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    print('API call successful:', response.json())
                else:
                    print('API call failed with status code:', response.status_code)
            except Exception as e:
                print('Error during API call:', e)
    
            time.sleep(10)  # Wait for 10 seconds
    
    # Start the background thread
threading.Thread(target=call_api_every_10_seconds, daemon=True).start()
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
