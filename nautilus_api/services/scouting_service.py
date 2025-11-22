"""
Scouting service for data aggregation and analysis.
"""
from typing import List, Dict, Any, Optional
from quart import current_app
from nautilus_api.config import Config
from nautilus_api.models.schemas import (
    TeamScoutingAggregation,
    ScoutingSample,
    ScoutingSampleAuto,
    ScoutingSampleTeleop,
    LevelPoints,
    LevelPercentages,
    ClimbCounts
)


async def get_collection(collection_name: str):
    """Helper to retrieve a MongoDB collection from the current app's database."""
    return current_app.db[collection_name]


async def submit(data, collection_name):
    """Submit scouting data to MongoDB."""
    scouting_collection = await get_collection(collection_name)
    print(await scouting_collection.insert_one(data))
    return


def compute_match_points(match_data: Dict[str, Any], scoring_config: Dict[str, Any]) -> float:
    """
    Compute total points for a match using the scoring configuration.
    
    Args:
        match_data: Match document from MongoDB
        scoring_config: Scoring configuration from Config.SCORING_CONFIG
    
    Returns:
        Total points for the match
    """
    points = 0.0
    
    # Auto phase coral points
    auto_coral = match_data.get("auto", {}).get("coral", [0, 0, 0, 0])
    for i, count in enumerate(auto_coral[:4]):  # Ensure max 4 levels
        points += count * scoring_config["auto"]["coral_points_per_level"][i]
    
    # Auto phase algae points
    auto_algae = match_data.get("auto", {}).get("algae", [0, 0])
    points += auto_algae[0] * scoring_config["auto"]["algae_points"]["ground"]
    if len(auto_algae) > 1:
        points += auto_algae[1] * scoring_config["auto"]["algae_points"]["net"]
    
    # Teleop phase coral points
    teleop_coral = match_data.get("teleop", {}).get("coral", [0, 0, 0, 0])
    for i, count in enumerate(teleop_coral[:4]):
        points += count * scoring_config["teleop"]["coral_points_per_level"][i]
    
    # Teleop phase algae points
    teleop_algae = match_data.get("teleop", {}).get("algae", [0, 0])
    points += teleop_algae[0] * scoring_config["teleop"]["algae_points"]["ground"]
    if len(teleop_algae) > 1:
        points += teleop_algae[1] * scoring_config["teleop"]["algae_points"]["net"]
    
    # Climb points
    climb = match_data.get("climb", "PARK")
    # Normalize unknown climb types to PARK
    if climb not in scoring_config["climb_points"]:
        climb = "PARK"
    points += scoring_config["climb_points"].get(climb, 0)
    
    return points


def compute_level_points(match_data: Dict[str, Any], scoring_config: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute points attributed to each coral level (L1-L4) for a match.
    Only coral points count toward level attribution, not algae or climb.
    
    Args:
        match_data: Match document from MongoDB
        scoring_config: Scoring configuration
    
    Returns:
        Dict with keys L1, L2, L3, L4 and their point contributions
    """
    level_points = {"L1": 0.0, "L2": 0.0, "L3": 0.0, "L4": 0.0}
    
    # Auto coral
    auto_coral = match_data.get("auto", {}).get("coral", [0, 0, 0, 0])
    for i, count in enumerate(auto_coral[:4]):
        level_key = f"L{i + 1}"
        level_points[level_key] += count * scoring_config["auto"]["coral_points_per_level"][i]
    
    # Teleop coral
    teleop_coral = match_data.get("teleop", {}).get("coral", [0, 0, 0, 0])
    for i, count in enumerate(teleop_coral[:4]):
        level_key = f"L{i + 1}"
        level_points[level_key] += count * scoring_config["teleop"]["coral_points_per_level"][i]
    
    return level_points


async def get_team_aggregation(
    competition: str,
    team_number: str,
    scoring_config: Optional[Dict[str, Any]] = None
) -> TeamScoutingAggregation:
    """
    Aggregate scouting data for a specific team at a competition.
    
    Args:
        competition: Competition ID (e.g., "sdr-practice-2025")
        team_number: Team number (e.g., "254" or "2658")
        scoring_config: Scoring configuration (defaults to Config.SCORING_CONFIG)
    
    Returns:
        TeamScoutingAggregation with computed statistics
    """
    if scoring_config is None:
        scoring_config = Config.SCORING_CONFIG
    
    # Get scouting collection
    scouting_collection = await get_collection("scouting")
    
    # Query for all matches for this team at this competition
    query = {
        "competition": competition,
        "teamNumber": str(team_number)  # Ensure string comparison
    }
    
    cursor = scouting_collection.find(query)
    matches = await cursor.to_list(length=None)
    
    # Initialize aggregation variables
    matches_scouted = len(matches)
    total_points = 0.0
    level_points_total = {"L1": 0.0, "L2": 0.0, "L3": 0.0, "L4": 0.0}
    climb_counts = {"PARK": 0, "SHALLOW_CAGE": 0, "DEEP_CAGE": 0}
    samples: List[ScoutingSample] = []
    
    # Process each match
    for match in matches:
        # Normalize arrays to ensure proper length
        auto_coral = match.get("auto", {}).get("coral", [0, 0, 0, 0])
        auto_coral = (auto_coral + [0, 0, 0, 0])[:4]  # Pad and truncate to 4
        
        auto_algae = match.get("auto", {}).get("algae", [0, 0])
        auto_algae = (auto_algae + [0, 0])[:2]  # Pad and truncate to 2
        
        teleop_coral = match.get("teleop", {}).get("coral", [0, 0, 0, 0])
        teleop_coral = (teleop_coral + [0, 0, 0, 0])[:4]
        
        teleop_algae = match.get("teleop", {}).get("algae", [0, 0])
        teleop_algae = (teleop_algae + [0, 0])[:2]
        
        # Normalize climb enum
        climb = match.get("climb", "PARK")
        if climb not in ["PARK", "SHALLOW_CAGE", "DEEP_CAGE"]:
            current_app.logger.warning(f"Unknown climb type '{climb}' for match {match.get('matchNumber')}, defaulting to PARK")
            climb = "PARK"
        
        # Compute points for this match
        match_points = compute_match_points(match, scoring_config)
        total_points += match_points
        
        # Compute level points for this match
        level_points = compute_level_points(match, scoring_config)
        for level in ["L1", "L2", "L3", "L4"]:
            level_points_total[level] += level_points[level]
        
        # Count climb type
        climb_counts[climb] += 1
        
        # Create sample object
        sample = ScoutingSample(
            matchNumber=str(match.get("matchNumber", "")),
            won=match.get("won", 0),
            comments=match.get("comments"),
            defensive=match.get("defensive"),
            brokeDown=match.get("brokeDown"),
            rankingPoints=match.get("rankingPoints"),
            auto=ScoutingSampleAuto(coral=auto_coral, algae=auto_algae),
            teleop=ScoutingSampleTeleop(coral=teleop_coral, algae=teleop_algae),
            climb=climb,
            points=match_points
        )
        samples.append(sample)
    
    # Compute averages and percentages
    avg_ppg_scouted = total_points / matches_scouted if matches_scouted > 0 else 0.0
    
    # Compute level percentages
    total_level_points = sum(level_points_total.values())
    if total_level_points > 0:
        level_pct = {
            "L1": (level_points_total["L1"] / total_level_points) * 100,
            "L2": (level_points_total["L2"] / total_level_points) * 100,
            "L3": (level_points_total["L3"] / total_level_points) * 100,
            "L4": (level_points_total["L4"] / total_level_points) * 100,
        }
    else:
        level_pct = {"L1": 0.0, "L2": 0.0, "L3": 0.0, "L4": 0.0}
    
    # Create aggregation response
    aggregation = TeamScoutingAggregation(
        competition=competition,
        teamNumber=str(team_number),
        matchesScouted=matches_scouted,
        totalPoints=round(total_points, 2),
        avgPpgScouted=round(avg_ppg_scouted, 2),
        levelPoints=LevelPoints(**{k: round(v, 2) for k, v in level_points_total.items()}),
        levelPct=LevelPercentages(**{k: round(v, 2) for k, v in level_pct.items()}),
        climbCounts=ClimbCounts(**climb_counts),
        samples=samples
    )
    
    return aggregation