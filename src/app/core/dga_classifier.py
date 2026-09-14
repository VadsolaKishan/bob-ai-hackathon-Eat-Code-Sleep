"""
GridPulse AI — IEEE C57.104-Inspired DGA Fault Classification Module
=====================================================================

Module: dga_classifier.py
Team:   Eat-Code-Sleep
Author: Kishan Vadsola (Asset Health Intelligence)

PURPOSE
-------
This module implements a ratio-based Dissolved Gas Analysis (DGA) screening
classifier for power transformers.  It is *inspired by* the key gas-ratio
thresholds described in IEEE C57.104 (Guide for the Interpretation of Gases
Generated in Oil-Immersed Transformers) but is **not a certified replacement**
for a full IEEE C57.104 diagnostic procedure.  It is intended for the
GridPulse AI hackathon demonstration and educational purposes only.

HOW IT WORKS
------------
Rather than relying solely on absolute ppm thresholds, the classifier places
primary emphasis on gas *ratios*.  Fault-type reasoning follows standard
power-transformer chemistry:

  CH4 / H2     — distinguishes corona/discharge (low ratio) from thermal
                 activity (higher ratio)
  C2H2 / C2H4  — primary arcing indicator; >0.3 strongly suggests arcing
  C2H4 / C2H6  — primary thermal indicator; elevated when thermal fault
  C2H2 / CH4   — secondary arcing confirmation

Ratio-based diagnosis is more robust than absolute thresholds because gas
concentrations vary with oil volume, sampling conditions, and transformer age.

FAULT CLASSIFICATIONS RETURNED
-------------------------------
  NORMAL            — Gas pattern is consistent with healthy operation.
  PARTIAL_DISCHARGE — Hydrogen-dominated pattern suggests corona or low-energy
                      discharge activity.
  THERMAL           — Ethylene-rich, ratio pattern consistent with overheating.
  ARCING            — Acetylene elevated relative to ethylene/methane; suggests
                      high-energy electrical discharge or arc fault.

SEVERITY BANDS
--------------
  LOW       — Minor anomaly; routine monitoring adequate.
  MEDIUM    — Developing fault; increase sampling frequency.
  HIGH      — Significant degradation; schedule near-term inspection.
  CRITICAL  — Imminent failure risk; immediate action required.

DISCLAIMER
----------
This implementation is a hackathon screening heuristic.  Real utility
transformer diagnosis must follow certified IEEE C57.104 / IEC 60599
procedures performed by qualified engineers using laboratory gas-analysis
equipment.  Do not use this module for actual protection or switching
decisions on live equipment.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

# ---------------------------------------------------------------------------
# Public constants — ratio thresholds used in classification logic
# ---------------------------------------------------------------------------

# C2H2 / C2H4: key arcing indicator
_ARCING_RATIO_THRESHOLD_HIGH    = 0.3   # strong arcing signal
_ARCING_RATIO_THRESHOLD_MEDIUM  = 0.1   # moderate arcing suspicion

# C2H4 / C2H6: thermal fault indicator
_THERMAL_RATIO_THRESHOLD_HIGH   = 1.0   # clear thermal activity
_THERMAL_RATIO_THRESHOLD_MEDIUM = 0.5   # developing thermal

# CH4 / H2: discharge vs. thermal discriminator
_DISCHARGE_CH4_H2_MAX           = 0.2   # low ratio → hydrogen-dominant → discharge
_DISCHARGE_H2_ABSOLUTE_MIN      = 50.0  # ppm; H2 must be significant for PD flag

# C2H2 / CH4: secondary arcing confirmation
_ARCING_C2H2_CH4_THRESHOLD      = 0.05

# Absolute acetylene threshold that always elevates arcing suspicion (ppm)
_ACETYLENE_CRITICAL_PPM         = 5.0
_ACETYLENE_HIGH_PPM             = 2.0

# Total combustible gas (TCG) guideline levels (ppm) for severity banding
_TCG_MEDIUM_PPM  =  500.0
_TCG_HIGH_PPM    = 1500.0
_TCG_CRITICAL_PPM = 4000.0


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class GasSample:
    """Validated dissolved-gas concentrations in parts-per-million (ppm)."""
    h2_ppm:    float = 0.0
    ch4_ppm:   float = 0.0
    c2h6_ppm:  float = 0.0
    c2h4_ppm:  float = 0.0
    c2h2_ppm:  float = 0.0
    co_ppm:    float = 0.0
    co2_ppm:   float = 0.0


@dataclass
class DGARatios:
    """Computed gas ratios used for fault classification."""
    ch4_h2:    Optional[float] = None   # CH4 / H2
    c2h2_c2h4: Optional[float] = None   # C2H2 / C2H4
    c2h4_c2h6: Optional[float] = None   # C2H4 / C2H6
    c2h2_ch4:  Optional[float] = None   # C2H2 / CH4
    co2_co:    Optional[float] = None   # CO2 / CO (cellulose indicator)


@dataclass
class DGAResult:
    """Full DGA classification result returned to callers."""
    fault_type:        str               # NORMAL | PARTIAL_DISCHARGE | THERMAL | ARCING
    confidence:        float             # 0.0 – 1.0
    severity:          str               # LOW | MEDIUM | HIGH | CRITICAL
    ratios:            dict = field(default_factory=dict)
    explanation:       str = ""
    recommended_focus: str = ""
    valid:             bool = True       # False when input is invalid/incomplete
    validation_errors: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return a plain dictionary (Pydantic/JSON-serialisable)."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Step 1 — Input validation
# ---------------------------------------------------------------------------

def validate_gas_sample(raw: dict) -> tuple[Optional[GasSample], list[str]]:
    """
    Parse and validate a raw gas-sample dictionary.

    Accepts keys: h2_ppm, ch4_ppm, c2h6_ppm, c2h4_ppm, c2h2_ppm, co_ppm, co2_ppm.
    All keys are optional; missing values default to 0.0.
    Returns (GasSample, []) on success or (None, [error_messages]) on failure.
    """
    errors: list[str] = []

    if not isinstance(raw, dict):
        return None, ["Input must be a dictionary of gas concentrations."]

    gas_keys = ("h2_ppm", "ch4_ppm", "c2h6_ppm", "c2h4_ppm", "c2h2_ppm", "co_ppm", "co2_ppm")
    parsed: dict[str, float] = {}

    for key in gas_keys:
        val = raw.get(key, 0.0)
        if val is None:
            val = 0.0
        try:
            fval = float(val)
        except (TypeError, ValueError):
            errors.append(f"Gas value '{key}' must be numeric; got {val!r}.")
            fval = 0.0
        if fval < 0.0:
            errors.append(f"Gas value '{key}' cannot be negative; got {fval}.")
            fval = 0.0
        parsed[key] = fval

    if errors:
        return None, errors

    return GasSample(**parsed), []


# ---------------------------------------------------------------------------
# Step 2 — Ratio calculation
# ---------------------------------------------------------------------------

def _safe_ratio(numerator: float, denominator: float) -> Optional[float]:
    """Return numerator / denominator, or None when denominator is zero."""
    if denominator == 0.0:
        return None
    return round(numerator / denominator, 4)


def calculate_dga_ratios(sample: GasSample) -> DGARatios:
    """
    Compute standard DGA diagnostic ratios from a validated GasSample.
    Any ratio whose denominator is zero is returned as None to avoid division
    errors and to signal that the ratio is 'indeterminate' for this sample.
    """
    return DGARatios(
        ch4_h2    = _safe_ratio(sample.ch4_ppm,   sample.h2_ppm),
        c2h2_c2h4 = _safe_ratio(sample.c2h2_ppm,  sample.c2h4_ppm),
        c2h4_c2h6 = _safe_ratio(sample.c2h4_ppm,  sample.c2h6_ppm),
        c2h2_ch4  = _safe_ratio(sample.c2h2_ppm,  sample.ch4_ppm),
        co2_co    = _safe_ratio(sample.co2_ppm,    sample.co_ppm),
    )


# ---------------------------------------------------------------------------
# Step 3 — Core fault-type scorer
# ---------------------------------------------------------------------------

def _score_fault_candidates(sample: GasSample, ratios: DGARatios) -> dict[str, float]:
    """
    Return a score (0.0 – 1.0) for each fault category based on gas chemistry.
    Higher score means stronger evidence for that fault type.
    Scoring is additive and capped at 1.0 per category.
    """
    scores: dict[str, float] = {
        "NORMAL":            0.0,
        "PARTIAL_DISCHARGE": 0.0,
        "THERMAL":           0.0,
        "ARCING":            0.0,
    }

    # ---- ARCING evidence ------------------------------------------------
    # C2H2 / C2H4 is the most reliable arcing indicator
    if ratios.c2h2_c2h4 is not None:
        if ratios.c2h2_c2h4 >= _ARCING_RATIO_THRESHOLD_HIGH:
            scores["ARCING"] += 0.50
        elif ratios.c2h2_c2h4 >= _ARCING_RATIO_THRESHOLD_MEDIUM:
            scores["ARCING"] += 0.25

    # C2H2 / CH4 secondary arcing confirmation
    if ratios.c2h2_ch4 is not None:
        if ratios.c2h2_ch4 >= _ARCING_C2H2_CH4_THRESHOLD:
            scores["ARCING"] += 0.20

    # Absolute acetylene is a direct arcing marker
    if sample.c2h2_ppm >= _ACETYLENE_CRITICAL_PPM:
        scores["ARCING"] += 0.25
    elif sample.c2h2_ppm >= _ACETYLENE_HIGH_PPM:
        scores["ARCING"] += 0.15

    # ---- THERMAL evidence -----------------------------------------------
    # C2H4 / C2H6 is the primary thermal indicator
    if ratios.c2h4_c2h6 is not None:
        if ratios.c2h4_c2h6 >= _THERMAL_RATIO_THRESHOLD_HIGH:
            scores["THERMAL"] += 0.50
        elif ratios.c2h4_c2h6 >= _THERMAL_RATIO_THRESHOLD_MEDIUM:
            scores["THERMAL"] += 0.25

    # Elevated raw ethylene supports thermal
    if sample.c2h4_ppm > 50.0:
        scores["THERMAL"] += 0.20
    elif sample.c2h4_ppm > 20.0:
        scores["THERMAL"] += 0.10

    # CH4 / H2 > 1.0 indicates thermal rather than discharge
    if ratios.ch4_h2 is not None and ratios.ch4_h2 > 1.0:
        scores["THERMAL"] += 0.15

    # ---- PARTIAL DISCHARGE evidence -------------------------------------
    # Low CH4/H2 (<0.2) with meaningful H2 level suggests corona/discharge
    if sample.h2_ppm >= _DISCHARGE_H2_ABSOLUTE_MIN:
        if ratios.ch4_h2 is not None and ratios.ch4_h2 <= _DISCHARGE_CH4_H2_MAX:
            scores["PARTIAL_DISCHARGE"] += 0.55
        elif ratios.ch4_h2 is None:
            # H2 present but CH4 is zero → hydrogen-dominant, strong PD signal
            scores["PARTIAL_DISCHARGE"] += 0.55
    elif sample.h2_ppm > 0.0:
        scores["PARTIAL_DISCHARGE"] += 0.10

    # ---- NORMAL / baseline ----------------------------------------------
    # Start from a neutral base; reduce for any anomaly
    tcg = (
        sample.h2_ppm + sample.ch4_ppm + sample.c2h6_ppm
        + sample.c2h4_ppm + sample.c2h2_ppm + sample.co_ppm
    )
    if tcg < 100.0:
        scores["NORMAL"] += 0.80
    elif tcg < 300.0:
        scores["NORMAL"] += 0.40
    elif tcg < _TCG_MEDIUM_PPM:
        scores["NORMAL"] += 0.15

    # Cap all scores at 1.0
    return {k: min(v, 1.0) for k, v in scores.items()}


# ---------------------------------------------------------------------------
# Step 4 — Severity banding
# ---------------------------------------------------------------------------

def _compute_severity(sample: GasSample, fault_type: str, confidence: float) -> str:
    """
    Determine severity based on total combustible gas level, fault type, and
    classification confidence.
    """
    tcg = (
        sample.h2_ppm + sample.ch4_ppm + sample.c2h6_ppm
        + sample.c2h4_ppm + sample.c2h2_ppm + sample.co_ppm
    )

    # Arcing is always at least HIGH severity due to fire/explosion risk
    if fault_type == "ARCING" and sample.c2h2_ppm >= _ACETYLENE_CRITICAL_PPM:
        return "CRITICAL"
    if fault_type == "ARCING":
        return "HIGH"

    if tcg >= _TCG_CRITICAL_PPM:
        return "CRITICAL"
    if tcg >= _TCG_HIGH_PPM:
        return "HIGH"
    if tcg >= _TCG_MEDIUM_PPM:
        return "MEDIUM"
    if fault_type == "NORMAL":
        return "LOW"
    # Non-normal but low TCG → confidence-driven
    if confidence >= 0.5:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Step 5 — Explanation & recommended focus
# ---------------------------------------------------------------------------

_EXPLANATIONS: dict[str, str] = {
    "NORMAL": (
        "Gas concentrations and ratios are within normal operating limits. "
        "No evidence of active fault development."
    ),
    "PARTIAL_DISCHARGE": (
        "Hydrogen-rich gas pattern with low CH4/H2 ratio suggests low-energy "
        "corona or partial discharge activity within insulation voids. "
        "Common in oil-paper insulation with micro-voids or moisture ingress."
    ),
    "THERMAL": (
        "Elevated C2H4/C2H6 ratio and/or elevated ethylene indicate a thermal "
        "fault (overheating of oil or insulation). May be caused by hot spots, "
        "blocked cooling channels, or overloading."
    ),
    "ARCING": (
        "Elevated C2H2 relative to C2H4 and/or CH4 indicates high-energy "
        "electrical discharge or arc fault. Acetylene is almost exclusively "
        "produced under arcing conditions and is a critical safety indicator."
    ),
}

_RECOMMENDED: dict[str, str] = {
    "NORMAL": (
        "Continue routine DGA sampling at standard intervals (e.g., annually or "
        "per utility schedule). No immediate action required."
    ),
    "PARTIAL_DISCHARGE": (
        "Increase DGA sampling frequency. Perform on-line PD measurement if "
        "available. Investigate insulation moisture levels. Check bushing condition."
    ),
    "THERMAL": (
        "Inspect cooling system (radiators, fans, pumps, oil-flow valves). "
        "Review loading history. Schedule thermographic survey. Consider "
        "reducing load until root cause is identified."
    ),
    "ARCING": (
        "Immediate action required. Schedule urgent internal inspection. "
        "Consider de-energising asset or load-transfer to backup transformer. "
        "Notify protection & maintenance engineering teams."
    ),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_dga(gas_sample: dict) -> DGAResult:
    """
    IEEE C57.104-Inspired DGA Fault Screening Classifier.

    Parameters
    ----------
    gas_sample : dict
        Dictionary with any/all of the following keys (all optional, default 0.0):
            h2_ppm, ch4_ppm, c2h6_ppm, c2h4_ppm, c2h2_ppm, co_ppm, co2_ppm

    Returns
    -------
    DGAResult
        Structured result containing fault_type, confidence, severity, ratios,
        explanation, and recommended_focus.  Call .to_dict() for JSON output.
    """
    # -- Validate input --
    sample, errors = validate_gas_sample(gas_sample)

    if sample is None:
        return DGAResult(
            fault_type="UNKNOWN",
            confidence=0.0,
            severity="LOW",
            ratios={},
            explanation="Input validation failed. Cannot classify gas sample.",
            recommended_focus="Provide a valid gas-sample dictionary.",
            valid=False,
            validation_errors=errors,
        )

    # -- Calculate ratios --
    ratios = calculate_dga_ratios(sample)
    ratios_dict = {k: v for k, v in asdict(ratios).items() if v is not None}

    # -- Score fault candidates --
    scores = _score_fault_candidates(sample, ratios)

    # -- Select winning fault type --
    fault_type = max(scores, key=lambda k: scores[k])
    confidence = round(scores[fault_type], 3)

    # Tie-break: if two categories are within 0.05 of each other and ARCING
    # is one of them, prefer ARCING (conservative safety approach).
    if fault_type != "ARCING":
        if abs(scores["ARCING"] - scores[fault_type]) <= 0.05 and scores["ARCING"] > 0:
            fault_type = "ARCING"
            confidence = round(scores["ARCING"], 3)

    # If the top score is very low and TCG is low, declare NORMAL
    tcg = (
        sample.h2_ppm + sample.ch4_ppm + sample.c2h6_ppm
        + sample.c2h4_ppm + sample.c2h2_ppm + sample.co_ppm
    )
    if confidence < 0.15 and tcg < 50.0:
        fault_type = "NORMAL"
        confidence = round(max(scores["NORMAL"], 0.15), 3)

    # -- Determine severity --
    severity = _compute_severity(sample, fault_type, confidence)

    # -- Build validation warnings (non-fatal) --
    warn: list[str] = []
    if errors:
        warn.extend(errors)
    if tcg == 0.0:
        warn.append("All gas values are zero — sample may be absent or not yet collected.")

    return DGAResult(
        fault_type=fault_type,
        confidence=confidence,
        severity=severity,
        ratios=ratios_dict,
        explanation=_EXPLANATIONS.get(fault_type, "Classification produced an unexpected fault type."),
        recommended_focus=_RECOMMENDED.get(fault_type, "Consult a qualified transformer diagnostic engineer."),
        valid=True,
        validation_errors=warn,
    )


def calculate_duval_triangle_coordinates(
    ch4_ppm: float,
    c2h4_ppm: float,
    c2h2_ppm: float
) -> dict:
    """
    Calculate Duval Triangle 1 coordinates (percentages of CH4, C2H4, C2H2).
    According to IEC 60599 and IEEE C57.104, Duval Triangle 1 uses:
      %CH4  = 100 * CH4  / (CH4 + C2H4 + C2H2)
      %C2H4 = 100 * C2H4 / (CH4 + C2H4 + C2H2)
      %C2H2 = 100 * C2H2 / (CH4 + C2H4 + C2H2)

    Returns:
        dict with percentages and approximate Duval Triangle 1 zone (PD, T1, T2, T3, D1, D2, DT).
    """
    ch4 = max(0.0, float(ch4_ppm or 0.0))
    c2h4 = max(0.0, float(c2h4_ppm or 0.0))
    c2h2 = max(0.0, float(c2h2_ppm or 0.0))

    total = ch4 + c2h4 + c2h2
    if total <= 0.0:
        return {
            "pct_ch4": 0.0,
            "pct_c2h4": 0.0,
            "pct_c2h2": 0.0,
            "total_triangle_gas": 0.0,
            "duval_zone": "NORMAL_OR_NO_GAS",
        }

    pct_ch4 = round(100.0 * ch4 / total, 2)
    pct_c2h4 = round(100.0 * c2h4 / total, 2)
    pct_c2h2 = round(100.0 * c2h2 / total, 2)

    if pct_ch4 >= 98.0:
        zone = "PD"  # Partial Discharge
    elif pct_c2h2 >= 13.0 and pct_c2h4 < 23.0:
        zone = "D1"  # Discharges of low energy (sparking)
    elif pct_c2h2 >= 29.0 or (pct_c2h2 >= 13.0 and pct_c2h4 >= 23.0):
        zone = "D2"  # Discharges of high energy (arcing)
    elif pct_c2h4 >= 50.0:
        zone = "T3"  # Thermal fault T > 700°C
    elif pct_c2h4 >= 20.0 and pct_ch4 < 50.0:
        zone = "T2"  # Thermal fault 300 < T < 700°C
    elif pct_ch4 >= 50.0 and pct_c2h4 < 20.0 and pct_c2h2 < 4.0:
        zone = "T1"  # Thermal fault T < 300°C
    else:
        zone = "DT"  # Mixed electrical & thermal

    return {
        "pct_ch4": pct_ch4,
        "pct_c2h4": pct_c2h4,
        "pct_c2h2": pct_c2h2,
        "total_triangle_gas": round(total, 2),
        "duval_zone": zone,
    }


def get_dga_severity_weight(severity: str) -> float:
    """
    Map DGA severity string to a normalized risk engine weighting factor (0.0 to 1.0).

    Args:
        severity: One of 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'

    Returns:
        float: Normalized severity factor (0.0 for LOW to 1.0 for CRITICAL)
    """
    weights = {
        "LOW": 0.0,
        "MEDIUM": 0.35,
        "HIGH": 0.70,
        "CRITICAL": 1.0,
    }
    return weights.get(str(severity).upper(), 0.0)


