"""
GridPulse AI — Chat Intent & Asset Resolution Module
Deterministic intent classification and entity resolution for natural-language queries.
"""
import re
from enum import Enum
from typing import Optional, List, Tuple, Dict, Any


class ChatIntent(str, Enum):
    ASSET_LOOKUP = "ASSET_LOOKUP"
    ASSET_HEALTH = "ASSET_HEALTH"
    DGA_ANALYSIS = "DGA_ANALYSIS"
    WEATHER_RISK = "WEATHER_RISK"
    RISK_ANALYSIS = "RISK_ANALYSIS"
    CASCADE_IMPACT = "CASCADE_IMPACT"
    CRITICAL_FACILITY = "CRITICAL_FACILITY"
    CREW_DISPATCH = "CREW_DISPATCH"
    MAINTENANCE = "MAINTENANCE"
    TOP_RISK_ASSETS = "TOP_RISK_ASSETS"
    COMPARE_ASSETS = "COMPARE_ASSETS"
    COMPOUND_RISK = "COMPOUND_RISK"
    LIGHTNING_ASSETS = "LIGHTNING_ASSETS"
    DGA_WARNING_ASSETS = "DGA_WARNING_ASSETS"
    UNKNOWN_ASSET = "UNKNOWN_ASSET"
    GREETING = "GREETING"
    GENERAL_GRID = "GENERAL_GRID"


# Monitored active network assets
VALID_ASSET_IDS = {
    "TX-001", "TX-002", "TX-003", "TX-004",
    "SUB-001", "SUB-002",
    "FD-001", "FD-002", "FD-003",
    "CF-001"
}

# Canonical mapping for asset aliases and names
KNOWN_ALIASES: Dict[str, str] = {
    # T-aliases
    "T-101": "TX-001",
    "T101": "TX-001",
    "T-202": "TX-002",
    "T202": "TX-002",
    "T-303": "TX-003",
    "T303": "TX-003",
    "T-404": "TX-004",
    "T404": "TX-004",
    # F-aliases
    "F-101": "FD-001",
    "F101": "FD-001",
    "F-202": "FD-002",
    "F202": "FD-002",
    "F-303": "FD-003",
    "F303": "FD-003",
    # Direct IDs normalized
    "TX001": "TX-001",
    "TX002": "TX-002",
    "TX003": "TX-003",
    "TX004": "TX-004",
    "SUB001": "SUB-001",
    "SUB002": "SUB-002",
    "FD001": "FD-001",
    "FD002": "FD-002",
    "FD003": "FD-003",
    "CF001": "CF-001",
}

# Name pattern mappings
NAME_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"north\s+cascade\s+primary\s+substation", re.IGNORECASE), "SUB-001"),
    (re.compile(r"north\s+cascade\s+substation", re.IGNORECASE), "SUB-001"),
    (re.compile(r"metro\s+harbor\s+substation", re.IGNORECASE), "SUB-002"),
    (re.compile(r"metro\s+harbor\s+distribution\s+substation", re.IGNORECASE), "SUB-002"),
    (re.compile(r"north\s+cascade\s+primary\s+transformer", re.IGNORECASE), "TX-001"),
    (re.compile(r"north\s+cascade\s+transformer", re.IGNORECASE), "TX-001"),
    (re.compile(r"primary\s+transformer\s+in\s+north\s+cascade", re.IGNORECASE), "TX-001"),
    (re.compile(r"north\s+cascade", re.IGNORECASE), "TX-001"),
    (re.compile(r"harbor\s+view\s+distribution\s+transformer", re.IGNORECASE), "TX-002"),
    (re.compile(r"harbor\s+view\s+transformer", re.IGNORECASE), "TX-002"),
    (re.compile(r"harbor\s+view", re.IGNORECASE), "TX-002"),
    (re.compile(r"east\s+valley\s+industrial\s+transformer", re.IGNORECASE), "TX-003"),
    (re.compile(r"east\s+valley\s+transformer", re.IGNORECASE), "TX-003"),
    (re.compile(r"east\s+valley", re.IGNORECASE), "TX-003"),
    (re.compile(r"valley\s+solar\s+intertie\s+transformer", re.IGNORECASE), "TX-004"),
    (re.compile(r"valley\s+solar\s+transformer", re.IGNORECASE), "TX-004"),
    (re.compile(r"valley\s+solar", re.IGNORECASE), "TX-004"),
    (re.compile(r"north\s+feeder", re.IGNORECASE), "FD-001"),
    (re.compile(r"harbor\s+feeder", re.IGNORECASE), "FD-002"),
    (re.compile(r"city\s+general\s+hospital", re.IGNORECASE), "CF-001"),
    (re.compile(r"hospital", re.IGNORECASE), "CF-001"),
]

# Non-asset words that must never be treated as asset IDs
NON_ASSET_WORDS = {
    "the", "a", "an", "this", "that", "these", "those", "grid", "all", "asset", "assets",
    "system", "systems", "transformer", "transformers", "substation", "substations",
    "feeder", "feeders", "first", "highest", "most", "worst", "our", "we", "crews", "crew",
    "team", "teams", "your", "name", "today", "now", "here", "current", "risk", "risks",
    "health", "weather", "storm", "cascade", "impact", "failure", "facilities", "facility",
    "hospital", "maintenance", "action", "actions", "suggestion", "suggestions", "order",
    "orders", "plan", "plans", "work", "report", "overview", "status", "condition", "details",
    "detqails", "info", "information", "what", "which", "where", "how", "why", "who",
    "hello", "hi", "hey", "help", "please", "urgent", "critical", "warning", "routine",
    "check", "inspect", "inspection", "dispatch", "position", "positioned", "affect", "affected"
}


def resolve_asset_ids(text: str) -> List[str]:
    """
    Extracts and resolves all asset IDs referenced in the input text.
    Supports exact IDs, case-insensitive IDs, common aliases, and full/partial names.
    If an unknown asset is explicitly queried, returns the candidate ID.
    Returns ordered unique list of resolved asset IDs.
    """
    found: List[str] = []

    # 1. Match explicit known IDs: TX-001, SUB-001, FD-001, CF-001, etc.
    exact_id_matches = re.findall(r"\b(TX|SUB|FD|CF)-?(\d{3})\b", text, re.IGNORECASE)
    for prefix, num in exact_id_matches:
        aid = f"{prefix.upper()}-{num}"
        if aid not in found:
            found.append(aid)

    # 2. Match aliases: T-101, F-101, etc.
    alias_matches = re.findall(r"\b(T|F)-?(\d{3})\b", text, re.IGNORECASE)
    for prefix, num in alias_matches:
        alias_key = f"{prefix.upper()}-{num}"
        resolved = KNOWN_ALIASES.get(alias_key) or KNOWN_ALIASES.get(f"{prefix.upper()}{num}")
        if resolved and resolved not in found:
            found.append(resolved)

    # 3. Match by name patterns
    for pattern, mapped_id in NAME_PATTERNS:
        if pattern.search(text) and mapped_id not in found:
            found.append(mapped_id)

    # 4. Check for arbitrary alphanumeric code patterns like dd-2, tx-999, ab-12, t-999
    code_matches = re.findall(r"\b([a-zA-Z]{1,5}[-_]\d{1,4})\b", text, re.IGNORECASE)
    for code in code_matches:
        code_upper = code.strip().upper()
        if code.lower() in NON_ASSET_WORDS:
            continue
        # Resolve aliases if known
        resolved = KNOWN_ALIASES.get(code_upper) or KNOWN_ALIASES.get(code_upper.replace("-", ""))
        target = resolved or code_upper
        if target not in found:
            found.append(target)

    # 5. Check explicitly queried asset patterns like "details of XYZ", "status of asset XYZ-99"
    if not found:
        match = re.search(
            r"(?:details?|detqails?|info(?:rmation)?|status|condition)\s+of\s+(?:the\s+|a\s+|an\s+|asset\s+|transformer\s+|substation\s+|feeder\s+)*([a-zA-Z0-9_-]+)",
            text,
            re.IGNORECASE
        )
        if not match:
            match = re.search(
                r"\b(?:asset|transformer|substation|feeder)\s+([a-zA-Z0-9_-]+)",
                text,
                re.IGNORECASE
            )

        if match:
            cand = match.group(1).strip()
            if cand.lower() not in NON_ASSET_WORDS and len(cand) >= 2:
                # Must look like an asset identifier (contains digits or hyphen/underscore)
                if re.search(r"\d", cand) or "-" in cand or "_" in cand:
                    cand_upper = cand.upper()
                    resolved = KNOWN_ALIASES.get(cand_upper) or cand_upper
                    if resolved not in found:
                        found.append(resolved)

    return found


def detect_chat_intent(message: str, resolved_assets: List[str]) -> ChatIntent:
    """
    Deterministically detects the operator's primary intent from query text and resolved assets.
    """
    msg = message.lower().strip()

    # 0. Unknown/unrecognized asset queried: e.g. "details of dd-2", "status of TX-999"
    if resolved_assets and any(aid not in VALID_ASSET_IDS for aid in resolved_assets):
        return ChatIntent.UNKNOWN_ASSET

    # 1. Greetings & Bot Identity / Capability Queries
    greeting_exact = {"hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "help"}
    if msg in greeting_exact or any(
        phrase in msg for phrase in [
            "who are you", "what is your name", "what can you do", "how do you work",
            "how does this work", "what are you", "introduce yourself"
        ]
    ):
        return ChatIntent.GREETING

    # 2. Asset comparison: "Compare TX-001 and TX-004", "Why is TX-001 prioritized over TX-004?"
    if len(resolved_assets) >= 2 or "compare" in msg or "prioritized over" in msg or "priority over" in msg:
        return ChatIntent.COMPARE_ASSETS

    # 3. Compound risk: "both poor health and severe weather", "poor health and weather"
    if ("poor health" in msg or "degraded" in msg) and ("weather" in msg or "storm" in msg):
        return ChatIntent.COMPOUND_RISK

    # 4. Lightning queries: "affected by lightning", "lightning risk"
    if "lightning" in msg:
        if resolved_assets:
            return ChatIntent.WEATHER_RISK
        return ChatIntent.LIGHTNING_ASSETS

    # 5. Cascading failure: "what happens if TX-001 fails", "cascading failure", "most dangerous cascade", "if TX-001 fails", "cascade risk for this asset"
    if any(k in msg for k in ["what happens if", "if tx-", "fails", "fail", "cascad", "downstream", "outage spread", "n-1"]):
        return ChatIntent.CASCADE_IMPACT

    # 6. DGA warning signs across assets: "which assets have dga warning", "assets with dga"
    if ("which" in msg or "assets" in msg or "transformers" in msg) and ("dga" in msg or "gas" in msg or "arcing" in msg or "acetylene" in msg):
        if not resolved_assets:
            return ChatIntent.DGA_WARNING_ASSETS

    # 7. DGA Analysis for specific asset: "What does DGA indicate for TX-001?", "DGA of TX-001"
    if any(k in msg for k in ["dga", "dissolved gas", "acetylene", "ethylene", "hydrogen", "arcing", "methane"]):
        return ChatIntent.DGA_ANALYSIS

    # 8. Asset Health Index: "health index of TX-001", "condition of TX-001", "health score"
    if any(k in msg for k in ["health index", "health score", "ahi", "health band", "condition of"]):
        return ChatIntent.ASSET_HEALTH

    # 9. Critical facility queries: "critical facilities affected", "facilities affected", "hospital", "water plant"
    if any(k in msg for k in ["critical facilit", "hospital", "water plant", "airport", "facilities at risk", "facilities affected", "facility risk"]):
        return ChatIntent.CRITICAL_FACILITY

    # 10. Crew dispatch & pre-positioning: "where should crews be positioned", "which crew", "crew pre-position"
    if any(k in msg for k in ["crew", "dispatch", "pre-position", "staging", "48 hour", "where should crews"]):
        return ChatIntent.CREW_DISPATCH

    # 11. Maintenance: "what should the maintenance team do today", "work order", "maintenance suggestions"
    if any(k in msg for k in ["maintenance", "work order", "workorder", "repair", "maintenance team", "maintenance suggestion", "maintenance action", "maintenance task", "schedule maintenance"]):
        return ChatIntent.MAINTENANCE

    # 12. Top risk / inspect first / immediate inspection: "what asset should we inspect first", "highest risk", "which asset needs immediate inspection"
    if any(k in msg for k in [
        "inspect first", "highest risk", "worst", "top risk", "most critical",
        "priority asset", "immediate inspection", "needs immediate", "inspect immediately",
        "which asset needs", "which asset should we inspect", "what to inspect"
    ]):
        return ChatIntent.TOP_RISK_ASSETS

    # 13. Weather risk: "how does current weather affect risk", "storm vulnerability", "weather affecting"
    if any(k in msg for k in ["weather", "storm", "wind", "hurricane", "flood", "rain", "vulnerable to the storm"]):
        return ChatIntent.WEATHER_RISK

    # 14. Risk analysis for specific asset: "Why is TX-001 high risk?", "risk of TX-001"
    if "why" in msg or "risk" in msg:
        if resolved_assets:
            return ChatIntent.RISK_ANALYSIS

    # 15. Asset lookup if asset mentioned
    if resolved_assets:
        return ChatIntent.ASSET_LOOKUP

    # 16. General summary / grid status
    if any(k in msg for k in ["summary", "overview", "status", "grid status", "control-room", "control room", "how does the grid look", "grid health"]):
        return ChatIntent.GENERAL_GRID

    return ChatIntent.GENERAL_GRID
