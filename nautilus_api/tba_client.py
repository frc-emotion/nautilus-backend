"""
The Blue Alliance (TBA) API client with caching and error handling.
"""
import aiohttp
import asyncio
from typing import Optional, Dict, Any, List
from quart import current_app
from nautilus_api.config import Config
from nautilus_api.utils.cache import cached
from nautilus_api.utils.errors import TBAError, TBATimeoutError, TBARateLimitError


TBA_BASE_URL = "https://www.thebluealliance.com/api/v3"
TBA_TIMEOUT = 10  # seconds


async def _make_tba_request(endpoint: str) -> Optional[Dict[str, Any]]:
    """
    Make a request to TBA API with proper headers and error handling.
    
    Args:
        endpoint: API endpoint path (e.g., "/event/2024casd/oprs")
    
    Returns:
        JSON response as dict, or None if error
    
    Raises:
        TBAError: On API errors
        TBATimeoutError: On timeout
        TBARateLimitError: On rate limit
    """
    url = f"{TBA_BASE_URL}{endpoint}"
    headers = {
        "X-TBA-Auth-Key": Config.TBA_AUTH_KEY,
        "Accept": "application/json"
    }
    
    try:
        timeout = aiohttp.ClientTimeout(total=TBA_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    current_app.logger.warning(f"TBA rate limit hit for {endpoint}")
                    raise TBARateLimitError()
                elif response.status == 404:
                    current_app.logger.warning(f"TBA resource not found: {endpoint}")
                    return None
                else:
                    error_text = await response.text()
                    current_app.logger.error(f"TBA API error {response.status}: {error_text}")
                    raise TBAError(f"TBA API returned status {response.status}")
    
    except asyncio.TimeoutError:
        current_app.logger.error(f"TBA API timeout for {endpoint}")
        raise TBATimeoutError()
    except aiohttp.ClientError as e:
        current_app.logger.error(f"TBA API client error: {e}")
        raise TBAError(f"TBA API client error: {str(e)}")


@cached(ttl_seconds=Config.CACHE_TTL_SECONDS)
async def get_event_oprs(event_key: str) -> Optional[Dict[str, Any]]:
    """
    Get OPR, DPR, and CCWM data for an event.
    
    Args:
        event_key: Event key (e.g., "2024casd")
    
    Returns:
        Dict with keys: "oprs", "dprs", "ccwms" mapping team keys to values
        Example: {"oprs": {"frc254": 89.5, ...}, "dprs": {...}, "ccwms": {...}}
    """
    endpoint = f"/event/{event_key}/oprs"
    return await _make_tba_request(endpoint)


@cached(ttl_seconds=Config.CACHE_TTL_SECONDS)
async def get_event_rankings(event_key: str) -> Optional[Dict[str, Any]]:
    """
    Get event rankings.
    
    Args:
        event_key: Event key (e.g., "2024casd")
    
    Returns:
        Dict with "rankings" key containing list of ranking entries
    """
    endpoint = f"/event/{event_key}/rankings"
    return await _make_tba_request(endpoint)


@cached(ttl_seconds=Config.CACHE_TTL_SECONDS)
async def get_team_info(team_number: str) -> Optional[Dict[str, Any]]:
    """
    Get team information.
    
    Args:
        team_number: Team number (e.g., "254")
    
    Returns:
        Dict with team info including "nickname"
    """
    endpoint = f"/team/frc{team_number}"
    return await _make_tba_request(endpoint)


@cached(ttl_seconds=Config.CACHE_TTL_SECONDS)
async def get_team_event_matches(team_number: str, event_key: str) -> Optional[List[Dict[str, Any]]]:
    """
    Get all matches for a team at an event.
    
    Args:
        team_number: Team number (e.g., "254")
        event_key: Event key (e.g., "2024casd")
    
    Returns:
        List of match objects
    """
    endpoint = f"/team/frc{team_number}/event/{event_key}/matches"
    return await _make_tba_request(endpoint)


@cached(ttl_seconds=Config.CACHE_TTL_SECONDS)
async def get_event_matches(event_key: str) -> Optional[List[Dict[str, Any]]]:
    """
    Get all matches for an event with full score breakdowns.
    
    Args:
        event_key: Event key (e.g., "2024casd")
    
    Returns:
        List of match objects with score_breakdown data
    """
    endpoint = f"/event/{event_key}/matches"
    return await _make_tba_request(endpoint)
