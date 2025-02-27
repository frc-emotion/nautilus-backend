import jwt
from quart import Blueprint, jsonify, g, request, current_app
from nautilus_api.config import Config
from nautilus_api.controllers import account_controller
from nautilus_api.routes.utils import require_access, sanitize_request
from typing import Optional, Any, Dict

account_api = Blueprint("account_api", __name__)

# @account_api.before_request
# def authenticate_user() -> None:
#     """Authenticate user using JWT token in the Authorization header."""
#     auth_header: Optional[str] = request.headers.get("Authorization")
#     if auth_header and auth_header.startswith("Bearer "):
#         token: str = auth_header.split(" ")[1]
#         try:
#             decoded_token: Dict[str, Any] = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
#             g.user = decoded_token
#             current_app.logger.info(f"User {g.user.get('user_id')} authenticated successfully")
#         except jwt.ExpiredSignatureError:
#             g.user = None
#             current_app.logger.warning("Expired token provided for authentication")
#         except jwt.InvalidTokenError:
#             g.user = None
#             current_app.logger.warning("Invalid token provided for authentication")
#     else:
#         g.user = None
#         current_app.logger.warning("No token provided for authentication")

@account_api.errorhandler(Exception)
async def handle_exception(e: Exception) -> Any:
    """Handle unexpected exceptions by logging the error and returning a generic error message."""
    # Check if 429 error is raised
    if type(e).__name__ == "RateLimitExceeded":
        # Retry after
        headers = e.get_headers()
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429, headers

    current_app.logger.error(f"Unhandled exception: {e}")
    return jsonify({"error": "An unexpected error occurred. Please report this immediately!"}), 500

@account_api.route("/users/<int:user_id>", methods=["PUT"])
@require_access(specific_roles=["admin"])
async def update_user(user_id: str) -> tuple[Dict[str, Any], int]:
    """Update user data by user ID."""
    uncleaned_data = await request.get_json()
    data = await sanitize_request(uncleaned_data)
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} updating user with ID {user_id} using data: {data}")
    result: Dict[str, Any] = await account_controller.update_user(user_id, data)
    return jsonify(result), result.get("status", 200)

@account_api.route("/users/<int:user_id>", methods=["DELETE"])
@require_access(specific_roles=["admin"])
async def delete_user(user_id: str) -> tuple[Dict[str, Any], int]:
    """Delete a user by user ID."""
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} deleting user with ID {user_id}")
    result: Dict[str, Any] = await account_controller.delete_user(user_id)
    return jsonify(result), result.get("status", 200)

@account_api.route("/users", methods=["GET"])
@require_access(minimum_role="executive")
async def get_all_users() -> tuple[Dict[str, Any], int]:
    """Retrieve all users."""
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} fetching all users")
    result: Dict[str, Any] = await account_controller.get_all_users()
    return jsonify(result), result.get("status", 200)

@account_api.route("/users/directory", methods=["GET"])
@require_access(minimum_role="member")
async def get_user_directory() -> tuple[Dict[str, Any], int]:
    """Retrieve all users."""
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} fetching all users")
    result: Dict[str, Any] = await account_controller.get_user_directory()
    return jsonify(result), result.get("status", 200)

@account_api.route("/users/directory/<int:user_id>", methods=["GET"])
@require_access(minimum_role="member")
async def get_user_directory_by_id(user_id: int) -> tuple[Dict[str, Any], int]:
    """Retrieve a specific user by their ID."""
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} fetching user with ID {user_id}")
    result: Dict[str, Any] = await account_controller.get_clean_user_by_id(user_id)
    return jsonify(result), result.get("status", 200)

@account_api.route("/users/<int:user_id>", methods=["GET"])
@require_access(specific_roles=["admin"])
async def get_user_by_id(user_id: int) -> tuple[Dict[str, Any], int]:
    """Retrieve a specific user by their ID."""
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} fetching user with ID {user_id}")
    result: Dict[str, Any] = await account_controller.get_user_by_id(user_id)
    return jsonify(result), result.get("status", 200)

# Mass verify users
@account_api.route("/users/verify", methods=["POST"])
@require_access(minimum_role="executive")
async def verify_user() -> tuple[Dict[str, Any], int]:
    """Update a user's role by user ID."""
    uncleaned_data = await request.get_json()
    data = await sanitize_request(uncleaned_data)
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} mass verifying users using data: {data}")
    result: Dict[str, Any] = await account_controller.mass_verify_users(data)
    return jsonify(result), result.get("status", 200)

# Mass delete users
@account_api.route("/users/delete", methods=["POST"])
@require_access(minimum_role="admin")
async def delete_users() -> tuple[Dict[str, Any], int]:
    """Delete multiple users by user ID."""
    uncleaned_data = await request.get_json()
    data = await sanitize_request(uncleaned_data)
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} mass deleting users using data: {data}")
    result: Dict[str, Any] = await account_controller.mass_delete_users(data)
    return jsonify(result), result.get("status", 200)


# # Update a user's profile 
# @account_api.route("/users/profile/<int:user_id>", methods=["PUT"])
# @require_access(minimum_role="member")
# async def update_user_profile(user_id: str) -> tuple[Dict[str, Any], int]:
#     """Update a user's profile by user ID."""
#     data: Dict[str, Any] = await request.get_json()
#     requester_id = g.user.get("user_id", "Unknown")
#     current_app.logger.info(f"User {requester_id} updating profile for user with ID {user_id} using data: {data}")
#     result: Dict[str, Any] = await account_controller.update_user_profile(user_id, data)
#     return jsonify(result), result.get("status", 200)

@account_api.route("/validate", methods=["GET"])
@require_access(minimum_role="unverified")
async def validate_token() -> tuple[Dict[str, Any], int]:
    """Validate a JWT token and return an updated one and user object (extended expiry)."""
    if not g.user:
        return jsonify({"error": "Invalid or expired token"}), 401

    result = await account_controller.refresh_user(g.user)

    return jsonify(result), 200

@account_api.route("/delete", methods=["DELETE"])
@require_access(minimum_role="unverified")
async def delete_user_g() -> tuple[Dict[str, Any], int]:
    """Delete a user account."""
    if not g.user:
        return jsonify({"error": "Invalid or expired token"}), 401

    result = await account_controller.delete_user(int(g.user["user_id"]))

    return jsonify(result), 200