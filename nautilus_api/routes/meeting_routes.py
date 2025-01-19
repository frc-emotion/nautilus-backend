import jwt
from quart import Blueprint, jsonify, g, request, current_app
from typing import Optional, Any, Dict
from nautilus_api.config import Config
from nautilus_api.controllers import attendance_controller
from nautilus_api.routes.utils import require_access, sanitize_request

meeting_api = Blueprint('meeting_api', __name__)

# @meeting_api.before_request
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

@meeting_api.errorhandler(Exception)
async def handle_exception(e: Exception) -> tuple[Dict[str, str], int]:
    """Handle unexpected errors and log the exception."""
    if type(e).__name__ == "RateLimitExceeded":
        # Retry after
        headers = e.get_headers()
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429, headers

    user_id = g.user.get("user_id") if g.user else "Unknown"
    current_app.logger.error(f"Unhandled exception for user {user_id}: {e}")
    return jsonify({"error": "An unexpected error occurred. Please report this immediately!"}), 500

@meeting_api.route("/", methods=["POST"])
@require_access(minimum_role="leadership")
async def create_meeting() -> tuple[Dict[str, Any], int]:
    """Create a new meeting with provided data."""
    uncleaned_data = await request.get_json()
    data = await sanitize_request(uncleaned_data)
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} creating a new meeting with data: {data}")
    data["created_by"] = requester_id
    result: Dict[str, Any] = await attendance_controller.create_meeting(data)
    return jsonify(result), result.get("status", 200)

@meeting_api.route("/<int:meeting_id>", methods=["PUT"])
@require_access(minimum_role="executive")
async def update_meeting(meeting_id: str) -> tuple[Dict[str, Any], int]:
    """Update meeting information by meeting ID."""
    uncleaned_data = await request.get_json()
    data = await sanitize_request(uncleaned_data)
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} updating meeting with ID {meeting_id} using data: {data}")
    result: Dict[str, Any] = await attendance_controller.update_meeting(meeting_id, data)
    return jsonify(result), result.get("status", 200)

@meeting_api.route("/<int:meeting_id>", methods=["DELETE"])
@require_access(minimum_role="admin")
async def delete_meeting(meeting_id: str) -> tuple[Dict[str, Any], int]:
    """Delete a meeting by meeting ID."""
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} deleting meeting with ID {meeting_id}")
    result: Dict[str, Any] = await attendance_controller.delete_meeting(meeting_id)
    return jsonify(result), result.get("status", 200)

@meeting_api.route("/", methods=["GET"])
@require_access(minimum_role="leadership")
async def get_all_meetings() -> tuple[Dict[str, Any], int]:
    """Retrieve all meetings."""
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} fetching all meetings")
    result: Dict[str, Any] = await attendance_controller.get_all_meetings()
    return jsonify(result), result.get("status", 200)

@meeting_api.route("/<int:meeting_id>", methods=["GET"])
@require_access(minimum_role="leadership")
async def get_meeting_by_id(meeting_id: str) -> tuple[Dict[str, Any], int]:
    """Retrieve a specific meeting by its ID."""
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} fetching meeting with ID {meeting_id}")
    result: Dict[str, Any] = await attendance_controller.get_meeting_by_id(meeting_id)
    return jsonify(result), result.get("status", 200)

@meeting_api.route("/<int:meeting_id>/info", methods=["GET"])
@require_access(minimum_role="member")
async def get_clean_meeting_by_id(meeting_id: str) -> tuple[Dict[str, Any], int]:
    """Retrieve a specific meeting by its ID without sensitive information."""
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} fetching meeting with ID {meeting_id}")
    result: Dict[str, Any] = await attendance_controller.get_clean_meeting_by_id(meeting_id)
    return jsonify(result), result.get("status", 200)

@meeting_api.route("/info", methods=["GET"])
@require_access(minimum_role="member")
async def get_all_clean_meetings() -> tuple[Dict[str, Any], int]:
    """Retrieve all meetings without sensitive information."""
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} fetching all meetings")
    result: Dict[str, Any] = await attendance_controller.get_all_clean_meetings()
    return jsonify(result), result.get("status", 200)