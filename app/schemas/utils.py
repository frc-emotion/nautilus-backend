from pydantic import ValidationError

def format_validation_error(error: ValidationError) -> str:
    """
    Helper function to format Pydantic validation errors into a single, readable message.
    
    :param error: ValidationError instance from Pydantic.
    :return: A formatted string summarizing all validation issues.
    """
    return "; ".join(
        f"{err['loc'][0]}: {err['msg']}" for err in error.errors()
    )