import jwt
from quart import Blueprint, jsonify, g, request, current_app
from nautilus_api.config import Config
from nautilus_api.controllers import notification_controller
from nautilus_api.routes.utils import require_access
from typing import Optional, Any, Dict

notification_api = Blueprint("notification_api", __name__)

@notification_api.before_request
def authenticate_user() -> None:
    """Authenticate user using JWT token in the Authorization header."""
    auth_header: Optional[str] = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token: str = auth_header.split(" ")[1]
        try:
            decoded_token: Dict[str, Any] = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
            g.user = decoded_token
            current_app.logger.info(f"User {g.user.get('user_id')} authenticated successfully")
        except jwt.ExpiredSignatureError:
            g.user = None
            current_app.logger.warning("Expired token provided for authentication")
        except jwt.InvalidTokenError:
            g.user = None
            current_app.logger.warning("Invalid token provided for authentication")
    else:
        g.user = None
        current_app.logger.warning("No token provided for authentication")

@notification_api.errorhandler(Exception)
async def handle_exception(e: Exception) -> Any:
    """Handle unexpected exceptions by logging the error and returning a generic error message."""
    current_app.logger.error(f"Unhandled exception: {e}")
    return jsonify({"error": "An unexpected error occurred. Please report this immediately!"}), 500

@notification_api.route("/", methods=["DELETE"])
@require_access(minimum_role="member")
async def delete_notification_token() -> tuple[Dict[str, Any], int]:
    """Delete a user's notification token."""
    user_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {user_id} deleting notification token")
    result: Dict[str, Any] = await notification_controller.delete_notification_token(user_id)
    return jsonify(result), result.get("status", 200)

# Trigger notification
@notification_api.route("/trigger", methods=["POST"])
@require_access(minimum_role="executive")
async def trigger_notification() -> tuple[Dict[str, Any], int]:
    """Trigger a notification for a user."""
    data: Dict[str, Any] = await request.get_json()
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} triggering notification with data: {data}")
    result: Dict[str, Any] = await notification_controller.trigger_notification(data)
    return jsonify(result), result.get("status", 200)

@notification_api.route("/", methods=["PUT"])
@require_access(minimum_role="member")
async def update_notification_token() -> tuple[Dict[str, Any], int]:
    """Update a user's notification token."""
    data: Dict[str, Any] = await request.get_json()
    user_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {user_id} updating notification token with data: {data}")
    result: Dict[str, Any] = await notification_controller.update_notification_token(user_id, data)
    return jsonify(result), result.get("status", 200)