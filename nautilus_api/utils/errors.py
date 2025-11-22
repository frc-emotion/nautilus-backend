"""
Custom error classes and handlers for the API.
"""
from typing import Dict, Any, Optional


class HTTPError(Exception):
    """Base HTTP error class."""
    
    def __init__(self, code: str, message: str, status_code: int = 500):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to JSON-serializable dict."""
        return {
            "error": {
                "code": self.code,
                "message": self.message
            }
        }


class BadRequestError(HTTPError):
    """400 Bad Request error."""
    
    def __init__(self, message: str, code: str = "BAD_REQUEST"):
        super().__init__(code=code, message=message, status_code=400)


class NotFoundError(HTTPError):
    """404 Not Found error."""
    
    def __init__(self, message: str, code: str = "NOT_FOUND"):
        super().__init__(code=code, message=message, status_code=404)


class TBAError(HTTPError):
    """Error related to TBA API calls."""
    
    def __init__(self, message: str, code: str = "TBA_ERROR", status_code: int = 502):
        super().__init__(code=code, message=message, status_code=status_code)


class TBATimeoutError(TBAError):
    """TBA API timeout."""
    
    def __init__(self, message: str = "TBA API request timed out"):
        super().__init__(message=message, code="TBA_TIMEOUT", status_code=504)


class TBARateLimitError(TBAError):
    """TBA API rate limit exceeded."""
    
    def __init__(self, message: str = "TBA API rate limit exceeded"):
        super().__init__(message=message, code="TBA_RATE_LIMIT", status_code=429)


def format_error_response(code: str, message: str) -> Dict[str, Any]:
    """Format error response as standard JSON structure."""
    return {
        "error": {
            "code": code,
            "message": message
        }
    }
