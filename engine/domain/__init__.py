"""Domain models representing living entities, characters, progression, universe, and plot causal graphs for Novel Studio 5.0.

Everything is living and object-oriented. Zero literary hardcoding.
"""

from engine.domain.character import (
    LivingCharacter,
    ChapterMotive,
    PhysiologicalState,
    TrumpCard,
    ChapterTrumpDecision,
    Epistemology,
    DebtRelation,
)
from engine.domain.golden_finger import (
    LivingGoldenFinger,
    GoldenFingerStage,
    EnergyTransaction,
)
from engine.domain.universe import (
    LivingUniverse,
    SpatiotemporalGrid,
    MacroEvent,
)
from engine.domain.plot_graph import (
    LivingPlotGraph,
    ForeshadowingItem,
    SubplotBranch,
    ChapterContinuityHandover,
)

__all__ = [
    "LivingCharacter",
    "ChapterMotive",
    "PhysiologicalState",
    "TrumpCard",
    "ChapterTrumpDecision",
    "Epistemology",
    "DebtRelation",
    "LivingGoldenFinger",
    "GoldenFingerStage",
    "EnergyTransaction",
    "LivingUniverse",
    "SpatiotemporalGrid",
    "MacroEvent",
    "LivingPlotGraph",
    "ForeshadowingItem",
    "SubplotBranch",
    "ChapterContinuityHandover",
]
