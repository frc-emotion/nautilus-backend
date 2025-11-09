import json
import jwt
from quart import Blueprint, jsonify, g, request, current_app
from typing import Optional, Any, Dict
from nautilus_api.config import Config
from nautilus_api.controllers import scouting_controller
from nautilus_api.routes.utils import require_access, sanitize_request

scouting_api = Blueprint('scouting_api', __name__)

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

@scouting_api.errorhandler(Exception)
async def handle_exception(e: Exception) -> tuple[Dict[str, str], int]:
    """Handle unexpected errors and log the exception."""
    if type(e).__name__ == "RateLimitExceeded":
        # Retry after
        headers = e.get_headers()
        return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429, headers

    user_id = g.user.get("user_id") if g.user else "Unknown"
    current_app.logger.error(f"Unhandled exception for user {user_id}: {e}")
    return jsonify({"error": "An unexpected error occurred. Please report this immediately!"}), 500

@scouting_api.route("/form", methods=["POST"])
@require_access(minimum_role="member")
async def scouting_form() -> tuple[Dict[str, Any], int]:
    """Create a new meeting with provided data."""
    uncleaned_data = await request.get_json()
    data = await sanitize_request(uncleaned_data)
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} submitting a new scouting form with data: {data}")
    await scouting_controller.submit_data(data, "scouting")
    return {"yes":"yes"}, 200

@scouting_api.route("/pitform", methods = ["POST"])
@require_access(minimum_role = "member")
async def pitscouting_form() -> tuple[Dict[str, Any], int]:
    """Create a new pit scouting form with provided data."""
    uncleaned_data = await request.get_json()
    data = await sanitize_request(uncleaned_data)
    requester_id = g.user.get("user_id", "Unknown")
    current_app.logger.info(f"User {requester_id} submitting a new pitscouting form with data: {data}")
    await scouting_controller.submit_data(data, "pitscouting")
    return {"yes": "yes"}, 200



def load_competitions():
    with open("competitions.json", "r") as file:
        return json.load(file)

@scouting_api.route("/competitions", methods=["GET"])
@require_access(minimum_role="member")
async def get_competitions() -> tuple[Dict[str, Any], int]:
    """
    Get list of all competitions.
    
    Returns:
        List of competition objects with label and value
    """
    return load_competitions(), 200


@scouting_api.route("/team_aggregation", methods=["GET"])
@require_access(minimum_role="member")
async def get_team_aggregation() -> tuple[Dict[str, Any], int]:
    """
    Get aggregated scouting data for a team at a competition.
    
    Query Parameters:
        competition: Competition ID (e.g., "sdr-practice-2025")
        team: Team number (e.g., "254")
    
    Returns:
        TeamScoutingAggregation JSON
    """
    from nautilus_api.services import scouting_service
    from nautilus_api.utils.errors import BadRequestError
    
    competition = request.args.get("competition")
    team = request.args.get("team")
    
    # Validate inputs
    if not competition:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing required parameter: competition"}}), 400
    if not team:
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Missing required parameter: team"}}), 400
    
    # Validate team is numeric
    if not str(team).replace("-", "").isdigit():
        return jsonify({"error": {"code": "BAD_REQUEST", "message": "Team number must be numeric"}}), 400
    
    current_app.logger.info(f"Fetching scouting aggregation for team {team} at {competition}")
    
    try:
        aggregation = await scouting_service.get_team_aggregation(competition, str(team))
        return jsonify(aggregation.model_dump()), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching team aggregation: {e}")
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "Failed to fetch scouting data"}}), 500