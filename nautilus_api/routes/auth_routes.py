from quart import Blueprint, jsonify, g, request, current_app
from typing import Dict, Union
from nautilus_api.controllers import account_controller

auth_api = Blueprint('auth_api', __name__)

@auth_api.errorhandler(Exception)
async def handle_exception(e: Exception) -> tuple[Dict[str, str], int]:
    """Handle unexpected errors and log the exception."""
    user_id = g.user.get("user_id") if g.user else "Unknown"
    current_app.logger.error(f"Unhandled exception for user {user_id}: {e}")
    return jsonify({"error": "An unexpected error occurred. Please report this immediately!"}), 500

# Register user account
@auth_api.route("/register", methods=["POST"])
async def register() -> tuple[Dict[str, Union[str, int]], int]:
    """Register a new user account."""

    data = await request.get_json()
    current_app.logger.info(f"Registering new user with data: {data.get('email', 'unknown')}")

    result = await account_controller.register_user(data)

    if "error" in result:
        current_app.logger.error(f"Failed to register user: {result['error']}")
    else:
        current_app.logger.info("User registered successfully")

    return jsonify(result), result.get("status", 200)

# Login user
@auth_api.route("/login", methods=["POST"])
async def login():
    """Log in a user and return a JWT token if successful."""

    data = await request.get_json()

    current_app.logger.info(f"Attempting to log in user with data: {data.get('email', 'unknown')}")

    result = await account_controller.login_user(data)

    if "error" in result:
        current_app.logger.error(f"Failed login attempt for user: {data.get('email', 'unknown')}")
    else:
        current_app.logger.info("User logged in successfully")

    return jsonify(result), result.get("status", 200)

@auth_api.route("/forgot-password", methods=["POST"])
async def send_email():
    data = await request.get_json()


    current_app.logger.info(f"Attempting to send email to user with mail: {data.get('email')}")


    result = await account_controller.send_password_email(data.get('email'))


    if "error" in result:
        current_app.logger.error(f"Failed email sending attempt for user: {data.get('email')}")
    else:
        current_app.logger.info("Email sent successfully")


    return jsonify(result), result.get("status", 200)


@auth_api.route("/forgot-password", methods=["PUT"])
async def update_password():


    data=await request.get_json()


    current_app.logger.info(f"Attempting to update password for user with email: {data.get('email')}")


    result=await account_controller.update_password(data)


    if "error" in result:
        current_app.logger.error(f"Failed updating password for user with email: {data.get('email')}")
    else:
        current_app.logger.info("Password updated successfully")


    return jsonify(result), result.get("status", 200)