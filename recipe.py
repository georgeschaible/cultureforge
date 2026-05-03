"""Recipe dataclasses (Phase 2c).

A Recipe is the cultivation medium output produced by `compose_recipe.py` from
a RecipeContext (Phase 2b). It contains every detail a microbiologist would
need to attempt cultivation: ingredients with concentrations + rationale +
confidence, gas phase, incubation conditions, thermodynamic feasibility check,
uncertainty flags traced to docs/LIMITATIONS.md categories, and overall confidence.

The schema deliberately preserves rationale and confidence on every ingredient
so the recipe is auditable end-to-end. A reader can trace any decision back to
its source in the CapabilityProfile, RecipeContext, or thermodynamic check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class IngredientCategory(Enum):
    CARBON_SOURCE = "carbon_source"
    NITROGEN_SOURCE = "nitrogen_source"
    SULFUR_SOURCE = "sulfur_source"
    PHOSPHORUS_SOURCE = "phosphorus_source"
    ELECTRON_DONOR = "electron_donor"
    ELECTRON_ACCEPTOR = "electron_acceptor"
    BUFFER = "buffer"
    REDUCING_AGENT = "reducing_agent"
    TRACE_METAL = "trace_metal"
    VITAMIN = "vitamin"
    SALT = "salt"
    GAS_PHASE = "gas_phase"
    SUPPLEMENT = "supplement"


@dataclass
class Ingredient:
    """One component of a recipe.

    Concentrations use the unit appropriate for the ingredient class: g/L for
    salts and buffers, mM or g/L for organics, μg/L for vitamins, atm for gas
    partial pressures (carried as concentration on a per-component basis).
    """
    name: str                                    # e.g. "NaCl", "yeast extract", "Fe(III) citrate"
    chemical_formula: Optional[str]
    concentration: float
    concentration_unit: str                      # "g/L", "mM", "%w/v", "atm", "μg/L", "mL/L"
    category: IngredientCategory
    rationale: str                               # human-readable explanation
    confidence: float                            # 0.0 to 1.0 confidence in this specific ingredient
    derived_from: List[str] = field(default_factory=list)  # capability names or context fields that led to this


@dataclass
class GasPhase:
    """Headspace gas composition.

    `composition` maps gas species to mole fractions (sum to ~1.0). For
    methanogen culture under H2/CO2 the typical value is {"H2": 0.80,
    "CO2": 0.20} at 2 atm. For aerobic culture in atmospheric headspace,
    {"air": 1.0} at 1 atm.
    """
    composition: Dict[str, float]
    pressure_atm: float = 1.0
    rationale: str = ""


@dataclass
class IncubationConditions:
    """Temperature, pH, light, agitation."""
    temperature_c: float
    ph: float
    light_required: bool = False
    light_intensity_umol_per_m2_per_s: Optional[float] = None
    shaking_rpm: Optional[int] = None            # None = static
    rationale: str = ""


@dataclass
class ThermodynamicCheck:
    """Result of thermodynamic gating for one capability."""
    capability_name: str
    primary_reaction: str                        # e.g. "4 H2 + CO2 → CH4 + 2 H2O"
    delta_g_kj_per_mol: float
    feasible: bool                               # True if ΔG < -10 kJ/mol; False if ΔG > 0
    feasibility_class: str = "feasible"          # "feasible" | "marginal" | "infeasible" | "unknown"
    notes: str = ""


@dataclass
class Recipe:
    """Cultivation medium recipe for a single organism.

    Generated from a RecipeContext by the Phase 2c recipe composer.
    The structure deliberately preserves provenance: every ingredient carries
    rationale + confidence + derived_from, and the recipe-level uncertainty
    flags reference docs/LIMITATIONS.md categories so the user can trace risk.
    """
    genome_id: int
    species: str
    primary_cultivation_mode: str
    alternative_cultivation_modes: List[str] = field(default_factory=list)

    ingredients: List[Ingredient] = field(default_factory=list)
    gas_phase: Optional[GasPhase] = None
    conditions: Optional[IncubationConditions] = None

    thermodynamic_checks: List[ThermodynamicCheck] = field(default_factory=list)

    # Trail of decisions
    composition_rationale: List[str] = field(default_factory=list)

    # Honest uncertainty
    uncertainty_flags: List[str] = field(default_factory=list)
    limitations_referenced: List[str] = field(default_factory=list)  # e.g. ["A.1", "C.1"] from docs/LIMITATIONS.md

    # Overall confidence
    overall_confidence: float = 0.0
    confidence_rationale: str = ""

    # Reference media for comparison (Phase 2d will populate)
    similar_published_media: List[str] = field(default_factory=list)

    # Special-case escalation (set when no recipe could be composed)
    escalated: bool = False
    escalation_reason: str = ""
