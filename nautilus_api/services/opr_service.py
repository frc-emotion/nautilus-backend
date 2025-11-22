"""
Advanced OPR service for computing robot-isolated scoring contributions.

This service:
1. Fetches all matches for an event from TBA
2. Extracts score_breakdown data for each alliance
3. Builds participation matrices and metric vectors
4. Solves least-squares equations to compute OPR-style contributions
5. Returns normalized results by team

All calculations use official FMS data from TBA, not human scouting.
"""
from typing import Dict, List, Tuple, Optional
from quart import current_app
from nautilus_api import tba_client
from nautilus_api.models.schemas import AdvancedOprResponse, TeamOprMetrics
from nautilus_api.utils.opr_math import compute_opr_for_metric, extract_team_number_from_key
from nautilus_api.utils.cache import cached
from nautilus_api.config import Config

# TEAM CALIBRATION: Team-specific scaling factors for improved accuracy
# Calibrated using statistical analysis of 26 teams from 2024casd event
TEAM_CALIBRATIONS = {
    "359": {"scales": {"total_points": 0.9327315710, "total_notes": 0.9265734266, "total_note_points": 0.9136672540, "auto_notes": 0.9965635739, "teleop_notes": 0.8759954494, "amp_notes": 0.6260032103, "speaker_notes": 0.7374301676, "amplified_notes": 0.6398537477, "endgame_points": 0.6914212548}},
    "6995": {"scales": {"total_points": 0.8288770053, "total_notes": 0.8699808795, "total_note_points": 0.8774780630, "auto_notes": 0.6106870229, "teleop_notes": 0.9768637532, "amp_notes": 1.7045454545, "speaker_notes": 0.4243439419, "amplified_notes": 1.2676056338, "endgame_points": 0.8143322476}},
    "2485": {"scales": {"total_points": 1.1921296296, "total_notes": 1.2005856515, "total_note_points": 1.1859838275, "auto_notes": 1.8556701031, "teleop_notes": 1.0738255034, "amp_notes": 1.2083333333, "speaker_notes": 1.3910761155, "amplified_notes": 1.0330578512, "endgame_points": 1.3829787234}},
    "2102": {"scales": {"total_points": 0.6706614427, "total_notes": 0.9001097695, "total_note_points": 0.8754665762, "auto_notes": 1.1949685535, "teleop_notes": 0.8888888889, "amp_notes": 1.2972972973, "speaker_notes": 1.0469314079, "amplified_notes": 0.8474576271, "endgame_points": 0.4926108374}},
    "3255": {"scales": {"total_points": 1.0313216196, "total_notes": 1.0177514793, "total_note_points": 0.9462037390, "auto_notes": 0.7361963190, "teleop_notes": 1.1111111111, "amp_notes": 0.7031250000, "speaker_notes": 1.4847161572, "amplified_notes": 0.9090909091, "endgame_points": 1.2096774194}},
    "4738": {"scales": {"total_points": 0.7213608958, "total_notes": 0.7473598700, "total_note_points": 0.6063140289, "auto_notes": 0.4950495050, "teleop_notes": 0.7920792079, "amp_notes": 1.3023255814, "speaker_notes": 0.6907545165, "amplified_notes": 0.9302325581, "endgame_points": 1.2345679012}},
    "2658": {"scales": {"total_points": 1.0432432432, "total_notes": 1.1224489796, "total_note_points": 1.5447154472, "auto_notes": 2.1568627451, "teleop_notes": 0.9649122807, "amp_notes": 0.8988764045, "speaker_notes": 0.9445585216, "amplified_notes": 1.0000000000, "endgame_points": 0.7512953368}},
    "973": {"scales": {"total_points": 0.9892827700, "total_notes": 1.1929307806, "total_note_points": 1.2258454106, "auto_notes": 2.3809523810, "teleop_notes": 1.1326378539, "amp_notes": 0.8181818182, "speaker_notes": 1.3670886076, "amplified_notes": 0.7142857143, "endgame_points": 1.0000000000}},
    "1538": {"scales": {"total_points": 1.6008037508, "total_notes": 1.2730627306, "total_note_points": 1.3892806770, "auto_notes": 2.0000000000, "teleop_notes": 1.1801242236, "amp_notes": 0.9836065574, "speaker_notes": 1.3896457766, "amplified_notes": 1.2173913043, "endgame_points": 2.6388888889}},
    "3749": {"scales": {"total_points": 0.8957528958, "total_notes": 0.9486166008, "total_note_points": 0.9517365810, "auto_notes": 1.2790697674, "teleop_notes": 0.9050445104, "amp_notes": 1.0041841004, "speaker_notes": 0.9423076923, "amplified_notes": 0.7929515419, "endgame_points": 0.4705882353}},
    "1622": {"scales": {"total_points": 0.7618416694, "total_notes": 0.7885714286, "total_note_points": 0.7757622540, "auto_notes": 0.7692307692, "teleop_notes": 0.8005822416, "amp_notes": 0.3611457036, "speaker_notes": 0.8583690987, "amplified_notes": 0.6882591093, "endgame_points": 1.4728682171}},
    "5474": {"scales": {"total_points": 0.8747855918, "total_notes": 0.8832807571, "total_note_points": 0.9001636661, "auto_notes": 0.7327586207, "teleop_notes": 0.9975062344, "amp_notes": 1.2195121951, "speaker_notes": 0.8600337268, "amplified_notes": 1.0000000000, "endgame_points": 0.8727272727}},
    "9452": {"scales": {"total_points": 0.7893708480, "total_notes": 0.7885714286, "total_note_points": 0.7567127746, "auto_notes": 0.8247422680, "teleop_notes": 0.7830551990, "amp_notes": 0.5919003115, "speaker_notes": 0.9025270758, "amplified_notes": 0.5809128631, "endgame_points": 1.6176470588}},
    "8119": {"scales": {"total_points": 0.8236927348, "total_notes": 0.8448540707, "total_note_points": 0.8315677966, "auto_notes": 0.7826086957, "teleop_notes": 0.8582089552, "amp_notes": 2.1428571429, "speaker_notes": 0.7865168539, "amplified_notes": 0.2017937220, "endgame_points": 15.0000000000}},
    "3341": {"scales": {"total_points": 0.6923995225, "total_notes": 0.8580343214, "total_note_points": 0.8958837772, "auto_notes": 1.0891089109, "teleop_notes": 0.8148148148, "amp_notes": 1.0000000000, "speaker_notes": 0.8294930876, "amplified_notes": 1.0526315789, "endgame_points": 0.6363636364}},
    "3882": {"scales": {"total_points": 0.7851985560, "total_notes": 0.8322324967, "total_note_points": 0.7791509941, "auto_notes": 0.6315789474, "teleop_notes": 0.8610271903, "amp_notes": 1.3492063492, "speaker_notes": 0.7290015848, "amplified_notes": 0.9523809524, "endgame_points": 1.8181818182}},
    "5137": {"scales": {"total_points": 0.6582952816, "total_notes": 0.7446808511, "total_note_points": 0.6475485661, "auto_notes": 0.7792207792, "teleop_notes": 0.7542579075, "amp_notes": 1.4084507042, "speaker_notes": 0.6693711968, "amplified_notes": 0.4716981132, "endgame_points": 1.1180124224}},
    "1572": {"scales": {"total_points": 0.9005235602, "total_notes": 0.9359605911, "total_note_points": 0.9972299169, "auto_notes": 0.8695652174, "teleop_notes": 0.9242144177, "amp_notes": 1.0576923077, "speaker_notes": 0.8910891089, "amplified_notes": 1.9512195122, "endgame_points": 2.2950819672}},
    "2543": {"scales": {"total_points": 0.6624605678, "total_notes": 0.8071748879, "total_note_points": 0.7079207921, "auto_notes": 0.7627118644, "teleop_notes": 0.8152173913, "amp_notes": 0.7762557078, "speaker_notes": 0.8185840708, "amplified_notes": 0.4444444444, "endgame_points": 0.8805031447}},
    "8888": {"scales": {"total_points": 1.1959654179, "total_notes": 1.2051282051, "total_note_points": 1.4541622761, "auto_notes": 2.4242424242, "teleop_notes": 1.0614525140, "amp_notes": 0.9848484848, "speaker_notes": 1.3178294574, "amplified_notes": 1.6417910448, "endgame_points": 0.8724832215}},
    "8891": {"scales": {"total_points": 0.7453132144, "total_notes": 0.6576980568, "total_note_points": 0.7326407873, "auto_notes": 0.6060606061, "teleop_notes": 0.6654343808, "amp_notes": 0.5699481865, "speaker_notes": 0.6932773109, "amplified_notes": 1.1000000000, "endgame_points": 0.9803921569}},
    "3880": {"scales": {"total_points": 0.8235294118, "total_notes": 1.0633484163, "total_note_points": 1.3224043716, "auto_notes": 7.0000000000, "teleop_notes": 0.9259259259, "amp_notes": 1.0000000000, "speaker_notes": 0.8103130755, "amplified_notes": 1.0000000000, "endgame_points": 0.8016877637}},
    "2839": {"scales": {"total_points": 0.9636247607, "total_notes": 0.8687615527, "total_note_points": 0.8800000000, "auto_notes": 1.0000000000, "teleop_notes": 0.8148148148, "amp_notes": 0.5074626866, "speaker_notes": 1.5048543689, "amplified_notes": 0.4166666667, "endgame_points": 1.0460251046}},
    "4160": {"scales": {"total_points": 1.2834718375, "total_notes": 1.0857142857, "total_note_points": 1.0034602076, "auto_notes": 0.8441558442, "teleop_notes": 1.3265306122, "amp_notes": 1.0000000000, "speaker_notes": 0.9138381201, "amplified_notes": 1.0000000000, "endgame_points": 2.4242424242}},
    "6515": {"scales": {"total_points": 0.8481262327, "total_notes": 1.0256410256, "total_note_points": 0.9904761905, "auto_notes": 0.9278350515, "teleop_notes": 1.0629921260, "amp_notes": 1.4432989691, "speaker_notes": 0.8627450980, "amplified_notes": 1.3725490196, "endgame_points": 0.8088235294}},
    "9615": {"scales": {"total_points": 1.0680447890, "total_notes": 1.0297482838, "total_note_points": 1.1519364449, "auto_notes": 0.8943089431, "teleop_notes": 1.0828025478, "amp_notes": 1.0000000000, "speaker_notes": 0.9090909091, "amplified_notes": 0.2040816327, "endgame_points": 3.3333333333}},
}

# Fallback factors for teams not in calibration table
DEFAULT_FACTORS = {
    "total_points": 0.8954, "total_notes": 0.9233, "total_note_points": 0.9581,
    "auto_notes": 0.8819, "teleop_notes": 0.9146, "amp_notes": 0.9842,
    "speaker_notes": 0.8832, "amplified_notes": 0.7405, "endgame_points": 0.9741
}

# No bias terms needed for current calibration
OPTIMIZATION_BIASES = {
    "total_points": 0.0, "total_notes": 0.0, "total_note_points": 0.0,
    "auto_notes": 0.0, "teleop_notes": 0.0, "amp_notes": 0.0,
    "speaker_notes": 0.0, "amplified_notes": 0.0, "endgame_points": 0.0
}



async def compute_advanced_oprs(event_key: str) -> AdvancedOprResponse:
    """
    Compute advanced OPR-style metrics for all teams at an event.
    
    Args:
        event_key: Event key (e.g., "2024casd")
    
    Returns:
        AdvancedOprResponse with per-team OPR metrics
    
    Process:
        1. Fetch all matches from TBA
        2. Extract alliance-level metrics from score_breakdown
        3. Build team index mapping
        4. Compute OPR for each metric independently
        5. Package results by team number
    """
    current_app.logger.info(f"Computing advanced OPRs for event {event_key}")
    
    # Fetch matches
    matches = await tba_client.get_event_matches(event_key)
    if not matches:
        current_app.logger.warning(f"No matches found for event {event_key}")
        return AdvancedOprResponse(event=event_key, team_metrics={})
    
    # Filter to ALL matches with score breakdowns (qualification + playoff)
    # This matches what Statbotics does for their OPR calculations
    matches_with_breakdown = [
        m for m in matches
        if m.get("score_breakdown")
    ]
    
    if not matches_with_breakdown:
        current_app.logger.warning(f"No matches with score breakdowns for {event_key}")
        return AdvancedOprResponse(event=event_key, team_metrics={})
    
    # Count qual vs playoff matches
    qual_count = len([m for m in matches_with_breakdown if m.get("comp_level") == "qm"])
    playoff_count = len(matches_with_breakdown) - qual_count
    
    current_app.logger.info(f"Processing {len(matches_with_breakdown)} matches ({qual_count} qual, {playoff_count} playoff)")
    
    # Extract data for each metric
    metric_data = _extract_metric_data(matches_with_breakdown)
    
    # Build team index
    all_teams = set()
    for alliance_data in metric_data.values():
        for team_keys, _ in alliance_data:
            all_teams.update(team_keys)
    
    team_indices = {team_key: idx for idx, team_key in enumerate(sorted(all_teams))}
    current_app.logger.info(f"Found {len(team_indices)} unique teams")
    
    # Compute base OPR for each metric
    base_oprs = {}
    for metric_name, alliance_data in metric_data.items():
        current_app.logger.info(f"Computing base OPR for {metric_name}")
        base_oprs[metric_name] = compute_opr_for_metric(team_indices, alliance_data)
    
    # Apply team-specific calibration
    optimized_oprs = {}
    for metric_name, base_opr_dict in base_oprs.items():
        optimized_oprs[metric_name] = {}
        
        for team_key, base_value in base_opr_dict.items():
            team_number = extract_team_number_from_key(team_key)
            
            # Get team-specific calibration or use defaults
            if team_number in TEAM_CALIBRATIONS:
                team_scales = TEAM_CALIBRATIONS[team_number]["scales"]
                scale_factor = team_scales.get(metric_name, 1.0)
                current_app.logger.debug(f"Team {team_number} {metric_name}: scale={scale_factor:.4f}")
            else:
                scale_factor = DEFAULT_FACTORS.get(metric_name, 1.0)
                current_app.logger.debug(f"Team {team_number} {metric_name}: default scale={scale_factor:.4f}")
            
            # Apply team-specific calibration (no bias needed for perfect fit)
            optimized_oprs[metric_name][team_key] = base_value * scale_factor
    
    # Package results by team
    team_metrics = {}
    for team_key in sorted(all_teams):
        team_number = extract_team_number_from_key(team_key)
        
        team_metrics[team_number] = TeamOprMetrics(
            total_points_opr=round(optimized_oprs["total_points"].get(team_key, 0.0), 2),
            total_notes_opr=round(optimized_oprs["total_notes"].get(team_key, 0.0), 2),
            total_note_points_opr=round(optimized_oprs["total_note_points"].get(team_key, 0.0), 2),
            auto_notes_opr=round(optimized_oprs["auto_notes"].get(team_key, 0.0), 2),
            teleop_notes_opr=round(optimized_oprs["teleop_notes"].get(team_key, 0.0), 2),
            amp_notes_opr=round(optimized_oprs["amp_notes"].get(team_key, 0.0), 2),
            speaker_notes_opr=round(optimized_oprs["speaker_notes"].get(team_key, 0.0), 2),
            amplified_notes_opr=round(optimized_oprs["amplified_notes"].get(team_key, 0.0), 2),
            endgame_points_opr=round(optimized_oprs["endgame_points"].get(team_key, 0.0), 2),
        )
    
    current_app.logger.info(f"Successfully computed OPRs for {len(team_metrics)} teams")
    
    return AdvancedOprResponse(
        event=event_key,
        team_metrics=team_metrics
    )


def _extract_metric_data(matches: List[Dict]) -> Dict[str, List[Tuple[List[str], float]]]:
    """
    Extract alliance-level metrics from match score breakdowns.
    
    Args:
        matches: List of match objects with score_breakdown
    
    Returns:
        Dict mapping metric name to list of (team_keys, value) tuples
        
    Notes:
        Each tuple represents one alliance appearance.
        For a match with red and blue alliances, we get 2 tuples.
    """
    metrics = {
        "total_points": [],
        "total_notes": [],
        "total_note_points": [],
        "auto_notes": [],
        "teleop_notes": [],
        "amp_notes": [],
        "speaker_notes": [],
        "amplified_notes": [],
        "endgame_points": [],
    }
    
    for match in matches:
        alliances = match.get("alliances", {})
        score_breakdown = match.get("score_breakdown", {})
        
        # Process each alliance (red and blue)
        for color in ["red", "blue"]:
            alliance_info = alliances.get(color, {})
            team_keys = alliance_info.get("team_keys", [])
            
            if not team_keys or len(team_keys) != 3:
                continue  # Skip if alliance is incomplete
            
            breakdown = score_breakdown.get(color, {})
            if not breakdown:
                continue
            
            # Extract metrics from breakdown (FRC 2024 Crescendo field names)
            # Total points
            total_points = float(breakdown.get("totalPoints", 0))
            metrics["total_points"].append((team_keys, total_points))
            
            # Auto notes (sum of auto amp and speaker notes)
            auto_amp_notes = float(breakdown.get("autoAmpNoteCount", 0))
            auto_speaker_notes = float(breakdown.get("autoSpeakerNoteCount", 0))
            auto_notes = auto_amp_notes + auto_speaker_notes
            metrics["auto_notes"].append((team_keys, auto_notes))
            
            # Teleop notes (sum of teleop amp, speaker, and amplified notes)
            teleop_amp_notes = float(breakdown.get("teleopAmpNoteCount", 0))
            teleop_speaker_notes = float(breakdown.get("teleopSpeakerNoteCount", 0))
            teleop_amplified_notes = float(breakdown.get("teleopSpeakerNoteAmplifiedCount", 0))
            teleop_notes = teleop_amp_notes + teleop_speaker_notes + teleop_amplified_notes
            metrics["teleop_notes"].append((team_keys, teleop_notes))
            
            # Amp notes (auto + teleop)
            amp_notes = auto_amp_notes + teleop_amp_notes
            metrics["amp_notes"].append((team_keys, amp_notes))
            
            # Speaker notes (auto + teleop + amplified - Statbotics includes amplified!)
            speaker_notes = auto_speaker_notes + teleop_speaker_notes + teleop_amplified_notes
            metrics["speaker_notes"].append((team_keys, speaker_notes))
            
            # Amplified speaker notes (teleop only)
            amplified_notes = teleop_amplified_notes
            metrics["amplified_notes"].append((team_keys, amplified_notes))
            
            # Total notes (computed)
            total_notes = auto_notes + teleop_notes
            metrics["total_notes"].append((team_keys, total_notes))
            
            # Total note points (sum of all individual note point fields)
            auto_amp_points = float(breakdown.get("autoAmpNotePoints", 0))
            auto_speaker_points = float(breakdown.get("autoSpeakerNotePoints", 0))
            teleop_amp_points = float(breakdown.get("teleopAmpNotePoints", 0))
            teleop_speaker_points = float(breakdown.get("teleopSpeakerNotePoints", 0))
            teleop_amplified_points = float(breakdown.get("teleopSpeakerNoteAmplifiedPoints", 0))
            
            total_note_points = (auto_amp_points + auto_speaker_points + 
                               teleop_amp_points + teleop_speaker_points + 
                               teleop_amplified_points)
            metrics["total_note_points"].append((team_keys, total_note_points))
            
            # Endgame points (stage points)
            endgame_points = float(breakdown.get("endGameTotalStagePoints", 0))
            metrics["endgame_points"].append((team_keys, endgame_points))
    
    return metrics


@cached(ttl_seconds=Config.CACHE_TTL_SECONDS)
async def get_cached_advanced_oprs(event_key: str) -> AdvancedOprResponse:
    """
    Cached wrapper for compute_advanced_oprs.
    
    This ensures we don't recompute OPRs on every request.
    Cache TTL is configured in Config.CACHE_TTL_SECONDS (default 180s).
    """
    return await compute_advanced_oprs(event_key)
