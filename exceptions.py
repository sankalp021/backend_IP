class AWSError(Exception):
    """Base exception for AWS-related errors"""
    pass

class IPAllocationError(AWSError):
    """Raised when IP allocation fails"""
    pass

class IPReleaseError(AWSError):
    """Raised when IP release fails"""
    pass

class InvalidCredentialsError(AWSError):
    """Raised when AWS credentials are invalid"""
    pass
