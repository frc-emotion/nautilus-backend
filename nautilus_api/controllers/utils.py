from typing import Any, Dict
from pydantic import ValidationError
from quart import current_app

from nautilus_api.schemas.utils import format_validation_error


def error_response(message: str, status: int, additional_data: Dict = {}) -> Dict[str, Any]:
    """Returns a standardized error response."""
    current_app.logger.error(message)
    return {"error": message, "status": status, "data": additional_data}

def success_response(message: str, status: int, additional_data: Dict = {}) -> Dict[str, Any]:
    """Returns a standardized success response."""
    current_app.logger.info(message)
    return {"message": message, "status": status, "data": additional_data}

def validate_schema(data: Dict[str, Any], schema):
    """Validate data against a schema and return error message if validation fails."""
    try:
        return schema(**data), None
    except ValidationError as e:
        return None, format_validation_error(e)
