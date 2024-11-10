from pydantic import ValidationError
from quart import jsonify, current_app
from app.config import Config
import app.services.account_service as account_service
from app.schemas.register_schema import RegisterSchema
from app.schemas.login_schema import LoginSchema
from werkzeug.security import generate_password_hash, check_password_hash
from app.schemas.utils import format_validation_error

async def register_user(data):
    # Validate incoming data using RegisterSchema
    try:
        # Validate incoming data using RegisterSchema
        validated_data = RegisterSchema(**data)
        current_app.logger.info(f"Register data validated successfully for email: {validated_data.email}")
    except ValidationError as e:
        # Log validation error and return a formatted error message
        current_app.logger.error(f"Validation error in register data: {e.errors()}")
        return {"error": format_validation_error(e), "status": 400}

    # Check if the email is already taken
    existing_user = await account_service.find_user_by_email(validated_data.email)
    if existing_user:
        current_app.logger.warning(f"Attempt to register with existing email: {validated_data.email}")
        return {"error": "Email already taken", "status": 409}

    # Validate password requirements
    if len(validated_data.password) < 8 or \
       not any(char.isalpha() for char in validated_data.password) or \
       not any(char.isdigit() for char in validated_data.password):
        current_app.logger.warning(f"Password validation failed for email: {validated_data.email}")
        return {"error": "Password must be at least 8 characters long and contain at least 1 letter and 1 number", "status": 400}

    # Hash the password before storing it
    hashed_password = generate_password_hash(validated_data.password)
    
    # Prepare data for insertion
    user_data = validated_data.model_dump(exclude_unset=True)
    user_data["password"] = hashed_password
    user_data["api_version"] = Config.API_VERSION
    user_data["role"] = "unverified"

    # Insert the new user into the database
    result = await account_service.add_new_user(user_data)
    if not result.inserted_id:
        current_app.logger.error(f"Failed to insert new user for email: {validated_data.email}")
        return {"error": "Something went wrong creating your account. Please report this immediately!", "status": 500}

    # Log success and return response
    current_app.logger.info(f"User registered successfully with email: {validated_data.email}")
    return {"message": "User registered successfully", "status": 201}

async def login_user(data):
    # Validate incoming data using LoginSchema
    try:
        validated_data = LoginSchema(**data)
        current_app.logger.info(f"Login data validated successfully for email: {validated_data.email}")
    except ValidationError as e:
        # Log validation error and return a response
        current_app.logger.error(f"Validation error in login data: {e.errors()}")
        return {"error": format_validation_error(e), "status": 400}

    # Attempt to find the user by email
    user = await account_service.find_user_by_email(validated_data.email)
    if not user:
        current_app.logger.warning(f"Login attempt failed for non-existent email: {validated_data.email}")
        return {"error": "Invalid email or password", "status": 401}

    # Check if the password is correct
    if not check_password_hash(user["password"], validated_data.password):
        current_app.logger.warning(f"Invalid password attempt for email: {validated_data.email}")
        return {"error": "Invalid email or password", "status": 401}

    # Generate a new JWT token upon successful login
    token = await account_service.generate_jwt_token(user)
    current_app.logger.info(f"User logged in successfully with email: {validated_data.email}")

    # Return the token as a response
    return {"token": token, "status": 200}