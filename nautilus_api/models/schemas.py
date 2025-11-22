"""
Pydantic schemas for API request/response validation.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


# ============================================================================
# TBA Event Summary Schema
# ============================================================================

class TbaRecord(BaseModel):
    """Team's win/loss/tie record."""
    wins: int
    losses: int
    ties: int
    winratePct: float = Field(..., description="Win rate as percentage (0-100)")


class TbaRanking(BaseModel):
    """Team's ranking information."""
    rank: int
    rp: Optional[float] = None
    dq: Optional[int] = None


class TbaEventSummary(BaseModel):
    """Summary of TBA data for a team at an event."""
    eventKey: str
    teamNumber: str
    teamName: Optional[str] = None
    matchesPlayed: Optional[int] = None
    record: Optional[TbaRecord] = None
    opr: Optional[float] = None
    dpr: Optional[float] = None
    ccwm: Optional[float] = None
    ranking: Optional[TbaRanking] = None


# ============================================================================
# Scouting Aggregation Schema
# ============================================================================

class LevelPoints(BaseModel):
    """Points attributed per coral level."""
    L1: float
    L2: float
    L3: float
    L4: float


class LevelPercentages(BaseModel):
    """Percentage contribution per coral level."""
    L1: float
    L2: float
    L3: float
    L4: float


class ClimbCounts(BaseModel):
    """Counts of each climb type."""
    PARK: int
    SHALLOW_CAGE: int
    DEEP_CAGE: int


class ScoutingSampleAuto(BaseModel):
    """Auto phase data for a sample."""
    coral: List[int] = Field(..., description="Coral counts [L1, L2, L3, L4]")
    algae: List[int] = Field(..., description="Algae counts [ground, net]")


class ScoutingSampleTeleop(BaseModel):
    """Teleop phase data for a sample."""
    coral: List[int] = Field(..., description="Coral counts [L1, L2, L3, L4]")
    algae: List[int] = Field(..., description="Algae counts [ground, net]")


class ScoutingSample(BaseModel):
    """Individual scouting match sample."""
    matchNumber: str
    won: int | bool = Field(..., description="1=won, 0=tied, -1=lost, or boolean")
    comments: Optional[str] = None
    defensive: Optional[bool] = None
    brokeDown: Optional[bool] = None
    rankingPoints: Optional[int] = None
    auto: ScoutingSampleAuto
    teleop: ScoutingSampleTeleop
    climb: Optional[str] = Field(None, description="PARK, SHALLOW_CAGE, or DEEP_CAGE")
    points: float = Field(..., description="Computed points for this match")


class TeamScoutingAggregation(BaseModel):
    """Aggregated scouting data for a team at a competition."""
    competition: str
    teamNumber: str
    matchesScouted: int = Field(..., description="Number of matches we scouted (N)")
    totalPoints: float = Field(..., description="Total points across scouted matches")
    avgPpgScouted: float = Field(..., description="Average points per game (scouted)")
    levelPoints: LevelPoints = Field(..., description="Points per level L1-L4")
    levelPct: LevelPercentages = Field(..., description="Percentage per level L1-L4")
    climbCounts: ClimbCounts = Field(..., description="Counts of climb types")
    samples: List[ScoutingSample] = Field(default_factory=list, description="Individual match samples")


# ============================================================================
# Health Check Schema
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    ok: bool
    ts: str = Field(..., description="ISO timestamp")


# ============================================================================
# Advanced OPR Analytics Schema
# ============================================================================

class TeamOprMetrics(BaseModel):
    """OPR-style metrics for a single team."""
    total_points_opr: float = Field(..., description="Total points contribution (OPR)")
    total_notes_opr: float = Field(..., description="Total notes contribution")
    total_note_points_opr: float = Field(..., description="Total note points contribution")
    auto_notes_opr: float = Field(..., description="Auto notes contribution")
    teleop_notes_opr: float = Field(..., description="Teleop notes contribution")
    amp_notes_opr: float = Field(..., description="Amp notes contribution")
    speaker_notes_opr: float = Field(..., description="Speaker notes contribution")
    amplified_notes_opr: float = Field(..., description="Amplified speaker notes contribution")
    endgame_points_opr: float = Field(..., description="Endgame points contribution")


class AdvancedOprResponse(BaseModel):
    """Response for advanced OPR analytics endpoint."""
    event: str = Field(..., description="Event key (e.g., '2024casd')")
    team_metrics: Dict[str, TeamOprMetrics] = Field(
        ...,
        description="Mapping from team number (e.g., '254') to OPR metrics"
    )
