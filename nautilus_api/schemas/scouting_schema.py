from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class MatchPhaseSchema(BaseModel):
    """Auto/teleop phase data for a match scouting form."""
    coral: List[int] = Field(..., description="Coral counts [L1, L2, L3, L4]")
    algae: List[int] = Field(..., description="Algae counts [ground, net]")


class ScoutingFormSchema(BaseModel):
    """Match scouting form submission (POST /api/scouting/form)."""
    competition: str = Field(..., description="Competition ID")
    # Stored as strings: the aggregation query filters by str(teamNumber), and the
    # frontend sends these from text inputs. Coerce so either "254" or 254 stores as "254".
    teamNumber: str = Field(..., description="Team number scouted")
    matchNumber: str = Field(..., description="Match number")
    won: int = Field(..., description="1=won, 0=tied, -1=lost")

    @field_validator("teamNumber", "matchNumber", mode="before")
    @classmethod
    def coerce_to_str(cls, value: object) -> str:
        return str(value)
    comments: Optional[str] = Field(default="", description="Free-form comments")
    defensive: Optional[bool] = Field(default=False, description="Played defense")
    brokeDown: Optional[bool] = Field(default=False, description="Broke down during the match")
    rankingPoints: Optional[int] = Field(default=0, description="Ranking points earned")
    auto: MatchPhaseSchema = Field(..., description="Autonomous phase data")
    teleop: MatchPhaseSchema = Field(..., description="Teleop phase data")
    climb: str = Field(..., description="PARK, SHALLOW_CAGE, DEEP_CAGE, or N/A")


class PitPhaseSchema(BaseModel):
    """Scoring/auto capability counts for a pit scouting form."""
    coral: int = Field(..., description="Coral capability")
    algae: int = Field(..., description="Algae capability")


class PitScoutingFormSchema(BaseModel):
    """Pit scouting form submission (POST /api/scouting/pitform)."""
    competition: str = Field(..., description="Competition ID")
    teamNumber: str = Field(..., description="Team number scouted")
    teamName: Optional[str] = Field(default="", description="Team name")

    @field_validator("teamNumber", mode="before")
    @classmethod
    def coerce_team_number_to_str(cls, value: object) -> str:
        return str(value)
    scoring: PitPhaseSchema = Field(..., description="General scoring capability")
    prefPiece: Optional[str] = Field(default="", description="Preferred game piece")
    climb: Optional[str] = Field(default="", description="Climb capability")
    vision: Optional[bool] = Field(default=None, description="Has vision system")
    autonomous: Optional[bool] = Field(default=None, description="Has autonomous routine")
    auto: PitPhaseSchema = Field(..., description="Autonomous capability")
    favcomments: Optional[str] = Field(default="", description="Favorite/notable comments")
    comments: Optional[str] = Field(default="", description="Free-form comments")
