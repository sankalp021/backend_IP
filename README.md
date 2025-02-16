# AWS IP Allocation Tool

A Flask-based backend service that manages AWS Elastic IP allocation with specific IP range preferences.

## Features

- Automated AWS Elastic IP allocation and management
- IP filtering based on preferred IP ranges
- Real-time allocation status updates
- Database tracking of IP allocation history
- API rate limiting
- Health check monitoring
- Swagger API documentation
- Environment configuration support

## Prerequisites

- Python 3.8+
- AWS Account with appropriate IAM permissions
- AWS Access Key and Secret Key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd backend_IP
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from the template:
```bash
cp .env.example .env
# Then edit .env with your actual configuration values
```

5. Initialize the database:
```bash
python -c "from models import Base; from App import engine; Base.metadata.create_all(engine)"
```

## Usage

1. Start the server:
```bash
python App.py
```

2. Access the API documentation:
- Open `http://localhost:5000/api/docs` in your browser

## API Endpoints

### POST /allocate-ip
Start IP allocation process with AWS credentials:
```json
{
    "aws_access_key_id": "your-access-key",
    "aws_secret_access_key": "your-secret-key",
    "region_name": "aws-region"
}
```

### POST /stop
Stop the current IP allocation process.

### GET /fetch_regions
Get list of available AWS regions.

### GET /allocation-history
View history of IP allocations.

## Configuration

The application can be configured using environment variables:

- `MAX_ELASTIC_IPS`: Maximum number of Elastic IPs to manage (default: 5)
- `IP_CHECK_INTERVAL`: Interval between IP checks in seconds (default: 60)
- `HEALTH_CHECK_INTERVAL`: Health check interval in seconds (default: 10)
- `DATABASE_URL`: SQLite database URL
- `HEALTH_CHECK_URL`: URL for health monitoring

## Error Handling

The application includes comprehensive error handling for:
- Invalid AWS credentials
- IP allocation failures
- IP release failures
- Rate limiting violations
- General API errors

## Security

- API rate limiting implemented
- AWS credentials validated before use
- CORS enabled for cross-origin requests
- Environment-based configuration

## Development

To contribute to the project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Your License Type]
