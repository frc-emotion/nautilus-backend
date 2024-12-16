from datetime import datetime, timezone

from quart import current_app
from nautilus_api.config import Config
from nautilus_api.controllers.utils import error_response, success_response, validate_data
from nautilus_api.services import account_service
from nautilus_api.schemas.auth_schema import ForgotPasswordSchema, RegisterSchema, LoginSchema, UpdateUserSchema, VerifyUsersSchema
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Any, Dict

async def cross_reference_studentID(student_id: int, first_name: str, last_name: str, grade: int) -> Dict[str, Any]:
    """Cross reference student ID against directory records, returning flags."""
    flags = []
    user = await account_service.find_student_id_directory(student_id)

    if not user:
        flags.append({
            "field": "student_id",
            "issue": "not_found",
            "student_id": student_id
        })
        return {"flags": flags}

    # Check for missing first_name in directory
    if user["first_name"] == "":
        flags.append({
            "field": "first_name",
            "issue": "missing_directory"
        })

    # Handle missing last_name in directory case
    if user["last_name"] == "":
        # Compare given first_name to directory's first_name
        if user["first_name"].lower() != first_name.lower():
            flags.append({
                "field": "first_name",
                "issue": "mismatch",
                "expected": user["first_name"],
                "actual": first_name
            })
    else:
        # Directory has a last_name, compare both
        if user["first_name"].lower() != first_name.lower():
            flags.append({
                "field": "first_name",
                "issue": "mismatch",
                "expected": user["first_name"],
                "actual": first_name
            })

        if user["last_name"].lower() != last_name.lower():
            flags.append({
                "field": "last_name",
                "issue": "mismatch",
                "expected": user["last_name"],
                "actual": last_name
            })

    # Compare grades
    if user.get("grade") is not None and user["grade"] != grade:
        flags.append({
            "field": "grade",
            "issue": "mismatch",
            "expected": int(user["grade"]),
            "actual": int(grade)
        })

    return flags

async def register_user(data: Dict[str, Any]) -> Dict[str, Any]:
    """Register a new user with validated data."""
    validated_data, error = validate_data(RegisterSchema, data)
    
    if error:
        return validated_data

    if await account_service.find_user_by_email(validated_data.email):
        return error_response("Email already taken", 409)
    
    if await account_service.find_user_by_student_id(validated_data.student_id):
        return error_response("Student ID already taken", 409)

    if not (len(validated_data.password) >= 8 and any(char.isalpha() for char in validated_data.password) and any(char.isdigit() for char in validated_data.password)):
        return error_response("Password must be at least 8 characters long, contain a letter and a number", 400)
    
    flags = await cross_reference_studentID(int(validated_data.student_id), validated_data.first_name, validated_data.last_name, validated_data.grade)

    user_data = validated_data.model_dump(exclude_unset=True)
    user_data.update(
        {
            "api_version": Config.API_VERSION, 
            "role": "unverified", 
            "password": generate_password_hash(validated_data.password),
            "created_at": datetime.now(timezone.utc).timestamp(),
            "notification_token": "",
            "flags": flags
        }
    )

    if not (result := await account_service.add_new_user(user_data)).inserted_id:
        return error_response("Error creating account. Please try again later!", 500)

    return success_response("User registered successfully", 201)

async def login_user(data: Dict[str, Any]) -> Dict[str, Any]:
    """Authenticate a user and generate a JWT token."""
    validated_data, error = validate_data(LoginSchema, data)
    
    if error:
        return validated_data

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
    validated_data, error = validate_data(UpdateUserSchema, data)
    
    if error:
        return validated_data

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
    user.pop("notification_token", None)
    user.pop("flags", None)

    return success_response("User retrieved", 200, {"user": user})

async def mass_verify_users(data: Dict[str, any]) -> Dict[str, Any]:
    """Mass verify user's based on ID"""
    validated_data, error = validate_data(VerifyUsersSchema, data)
    
    if error:
        return validated_data

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

async def update_password(data: Dict[str,Any]):
        validated_data, error = validate_data(ForgotPasswordSchema, data)
        decode = account_service.verify_jwt_token(validated_data.token)

        if not decode:
            return error_response("Invalid JWT token", 400)

        if error:
            return validated_data

        user = await account_service.find_user_by_id(decode["user_id"])

        if not (len(validated_data.password) >= 8 and any(char.isalpha() for char in validated_data.password) and any(char.isdigit() for char in validated_data.password)):
            return error_response("Password must be at least 8 characters long, contain a letter and a number", 400)

        user_data = validated_data.model_dump(exclude_unset=True)

        user_data.update({"password": generate_password_hash(validated_data.password)})

        user_id = int(user["_id"])

        if not (result := await account_service.update_user_profile(user_id, user_data)).modified_count:
            return error_response("Not found or unchanged", 404)

        return {"message": "User password updated", "status": 200}

async def send_password_email(email: str):
    user = await account_service.find_user_by_email(email)

    if user is None:
        # Do not reveal whether the email exists
        return success_response("If the email exists, a reset link has been sent.", 200)

    token = await account_service.generate_jwt_token(user)

    button_link = f"{Config.API_URL}/api/auth/redirect?token={token}"
    reset_link = f"nautilus://forgot-password/{token}"

    html = f"""
                <html>
  <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; margin: 0; padding: 0;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
      <div style="background-color: #fcf000; padding: 20px; text-align: center;">
        <img src="https://cdn.team2658.org/web-public/icon.png" alt="App Icon" style="max-height: 128px; margin-bottom: 10px;" />
        <h1 style="color: #262400; margin: 0; font-size: 24px;">Reset Your Password</h1>
      </div>

      <div style="padding: 20px;">
        <p style="font-size: 16px; color: #333333;">
          Hey there, <br />
          Looks like you’ve just forgot your password again. Don’t worry, we’ve seen it all before. Click the button below to reset it and get things back on track. <strong>Warning: Resetting your password only works on mobile</strong>
        </p>

        <div style="text-align: center; margin: 20px 0;">
          <a href="{button_link}" style="background-color: #fcf000; color: #262400; text-decoration: none; font-size: 16px; padding: 10px 20px; border-radius: 5px; display: inline-block; font-weight: bold; border: 2px solid #d9ce00;">
            Reset Password
          </a>
        </div>

        <p style="font-size: 14px; color: #666666;">
          If the button above doesn’t work, you can copy and paste this URL into your <strong>mobile</strong> browser:
        </p>
        <p style="background-color: #fcfaca; border: 1px solid #fcf465; padding: 10px; border-radius: 4px; color: #333333; font-size: 14px; word-break: break-all;">
          {reset_link}
        </p>
      </div>

      <div style="background-color: #f9f9f9; text-align: center; padding: 10px; font-size: 12px; color: #888888;">
        <p>
          Didn’t request this? No worries—you can safely ignore this email.<br>(But if you somehow clicked "Reset Password" by accident, maybe rethink your clicking strategy.)
        </p>
        <p>
          FRC Team #2658 | Made with ❤️ by Software
        </p>
      </div>
    </div>
  </body>
</html>
            """

    
    current_app.logger.info(html)
    response = await current_app.http_client.post(
        Config.MAILGUN_ENDPOINT,
        auth=("api", Config.MAILGUN_API_KEY),
        data={
            "from": Config.MAILGUN_FROM_EMAIL,
            "to": [email],
            "subject": "Forgot Your Password Again? We’ve Got You.",
            "text": f"Open this link to reset your password for the Nautilus app: {reset_link}",
            "html": html
        }
    )

    l

    if response.status_code != 200:
        return error_response(f"Failed to send email. Mailgun response: {response.text}", response.status_code)

    return success_response("If the email exists, a reset link has been sent.", 200)

async def mass_delete_users(data: Dict[str, any]) -> Dict[str, Any]:
    """Mass delete user's based on ID"""
    validated_data, error = validate_data(VerifyUsersSchema, data)
    
    if error:
        return validated_data

    if not (deleted := await account_service.mass_delete_users(data["users"])).deleted_count:
        return error_response("Not found or unchanged", 404)

    return success_response("Users deleted", 200)