from typing import List

DESIRED_IPS: List[str] = [
    '43.204.22','43.204.25', '43.204.24', '43.204.23', '43.204.28', '43.204.30',  
    '43.205.232', '43.205.113', '43.205.207', '43.205.178', '43.205.126', '43.205.124',
    # ...existing IPs...
]

MAX_ELASTIC_IPS = 5
HEALTH_CHECK_INTERVAL = 10  # seconds
IP_CHECK_INTERVAL = 60  # seconds
