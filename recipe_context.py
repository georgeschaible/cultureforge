"""RecipeContext — structured recipe-relevant facts derived from a CapabilityProfile.

This is the input format for recipe synthesis (Phase 2c). It does NOT contain
a recipe; it contains the structured biological information needed to compose one.

Each field carries evidence strings showing where the value came from.  When
the recipe composer in Phase 2c uses RecipeContext, it can trace any decision
back to its source data.

Fields default to None or empty when underlying data is missing.  The recipe
composer decides how to handle missing information; RecipeContext does not
hide it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Atmosphere(Enum):
    AEROBIC = "aerobic"                 # ~21% O2
    MICROAEROBIC = "microaerobic"       # 2-5% O2
    ANAEROBIC = "anaerobic"             # no O2
    PHOTOTROPHIC = "phototrophic"       # anaerobic + light
    SPECIAL_GAS = "special_gas"         # H2/CO2 for methanogens, etc.


@dataclass
class CarbonSource:
    name: str                           # e.g. "malate", "glucose", "CO2"
    type: str                           # "organic_acid", "sugar", "amino_acid", "CO2", "methane"
    confidence: float                   # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    derived_from_capability: Optional[str] = None


@dataclass
class ElectronDonor:
    name: str                           # e.g. "H2", "NH4+", "Fe(II)", "organic"
    confidence: float
    evidence: List[str] = field(default_factory=list)
    derived_from_capability: Optional[str] = None


@dataclass
class ElectronAcceptor:
    name: str                           # e.g. "O2", "NO3-", "SO4-2", "Fe(III)", "CO2"
    confidence: float
    evidence: List[str] = field(default_factory=list)
    derived_from_capability: Optional[str] = None


@dataclass
class NitrogenSource:
    name: str                           # e.g. "NH4+", "NO3-", "N2", "organic_amino_acids"
    confidence: float
    evidence: List[str] = field(default_factory=list)


@dataclass
class TraceMetal:
    element: str                        # e.g. "Fe", "Mo", "Ni", "Se", "W", "V"
    importance: str                     # "essential", "supporting", "trace"
    evidence: List[str] = field(default_factory=list)


@dataclass
class CofactorRequirement:
    name: str                           # e.g. "F420", "B12", "biotin", "thiamine"
    can_synthesize: bool                # True = organism makes its own; False = must supplement
    completeness: float                 # pathway completeness 0-100
    confidence: float
    evidence: List[str] = field(default_factory=list)


@dataclass
class GrowthConditions:
    temperature_optimum_c: Optional[float] = None
    temperature_range_c: Optional[Tuple[float, float]] = None
    ph_optimum: Optional[float] = None
    ph_range: Optional[Tuple[float, float]] = None
    salinity_category: Optional[str] = None     # "non_halophile", "halotolerant", "moderate_halophile", "extreme_halophile"
    salinity_g_per_l: Optional[float] = None    # numeric salinity override (Phase 3.1)
    salinity_evidence: List[str] = field(default_factory=list)
    source: str = "unknown"                     # per-field: "temp:tempura, ph:user_override, salinity:not_set"


@dataclass
class SpecialRequirement:
    requirement: str                    # e.g. "syntrophic_partner", "light", "elevated_pressure"
    description: str
    evidence: List[str] = field(default_factory=list)


@dataclass
class RecipeContext:
    """Structured recipe-relevant facts derived from a CapabilityProfile."""
    genome_id: int
    species: str

    # Atmosphere and gas requirements
    primary_atmosphere: Optional[Atmosphere] = None
    alternative_atmospheres: List[Atmosphere] = field(default_factory=list)
    gas_requirements: List[str] = field(default_factory=list)

    # Carbon, donors, acceptors
    carbon_sources: List[CarbonSource] = field(default_factory=list)
    electron_donors: List[ElectronDonor] = field(default_factory=list)
    electron_acceptors: List[ElectronAcceptor] = field(default_factory=list)
    nitrogen_sources: List[NitrogenSource] = field(default_factory=list)

    # Growth conditions
    conditions: Optional[GrowthConditions] = None

    # Trace metals and cofactors
    trace_metals: List[TraceMetal] = field(default_factory=list)
    cofactors: List[CofactorRequirement] = field(default_factory=list)

    # Special requirements
    special_requirements: List[SpecialRequirement] = field(default_factory=list)

    # Cultivation mode information (preserved from CapabilityProfile)
    primary_cultivation_modes: List[str] = field(default_factory=list)
    cultivation_mode_notes: List[str] = field(default_factory=list)

    # Provenance and confidence
    overall_confidence: float = 0.0
    incompleteness_flags: List[str] = field(default_factory=list)
