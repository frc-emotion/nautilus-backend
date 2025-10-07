import json
import jwt
from quart import Blueprint, jsonify, g, request, current_app
from typing import Optional, Any, Dict
from nautilus_api.config import Config
from nautilus_api.controllers import pitscouting_controller  
from nautilus_api.routes.utils import require_access, sanitize_request

pitscouting_api = Blueprint('pitscouting_api', __name__)

@pitscouting_api.errorhandler(Exception)
async def handle_exception(e: Exception) -> tuple[Dict[str, str], int]:
    if type(e).__name__ == "RateLimitExceeded":
        headers = e.get_headers()
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429, headers

    user_id = g.user.get("user_id") if g.user else "Unknown"
    current_app.logger.error(f"Unhandled exception for user {user_id}: {e}")
    return jsonify({"error": "An unexpected error occurred. Please report this immediately!"}), 500

@pitscouting_api.route("/form", methods=["POST"])
@require_access(minimum_role="member")
async def pitscouting_form() -> tuple[Dict[str, Any], int]:
    """Create a new pit scouting form with provided data."""
    uncleaned_data = await request.get_json()
    data = await sanitize_request(uncleaned_data)
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} submitting a new pitscouting form with data: {data}")
    await pitscouting_controller.submit_data(data)
    return {"yes": "yes"}, 200

def load_competitions():
    with open("competitions.json", "r") as file:
        return json.load(file)

@pitscouting_api.route("competitions", methods=["GET"])
@require_access(minimum_role="member")
async def get_competitions() -> tuple[Dict[str, Any], int]:
    return load_competitions()
