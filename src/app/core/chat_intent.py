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
        # Resolve aliases if known
        resolved = KNOWN_ALIASES.get(code_upper) or KNOWN_ALIASES.get(code_upper.replace("-", ""))
        target = resolved or code_upper
        if target not in found:
            found.append(target)

    # 5. If still no asset was matched, check phrase queries like "details of XYZ", "info on ABC"
    if not found:
        match = re.search(
            r"(?:details?|detqails?|info(?:rmation)?|status|condition|about|what\s+is|health|risk|maintenance)\s+(?:of\s+|for\s+|about\s+|on\s+)?(?:the\s+|a\s+|an\s+|asset\s+|transformer\s+|substation\s+|feeder\s+)*([a-zA-Z0-9_-]+)",
            text,
            re.IGNORECASE
        )
        if match:
            cand = match.group(1).strip()
            stopwords = {"the", "a", "an", "this", "that", "grid", "all", "asset", "assets", "system", "transformer", "transformers", "substation", "substations", "first", "highest", "most", "worst", "our", "we", "crews", "crew"}
            if cand.lower() not in stopwords and len(cand) >= 2:
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

    # 1. Asset comparison: "Compare TX-001 and TX-004", "Why is TX-001 prioritized over TX-004?"
    if len(resolved_assets) >= 2 or "compare" in msg or "prioritized over" in msg or "priority over" in msg:
        return ChatIntent.COMPARE_ASSETS

    # 2. Compound risk: "both poor health and severe weather", "poor health and weather"
    if ("poor health" in msg or "degraded" in msg) and ("weather" in msg or "storm" in msg):
        return ChatIntent.COMPOUND_RISK

    # 3. Lightning queries: "affected by lightning", "lightning risk"
    if "lightning" in msg:
        if resolved_assets:
            return ChatIntent.WEATHER_RISK
        return ChatIntent.LIGHTNING_ASSETS

    # 4. Cascading failure: "what happens if TX-001 fails", "cascading failure", "most dangerous cascade", "if TX-001 fails"
    if any(k in msg for k in ["what happens if", "if tx-", "fails", "fail", "cascad", "downstream", "outage spread"]):
        return ChatIntent.CASCADE_IMPACT

    # 5. DGA warning signs across assets: "which assets have dga warning", "assets with dga"
    if ("which" in msg or "assets" in msg or "transformers" in msg) and ("dga" in msg or "gas" in msg or "arcing" in msg or "acetylene" in msg):
        if not resolved_assets:
            return ChatIntent.DGA_WARNING_ASSETS

    # 6. DGA Analysis for specific asset: "What does DGA indicate for TX-001?", "DGA of TX-001"
    if any(k in msg for k in ["dga", "dissolved gas", "acetylene", "ethylene", "hydrogen", "arcing", "methane"]):
        return ChatIntent.DGA_ANALYSIS

    # 7. Asset Health Index: "health index of TX-001", "condition of TX-001", "health score"
    if any(k in msg for k in ["health index", "health score", "ahi", "health band", "condition of"]):
        return ChatIntent.ASSET_HEALTH

    # 8. Weather risk: "vulnerable to the storm", "weather affecting", "storm vulnerability"
    if any(k in msg for k in ["weather", "storm", "wind", "hurricane", "flood", "rain", "vulnerable to the storm"]):
        return ChatIntent.WEATHER_RISK

    # 9. Critical facility queries: "critical facilities affected", "facilities affected", "hospital", "water plant"
    if any(k in msg for k in ["critical facilit", "hospital", "water plant", "airport", "facilities affected"]):
        return ChatIntent.CRITICAL_FACILITY

    # 10. Crew dispatch & pre-positioning: "where should crews be positioned", "which crew", "crew pre-position"
    if any(k in msg for k in ["crew", "dispatch", "pre-position", "staging", "48 hour", "where should crews"]):
        return ChatIntent.CREW_DISPATCH

    # 11. Maintenance: "what maintenance should be performed", "work order", "actions for"
    if any(k in msg for k in ["maintenance", "work order", "repair", "inspection required", "what action"]):
        return ChatIntent.MAINTENANCE

    # 12. Top risk / inspect first: "what asset should we inspect first", "highest risk", "most critical asset"
    if any(k in msg for k in ["inspect first", "highest risk", "worst", "top risk", "most critical", "priority asset"]):
        return ChatIntent.TOP_RISK_ASSETS

    # 13. Risk analysis for specific asset: "Why is TX-001 high risk?", "risk of TX-001"
    if "why" in msg or "risk" in msg:
        if resolved_assets:
            return ChatIntent.RISK_ANALYSIS

    # 14. Asset lookup if asset mentioned
    if resolved_assets:
        return ChatIntent.ASSET_LOOKUP

    # 15. General summary
    if any(k in msg for k in ["summary", "overview", "status", "grid status", "control-room", "control room"]):
        return ChatIntent.GENERAL_GRID

    return ChatIntent.GENERAL_GRID
