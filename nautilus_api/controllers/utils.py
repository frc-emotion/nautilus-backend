from typing import Any, Dict, Union
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

    
def validate_data(schema, data: Dict[str, Any], action: str = "N/A") -> Union[Any, Dict[str, Union[str, int]]]:
    """Validates data against a schema, logging errors if validation fails."""
    try:
        validated_data = schema(**data)
        current_app.logger.info(f"{action} data validated: {validated_data}")
        return validated_data, False
    except ValidationError as e:
        current_app.logger.error(f"Validation error in {action}: {e.errors()}")
        return error_response(format_validation_error(e), 400), True