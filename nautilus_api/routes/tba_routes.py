"""
TBA API proxy routes.
"""
from quart import Blueprint, jsonify, request, current_app
from typing import Dict, Any
from nautilus_api.services import tba_service
from nautilus_api.utils.errors import BadRequestError, format_error_response, TBAError


tba_api = Blueprint('tba_api', __name__)


@tba_api.errorhandler(Exception)
async def handle_exception(e: Exception) -> tuple[Dict[str, Any], int]:
    """Handle exceptions and return JSON errors."""
    if isinstance(e, BadRequestError):
        return jsonify(e.to_dict()), e.status_code
    elif isinstance(e, TBAError):
        return jsonify(e.to_dict()), e.status_code
    
    current_app.logger.error(f"Unhandled exception in TBA routes: {e}")
    return jsonify(format_error_response("INTERNAL_ERROR", "An unexpected error occurred")), 500


@tba_api.route("/event_summary", methods=["GET"])
async def get_event_summary() -> tuple[Dict[str, Any], int]:
    """
    Get aggregated TBA event summary for a team.
    
    Query Parameters:
        event: Event key (e.g., "2024casd")
        team: Team number (e.g., "254")
    
    Returns:
        TbaEventSummary JSON
    """
    event_key = request.args.get("event")
    team_number = request.args.get("team")
    
    # Validate inputs
    if not event_key:
        raise BadRequestError("Missing required parameter: event")
    if not team_number:
        raise BadRequestError("Missing required parameter: team")
    
    # Validate team number is numeric
    if not team_number.isdigit():
        raise BadRequestError("Team number must be numeric")
    
    current_app.logger.info(f"Fetching TBA event summary for team {team_number} at {event_key}")
    
    try:
        summary = await tba_service.get_event_summary(event_key, team_number)
        return jsonify(summary.model_dump()), 200
    except TBAError as e:
        # Re-raise TBA errors to be handled by error handler
        raise
    except Exception as e:
        current_app.logger.error(f"Error fetching TBA event summary: {e}")
        raise TBAError(f"Failed to fetch TBA data: {str(e)}")
