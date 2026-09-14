"""
GridPulse AI — Unit Tests for DGA Classification and Asset Health Intelligence
==============================================================================

Module: tests/test_dga.py
Team:   Eat-Code-Sleep
Author: Kishan Vadsola (Asset Health Intelligence)

Covers:
  1.  Healthy gas sample              → NORMAL
  2.  Partial discharge sample        → PARTIAL_DISCHARGE
  3.  Thermal fault sample            → THERMAL
  4.  Arcing sample                   → ARCING
  5.  Zero denominator safety         → no exception; indeterminate ratios = None
  6.  Missing optional gases          → handled with defaults
  7.  Invalid input type              → DGAResult.valid = False
  8.  Negative gas value              → validation error, still returns result
  9.  Ratio values are correct        → spot-check arithmetic
  10. Confidence is in [0.0, 1.0]
  11. Severity is a known value
  12. Asset health returns 0–100
  13. Asset health bands are correct
  14. Legacy acetylene_ppm / ethylene_ppm mapping works
  15. All-zero gas sample             → NORMAL / no crash

Run with:
    pytest tests/test_dga.py -v
"""

import json
import os
import pytest

from src.app.core.dga_classifier import (
    classify_dga,
    validate_gas_sample,
    calculate_dga_ratios,
    GasSample,
    DGAResult,
)
from src.app.core.asset_health import calculate_asset_health


# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

HEALTHY_GAS = {
    "h2_ppm":   22.0,
    "ch4_ppm":  18.0,
    "c2h6_ppm": 12.0,
    "c2h4_ppm":  6.0,
    "c2h2_ppm":  0.05,
    "co_ppm":  110.0,
    "co2_ppm": 820.0,
}

PD_GAS = {
    "h2_ppm":   340.0,
    "ch4_ppm":   55.0,
    "c2h6_ppm":  20.0,
    "c2h4_ppm":  14.0,
    "c2h2_ppm":   0.3,
    "co_ppm":    95.0,
    "co2_ppm":  640.0,
}

THERMAL_GAS = {
    "h2_ppm":    60.0,
    "ch4_ppm":   95.0,
    "c2h6_ppm":  38.0,
    "c2h4_ppm":  72.0,
    "c2h2_ppm":   3.8,
    "co_ppm":   280.0,
    "co2_ppm": 2200.0,
}

ARCING_GAS = {
    "h2_ppm":   180.0,
    "ch4_ppm":  120.0,
    "c2h6_ppm":  45.0,
    "c2h4_ppm":  88.0,
    "c2h2_ppm":  38.5,
    "co_ppm":   520.0,
    "co2_ppm": 3100.0,
}

KNOWN_SEVERITY_VALUES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
KNOWN_FAULT_TYPES     = {"NORMAL", "PARTIAL_DISCHARGE", "THERMAL", "ARCING", "UNKNOWN"}
KNOWN_HEALTH_BANDS    = {"EXCELLENT", "GOOD", "WARNING", "POOR", "CRITICAL"}


# ===========================================================================
# Part 1 — DGA Classification
# ===========================================================================

class TestDGANormal:
    """Test 1: healthy gas sample → NORMAL classification."""

    def test_fault_type_is_normal(self):
        result = classify_dga(HEALTHY_GAS)
        assert result.fault_type == "NORMAL", (
            f"Expected NORMAL, got {result.fault_type}. Scores debug: ratios={result.ratios}"
        )

    def test_severity_is_low(self):
        result = classify_dga(HEALTHY_GAS)
        assert result.severity == "LOW"

    def test_result_is_valid(self):
        result = classify_dga(HEALTHY_GAS)
        assert result.valid is True

    def test_confidence_in_range(self):
        result = classify_dga(HEALTHY_GAS)
        assert 0.0 <= result.confidence <= 1.0


class TestDGAPartialDischarge:
    """Test 2: PD gas sample → PARTIAL_DISCHARGE."""

    def test_fault_type_is_pd(self):
        result = classify_dga(PD_GAS)
        assert result.fault_type == "PARTIAL_DISCHARGE", (
            f"Expected PARTIAL_DISCHARGE, got {result.fault_type}. ratios={result.ratios}"
        )

    def test_severity_not_low(self):
        result = classify_dga(PD_GAS)
        assert result.severity in ("MEDIUM", "HIGH", "CRITICAL")

    def test_confidence_in_range(self):
        result = classify_dga(PD_GAS)
        assert 0.0 <= result.confidence <= 1.0


class TestDGAThermal:
    """Test 3: thermal gas sample → THERMAL classification."""

    def test_fault_type_is_thermal(self):
        result = classify_dga(THERMAL_GAS)
        assert result.fault_type == "THERMAL", (
            f"Expected THERMAL, got {result.fault_type}. ratios={result.ratios}"
        )

    def test_severity_elevated(self):
        result = classify_dga(THERMAL_GAS)
        assert result.severity in ("MEDIUM", "HIGH", "CRITICAL")

    def test_confidence_in_range(self):
        result = classify_dga(THERMAL_GAS)
        assert 0.0 <= result.confidence <= 1.0


class TestDGAArcing:
    """Test 4: arcing gas sample → ARCING classification."""

    def test_fault_type_is_arcing(self):
        result = classify_dga(ARCING_GAS)
        assert result.fault_type == "ARCING", (
            f"Expected ARCING, got {result.fault_type}. ratios={result.ratios}"
        )

    def test_severity_is_critical(self):
        result = classify_dga(ARCING_GAS)
        assert result.severity == "CRITICAL"

    def test_confidence_in_range(self):
        result = classify_dga(ARCING_GAS)
        assert 0.0 <= result.confidence <= 1.0


class TestDGAZeroDenominator:
    """Test 5: zero denominators do not raise exceptions; ratios return None."""

    def test_no_crash_on_zero_h2(self):
        gas = {**HEALTHY_GAS, "h2_ppm": 0.0}
        result = classify_dga(gas)
        assert isinstance(result, DGAResult)

    def test_ch4_h2_ratio_is_none_when_h2_zero(self):
        sample = GasSample(h2_ppm=0.0, ch4_ppm=15.0)
        ratios = calculate_dga_ratios(sample)
        assert ratios.ch4_h2 is None, "ch4_h2 should be None when H2 is zero"

    def test_c2h2_c2h4_ratio_is_none_when_c2h4_zero(self):
        sample = GasSample(c2h2_ppm=5.0, c2h4_ppm=0.0)
        ratios = calculate_dga_ratios(sample)
        assert ratios.c2h2_c2h4 is None

    def test_all_zeros_no_crash(self):
        result = classify_dga({k: 0.0 for k in HEALTHY_GAS})
        assert isinstance(result, DGAResult)
        assert result.fault_type in KNOWN_FAULT_TYPES


class TestDGAMissingGases:
    """Test 6: missing optional gas keys are handled with defaults."""

    def test_empty_dict_no_crash(self):
        result = classify_dga({})
        assert isinstance(result, DGAResult)
        assert result.valid is True

    def test_partial_keys_only(self):
        result = classify_dga({"h2_ppm": 300.0, "ch4_ppm": 50.0})
        assert isinstance(result, DGAResult)
        assert result.fault_type in KNOWN_FAULT_TYPES

    def test_none_values_treated_as_zero(self):
        result = classify_dga({"h2_ppm": None, "c2h2_ppm": None})
        assert isinstance(result, DGAResult)
        assert result.valid is True


class TestDGAInvalidInput:
    """Test 7: invalid input type produces a controlled error result."""

    def test_string_input_is_invalid(self):
        result = classify_dga("not-a-dict")
        assert result.valid is False
        assert result.fault_type == "UNKNOWN"
        assert len(result.validation_errors) > 0

    def test_none_input_is_invalid(self):
        result = classify_dga(None)
        assert result.valid is False

    def test_integer_input_is_invalid(self):
        result = classify_dga(42)
        assert result.valid is False


class TestDGANegativeValues:
    """Test 8: negative gas values produce a validation error but still return a result."""

    def test_negative_value_produces_error(self):
        result = classify_dga({"h2_ppm": -10.0})
        assert len(result.validation_errors) > 0

    def test_result_is_still_returned(self):
        result = classify_dga({"h2_ppm": -10.0, "c2h2_ppm": -5.0})
        assert isinstance(result, DGAResult)
        assert result.fault_type in KNOWN_FAULT_TYPES


class TestDGARatioCalculation:
    """Test 9: ratio values are calculated correctly."""

    def test_ch4_h2_ratio_exact(self):
        sample = GasSample(h2_ppm=100.0, ch4_ppm=50.0)
        ratios = calculate_dga_ratios(sample)
        assert ratios.ch4_h2 == pytest.approx(0.5, rel=1e-4)

    def test_c2h2_c2h4_ratio_exact(self):
        sample = GasSample(c2h4_ppm=80.0, c2h2_ppm=40.0)
        ratios = calculate_dga_ratios(sample)
        assert ratios.c2h2_c2h4 == pytest.approx(0.5, rel=1e-4)

    def test_c2h4_c2h6_ratio_exact(self):
        sample = GasSample(c2h6_ppm=20.0, c2h4_ppm=40.0)
        ratios = calculate_dga_ratios(sample)
        assert ratios.c2h4_c2h6 == pytest.approx(2.0, rel=1e-4)

    def test_co2_co_ratio_exact(self):
        sample = GasSample(co_ppm=100.0, co2_ppm=1000.0)
        ratios = calculate_dga_ratios(sample)
        assert ratios.co2_co == pytest.approx(10.0, rel=1e-4)


class TestDGAConfidenceSeverityRange:
    """Test 10 & 11: confidence and severity are within documented ranges."""

    @pytest.mark.parametrize("gas_sample", [
        HEALTHY_GAS, PD_GAS, THERMAL_GAS, ARCING_GAS,
    ])
    def test_confidence_bounded(self, gas_sample):
        result = classify_dga(gas_sample)
        assert 0.0 <= result.confidence <= 1.0, (
            f"Confidence {result.confidence} out of [0,1] for sample {gas_sample}"
        )

    @pytest.mark.parametrize("gas_sample", [
        HEALTHY_GAS, PD_GAS, THERMAL_GAS, ARCING_GAS,
    ])
    def test_severity_is_known(self, gas_sample):
        result = classify_dga(gas_sample)
        assert result.severity in KNOWN_SEVERITY_VALUES, (
            f"Unknown severity value: {result.severity}"
        )

    @pytest.mark.parametrize("gas_sample", [
        HEALTHY_GAS, PD_GAS, THERMAL_GAS, ARCING_GAS,
    ])
    def test_fault_type_is_known(self, gas_sample):
        result = classify_dga(gas_sample)
        assert result.fault_type in KNOWN_FAULT_TYPES


# ===========================================================================
# Part 2 — Asset Health Index
# ===========================================================================

class TestAssetHealthIndex:
    """Test 12 & 13: health_index is 0–100 and bands are correct."""

    def _make_sensor(self, gas: dict, temp: float = 65.0, vib: float = 1.5, pd: float = 100.0) -> dict:
        return {
            "oil_temperature_c":    temp,
            "vibration_mms":        vib,
            "partial_discharge_pc": pd,
            **gas,
        }

    def test_healthy_hi_in_range(self):
        sensor = self._make_sensor(HEALTHY_GAS)
        result = calculate_asset_health(sensor)
        hi = result["health_index"]
        assert 0.0 <= hi <= 100.0

    def test_healthy_band_is_excellent_or_good(self):
        sensor = self._make_sensor(HEALTHY_GAS)
        result = calculate_asset_health(sensor)
        assert result["health_band"] in ("EXCELLENT", "GOOD")

    def test_arcing_hi_in_range(self):
        sensor = self._make_sensor(ARCING_GAS, temp=104.0, vib=7.0, pd=1400.0)
        result = calculate_asset_health(sensor)
        hi = result["health_index"]
        assert 0.0 <= hi <= 100.0

    def test_arcing_band_is_poor_or_critical(self):
        sensor = self._make_sensor(ARCING_GAS, temp=104.0, vib=7.0, pd=1400.0)
        result = calculate_asset_health(sensor)
        assert result["health_band"] in ("POOR", "CRITICAL")

    def test_arcing_hi_lower_than_healthy(self):
        healthy_result = calculate_asset_health(self._make_sensor(HEALTHY_GAS))
        arcing_result  = calculate_asset_health(
            self._make_sensor(ARCING_GAS, temp=104.0, vib=7.0, pd=1400.0)
        )
        assert arcing_result["health_index"] < healthy_result["health_index"]

    def test_hi_never_below_zero(self):
        worst_case = {
            "oil_temperature_c":    200.0,
            "vibration_mms":        50.0,
            "partial_discharge_pc": 10000.0,
            **{k: 9999.0 for k in ARCING_GAS},
        }
        result = calculate_asset_health(worst_case)
        assert result["health_index"] >= 0.0

    def test_hi_never_above_100(self):
        best_case = {
            "oil_temperature_c":    20.0,
            "vibration_mms":        0.0,
            "partial_discharge_pc": 0.0,
            **HEALTHY_GAS,
        }
        result = calculate_asset_health(best_case)
        assert result["health_index"] <= 100.0

    def test_health_band_is_known(self):
        for gas in (HEALTHY_GAS, PD_GAS, THERMAL_GAS, ARCING_GAS):
            sensor = self._make_sensor(gas)
            result = calculate_asset_health(sensor)
            assert result["health_band"] in KNOWN_HEALTH_BANDS

    def test_result_has_required_keys(self):
        sensor = self._make_sensor(HEALTHY_GAS)
        result = calculate_asset_health(sensor)
        required = {
            "health_index", "health_band",
            "thermal_score", "vibration_score", "partial_discharge_score", "dga_score",
            "dga_fault_type", "dga_severity", "dga_confidence", "dga_ratios",
            "dominant_risk", "explanation", "recommended_action",
        }
        for key in required:
            assert key in result, f"Missing key in health result: {key}"

    def test_invalid_sensor_data_type(self):
        result = calculate_asset_health("not-a-dict")
        assert result["valid"] is False

    def test_partial_discharge_score_degrades_with_high_pd(self):
        low_pd  = calculate_asset_health({"partial_discharge_pc": 100.0})
        high_pd = calculate_asset_health({"partial_discharge_pc": 1500.0})
        assert high_pd["partial_discharge_score"] < low_pd["partial_discharge_score"]

    def test_thermal_score_degrades_with_high_temp(self):
        cool = calculate_asset_health({"oil_temperature_c": 55.0})
        hot  = calculate_asset_health({"oil_temperature_c": 110.0})
        assert hot["thermal_score"] < cool["thermal_score"]


class TestLegacyGasMapping:
    """Test 14: legacy acetylene_ppm / ethylene_ppm keys are mapped correctly."""

    def test_acetylene_ethylene_mapping(self):
        """
        Legacy two-gas mapping: acetylene_ppm → c2h2_ppm, ethylene_ppm → c2h4_ppm.

        The existing SUBSTATIONS telemetry (main.py) only carries acetylene_ppm
        and ethylene_ppm.  This test verifies that:
          1. The legacy fields are accepted without errors.
          2. The returned health index is in the valid 0–100 range.
          3. The mapped gas values appear in the DGA ratios (c2h2_c2h4 ratio
             is computed from the mapped keys).

        Note: with only two gases supplied (no H2/CH4/C2H6 context) the DGA
        classifier sensibly falls back to NORMAL because TCG is low and the
        single available ratio (C2H2/C2H4 ≈ 0.062) is below the medium arcing
        threshold.  This is the correct conservative behaviour for incomplete
        gas data.
        """
        sensor = {
            "oil_temperature_c":    92.4,
            "vibration_mms":         4.8,
            "partial_discharge_pc": 540.0,
            "acetylene_ppm":          4.2,
            "ethylene_ppm":          68.0,
        }
        result = calculate_asset_health(sensor)
        # Mapping must succeed without errors
        assert result["valid"] is True
        # Health index must be in valid range
        assert 0.0 <= result["health_index"] <= 100.0
        # The C2H2/C2H4 ratio should be present (mapping worked)
        assert "c2h2_c2h4" in result["dga_ratios"], (
            "c2h2_c2h4 ratio should be computed from the mapped legacy gas keys"
        )

    def test_legacy_returns_valid_hi(self):
        sensor = {
            "oil_temperature_c": 75.0,
            "acetylene_ppm": 0.5,
            "ethylene_ppm":  15.0,
        }
        result = calculate_asset_health(sensor)
        assert 0.0 <= result["health_index"] <= 100.0


class TestAllZeroGasSample:
    """Test 15: all-zero gas sample does not crash."""

    def test_all_zeros_dga_no_crash(self):
        result = classify_dga({k: 0.0 for k in HEALTHY_GAS})
        assert isinstance(result, DGAResult)

    def test_all_zeros_asset_health_no_crash(self):
        sensor = {
            "oil_temperature_c":    65.0,
            "vibration_mms":         1.5,
            "partial_discharge_pc": 100.0,
            **{k: 0.0 for k in HEALTHY_GAS},
        }
        result = calculate_asset_health(sensor)
        assert 0.0 <= result["health_index"] <= 100.0


# ===========================================================================
# Integration test: load telemetry JSON and verify all records produce valid
# health assessments
# ===========================================================================

class TestTelemetryIntegration:
    """Integration: every record in sample_telemetry.json produces a valid result."""

    _telemetry_path = os.path.join(
        os.path.dirname(__file__), "..", "src", "data", "telemetry", "sample_telemetry.json"
    )

    def _load_telemetry(self):
        with open(self._telemetry_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_telemetry_file_is_valid_json(self):
        records = self._load_telemetry()
        assert isinstance(records, list)
        assert len(records) >= 5, "Expected at least 5 telemetry records"

    def test_all_records_produce_valid_hi(self):
        records = self._load_telemetry()
        for rec in records:
            result = calculate_asset_health(rec)
            hi = result["health_index"]
            assert 0.0 <= hi <= 100.0, (
                f"HI out of range for {rec.get('asset_id', 'unknown')}: {hi}"
            )

    def test_healthy_record_has_good_or_excellent_band(self):
        records = self._load_telemetry()
        healthy = next(r for r in records if r.get("expected_fault_type") == "NORMAL")
        result = calculate_asset_health(healthy)
        assert result["health_band"] in ("EXCELLENT", "GOOD"), (
            f"Healthy record should be EXCELLENT/GOOD, got {result['health_band']}"
        )

    def test_arcing_record_has_poor_or_critical_band(self):
        records = self._load_telemetry()
        arcing = next(r for r in records if r.get("expected_fault_type") == "ARCING")
        result = calculate_asset_health(arcing)
        assert result["health_band"] in ("POOR", "CRITICAL"), (
            f"Arcing record should be POOR/CRITICAL, got {result['health_band']}"
        )


class TestRemainingUsefulLife:
    """Tests for calculate_remaining_useful_life in asset_health module."""

    def test_healthy_asset_has_long_rul(self):
        from src.app.core.asset_health import calculate_remaining_useful_life

        rul = calculate_remaining_useful_life(health_index=90.0, degradation_rate=0.1)
        assert rul["estimated_operating_hours_remaining"] > 500000
        assert rul["estimated_days_remaining"] > 20000
        assert not rul["urgent_inspection_required"]
        assert rul["recommended_inspection_days"] == 90

    def test_degraded_asset_requires_urgent_inspection(self):
        from src.app.core.asset_health import calculate_remaining_useful_life

        rul = calculate_remaining_useful_life(health_index=20.0, degradation_rate=0.1)
        assert rul["estimated_operating_hours_remaining"] == 0.0
        assert rul["urgent_inspection_required"] is True
        assert rul["recommended_inspection_days"] == 1

    def test_boundary_clamping_hi(self):
        from src.app.core.asset_health import calculate_remaining_useful_life

        rul_high = calculate_remaining_useful_life(health_index=150.0)
        assert rul_high["health_index"] == 100.0

        rul_low = calculate_remaining_useful_life(health_index=-10.0)
        assert rul_low["health_index"] == 0.0


class TestDuvalTriangle:
    """Tests for calculate_duval_triangle_coordinates in dga_classifier module."""

    def test_all_zeros_handled_gracefully(self):
        from src.app.core.dga_classifier import calculate_duval_triangle_coordinates

        res = calculate_duval_triangle_coordinates(0.0, 0.0, 0.0)
        assert res["total_triangle_gas"] == 0.0
        assert res["pct_ch4"] == 0.0
        assert res["duval_zone"] == "NORMAL_OR_NO_GAS"

    def test_thermal_fault_t3_classification(self):
        from src.app.core.dga_classifier import calculate_duval_triangle_coordinates

        res = calculate_duval_triangle_coordinates(ch4_ppm=20.0, c2h4_ppm=75.0, c2h2_ppm=5.0)
        assert res["pct_c2h4"] == 75.0
        assert res["duval_zone"] == "T3"

    def test_arcing_d2_classification(self):
        from src.app.core.dga_classifier import calculate_duval_triangle_coordinates

        res = calculate_duval_triangle_coordinates(ch4_ppm=30.0, c2h4_ppm=30.0, c2h2_ppm=40.0)
        assert res["pct_c2h2"] == 40.0
        assert res["duval_zone"] == "D2"

    def test_percentages_sum_to_100(self):
        from src.app.core.dga_classifier import calculate_duval_triangle_coordinates

        res = calculate_duval_triangle_coordinates(ch4_ppm=45.0, c2h4_ppm=35.0, c2h2_ppm=20.0)
        total_pct = res["pct_ch4"] + res["pct_c2h4"] + res["pct_c2h2"]
        assert abs(total_pct - 100.0) < 0.1


class TestDGASeverityWeight:
    """Tests for get_dga_severity_weight in dga_classifier module."""

    def test_severity_weight_mappings(self):
        from src.app.core.dga_classifier import get_dga_severity_weight

        assert get_dga_severity_weight("LOW") == 0.0
        assert get_dga_severity_weight("MEDIUM") == 0.35
        assert get_dga_severity_weight("HIGH") == 0.70
        assert get_dga_severity_weight("CRITICAL") == 1.0

    def test_unknown_severity_returns_zero(self):
        from src.app.core.dga_classifier import get_dga_severity_weight

        assert get_dga_severity_weight("UNKNOWN") == 0.0
        assert get_dga_severity_weight("") == 0.0



