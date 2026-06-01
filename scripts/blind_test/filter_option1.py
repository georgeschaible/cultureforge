#!/usr/bin/env python3
"""
Blind-test cohort assembly — Option 1 scope filter (authoritative).

This script is the authoritative implementation of the §13.2 / §14 scope
filter for the Phase 6 blind-test cohort, referenced by name from
docs/phase6/blind_test_cohort_design.md (§§13–14).

The pre-registration design doc records the SCOPE INTENT (environmental,
non-host-associated MAG provenance, uniform across all §7 categories) and
the three operational refinements (§14.2 Clause 4 invertebrate-host with
reef-environmental exemption; §14.3 positive-environmental-signal gate;
§14.4 Clause 1 env-host-value exemption). This script holds the
matching logic — token lists, pattern regexes, keyword vocabularies,
exemption tests — that the doc cites by name.

Single source of truth: the doc must not redefine any list this script
contains. Token / vocab / pattern changes happen here first, then a
follow-up amendment to the design doc references the new version of this
script. The doc and the script land together in their first commit so
the cross-reference is anchored without follow-up edits.

Pipeline:
  - Reads raw NCBI `datasets summary genome` JSONL dump (bacteria + archaea)
    persisted under data/validation/blind_test_batch1/.
  - Applies §13.2 scope filter (4 clauses + positive-env-signal gate +
    Clause 1 env-vocab exemption).
  - Applies §3/§4 mechanical filter (not in cultureforge.db.genomes,
    not in marker *_refs.fasta source taxids, not Thiovulum).
  - Bins survivors by §7 metabolic category (post-hoc, name-based).
  - Writes scope_filter_kept_v3.jsonl / scope_filter_rejected_v3.jsonl /
    mechanical_filter_rejected_v3.tsv / survivors_v3.tsv /
    category_bins_v3.tsv to data/validation/blind_test_batch1/.

Filename history note: the development versions were /tmp/blind_test_filter_v3.py;
the v3 suffix in artifact filenames is preserved for the 2026-05-31 run record.
Future filter iterations get NEW commits (new git history) under the same
scripts/blind_test/filter_option1.py path, not new "_v4" filenames — the
committed version of this file IS the canonical version at any given SHA.
"""

import json
import os
import re
import sys
from collections import defaultdict, Counter

OUT = "data/validation/blind_test_batch1"
BACT_JSONL = f"{OUT}/broad_query_bacteria.jsonl"
ARCH_JSONL = f"{OUT}/broad_query_archaea.jsonl"

# ---------------------------------------------------------------------------
# Constants — missingness recogniser
# ---------------------------------------------------------------------------
MISSING_TOKENS = {"", "missing", "not applicable", "not collected", "n/a",
                  "na", "none", "not provided", "unknown", "unclassified",
                  "not relevant", "not specified"}

def is_missing(v):
    return v is None or str(v).strip().lower() in MISSING_TOKENS


# ---------------------------------------------------------------------------
# §13.2 Scope filter v3 — 4 clauses + positive-signal gate + Clause 1
# env-host-value exemption.
# ---------------------------------------------------------------------------

# Clause 1: populated host fields on the BioSample
HOST_FIELDS = {"host", "host_taxid", "host_scientific_name",
               "host_description", "host_common_name",
               "host_disease", "host_age", "host_sex", "host_body_site",
               "host_subject_id", "host_tissue_sampled"}

# Strict host fields: any populated value here unambiguously signals
# biological host. No exemption.
STRICT_HOST_FIELDS = HOST_FIELDS - {"host", "host_description"}

# Conservative env-substrate vocabulary applied ONLY to `host` and
# `host_description`. A value matching this vocab AND containing NO
# biological-host indicator is exempted from Clause 1 rejection — the
# record is passed through to the other clauses and the positive-env-signal
# gate (which the value usually satisfies on its own).
ENV_HOST_VALUE_VOCAB = [
    # geological substrates
    "subsurface", "shale", "rock", "mineral", "sediment", "soil",
    "sand", "clay", "silt", "mud", "ore", "regolith", "dust",
    "bedrock", "basalt", "granite", "limestone", "carbonate",
    "gravel", "loam",
    # waters
    "water", "seawater", "sea water", "freshwater", "fresh water",
    "groundwater", "ground water", "porewater", "pore water",
    "aquifer", "marine water",
    # ice
    "ice", "snow", "permafrost", "frozen", "glacier", "subglacial",
    "cryoconite",
    # salts / saline
    "brine", "salt", "saline", "hypersaline", "halite", "evaporite",
    # engineered / built environment
    "sludge", "activated sludge", "bioreactor", "reactor",
    "anaerobic digester", "compost", "biogas",
    "wastewater", "waste water", "effluent",
    # microbial structures
    "biofilm", "stromatolite", "crust",
    # extreme habitats
    "hot spring", "geothermal", "hydrothermal",
    "vent", "seep", "fumarole",
    # ENVO ontology marker (any ENVO IRI in host field = env signal)
    "envo:", "envo_",
]

# Biological-host indicators that defeat the env-vocab exemption. If any
# of these appear in the host value, the rejection stands — even if env
# vocab is also present. Conservative; user spec: "I'd rather lose a few
# real environmental MAGs than punch a hole in it."
BIO_HOST_INDICATORS = [
    # mammals / vertebrates (common names)
    "human", "homo sapien", "animal", "mouse", "mice", "rat",
    "pig", "swine", "cow", "cattle", "bovine", "bull", "calf",
    "fish", "bird", "chicken", "poultry", "duck", "turkey",
    "dog", "cat ", " cat", "sheep", "ovine", "goat", "caprine",
    "horse", "equine", "primate", "mammal", "rodent",
    "bat ", " bat", "whale", "dolphin", "seal", "porpoise",
    "salmon", "tilapia", "trout", "shark", "tuna",
    "frog", "toad", "lizard", "snake", "reptile", "amphibian",
    # invertebrates
    "insect", "beetle", "termite", "ant ", " ant", "wasp",
    "bee ", " bee", "fly ", "mosquito", "drosophila", "nematode",
    "sponge", "coral", "anemone", "oyster", "mussel",
    "clam", "scallop", "crab", "shrimp", "lobster", "krill",
    "snail", "slug", "polychaete", "tubeworm", "tube worm",
    "earthworm", "spider", "tick", "mite",
    # plant tissues / common crop names
    "leaf", "leaves", "root", "stem", "shoot", "petal",
    "flower", "fruit", "seed", "bark", "wood",
    "grass", "tree", "shrub",
    "soybean", "rice ", "maize", "wheat", "corn ", "barley",
    "cotton", "tomato", "potato", "tobacco", "arabidopsis",
    "oak", "pine", "fir ", " fir", "spruce", "birch", "willow",
    # general organism / host indicators
    "organism", "host of", "isolate from a ",
    "gut", "intestin", "fecal", "faecal", "feces", "stool",
    "mucosa", "mucus", "skin", "tissue", "blood", "saliva",
    "rumen", "milk", "udder", "phyllosphere", "rhizosphere",
    "endophyte", "endosphere",
]

ENV_HOST_VOCAB_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(t) for t in ENV_HOST_VALUE_VOCAB) + r")",
    re.IGNORECASE,
)
BIO_HOST_RE = re.compile(
    r"(?:" + "|".join(re.escape(t) for t in BIO_HOST_INDICATORS) + r")",
    re.IGNORECASE,
)

def host_value_is_env_only(value):
    """True iff value matches env-substrate vocab AND contains no bio-host
    indicator. Conservative: if uncertain → False (keep rejection)."""
    if is_missing(value):
        return False
    lower = value.strip().lower()
    if not ENV_HOST_VOCAB_RE.search(lower):
        return False
    if BIO_HOST_RE.search(lower):
        return False
    return True


def host_field_populated(attrs_dict):
    """Returns (field, value) for biological-host rejection, or None.

    v3 refinement: for `host` and `host_description`, apply env-vocab
    exemption — if the value reads as environmental substrate only
    (e.g. 'Subsurface shale'), don't reject; pass the record through to
    the other clauses and the positive-env-signal gate.

    For all other host_* fields (host_taxid, host_scientific_name,
    host_common_name, host_disease, host_body_site, host_subject_id,
    host_tissue_sampled, host_age, host_sex), strict rejection — these
    fields unambiguously signal biological host.
    """
    # Strict pass
    for k in STRICT_HOST_FIELDS:
        v = attrs_dict.get(k, "")
        if not is_missing(v):
            return (k, v)
    # Lenient pass — `host` and `host_description` with env exemption
    for k in ("host", "host_description"):
        v = attrs_dict.get(k, "")
        if is_missing(v):
            continue
        if host_value_is_env_only(v):
            continue  # exempted — env substrate, not bio host
        return (k, v)
    return None

# Clause 2: ENVO host-associated branch in env_* fields
HOST_ASSOCIATED_TOKENS = [
    "envo:00009003",   # animal-associated habitat
    "envo:01000219",   # human-associated habitat
    "envo:01000220",   # plant-associated habitat
    "envo:00002025",   # human-associated
    "human gut", "human stool", "human oral", "human skin", "human nasal",
    "human vaginal", "human respiratory", "human fecal", "human-associated",
    "host-associated", "animal-associated", "plant-associated",
    "mouse gut", "rat gut", "pig gut", "cattle gut", "rumen", "cow rumen",
    "bovine rumen", "poultry gut", "chicken gut", "fish gut",
    "gut microbiome", "oral microbiome", "skin microbiome",
    "intestinal microbiome", "respiratory microbiome", "vaginal microbiome",
    "endophyte", "rhizosphere", "phyllosphere", "leaf surface",
    "root nodule", "leaf endosphere", "root endosphere",
    "tumor microenvironment", "tumor",
    "saliva", "feces", "stool", "buccal mucosa", "dental plaque",
    "skin surface", "nasal cavity", "ear canal", "ear",
    "vaginal cavity", "intestine", "small intestine", "large intestine",
    "colon", "cecum", "caecum", "duodenum", "jejunum", "ileum",
    "esophagus", "stomach",
    "sputum", "lung", "bronchus", "lower respiratory tract",
    "blood", "urine", "wound",
]
ENV_FIELDS = ("env_broad_scale", "env_local_scale", "env_medium",
              "env_package", "env_feature")

def env_field_host_associated(attrs_dict):
    for k in ENV_FIELDS:
        v = attrs_dict.get(k, "")
        if not v:
            continue
        vl = v.lower()
        for tok in HOST_ASSOCIATED_TOKENS:
            if tok in vl:
                return (k, v, tok)
    return None

# Clause 3: isolation_source matches mammalian/vertebrate host-tissue terms
HOST_TISSUE_TERMS = [
    "gut", "stool", "feces", "faeces", "fecal", "faecal",
    "intestine", "intestinal", "colon", "cecum", "caecum",
    "duodenum", "jejunum", "ileum", "rectum",
    "oral cavity", "oral", "buccal", "tongue", "dental",
    "saliva", "tooth", "teeth", "gingiva", "subgingival", "supragingival",
    "plaque",
    "skin", "epidermis", "dermis", "sebaceous", "axilla", "armpit",
    "nasal", "nostril", "nare", "sinus", "respiratory",
    "lung", "bronchus", "trachea", "sputum",
    "vaginal", "vagina", "cervix", "uterus",
    "blood", "serum", "plasma",
    "urine", "urinary", "bladder",
    "rumen", "abomasum", "milk", "udder", "mammary",
    "egg", "embryo",
    "tonsil", "throat", "pharynx", "larynx", "ear",
    "wound", "ulcer", "abscess", "biopsy", "tissue",
    "tumor", "tumour", "neoplasm", "cancer",
    "host", "patient", "subject",
    "rhizosphere", "phyllosphere", "endophyte", "leaf", "root",
    "tumor microenvironment",
    "stool sample", "fecal sample",
    "mucosa", "mucosal", "mucus",
    "biofilm-on-host",
]

def isolation_source_host_tissue(attrs_dict):
    iso = attrs_dict.get("isolation_source", "")
    if not iso:
        return None
    isl = iso.lower()
    for term in HOST_TISSUE_TERMS:
        if re.search(r"\b" + re.escape(term) + r"\b", isl):
            return ("isolation_source", iso, term)
    return None

# ---------------------------------------------------------------------------
# Clause 4 (NEW): invertebrate-host detection (token + context-aware)
# ---------------------------------------------------------------------------

INVERTEBRATE_TOKENS = [
    # marine cnidaria/porifera
    "coral", "anemone", "sea anemone", "hydroid", "jellyfish", "scyphozoan",
    "polyp",
    "sponge", "porifera", "demosponge",
    # tunicates / ascidians
    "ascidian", "tunicate", "sea squirt", "salp",
    # echinoderms
    "echinoderm", "starfish", "sea star", "sea urchin", "echinoid",
    "holothurian", "sea cucumber", "ophiuroid", "brittle star", "crinoid",
    # molluscs / bivalves
    "oyster", "mussel", "bivalve", "clam", "scallop", "abalone",
    "gastropod", "snail", "slug", "cephalopod", "octopus", "squid",
    "limpet", "chiton",
    # crustaceans / arthropods
    "crustacean", "barnacle", "shrimp", "krill", "crab", "lobster",
    "amphipod", "copepod", "isopod", "decapod",
    "horseshoe crab",
    # annelids / worms
    "tube worm", "tubeworm", "polychaete", "siboglinid", "siboglinum",
    "vestimentifer", "riftia", "lamellibrachia",
    "earthworm", "nematode",
    # insects
    "termite", "beetle", "ant", "wasp", "bee", "moth", "butterfly",
    "drosophila", "mosquito", "aphid", "weevil", "cockroach",
    "cricket", "grasshopper", "leafhopper", "psyllid",
    # specific symbionts
    "endosymbion", "ectosymbion", "magnetosome", "holobiont",
]

# Reject patterns: token is in HOST-context
# Captures "X metagenome", "X microbiome", "X mucus", "X tissue",
# "X-associated", "isolated from X", "X gut", etc.
HOST_CONTEXT_SUFFIXES = (
    r"metagenom\w*|microbiom\w*|microbiota|mucus|mucos\w*|tissue|"
    r"holobiont|surface\b(?!\s+water|\s+seawater)|skin|"
    r"gut|intestin\w*|digestive|"
    r"associat\w*|symbion\w*|symbiosis|symbiotic|"
    r"mound|nest|colony\b(?!\s+counts)|colon\w*|"
    r"larva\w*|adult|egg|embryo|nymph\w*|"
    r"endos\w*|ectos\w*|"
    r"hindgut|midgut|foregut|crop|haemolymph|hemolymph|"
    r"body|host\b|specimen"
)
HOST_CONTEXT_PREFIXES = (
    r"associated with|isolated from\b(?!\s+\w*\s*reef|\s+\w*\s*sediment|"
    r"\s+\w*\s*seawater|\s+\w*\s*water\b)|"
    r"endosymbiont of|ectosymbiont of|symbiont of|inside|within|"
    r"living in|associated to|extracted from"
)

# Keep patterns: token is in ENVIRONMENTAL-context (reef sediment/water etc.)
ENV_CONTEXT_SUFFIXES = (
    r"reef\s+(sediment|seawater|sea\s*water|water|biome|community|"
    r"ecosystem|environ\w*|habitat|substr\w*|carbonate|fish|fluid)|"
    r"reef-associated\s+(sediment|seawater|water)|"
    r"reef\s+\w*\s*(sediment|water)|"
    r"bed\s+(sediment|seawater|water)|"
    r"-bed\s+(sediment|seawater|water)"
)
ENV_CONTEXT_PREFIXES = (
    r"near|adjacent\s+to|nearby|surrounding|outside|"
    r"non-\w*-associated|reef-wide"
)

# Pre-compile per-token regexes for performance
TOK_PATTERNS = []
for tok in INVERTEBRATE_TOKENS:
    t = re.escape(tok)
    TOK_PATTERNS.append((tok, re.compile(r"\b" + t + r"\b")))

ENV_SUFFIX_RE = re.compile(r"^\s*(?:" + ENV_CONTEXT_SUFFIXES + r")",
                            re.IGNORECASE)
ENV_PREFIX_RE = re.compile(r"(?:" + ENV_CONTEXT_PREFIXES + r")\s*$",
                            re.IGNORECASE)
HOST_SUFFIX_RE = re.compile(r"^\s*(?:" + HOST_CONTEXT_SUFFIXES + r")",
                             re.IGNORECASE)
HOST_PREFIX_RE = re.compile(r"(?:" + HOST_CONTEXT_PREFIXES + r")\s*$",
                             re.IGNORECASE)

# Also: bare invertebrate token surrounded by no qualifier (e.g.
# "coral" alone) should be HOST-context; "reef" without sediment/water
# we treat as ENV-context per user's "near coral" / "reef biome" intent.
REEF_ANY_RE = re.compile(r"^\s*reef\b", re.IGNORECASE)

def invertebrate_host_context(text):
    """Returns (token, context_snippet, decision) or None.

    decision in {"HOST", "ENV"}. ENV means env-context dominates; HOST
    means a host-context occurrence was found.

    Returns None if no invertebrate token is present at all.
    Returns ("X", "...", "HOST") if any occurrence of any token is in
    a host-context with no compensating env-context.
    Returns ("X", "...", "ENV") if all occurrences are in env-context.
    """
    if not text:
        return None
    lower = text.lower()

    any_token_seen = False
    saw_host = None      # (tok, snippet)
    saw_env = None

    for tok, pat in TOK_PATTERNS:
        for m in pat.finditer(lower):
            any_token_seen = True
            start, end = m.span()
            tail = lower[end:end+60]
            head = lower[max(0, start-40):start]

            # Special-case "reef" alone (no sediment/water/biome qualifier)
            # We err on the ENV side: "coral reef" alone → ENV ("near a reef")
            if REEF_ANY_RE.match(tail):
                # If "reef" is followed by a host-suffix term like
                # "reef metagenome" / "reef microbiome" — that's still
                # a reef-ecosystem MAG, treat as ENV (whole-reef
                # community is an environmental sample). User specified
                # this case ("coral reef seawater is environmental").
                saw_env = (tok, text[max(0, start-20):end+50])
                continue

            # Env-suffix: "coral reef sediment", "coral reef seawater"
            if ENV_SUFFIX_RE.match(tail):
                saw_env = (tok, text[max(0, start-20):end+50])
                continue

            # Env-prefix: "near coral", "adjacent to sponge"
            if ENV_PREFIX_RE.search(head):
                saw_env = (tok, text[max(0, start-30):end+20])
                continue

            # Host-suffix: "coral metagenome", "sponge microbiome", etc.
            if HOST_SUFFIX_RE.match(tail):
                saw_host = (tok, text[max(0, start-20):end+50])
                continue

            # Host-prefix: "isolated from sponge", "associated with coral"
            if HOST_PREFIX_RE.search(head):
                saw_host = (tok, text[max(0, start-40):end+20])
                continue

            # Bare token without env or host qualifier: treat as HOST.
            # Examples: "coral", "sponge sample". This is conservative —
            # ambiguous bare-token cases default to host-rejection.
            saw_host = (tok, text[max(0, start-20):end+30])

    if not any_token_seen:
        return None
    if saw_host:
        return (saw_host[0], saw_host[1], "HOST")
    if saw_env:
        return (saw_env[0], saw_env[1], "ENV")
    return None

def invertebrate_host(attrs_dict):
    """Returns (field, snippet, token) for HOST-context hit, else None."""
    # Pool isolation_source + env_* into one string-per-field scan; report
    # whichever field triggered.
    for field in ("isolation_source",) + ENV_FIELDS:
        v = attrs_dict.get(field, "")
        if is_missing(v):
            continue
        res = invertebrate_host_context(v)
        if res and res[2] == "HOST":
            return (field, res[1], res[0])
    return None


# ---------------------------------------------------------------------------
# NEW: positive environmental signal requirement
# ---------------------------------------------------------------------------

# Habitat keywords for isolation_source — covers diverse environmental niches.
ENV_HABITAT_KEYWORDS = [
    # geosphere / substrate
    "soil", "sediment", "sand", "dust", "rock", "mineral", "mud", "ore",
    "clay", "silt", "regolith", "alluvi",
    # hydrosphere
    "water", "seawater", "sea water", "freshwater", "fresh water",
    "ocean", "marine", "sea\b", "lake", "river", "stream",
    "pond", "reservoir", "aquifer", "groundwater", "ground water",
    "subsurface water", "porewater", "pore water",
    "estuary", "estuarine", "lagoon", "mangrove",
    "intertidal", "supratidal", "tidal",
    "coast", "coastal", "beach", "shore", "shoreline",
    # extreme
    "spring", "hot spring", "thermal", "geyser", "geothermal",
    "hydrothermal", "vent", "seep", "fumarole", "mud pot",
    "ice", "snow", "glacier", "permafrost", "polar", "cryosphere",
    "frozen", "subglacial",
    "brine", "salt", "saline", "hypersaline", "salt lake", "salt pan",
    "salt marsh", "playa", "soda lake", "alkaline lake", "acidic lake",
    "halite", "evaporite",
    "cave", "karst", "subsurface", "deep", "abyss", "abyssal",
    "bathy", "bathypelagic", "hadopelagic", "pelagic",
    "volcanic", "basalt", "rhyolite", "tuff", "pumice", "lava",
    # cryospheric / extreme cold
    "arctic", "antarctic", "antarctica", "alpine", "tundra",
    # arid / desert
    "desert", "arid", "semi-arid", "dune",
    # vegetated environments (note: rhizosphere/phyllosphere already
    # caught earlier as host-associated; here we mean ecosystem-scale)
    "forest", "woodland", "grassland", "prairie", "savanna", "savannah",
    "meadow", "tropical", "boreal", "temperate", "steppe",
    "biome", "ecosystem", "habitat",
    # peatlands / wetlands
    "peat", "bog", "fen", "wetland", "swamp", "marsh", "paddy", "mire",
    "rice paddy", "fenland",
    # built/engineered environment
    "bioreactor", "reactor", "sludge", "activated sludge",
    "anaerobic digester", "biogas", "compost", "composting",
    "wastewater", "waste water", "effluent", "treatment plant",
    "bioremediation", "remediation",
    "landfill", "leachate", "tailings",
    "aquaculture", "fishpond", "fish pond",
    # microbial communities
    "mat", "microbial mat", "stromatolite", "biofilm", "biocrust",
    "crust", "biological soil crust",
    # mining / industrial
    "mine", "mining", "acid mine drainage", "amd", "drainage",
    # hydrocarbon / oil
    "petroleum", "oil", "gas\b", "methane", "hydrocarbon", "tar",
    "asphalt", "oil sand", "tar sand",
    # ENVO ontology stamp — if iso has an ENVO IRI in any form, that's
    # an environmental ontology hit
    "envo:", "envo_",
    # other ecosystems
    "estuary", "river", "stream", "lake", "lacustrine", "fluvial",
    "limnic", "neritic",
    # cryoconite, snow
    "cryoconite",
]
# Compile a single big regex that matches any keyword (word-bounded
# where ambiguous, substring-OK where unambiguous like "envo:").
KW_RE = re.compile(
    "|".join(re.escape(k) if not k.endswith("\\b") else k[:-2] + r"\b"
              for k in ENV_HABITAT_KEYWORDS),
    re.IGNORECASE,
)

def has_positive_env_signal(attrs_dict):
    """Returns (field, value) where positive signal was found, or None.

    Positive signal sources, in order:
      1. Any populated env_* MIxS field (env_broad_scale/env_local_scale/
         env_medium/env_package/env_feature).
      2. isolation_source populated AND containing an environmental-habitat
         keyword.
      3. host or host_description populated AND env-substrate-only (e.g.
         'Subsurface shale'). The same env-vocab exemption that lets the
         record past Clause 1 ALSO counts here as positive env signal.
    """
    for k in ENV_FIELDS:
        v = attrs_dict.get(k, "")
        if not is_missing(v):
            return (k, v)
    iso = attrs_dict.get("isolation_source", "")
    if not is_missing(iso) and KW_RE.search(iso):
        return ("isolation_source", iso)
    # v3 extension: env-substrate-only host value counts as positive
    for k in ("host", "host_description"):
        v = attrs_dict.get(k, "")
        if not is_missing(v) and host_value_is_env_only(v):
            return (k, v)
    return None


# ---------------------------------------------------------------------------
# Mechanical §3/§4 (unchanged)
# ---------------------------------------------------------------------------
THIOVULUM_ACCESSION = "GCA_000276965.1"

def load_db_accessions(path):
    accs = set()
    with open(path) as f:
        for line in f:
            parts = line.strip().split("\t")
            if parts:
                accs.add(parts[0])
    return accs

def load_marker_taxids(path):
    with open(path) as f:
        return set(line.strip() for line in f if line.strip())


# ---------------------------------------------------------------------------
# Hit accessors
# ---------------------------------------------------------------------------
def biosample_attrs_dict(rec):
    bs = rec.get("assembly_info", {}).get("biosample", {}) or {}
    d = {}
    for attr in bs.get("attributes", []) or []:
        n = attr.get("name", "")
        v = attr.get("value", "")
        if n:
            d[n] = v
    for k in ("host", "host_disease", "isolation_source", "geo_loc_name",
              "lat_lon"):
        v = bs.get(k, "")
        if v and k not in d:
            d[k] = v
    return d

def get_accession(rec):
    return rec.get("accession", "") or rec.get("current_accession", "")

def get_taxid(rec):
    return str(rec.get("organism", {}).get("tax_id", ""))

def get_organism_name(rec):
    return rec.get("organism", {}).get("organism_name", "")

def get_assembly_stats(rec):
    s = rec.get("assembly_stats", {}) or {}
    return {
        "total_length": s.get("total_sequence_length", ""),
        "n50": s.get("contig_n50", ""),
        "n_contigs": s.get("number_of_contigs", ""),
        "gc": s.get("gc_percent", ""),
    }


# ---------------------------------------------------------------------------
# Scope filter v2 — 4 clauses, then positive-signal gate
# ---------------------------------------------------------------------------
def scope_filter_v3(rec):
    """Returns (decision, reason_label, field, value, term, recovered_host).

    decision in {"KEEP", "REJECT"}.
    reason_label: 'host_field' | 'env_host_token' | 'iso_host_tissue' |
                  'invertebrate_host' | 'no_positive_env_signal'.
    recovered_host: (field, value) tuple if Clause 1 was exempted (record
                    had a populated host/host_description that matched env
                    vocab and got passed through), else None.
    """
    attrs = biosample_attrs_dict(rec)

    # Track recovery: was there a populated host/host_description that
    # the v3 env-vocab exemption let through?
    recovered_host = None
    for k in ("host", "host_description"):
        v = attrs.get(k, "")
        if not is_missing(v) and host_value_is_env_only(v):
            recovered_host = (k, v)
            break

    h = host_field_populated(attrs)
    if h:
        return ("REJECT", "host_field", h[0], h[1], "", None)

    e = env_field_host_associated(attrs)
    if e:
        return ("REJECT", "env_host_token", e[0], e[1], e[2], recovered_host)

    i = isolation_source_host_tissue(attrs)
    if i:
        return ("REJECT", "iso_host_tissue", i[0], i[1], i[2],
                recovered_host)

    inv = invertebrate_host(attrs)
    if inv:
        return ("REJECT", "invertebrate_host", inv[0], inv[1], inv[2],
                recovered_host)

    p = has_positive_env_signal(attrs)
    if not p:
        return ("REJECT", "no_positive_env_signal", "", "", "",
                recovered_host)

    return ("KEEP", "", "", "", "", recovered_host)


def mechanical_filter(rec, db_accs, marker_taxids):
    acc = get_accession(rec)
    taxid = get_taxid(rec)
    if acc in db_accs:
        return ("REJECT", f"in_dev_cohort_db ({acc})")
    if acc == THIOVULUM_ACCESSION:
        return ("REJECT", f"thiovulum_exclusion ({acc})")
    if taxid and taxid in marker_taxids:
        return ("REJECT", f"taxid_in_marker_refs ({taxid})")
    return ("KEEP", "")


# ---------------------------------------------------------------------------
# §7 binning (unchanged)
# ---------------------------------------------------------------------------
CATEGORY_DEFS = [
    ("methanogenesis",       "strong", [r"\bmethano\w+", r"methanogen"]),
    ("methane metabolism",   "strong", [r"methylo\w*", r"methanotroph"]),
    ("sulfate reduction",    "strong", [r"desulf\w+", r"thermodesulf",
                                        r"\bSRB\b"]),
    ("acetogenesis",         "strong", [r"acetobacter", r"acetogen",
                                        r"\bacetate\b.*producer"]),
    ("phototrophy",          "strong", [r"chloroflex\w*", r"chlorobi\w*",
                                        r"rhodo\w+", r"cyanobact\w*",
                                        r"prochloro\w*", r"synechoc\w*",
                                        r"oscillator\w+", r"phototroph"]),
    ("anammox",              "mid",    [r"\banammox", r"brocadi\w+",
                                        r"kuenenia"]),
    ("ammonia oxidation",    "mid",    [r"nitroso\w+", r"\bAOB\b", r"\bAOA\b",
                                        r"thaumarch", r"nitrosomonas",
                                        r"nitrosopumilus"]),
    ("sulfur oxidation",     "mid",    [r"thiomicro\w+", r"thiobac\w+",
                                        r"thiothrix", r"acidithio\w+",
                                        r"sulfurov\w+", r"sulfuri\w+",
                                        r"beggiato\w*", r"thiopl\w+"]),
    ("lithoautotrophic iron","mid",    [r"galliona", r"mariproundus",
                                        r"sideroxydans", r"leptothrix",
                                        r"\bFeOB\b", r"acidithiobac\w+",
                                        r"iron oxidiz"]),
    ("halophile",            "mid",    [r"haloarc\w+", r"haloferax",
                                        r"halobact\w+", r"halorubr\w+",
                                        r"halomonas", r"salinibact\w*",
                                        r"halophil"]),
    ("hyperthermophile",     "mid",    [r"pyroco\w+", r"thermofil\w+",
                                        r"thermus", r"thermoto\w+",
                                        r"sulfolob\w+", r"aquifex",
                                        r"hydrogenobacul", r"hyperthermo"]),
    ("fermentative",         "mid",    [r"clostrid\w+", r"firmicut\w*",
                                        r"bacillus", r"lactobacill\w+",
                                        r"\bferment"]),
    ("extreme archaea",      "weak",   [r"crenarch\w*", r"euryarch\w*",
                                        r"asgardarc\w*", r"lokiarch\w*",
                                        r"thorarch\w*", r"heimdallarch\w*",
                                        r"odinarch\w*"]),
    ("syntrophy",            "weak",   [r"syntrophus", r"syntrophobact\w*",
                                        r"syntrophomon\w*", r"smithella",
                                        r"\bsyntroph"]),
    ("cable bacteria",       "weak",   [r"\belectrothrix", r"\bcalignei\w+",
                                        r"cable bacteria",
                                        r"electronisocae"]),
    ("ANME",                 "weak",   [r"\bANME[- ]?[12345]", r"\bANME\b",
                                        r"methanophagales", r"methanoperidi"]),
    ("microaerophile",       "weak",   [r"campylobacter", r"helicobacter",
                                        r"epsilonproteo", r"sulfuricurvum",
                                        r"sulfurospirillum",
                                        r"microaerophil"]),
    ("comammox",             "weak",   [r"\bcomammox", r"nitrospira inopinata"]),
]

def bin_category(rec):
    name = (get_organism_name(rec) or "").lower()
    attrs = biosample_attrs_dict(rec)
    env_text = " ".join(attrs.get(k, "") for k in
                        ("isolation_source", "env_broad_scale",
                         "env_local_scale", "env_medium",
                         "metagenome_source")).lower()
    hay = name + " || " + env_text
    tags = []
    for cat, strength, pats in CATEGORY_DEFS:
        for pat in pats:
            if re.search(pat, hay):
                tags.append((cat, strength))
                break
    return tags


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    db_accs = load_db_accessions("/tmp/db_accessions.tsv")
    marker_taxids = load_marker_taxids("/tmp/marker_taxids.txt")
    print(f"db_accessions={len(db_accs)}  marker_taxids={len(marker_taxids)}",
          file=sys.stderr)

    scope_kept_path     = f"{OUT}/scope_filter_kept_v3.jsonl"
    scope_rej_path      = f"{OUT}/scope_filter_rejected_v3.jsonl"
    mech_rej_path       = f"{OUT}/mechanical_filter_rejected_v3.tsv"
    survivors_path      = f"{OUT}/survivors_v3.tsv"
    bins_path           = f"{OUT}/category_bins_v3.tsv"

    total = 0
    scope_kept_n = 0
    rej_counter = Counter()    # by reason_label
    rej_field_counter = Counter()  # by triggering field
    sampled_per_reason = defaultdict(list)
    SAMPLE_CAP_PER_REASON = 12
    kept_samples = []
    KEPT_SAMPLE_CAP = 20

    # Special tracking: NEW-token rejects (invertebrate_host) — surface
    # these specifically so user can confirm hosts vs. reef-near-water.
    invert_host_samples = []
    INVERT_SAMPLE_CAP = 30

    # v3 instrumentation: track Clause 1 env-vocab exemption outcomes
    recovery_counter = Counter()
    recovered_samples = []
    RECOVERED_SAMPLE_CAP = 30

    survivors_after_mech = []
    mech_rej_counter = Counter()

    with open(scope_kept_path, "w") as fk, \
         open(scope_rej_path, "w") as fr, \
         open(mech_rej_path, "w") as fmr:

        fmr.write("accession\torganism\treason\n")

        for source_file, domain in ((BACT_JSONL, "bacteria"),
                                    (ARCH_JSONL, "archaea")):
            if not os.path.exists(source_file):
                print(f"MISSING {source_file}", file=sys.stderr)
                continue
            with open(source_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    total += 1
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    acc = get_accession(rec)
                    org = get_organism_name(rec)
                    decision, label, field, value, term, recovered_host = \
                        scope_filter_v3(rec)

                    # Instrumentation: track v3 Clause 1 recoveries
                    if recovered_host:
                        recovery_counter["recovered_total"] += 1
                        if decision == "KEEP":
                            recovery_counter["recovered_then_KEPT"] += 1
                        else:
                            recovery_counter[f"recovered_then_REJ_{label}"] += 1
                        if len(recovered_samples) < RECOVERED_SAMPLE_CAP:
                            attrs = biosample_attrs_dict(rec)
                            recovered_samples.append({
                                "accession": acc, "organism": org,
                                "domain": domain,
                                "host_field": recovered_host[0],
                                "host_value": recovered_host[1][:120],
                                "final_decision": decision,
                                "final_label": label,
                                "iso": attrs.get("isolation_source", "")[:80],
                                "env_broad": attrs.get("env_broad_scale", "")[:60],
                                "env_local": attrs.get("env_local_scale", "")[:60],
                                "env_medium": attrs.get("env_medium", "")[:60],
                            })

                    if decision == "REJECT":
                        rej_counter[label] += 1
                        if field:
                            rej_field_counter[field] += 1
                        if len(sampled_per_reason[label]) < SAMPLE_CAP_PER_REASON:
                            sampled_per_reason[label].append({
                                "accession": acc, "organism": org,
                                "domain": domain, "field": field,
                                "value": value[:140], "term": term,
                            })
                        if label == "invertebrate_host" and \
                           len(invert_host_samples) < INVERT_SAMPLE_CAP:
                            invert_host_samples.append({
                                "accession": acc, "organism": org,
                                "domain": domain, "field": field,
                                "value": value[:160], "term": term,
                            })
                        fr.write(json.dumps({
                            "accession": acc, "organism": org,
                            "rej_label": label, "field": field,
                            "value": value, "term": term,
                        }) + "\n")
                        continue

                    scope_kept_n += 1
                    fk.write(line + "\n")

                    if len(kept_samples) < KEPT_SAMPLE_CAP:
                        attrs = biosample_attrs_dict(rec)
                        kept_samples.append({
                            "accession": acc, "organism": org,
                            "domain": domain,
                            "iso": attrs.get("isolation_source", "")[:80],
                            "env_broad": attrs.get("env_broad_scale", "")[:60],
                            "env_local": attrs.get("env_local_scale", "")[:60],
                            "env_medium": attrs.get("env_medium", "")[:60],
                        })

                    mdec, mreason = mechanical_filter(rec, db_accs,
                                                       marker_taxids)
                    if mdec == "REJECT":
                        mech_rej_counter[mreason.split(" ", 1)[0]] += 1
                        fmr.write(f"{acc}\t{org}\t{mreason}\n")
                        continue
                    survivors_after_mech.append(rec)

    # Bin survivors
    bin_counts = Counter()
    with open(survivors_path, "w") as fs:
        fs.write("accession\torganism\ttaxid\ttotal_length\tn50\tgc_pct\t"
                 "isolation_source\tenv_broad_scale\tcategories\n")
        for rec in survivors_after_mech:
            tags = bin_category(rec)
            cats = [t[0] for t in tags] if tags else ["UNBINNED"]
            for c in cats:
                bin_counts[c] += 1
            stats = get_assembly_stats(rec)
            attrs = biosample_attrs_dict(rec)
            fs.write("\t".join([
                get_accession(rec), get_organism_name(rec), get_taxid(rec),
                str(stats["total_length"]), str(stats["n50"]),
                str(stats["gc"]),
                attrs.get("isolation_source", "")[:80],
                attrs.get("env_broad_scale", "")[:60],
                ";".join(cats),
            ]) + "\n")

    with open(bins_path, "w") as fb:
        fb.write("category\tstrength_tier\tn_survivors\n")
        sbc = {c: s for c, s, _ in CATEGORY_DEFS}
        for cat in [c for c, _, _ in CATEGORY_DEFS] + ["UNBINNED"]:
            fb.write(f"{cat}\t{sbc.get(cat,'n/a')}\t{bin_counts.get(cat,0)}\n")

    # Report
    print()
    print("=" * 76)
    print("TASK 2.1 FUNNEL v3 — Option 1 broad query, Clause 1 env exemption")
    print("=" * 76)
    print(f"Raw hits (bacteria + archaea):                       {total:>9,}")
    print(f"After §13.2 scope filter v3:                         "
          f"{scope_kept_n:>9,}  ({100*scope_kept_n/total:.1f}%)")
    print(f"After mechanical §3/§4 filter:                       "
          f"{len(survivors_after_mech):>9,}  "
          f"({100*len(survivors_after_mech)/total:.1f}%)")
    print()
    print("Scope rejection — by reason label:")
    for label, n in rej_counter.most_common():
        print(f"  {label:30s} {n:>9,}")
    print()
    print("Scope rejection — by triggering field (for the field-based reasons):")
    for f, n in rej_field_counter.most_common():
        print(f"  {f:30s} {n:>9,}")
    print()
    print("Mechanical rejection:")
    for r, n in mech_rej_counter.most_common():
        print(f"  {r:30s} {n:>9,}")
    print()
    print("=" * 76)
    print("v3 Clause 1 env-vocab EXEMPTION — recovery outcomes")
    print("=" * 76)
    rec_total = recovery_counter.get("recovered_total", 0)
    rec_kept = recovery_counter.get("recovered_then_KEPT", 0)
    print(f"Records exempted from Clause 1 rejection:           {rec_total:>9,}")
    print(f"Of those, KEPT after full evaluation:                {rec_kept:>9,}")
    other = {k.replace("recovered_then_REJ_", ""): v
             for k, v in recovery_counter.items()
             if k.startswith("recovered_then_REJ_")}
    if other:
        print("Of those, rejected by another clause:")
        for label, n in sorted(other.items(), key=lambda x: -x[1]):
            print(f"  → {label:30s} {n:>9,}")
    print()
    print(f"RECOVERED-sample eyeball (up to {RECOVERED_SAMPLE_CAP}; show host_field")
    print( "value + final disposition — confirm they're env, not slip-throughs):")
    for s in recovered_samples:
        outcome = "KEEP" if s["final_decision"] == "KEEP" \
                  else f"REJ ({s['final_label']})"
        print(f"  [{s['domain']:8s}] {s['accession']:18s} "
              f"{s['organism'][:30]:30s}  outcome={outcome}")
        print(f"      {s['host_field']}: '{s['host_value']}'")
        print(f"      iso: '{s['iso']}'")
        print(f"      env_b: '{s['env_broad']}'  env_l: '{s['env_local']}'  "
              f"env_m: '{s['env_medium']}'")
    print()
    print(f"INVERTEBRATE-HOST sample (NEW clause) — confirm these are hosts,")
    print(f"not seawater-near-coral; up to {INVERT_SAMPLE_CAP}:")
    for s in invert_host_samples:
        print(f"  [{s['domain']:8s}] {s['accession']:18s}  "
              f"{s['organism'][:38]:38s}  "
              f"tok={s['term']:12s}  field={s['field']}  "
              f"value='{s['value']}'")
    print()
    print(f"Sample of NEW reject class 'no_positive_env_signal' "
          f"(up to {SAMPLE_CAP_PER_REASON}):")
    for s in sampled_per_reason.get("no_positive_env_signal", []):
        print(f"  [{s['domain']:8s}] {s['accession']:18s}  {s['organism'][:50]}")
    print()
    print(f"KEPT-sample eyeball (first {KEPT_SAMPLE_CAP} v2 survivors):")
    for s in kept_samples:
        print(f"  [{s['domain']:8s}] {s['accession']:18s}  "
              f"{s['organism'][:38]:38s}")
        print(f"      iso: {s['iso']}")
        print(f"      env_broad: {s['env_broad']}")
        print(f"      env_local: {s['env_local']}")
        print(f"      env_medium: {s['env_medium']}")
    print()
    print("Category bins (post-hoc, on v2 mechanical-survivors):")
    print(f"  {'category':30s}  {'tier':10s}  {'n':>7s}")
    sbc = {c: s for c, s, _ in CATEGORY_DEFS}
    for cat in [c for c, _, _ in CATEGORY_DEFS] + ["UNBINNED"]:
        print(f"  {cat:30s}  {sbc.get(cat,'n/a'):10s}  "
              f"{bin_counts.get(cat,0):>7,}")

if __name__ == "__main__":
    main()
