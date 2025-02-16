from typing import List, Tuple, Dict
import boto3
import logging
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from models import IPAllocationHistory
from exceptions import IPAllocationError, IPReleaseError, InvalidCredentialsError
from config import DESIRED_IPS, MAX_ELASTIC_IPS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSManager:
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, region_name: str, db_session: sessionmaker):
        try:
            self.session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name
            )
            self.ec2 = self.session.client('ec2')
            self.db_session = db_session
            self.region = region_name
            # Verify credentials
            self.ec2.describe_regions()
        except Exception as e:
            raise InvalidCredentialsError(f"Invalid AWS credentials: {str(e)}")

    def get_elastic_ips(self) -> List[Tuple[str, str]]:
        response = self.ec2.describe_addresses()
        return [[address.get('PublicIp'), address.get('AllocationId')] 
                for address in response.get('Addresses', [])]

    def release_ip(self, allocation_id: str) -> None:
        try:
            self.ec2.release_address(AllocationId=allocation_id)
            with self.db_session() as session:
                ip_record = session.query(IPAllocationHistory).filter_by(
                    allocation_id=allocation_id,
                    released_at=None
                ).first()
                if ip_record:
                    ip_record.released_at = datetime.utcnow()
                    session.commit()
        except Exception as e:
            raise IPReleaseError(f"Failed to release IP: {str(e)}")

    def allocate_ip(self) -> Tuple[str, str]:
        try:
            response = self.ec2.allocate_address(Domain='vpc')
            public_ip = response.get('PublicIp')
            allocation_id = response.get('AllocationId')
            
            with self.db_session() as session:
                ip_history = IPAllocationHistory(
                    ip_address=public_ip,
                    allocation_id=allocation_id,
                    region=self.region
                )
                session.add(ip_history)
                session.commit()
            
            return public_ip, allocation_id
        except Exception as e:
            raise IPAllocationError(f"Failed to allocate IP: {str(e)}")

    def is_desired_ip(self, ip: str) -> bool:
        ip_prefix = '.'.join(ip.split('.')[:3])
        return ip_prefix in DESIRED_IPS
