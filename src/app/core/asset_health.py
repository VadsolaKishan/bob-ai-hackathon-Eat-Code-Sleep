"""
GridPulse AI — Asset Health Intelligence Module
================================================

Module: asset_health.py
Team:   Eat-Code-Sleep
Author: Kishan Vadsola (Asset Health Intelligence)

PURPOSE
-------
This module provides a dedicated, self-contained Asset Health Index (AHI)
calculation for power transformer assets.  It combines four independent
physical/chemical health signals into a single, transparent 0–100 score.

HEALTH INDEX SCALE
------------------
  100  — Pristine / excellent condition
   80  — Good; within normal operating bounds
   60  — Warning; one or more parameters showing early degradation
   40  — Poor; multiple indicators elevated; maintenance warranted
    0  — Critical; imminent failure risk

HEALTH BANDS
------------
  EXCELLENT   HI ≥ 85
  GOOD        HI ≥ 65
  WARNING     HI ≥ 45
  POOR        HI ≥ 25
  CRITICAL    HI <  25

COMPONENT SCORES (each 0–100 before weighting)
----------------------------------------------
  thermal_score           — Based on top-oil temperature (°C)
  vibration_score         — Based on tank vibration (mm/s)
  partial_discharge_score — Based on partial discharge level (pC)
  dga_score               — Derived from full DGA classification result

DEFAULT WEIGHTS
--------------
  Oil temperature  : 25 %
  Vibration        : 20 %
  Partial discharge: 25 %
  DGA condition    : 30 %

Weights are configurable via the WEIGHT_* constants at module level or by
passing a custom `weights` dict to calculate_asset_health().

RELATIONSHIP TO EquipmentRiskEngine
------------------------------------
The existing EquipmentRiskEngine.calculate_health_index() in src/app/engine.py
uses a simpler acetylene/ethylene-only DGA logic and is retained unchanged.
This module is the dedicated, richer Asset Health Intelligence layer for
Kishan Vadsola's module.  It can be imported independently and its output
consumed by Darshan's FastAPI routes without modifying engine.py.

DISCLAIMER
----------
Thresholds are representative references informed by IEC/IEEE insulation
management standards.  They are not a certified replacement for utility
protection procedures or laboratory analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

from src.app.core.dga_classifier import classify_dga, DGAResult

# ---------------------------------------------------------------------------
# Default component weights (must sum to 1.0)
# ---------------------------------------------------------------------------
WEIGHT_THERMAL    = 0.25
WEIGHT_VIBRATION  = 0.20
WEIGHT_PD         = 0.25
WEIGHT_DGA        = 0.30

# ---------------------------------------------------------------------------
# Thresholds for component score calculation
# ---------------------------------------------------------------------------

# Oil temperature (°C)
_TEMP_EXCELLENT  = 65.0   # ≤ excellent
_TEMP_GOOD       = 75.0   # ≤ good
_TEMP_WARNING    = 90.0   # ≤ warning
_TEMP_POOR       = 105.0  # ≤ poor; above = critical

# Vibration (mm/s RMS)
_VIB_EXCELLENT   = 1.5    # ≤ excellent
_VIB_GOOD        = 3.0    # ≤ good
_VIB_WARNING     = 5.0    # ≤ warning
_VIB_POOR        = 7.5    # ≤ poor; above = critical

# Partial discharge (pC peak)
_PD_EXCELLENT    = 150.0  # ≤ excellent
_PD_GOOD         = 300.0  # ≤ good
_PD_WARNING      = 600.0  # ≤ warning
_PD_POOR         = 1200.0 # ≤ poor; above = critical

# DGA severity → component score mapping
_DGA_SEVERITY_SCORES: dict[str, float] = {
    "LOW":      95.0,
    "MEDIUM":   60.0,
    "HIGH":     30.0,
    "CRITICAL":  5.0,
}

# DGA fault-type penalty applied on top of severity score
_DGA_FAULT_PENALTY: dict[str, float] = {
    "NORMAL":            0.0,
    "PARTIAL_DISCHARGE": 5.0,
    "THERMAL":          10.0,
    "ARCING":           15.0,
    "UNKNOWN":          20.0,
}

# Health band thresholds
_BAND_EXCELLENT = 85.0
_BAND_GOOD      = 65.0
_BAND_WARNING   = 45.0
_BAND_POOR      = 25.0


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class AssetHealthResult:
    """Full Asset Health calculation result."""
    health_index:             float   # 0–100 (100 = pristine)
    health_band:              str     # EXCELLENT | GOOD | WARNING | POOR | CRITICAL
    thermal_score:            float   # 0–100 component score
    vibration_score:          float   # 0–100 component score
    partial_discharge_score:  float   # 0–100 component score
    dga_score:                float   # 0–100 component score
    dga_fault_type:           str     # from DGAResult
    dga_severity:             str     # from DGAResult
    dga_confidence:           float   # 0–1 from DGAResult
    dga_ratios:               dict
    dominant_risk:            str     # name of the worst-performing component
    explanation:              str
    recommended_action:       str
    valid:                    bool = True
    validation_errors:        list = None   # type: ignore[assignment]

    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []

    def to_dict(self) -> dict:
        """Return a plain dictionary suitable for JSON serialisation."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Component score helpers
# ---------------------------------------------------------------------------

def _piecewise_score(
    value: float,
    excellent_threshold: float,
    good_threshold: float,
    warning_threshold: float,
    poor_threshold: float,
) -> float:
    """
    Map a raw sensor value to a 0–100 component health score using piecewise
    linear interpolation between four degradation thresholds.

    Score interpretation:
      100  — value ≤ excellent_threshold (no degradation)
       75  — linearly declines to good_threshold
       50  — linearly declines to warning_threshold
       25  — linearly declines to poor_threshold
        0  — value ≥ poor_threshold (critical)
    """
    if value <= excellent_threshold:
        return 100.0

    if value <= good_threshold:
        fraction = (value - excellent_threshold) / (good_threshold - excellent_threshold)
        return round(100.0 - fraction * 25.0, 2)   # 100 → 75

    if value <= warning_threshold:
        fraction = (value - good_threshold) / (warning_threshold - good_threshold)
        return round(75.0 - fraction * 25.0, 2)    # 75 → 50

    if value <= poor_threshold:
        fraction = (value - warning_threshold) / (poor_threshold - warning_threshold)
        return round(50.0 - fraction * 25.0, 2)    # 50 → 25

    # Beyond poor threshold — linear decay towards 0, floors at 0
    overshoot = (value - poor_threshold) / max(poor_threshold, 1.0)
    return max(0.0, round(25.0 - overshoot * 25.0, 2))


def _calculate_thermal_score(oil_temp_c: float) -> float:
    """0–100 score for top-oil temperature."""
    return _piecewise_score(
        oil_temp_c,
        _TEMP_EXCELLENT, _TEMP_GOOD, _TEMP_WARNING, _TEMP_POOR,
    )


def _calculate_vibration_score(vibration_mms: float) -> float:
    """0–100 score for tank vibration in mm/s RMS."""
    return _piecewise_score(
        vibration_mms,
        _VIB_EXCELLENT, _VIB_GOOD, _VIB_WARNING, _VIB_POOR,
    )


def _calculate_pd_score(partial_discharge_pc: float) -> float:
    """0–100 score for partial discharge level in picocoulombs (pC)."""
    return _piecewise_score(
        partial_discharge_pc,
        _PD_EXCELLENT, _PD_GOOD, _PD_WARNING, _PD_POOR,
    )


def _calculate_dga_score(dga_result: DGAResult) -> float:
    """
    0–100 score derived from DGA classification results.
    Uses severity as the primary driver with a fault-type penalty.
    """
    base = _DGA_SEVERITY_SCORES.get(dga_result.severity, 50.0)
    penalty = _DGA_FAULT_PENALTY.get(dga_result.fault_type, 0.0)
    return max(0.0, round(base - penalty, 2))


# ---------------------------------------------------------------------------
# Health band assignment
# ---------------------------------------------------------------------------

def _assign_health_band(health_index: float) -> str:
    """Map a 0–100 health index to a named health band."""
    if health_index >= _BAND_EXCELLENT:
        return "EXCELLENT"
    if health_index >= _BAND_GOOD:
        return "GOOD"
    if health_index >= _BAND_WARNING:
        return "WARNING"
    if health_index >= _BAND_POOR:
        return "POOR"
    return "CRITICAL"


# ---------------------------------------------------------------------------
# Dominant risk identification
# ---------------------------------------------------------------------------

def _dominant_risk(
    thermal: float,
    vibration: float,
    pd: float,
    dga: float,
    weights: dict[str, float],
) -> str:
    """
    Return the name of the component with the highest *weighted* contribution
    to overall health degradation (i.e., lowest weighted score contribution).
    """
    components = {
        "oil_temperature":    thermal   * weights["thermal"],
        "vibration":          vibration * weights["vibration"],
        "partial_discharge":  pd        * weights["pd"],
        "dga_condition":      dga       * weights["dga"],
    }
    # Lowest weighted score = worst component = dominant risk
    return min(components, key=lambda k: components[k])


# ---------------------------------------------------------------------------
# Explanation & action builders
# ---------------------------------------------------------------------------

_BAND_EXPLANATIONS: dict[str, str] = {
    "EXCELLENT": (
        "All monitored parameters are within healthy operating limits. "
        "No fault indicators detected."
    ),
    "GOOD": (
        "Asset is operating within acceptable limits. Minor deviations noted "
        "in one or more parameters; within normal variation."
    ),
    "WARNING": (
        "One or more health parameters are elevated beyond normal operating "
        "bounds. Developing degradation trend detected."
    ),
    "POOR": (
        "Multiple health parameters indicate significant equipment degradation. "
        "Risk of fault escalation is elevated."
    ),
    "CRITICAL": (
        "Asset health is severely compromised. Failure risk is imminent. "
        "Immediate intervention required."
    ),
}

_BAND_ACTIONS: dict[str, str] = {
    "EXCELLENT": (
        "Continue standard monitoring schedule. No immediate action required."
    ),
    "GOOD": (
        "Maintain regular monitoring. Review any minor anomalies at next "
        "scheduled inspection."
    ),
    "WARNING": (
        "Elevate monitoring frequency. Schedule inspection within 30 days. "
        "Investigate the dominant risk parameter."
    ),
    "POOR": (
        "Schedule urgent inspection within 7 days. Pre-stage maintenance "
        "resources. Consider load reduction on affected asset."
    ),
    "CRITICAL": (
        "Immediate action required. Notify engineering & operations teams. "
        "Consider de-energisation or emergency load transfer."
    ),
}


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def _validate_sensor_input(sensor_data: dict) -> tuple[dict, list[str]]:
    """
    Extract and validate scalar sensor fields from the input dictionary.
    Returns (validated_values, [error_messages]).
    All scalar fields default gracefully if absent.
    """
    errors: list[str] = []
    validated: dict = {}

    numeric_fields = {
        "oil_temperature_c":     65.0,
        "vibration_mms":          1.5,
        "partial_discharge_pc": 100.0,
    }

    for field_name, default in numeric_fields.items():
        raw = sensor_data.get(field_name, default)
        if raw is None:
            raw = default
        try:
            fval = float(raw)
        except (TypeError, ValueError):
            errors.append(
                f"Field '{field_name}' must be numeric; got {raw!r}. Using default {default}."
            )
            fval = default
        if fval < 0.0:
            errors.append(
                f"Field '{field_name}' cannot be negative; got {fval}. Using 0."
            )
            fval = 0.0
        validated[field_name] = fval

    return validated, errors


def _extract_gas_data(sensor_data: dict) -> dict:
    """
    Extract dissolved-gas fields from sensor_data.
    Supports both the full DGA key names (h2_ppm, …) and the legacy two-gas
    names used by the existing SUBSTATIONS telemetry (acetylene_ppm,
    ethylene_ppm) so this module works with both data formats.
    """
    gas: dict = {}
    gas_keys = ("h2_ppm", "ch4_ppm", "c2h6_ppm", "c2h4_ppm", "c2h2_ppm", "co_ppm", "co2_ppm")
    for key in gas_keys:
        if key in sensor_data:
            gas[key] = sensor_data[key]

    # Legacy compatibility: map acetylene_ppm → c2h2_ppm, ethylene_ppm → c2h4_ppm
    if "acetylene_ppm" in sensor_data and "c2h2_ppm" not in gas:
        gas["c2h2_ppm"] = sensor_data["acetylene_ppm"]
    if "ethylene_ppm" in sensor_data and "c2h4_ppm" not in gas:
        gas["c2h4_ppm"] = sensor_data["ethylene_ppm"]

    return gas


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_asset_health(
    sensor_data: dict,
    weights: Optional[dict[str, float]] = None,
) -> dict:
    """
    Calculate the Asset Health Index for a power transformer.

    Parameters
    ----------
    sensor_data : dict
        Dictionary containing sensor telemetry.  Supported keys:

          Scalar fields:
            oil_temperature_c     — Top-oil temperature in Celsius
            vibration_mms         — Tank vibration in mm/s RMS
            partial_discharge_pc  — PD level in picocoulombs

          DGA gas fields (ppm):
            h2_ppm, ch4_ppm, c2h6_ppm, c2h4_ppm, c2h2_ppm, co_ppm, co2_ppm

          Legacy DGA fields (mapped automatically):
            acetylene_ppm  → c2h2_ppm
            ethylene_ppm   → c2h4_ppm

    weights : dict, optional
        Custom weights dict with keys 'thermal', 'vibration', 'pd', 'dga'.
        Values must sum to 1.0.  Defaults to module-level WEIGHT_* constants.

    Returns
    -------
    dict
        Serialisable health result dictionary.  See AssetHealthResult for the
        full list of fields.
    """
    # -- Resolve weights --
    if weights is None:
        resolved_weights = {
            "thermal":   WEIGHT_THERMAL,
            "vibration": WEIGHT_VIBRATION,
            "pd":        WEIGHT_PD,
            "dga":       WEIGHT_DGA,
        }
    else:
        resolved_weights = weights

    # -- Validate basic input type --
    if not isinstance(sensor_data, dict):
        result = AssetHealthResult(
            health_index=0.0,
            health_band="CRITICAL",
            thermal_score=0.0,
            vibration_score=0.0,
            partial_discharge_score=0.0,
            dga_score=0.0,
            dga_fault_type="UNKNOWN",
            dga_severity="CRITICAL",
            dga_confidence=0.0,
            dga_ratios={},
            dominant_risk="input_validation",
            explanation="Input must be a dictionary of sensor readings.",
            recommended_action="Provide a valid sensor_data dictionary.",
            valid=False,
            validation_errors=["sensor_data must be a dict."],
        )
        return result.to_dict()

    # -- Validate and extract scalar fields --
    validated, errors = _validate_sensor_input(sensor_data)

    # -- Extract gas data --
    gas_data = _extract_gas_data(sensor_data)

    # -- Calculate component scores --
    thermal_score   = _calculate_thermal_score(validated["oil_temperature_c"])
    vibration_score = _calculate_vibration_score(validated["vibration_mms"])
    pd_score        = _calculate_pd_score(validated["partial_discharge_pc"])

    # -- Run DGA classifier --
    dga_result: DGAResult = classify_dga(gas_data)
    dga_score = _calculate_dga_score(dga_result)

    # -- Compute weighted Health Index --
    raw_hi = (
        thermal_score   * resolved_weights["thermal"]
        + vibration_score * resolved_weights["vibration"]
        + pd_score        * resolved_weights["pd"]
        + dga_score       * resolved_weights["dga"]
    )
    health_index = round(max(0.0, min(100.0, raw_hi)), 1)

    # -- Assign health band --
    health_band = _assign_health_band(health_index)

    # -- Identify dominant risk --
    dom_risk = _dominant_risk(
        thermal_score, vibration_score, pd_score, dga_score, resolved_weights
    )

    # -- Build explanation --
    band_explanation = _BAND_EXPLANATIONS[health_band]
    dga_note = (
        f"DGA screening indicates {dga_result.fault_type} "
        f"(severity: {dga_result.severity}, confidence: {dga_result.confidence:.0%})."
    )
    full_explanation = f"{band_explanation}  {dga_note}"

    # -- Build recommended action --
    band_action  = _BAND_ACTIONS[health_band]
    dga_action   = dga_result.recommended_focus
    recommended  = f"{band_action}  DGA advisory: {dga_action}"

    # -- Assemble result --
    result = AssetHealthResult(
        health_index=health_index,
        health_band=health_band,
        thermal_score=round(thermal_score, 2),
        vibration_score=round(vibration_score, 2),
        partial_discharge_score=round(pd_score, 2),
        dga_score=round(dga_score, 2),
        dga_fault_type=dga_result.fault_type,
        dga_severity=dga_result.severity,
        dga_confidence=dga_result.confidence,
        dga_ratios=dga_result.ratios,
        dominant_risk=dom_risk,
        explanation=full_explanation,
        recommended_action=recommended,
valid=not errors and dga_result.valid,
        validation_errors=errors + dga_result.validation_errors,
    )

    return result.to_dict()


def calculate_remaining_useful_life(
    health_index: float,
    degradation_rate: float = 0.1,
    critical_threshold: float = 25.0
) -> dict:
    """
    Estimate the Remaining Useful Life (RUL) and recommended inspection timeline
    based on the current Health Index (HI) and degradation rate per 1,000 operational hours.

    Args:
        health_index: Current asset health index (0 to 100).
        degradation_rate: Estimated HI degradation points lost per 1,000 operational hours.
        critical_threshold: HI score below which equipment failure is imminent (default 25.0).

    Returns:
        dict containing:
            - health_index: float
            - critical_threshold: float
            - estimated_operating_hours_remaining: float
            - estimated_days_remaining: float
            - urgent_inspection_required: bool
            - recommended_inspection_days: int
    """
    clamped_hi = max(0.0, min(100.0, float(health_index)))
    rate = max(0.01, float(degradation_rate))

    points_to_threshold = max(0.0, clamped_hi - critical_threshold)
    hours_remaining = round((points_to_threshold / rate) * 1000, 1)
    days_remaining = round(hours_remaining / 24.0, 1)

    urgent = clamped_hi <= critical_threshold
    if clamped_hi >= 85.0:
        recommended_inspection_days = 90
    elif clamped_hi >= 65.0:
        recommended_inspection_days = 45
    elif clamped_hi >= 45.0:
        recommended_inspection_days = 14
    elif clamped_hi >= 25.0:
        recommended_inspection_days = 5
    else:
        recommended_inspection_days = 1

    return {
        "health_index": clamped_hi,
        "critical_threshold": critical_threshold,
        "estimated_operating_hours_remaining": hours_remaining,
        "estimated_days_remaining": days_remaining,
        "urgent_inspection_required": urgent,
        "recommended_inspection_days": recommended_inspection_days,
    }

