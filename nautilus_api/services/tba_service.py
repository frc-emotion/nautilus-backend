"""
Service for aggregating TBA data into event summaries.
"""
from typing import Optional
from quart import current_app
from nautilus_api import tba_client
from nautilus_api.models.schemas import TbaEventSummary, TbaRecord, TbaRanking


async def get_event_summary(event_key: str, team_number: str) -> TbaEventSummary:
    """
    Aggregate TBA data for a team at an event into a single summary.
    
    Args:
        event_key: Event key (e.g., "2024casd")
        team_number: Team number (e.g., "254")
    
    Returns:
        TbaEventSummary with aggregated data from multiple TBA endpoints
    """
    team_key = f"frc{team_number}"
    
    # Initialize response with defaults
    team_name: Optional[str] = None
    matches_played: Optional[int] = None
    record: Optional[TbaRecord] = None
    opr: Optional[float] = None
    dpr: Optional[float] = None
    ccwm: Optional[float] = None
    ranking: Optional[TbaRanking] = None
    
    # Fetch team info for name
    try:
        team_info = await tba_client.get_team_info(team_number)
        if team_info:
            team_name = team_info.get("nickname")
    except Exception as e:
        current_app.logger.warning(f"Failed to fetch team info: {e}")
    
    # Fetch OPR/DPR/CCWM
    try:
        oprs_data = await tba_client.get_event_oprs(event_key)
        if oprs_data:
            opr = oprs_data.get("oprs", {}).get(team_key)
            dpr = oprs_data.get("dprs", {}).get(team_key)
            ccwm = oprs_data.get("ccwms", {}).get(team_key)
    except Exception as e:
        current_app.logger.warning(f"Failed to fetch OPRs: {e}")
    
    # Fetch rankings
    try:
        rankings_data = await tba_client.get_event_rankings(event_key)
        if rankings_data and "rankings" in rankings_data:
            # Find this team's ranking
            for rank_entry in rankings_data["rankings"]:
                if rank_entry.get("team_key") == team_key:
                    # Extract record
                    rank_record = rank_entry.get("record", {})
                    wins = rank_record.get("wins", 0)
                    losses = rank_record.get("losses", 0)
                    ties = rank_record.get("ties", 0)
                    total_matches = wins + losses + ties
                    winrate_pct = (wins / total_matches * 100) if total_matches > 0 else 0.0
                    
                    record = TbaRecord(
                        wins=wins,
                        losses=losses,
                        ties=ties,
                        winratePct=round(winrate_pct, 2)
                    )
                    
                    matches_played = total_matches
                    
                    # Extract ranking
                    ranking = TbaRanking(
                        rank=rank_entry.get("rank", 0),
                        rp=rank_entry.get("sort_orders", [None])[0],  # Usually first sort order is RP
                        dq=rank_entry.get("dq")
                    )
                    break
    except Exception as e:
        current_app.logger.warning(f"Failed to fetch rankings: {e}")
    
    # Optionally fetch matches to get count if not in rankings
    if matches_played is None:
        try:
            matches = await tba_client.get_team_event_matches(team_number, event_key)
            if matches:
                # Only count qualification and playoff matches (not practice)
                competitive_matches = [
                    m for m in matches 
                    if m.get("comp_level") in ["qm", "qf", "sf", "f"]
                ]
                matches_played = len(competitive_matches)
                
                # Compute record from matches if not from rankings
                if record is None:
                    wins = 0
                    losses = 0
                    ties = 0
                    for match in competitive_matches:
                        # Already filtered above
                        
                        # Find this team's alliance
                        alliances = match.get("alliances", {})
                        team_alliance = None
                        if team_key in alliances.get("red", {}).get("team_keys", []):
                            team_alliance = "red"
                        elif team_key in alliances.get("blue", {}).get("team_keys", []):
                            team_alliance = "blue"
                        
                        if team_alliance:
                            winning_alliance = match.get("winning_alliance")
                            if winning_alliance == team_alliance:
                                wins += 1
                            elif winning_alliance == "":
                                ties += 1
                            else:
                                losses += 1
                    
                    total = wins + losses + ties
                    winrate_pct = (wins / total * 100) if total > 0 else 0.0
                    record = TbaRecord(
                        wins=wins,
                        losses=losses,
                        ties=ties,
                        winratePct=round(winrate_pct, 2)
                    )
        except Exception as e:
            current_app.logger.warning(f"Failed to fetch matches: {e}")
    
    # Create and return summary
    summary = TbaEventSummary(
        eventKey=event_key,
        teamNumber=team_number,
        teamName=team_name,
        matchesPlayed=matches_played,
        record=record,
        opr=round(opr, 2) if opr is not None else None,
        dpr=round(dpr, 2) if dpr is not None else None,
        ccwm=round(ccwm, 2) if ccwm is not None else None,
        ranking=ranking
    )
    
    return summary
