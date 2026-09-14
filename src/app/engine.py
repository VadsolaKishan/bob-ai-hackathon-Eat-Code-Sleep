"""
GridPulse AI - Core Outage Prediction & Equipment Risk Advisor
"""
from typing import Dict, List, Optional
import math
import random

class EquipmentRiskEngine:
    """
    Computes Health Index (HI) and Outage Probability for electrical substation assets
    based on thermal, vibration, partial discharge, and Dissolved Gas Analysis (DGA).
    """

    @staticmethod
    def calculate_health_index(sensor_data: Dict[str, float]) -> float:
        """
        Calculates Asset Health Index from 0 (Critical/Failure Imminent) to 100 (Pristine).
        Based on weighted factors:
        - Top-oil temperature (normal: <75°C, warning: >90°C)
        - Dissolved Gas Analysis (Acetylene C2H2, Ethylene C2H4, Hydrogen H2)
        - Partial Discharge (pC)
        - Tank Vibration (mm/s)
        """
        oil_temp = sensor_data.get("oil_temperature_c", 65.0)
        vibration = sensor_data.get("vibration_mms", 1.5)
        partial_discharge = sensor_data.get("partial_discharge_pc", 120.0)
        acetylene = sensor_data.get("acetylene_ppm", 1.0) # C2H2 is key indicator of arcing
        ethylene = sensor_data.get("ethylene_ppm", 20.0) # C2H4 thermal fault

        # Thermal score (0-25)
        if oil_temp <= 65:
            thermal_score = 25.0
        elif oil_temp <= 85:
            thermal_score = 25.0 - (oil_temp - 65) * 0.75
        else:
            thermal_score = max(0.0, 10.0 - (oil_temp - 85) * 0.5)

        # Vibration score (0-20)
        if vibration <= 2.0:
            vib_score = 20.0
        elif vibration <= 4.5:
            vib_score = 20.0 - (vibration - 2.0) * 4.0
        else:
            vib_score = max(0.0, 10.0 - (vibration - 4.5) * 3.0)

        # Partial Discharge score (0-25)
        if partial_discharge <= 200:
            pd_score = 25.0
        elif partial_discharge <= 500:
            pd_score = 25.0 - (partial_discharge - 200) * 0.05
        else:
            pd_score = max(0.0, 10.0 - (partial_discharge - 500) * 0.02)

        # DGA Gas score (0-30) - Arcing is critical
        if acetylene > 3.0:
            dga_score = 5.0 # High risk of arcing breakdown
        elif ethylene > 50.0:
            dga_score = 15.0
        else:
            dga_score = 30.0

        return round(thermal_score + vib_score + pd_score + dga_score, 1)

    @staticmethod
    def calculate_weather_stress(weather_data: Dict[str, float]) -> float:
        """
        Calculates weather stress multiplier (0.0 to 1.0) based on:
        - Wind gusts / storm speed (km/h)
        - Ambient heatwave index (°C)
        - Lightning strike activity per 10km radius
        - Precipitation / flood risk (mm/h)
        """
        wind = weather_data.get("wind_speed_kmh", 20.0)
        temp = weather_data.get("ambient_temp_c", 28.0)
        lightning_hits = weather_data.get("lightning_strikes_10km", 0)
        precipitation = weather_data.get("precip_mmh", 0.0)

        stress = 0.0
        # Wind stress
        if wind > 70:
            stress += 0.35
        elif wind > 45:
            stress += 0.20

        # Ambient extreme heat stress
        if temp > 40:
            stress += 0.30
        elif temp > 35:
            stress += 0.15

        # Lightning strikes
        if lightning_hits > 10:
            stress += 0.25
        elif lightning_hits > 3:
            stress += 0.15

        # Flooding / rain
        if precipitation > 30:
            stress += 0.20
        elif precipitation > 15:
            stress += 0.10

        return min(round(stress, 2), 1.0)

    @classmethod
    def evaluate_outage_risk(
        cls,
        health_index: float,
        weather_stress: float,
        critical_customers_count: int,
        capacity_mva: float
    ) -> Dict[str, any]:
        """
        Synthesizes internal equipment health with external weather threat to produce:
        - Failure Probability (%)
        - Risk Classification (Low, Medium, High, Critical)
        - Grid Impact Severity (Score 1-100)
        - Recommended Immediate Mitigation
        """
        # Lower health index = higher internal vulnerability (0 to 1)
        internal_vulnerability = (100.0 - health_index) / 100.0

        # Fused failure probability
        raw_prob = (internal_vulnerability * 0.65) + (weather_stress * 0.35)
        # Non-linear scaling for compounding risk
        compounded_prob = min(round((raw_prob ** 1.3) * 100.0, 1), 99.4)

        # Criticality / Impact based on downstream capacity and customer vulnerability
        impact_score = min(
            100.0,
            round((capacity_mva * 0.3) + (min(critical_customers_count, 50000) / 500.0), 1)
        )

        # Composite Risk Priority Index (RPI) = Probability * Impact
        rpi = round((compounded_prob * impact_score) / 100.0, 1)

        if rpi >= 60.0 or compounded_prob >= 75.0:
            risk_level = "CRITICAL"
            recommended_action = "Pre-position emergency repair crew immediately; initiate contingency load transfer to adjacent feeders."
        elif rpi >= 40.0 or compounded_prob >= 50.0:
            risk_level = "HIGH"
            recommended_action = "Schedule urgent thermal inspection within 6 hours; stage mobile transformer backup unit."
        elif rpi >= 20.0:
            risk_level = "MEDIUM"
            recommended_action = "Elevate sensor polling frequency to 1-minute intervals; monitor dissolved gas trends."
        else:
            risk_level = "LOW"
            recommended_action = "Routine monitoring under standard operating limits."

        return {
            "health_index": health_index,
            "weather_stress": weather_stress,
            "failure_probability_pct": compounded_prob,
            "impact_score": impact_score,
            "risk_priority_index": rpi,
            "risk_level": risk_level,
            "recommended_action": recommended_action
        }
