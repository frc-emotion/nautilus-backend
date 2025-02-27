import jwt
from quart import Blueprint, jsonify, g, request, current_app
from typing import Optional, Any, Dict
from nautilus_api.config import Config
from nautilus_api.controllers import attendance_controller
from nautilus_api.routes.utils import require_access, sanitize_request

attendance_api = Blueprint('attendance_api', __name__)

# @attendance_api.before_request
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

@attendance_api.errorhandler(Exception)
async def handle_exception(e: Exception) -> tuple[Dict[str, str], int]:
    """Handle unexpected errors and log the exception."""
    if type(e).__name__ == "RateLimitExceeded":
        # Retry after
        headers = e.get_headers()
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429, headers
    
    user_id = g.user.get("user_id") if g.user else "Unknown"
    current_app.logger.error(f"Unhandled exception for user {user_id}: {e}")
    return jsonify({"error": "An unexpected error occurred. Please report this immediately!"}), 500

@attendance_api.route("/hours/<string:user_id>", methods=["GET"])
@require_access(minimum_role="leadership")
async def get_attendance_hours_by_id(user_id: str) -> tuple[Dict[str, Any], int]:
    """Retrieve attendance hours for a specific user by their ID."""
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} fetching attendance hours for user_id: {user_id}")
    result: Dict[str, Any] = await attendance_controller.get_attendance_hours(user_id)
    return jsonify(result), result.get("status", 200)

@attendance_api.route("/remove", methods=["DELETE"])
@require_access(minimum_role="advisor")
async def remove_attendance() -> tuple[Dict[str, Any], int]:
    """Remove attendance records based on provided data."""
    uncleaned_data = await request.get_json()
    data = await sanitize_request(uncleaned_data)
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} removing attendance with data: {data}")
    result: Dict[str, Any] = await attendance_controller.remove_attendance(data)
    return jsonify(result), result.get("status", 200)

@attendance_api.route("/modify", methods=["PUT"])
@require_access(specific_roles=["advisor"])
async def modify_attendance() -> tuple[Dict[str, Any], int]:
    """Modify attendance records based on provided data."""
    uncleaned_data = await request.get_json()
    data = await sanitize_request(uncleaned_data)
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} modifying attendance with data: {data}")
    result: Dict[str, Any] = await attendance_controller.modify_attendance(data)
    return jsonify(result), result.get("status", 200)


@attendance_api.route("/log", methods=["POST"])
@require_access(minimum_role="member")
async def log_attendance() -> Any:
    """Log attendance data for the authenticated user."""
    uncleaned_data = await request.get_json()
    data = await sanitize_request(uncleaned_data)
    user_id: Optional[int] = g.user.get("user_id")
    current_app.logger.info(f"User {user_id} logging attendance with data: {data}")
    
    result: Dict[str, Any] = await attendance_controller.log_attendance(data, user_id)
    return jsonify(result), result.get("status", 200)

@attendance_api.route("/hours", methods=["GET"])
@require_access(minimum_role="member")
async def get_attendance_hours() -> Any:
    """Retrieve total attendance hours for the authenticated user."""
    user_id: Optional[int] = g.user.get("user_id")
    current_app.logger.info(f"Fetching total hours for user {user_id}")
    
    result: Dict[str, Any] = await attendance_controller.get_attendance_hours(user_id)
    return jsonify(result), result.get("status", 200)

@attendance_api.route("/log", methods=["GET"])
@require_access(minimum_role="member")
async def get_attendance_logs() -> Any:
    """Retrieve attendance logs for the authenticated user."""
    user_id: Optional[int] = g.user.get("user_id")
    current_app.logger.info(f"Fetching attendance logs for user {user_id}")
    
    result: Dict[str, Any] = await attendance_controller.get_attendance_by_user_id(user_id)
    return jsonify(result), result.get("status", 200)

@attendance_api.route("/all", methods=["GET"])
@require_access(specific_roles=["advisor", "executive", "admin"])
async def get_all_attendance() -> Any:
    """Retrieve attendance hours per term and year for all users."""
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} fetching all users attendance hours")

    result: Dict[str, Any] = await attendance_controller.get_all_attendance()
    return jsonify(result), result.get("status", 200)

@attendance_api.route("/years", methods=["GET"])
@require_access(minimum_role="unverified")
async def get_attendance_years() -> Any:
    """Retrieve all years with attendance logs for the authenticated user."""
    user_id: Optional[int] = g.user.get("user_id")
    current_app.logger.info(f"Fetching attendance years for user {user_id}")
    
    result: Dict[str, Any] = Config.SCHOOL_YEAR
    return jsonify(result), result.get("status", 200)


@attendance_api.route("/manual/add", methods=["POST"])
@require_access(specific_roles=["admin", "advisor"])
async def add_manual_attendance():
    uncleaned_data = await request.get_json()
    data = await sanitize_request(uncleaned_data)
    result = await attendance_controller.add_manual_attendance(data)
    return jsonify(result), result.get("status", 200)