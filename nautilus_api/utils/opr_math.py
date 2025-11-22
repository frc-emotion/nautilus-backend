"""
OPR (Offensive Power Rating) calculation utilities using least-squares.

Mathematical Model:
For any scoring metric, we solve: x = (A^T A)^-1 A^T b
Where:
- A is the participation matrix (rows = alliances, cols = teams)
- b is the vector of alliance totals for the metric
- x is the vector of per-team contributions (OPR values)

This uses NumPy for efficient matrix operations and includes
defensive checks for singular matrices.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

# Try to get current_app logger, fallback to standard logging
def _get_logger():
    try:
        from quart import current_app
        return current_app.logger
    except RuntimeError:
        return logging.getLogger(__name__)

def compute_opr_for_metric(
    team_indices: Dict[str, int],
    alliance_data: List[Tuple[List[str], float]]
) -> Dict[str, float]:
    """
    Compute OPR-style contribution for a single metric using least-squares.
    
    Args:
        team_indices: Mapping from team_key (e.g., "frc254") to column index
        alliance_data: List of (team_keys_in_alliance, metric_value) tuples
    
    Returns:
        Dict mapping team_key to OPR contribution for this metric
    
    Mathematical Details:
        We build:
        - A: Participation matrix [num_alliances x num_teams]
        - b: Metric totals vector [num_alliances]
        
        Then solve: x = (A^T A)^-1 A^T b
        
        If matrix is singular, we use np.linalg.lstsq as fallback.
    """
    num_teams = len(team_indices)
    num_alliances = len(alliance_data)
    
    if num_alliances == 0 or num_teams == 0:
        return {}
    
    # Build participation matrix A
    A = np.zeros((num_alliances, num_teams), dtype=float)
    b = np.zeros(num_alliances, dtype=float)
    
    for alliance_idx, (team_keys, metric_value) in enumerate(alliance_data):
        b[alliance_idx] = metric_value
        for team_key in team_keys:
            if team_key in team_indices:
                team_idx = team_indices[team_key]
                A[alliance_idx, team_idx] = 1.0
    
    # Solve least-squares: x = (A^T A)^-1 A^T b
    try:
        # Try normal equation first
        ATA = A.T @ A
        ATb = A.T @ b
        
        # Check if matrix is invertible
        if np.linalg.matrix_rank(ATA) == num_teams:
            x = np.linalg.solve(ATA, ATb)
        else:
            # Singular matrix, use least squares
            logger = _get_logger()
            logger.warning("Singular matrix detected, using lstsq fallback")
            x, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
    
    except np.linalg.LinAlgError as e:
        logger = _get_logger()
        logger.error(f"LinAlgError in OPR calculation: {e}")
        # Fallback to lstsq
        x, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
    
    # Convert to dict
    result = {}
    for team_key, team_idx in team_indices.items():
        result[team_key] = float(x[team_idx])
    
    return result


def extract_team_number_from_key(team_key: str) -> str:
    """
    Extract team number from TBA team key.
    
    Args:
        team_key: Team key like "frc254"
    
    Returns:
        Team number like "254"
    """
    return team_key.replace("frc", "")
