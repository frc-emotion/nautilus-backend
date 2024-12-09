from quart import Blueprint, jsonify, g, redirect, request, current_app
from typing import Dict, Union
from nautilus_api.controllers import account_controller
from nautilus_api.controllers.utils import error_response, success_response

auth_api = Blueprint('auth_api', __name__)

@auth_api.errorhandler(Exception)
async def handle_exception(e: Exception) -> tuple[Dict[str, str], int]:
    """Handle unexpected errors and log the exception."""
    user_id = g.user.get("user_id") if g.user else "Unknown"
    current_app.logger.error(f"Unhandled exception for user {user_id}: {e}")
    return error_response("An unexpected error occurred. Please report this immediately!", 500)

# Register user account
@auth_api.route("/register", methods=["POST"])
async def register() -> tuple[Dict[str, Union[str, int]], int]:
    """Register a new user account."""

    data = await request.get_json()
    current_app.logger.info(f"Registering new user with data: {data.get('email', 'unknown')}")

    result = await account_controller.register_user(data)

    return result

# Login user
@auth_api.route("/login", methods=["POST"])
async def login():
    """Log in a user and return a JWT token if successful."""

    data = await request.get_json()

    current_app.logger.info(f"Attempting to log in user with data: {data.get('email', 'unknown')}")

    result = await account_controller.login_user(data)

    return result

@auth_api.route("/forgot-password", methods=["POST"])
async def send_email():
    data = await request.get_json()

    if "email" not in data:
        return error_response("Email is required", 400)

    result = await account_controller.send_password_email(data.get('email'))

    return result


@auth_api.route("/forgot-password", methods=["PUT"])
async def update_password_endpoint():
    """Endpoint to update user password using token."""
    data = await request.get_json()

    if "token" not in data or "password" not in data:
        return error_response("Token and password are required", 400)

    current_app.logger.info(f"Attempting to update password using token: {data.get('token')[:10]}...")

    result = await account_controller.update_password(data)

    if "error" in result:
        current_app.logger.error(f"Failed updating password with token: {data.get('token')[:10]}...")
    else:
        current_app.logger.info("Password updated successfully")

    return jsonify(result), result.get("status", 200)

@auth_api.route("/redirect", methods=["GET"])
async def redirectUser():
    # nautilus://forgot-password/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyMiwicm9sZSI6InVudmVyaWZpZWQiLCJleHAiOjE3MzM5NTAxMzl9.cyUR-luoTPuX7m21xnQm9rU_yFqHDTHvhiWHgJHDWl0
    # Redirect to this deep link to update password

    if "token" not in request.args:
        return error_response("Token is required", 400)

    # Get link from query params
    token = request.args.get("token")

    return redirect("nautilus://forgot-password/" + token, 302)