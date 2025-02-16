from typing import List, Tuple, Dict
import boto3
import logging
from config import DESIRED_IPS, MAX_ELASTIC_IPS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSManager:
    def __init__(self, aws_access_key_id: str, aws_secret_access_key: str, region_name: str):
        self.session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        self.ec2 = self.session.client('ec2')
        self.allocated_ips: Dict[str, str] = {}

    def get_elastic_ips(self) -> List[Tuple[str, str]]:
        response = self.ec2.describe_addresses()
        return [[address.get('PublicIp'), address.get('AllocationId')] 
                for address in response.get('Addresses', [])]

    def release_ip(self, allocation_id: str) -> None:
        try:
            self.ec2.release_address(AllocationId=allocation_id)
            logger.info(f"Released IP with allocation ID: {allocation_id}")
        except Exception as e:
            logger.error(f"Error releasing IP: {e}")

    def allocate_ip(self) -> Tuple[str, str]:
        response = self.ec2.allocate_address(Domain='vpc')
        return response.get('PublicIp'), response.get('AllocationId')

    def is_desired_ip(self, ip: str) -> bool:
        ip_prefix = '.'.join(ip.split('.')[:3])
        return ip_prefix in DESIRED_IPS
