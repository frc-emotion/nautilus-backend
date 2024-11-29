from datetime import datetime, timezone
from quart import current_app
from nautilus_api.config import Config
from nautilus_api.controllers.utils import error_response, success_response, validate_schema
from nautilus_api.services import account_service
from nautilus_api.schemas.auth_schema import RegisterSchema, LoginSchema, UpdateUserSchema, VerifyUsersSchema
from nautilus_api.schemas.utils import format_validation_error
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Any, Dict, List
from pydantic import ValidationError

async def register_user(data: Dict[str, Any]) -> Dict[str, Any]:
    """Register a new user with validated data."""
    validated_data, error = validate_schema(data, RegisterSchema)
    if error:
        return error_response(error, 400)
    
    if await account_service.find_user_by_email(validated_data.email):
        return error_response("Email already taken", 409)
    
    if await account_service.find_user_by_student_id(validated_data.student_id):
        return error_response("Student ID already taken", 409)

    if not (len(validated_data.password) >= 8 and any(char.isalpha() for char in validated_data.password) and any(char.isdigit() for char in validated_data.password)):
        return error_response("Password must be at least 8 characters long, contain a letter and a number", 400)

    user_data = validated_data.model_dump(exclude_unset=True)
    user_data.update(
        {
            "api_version": Config.API_VERSION, 
            "role": "unverified", 
            "password": generate_password_hash(validated_data.password),
            "created_at": datetime.now(timezone.utc).timestamp()    
            })


    if not (result := await account_service.add_new_user(user_data)).inserted_id:
        return error_response("Error creating account. Please try again later!", 500)

    return success_response("User registered successfully", 201)

async def login_user(data: Dict[str, Any]) -> Dict[str, Any]:
    """Authenticate a user and generate a JWT token."""
    validated_data, error = validate_schema(data, LoginSchema)
    if error:
        return error_response(error, 400)
    
    user = await account_service.find_user_by_email(validated_data.email)
    if not user or not check_password_hash(user["password"], validated_data.password):
        return error_response("Invalid email or password", 401)

    token = await account_service.generate_jwt_token(user)

    # Remove password field from user
    user.pop("password", None)

    # Return token and user data
    user.update({"token": token})

    return success_response("User logged in", 200, {"user": user})

async def update_user(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update user data by user ID."""
    validated_data, error = validate_schema(data, UpdateUserSchema)
    if error:
        return error_response(error, 400)
    
    result = await account_service.update_user(user_id, data)
    if not result.modified_count:
        return error_response("Not found or unchanged", 404)
    
    if not (user := await account_service.find_user_by_id(user_id)):
        return error_response("User not found", 404)
    
    # Remove password field from user
    user.pop("password", None)
    user.pop("email", None)
    user.pop("student_id", None)
    user.pop("phone", None)
    user.pop("api_version", None)
    user.pop("created_at", None)

    return success_response("User updated", 200, {"user": user})

async def delete_user(user_id: int) -> Dict[str, Any]:
    """Delete a user by user ID."""
    if not (result := await account_service.delete_user(user_id)).deleted_count:
        return error_response("User not found", 404)

    return success_response("User deleted", 200)

async def get_all_users() -> Dict[str, Any]:
    """Retrieve all users."""
    users = await account_service.get_all_users()
    if not users:
        return error_response("No users found", 404)

    return success_response("Users retrieved", 200, {"users": users})

async def get_user_directory() -> Dict[str, Any]:
    """Retrieve all users."""
    users = await account_service.get_user_directory()
    if not users:
        return error_response("No users found", 404)

    return success_response("Users retrieved", 200, {"users": users})

async def get_user_by_id(user_id: int) -> Dict[str, Any]:
    """Retrieve a specific user by their ID."""
    if not (user := await account_service.find_user_by_id(user_id)):
        return error_response("User not found", 404)
    
    # Remove password field from user
    user.pop("password", None)

    return success_response("User retrieved", 200, {"user": user})

async def get_clean_user_by_id(user_id: int) -> Dict[str, Any]:
    """Retrieve a specific user by their ID."""
    if not (user := await account_service.find_user_by_id(user_id)):
        return error_response("User not found", 404)
    
    # Remove password field from user
    user.pop("password", None)
    user.pop("email", None)
    user.pop("student_id", None)
    user.pop("phone", None)
    user.pop("api_version", None)
    user.pop("created_at", None)

    return success_response("User retrieved", 200, {"user": user})

async def mass_verify_users(data: Dict[str, any]) -> Dict[str, Any]:
    """Mass verify user's based on ID"""
    validated_data, error = validate_schema(data, VerifyUsersSchema)
    if error:
        return error_response(error, 400)
    
    if not (verified := await account_service.mass_verify_users(data["users"])).modified_count:
        return error_response("Not found or unchanged", 404)

    return success_response("Users verified", 200)

async def update_user_profile(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a user's profile by user ID."""
    if not (result := await account_service.update_user_profile(user_id, data)).modified_count:
        return error_response("Not found or unchanged", 404)

    return success_response("User profile updated", 200)

async def refresh_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a JWT token for a user."""
    
    user = await account_service.find_user_by_id(int(user["user_id"]))

    if not (user):
        return error_response("User not found", 404)

    token = await account_service.generate_jwt_token(user)

    # Remove password field from user
    user.pop("password", None)

    # Return token and user data
    user.update({"token": token})

    return success_response("User refreshed", 200, {"user": user})