"""DIINA source package: advanced engine + statistical analysis tooling."""

from .diina_advanced_engine import (
    DIINAAdvancedEngine,
    ENGINE_VERSION,
    ProvenanceRecord,
    SignalWeights,
    TierResult,
)

__version__ = ENGINE_VERSION
__all__ = [
    "DIINAAdvancedEngine",
    "ENGINE_VERSION",
    "ProvenanceRecord",
    "SignalWeights",
    "TierResult",
]
