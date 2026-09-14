# Solution Overview: GridPulse AI

## What We Built

**GridPulse AI** is an intelligent predictive maintenance and power outage mitigation platform designed for electrical transmission and distribution utilities. The system bridges the gap between hardware telemetry and meteorological intelligence: it continuously ingests high-frequency substation telemetry, calculates IEEE C57 compliant asset health indices, fuses incoming severe weather vectors, predicts equipment failure probabilities, and automatically generates prioritized emergency maintenance orders with tactical field crew pre-positioning routes.

## How It Works

1. **Substation Telemetry Ingestion**: GridPulse AI captures real-time sensor streams from transformer fleets, including top-oil temperature, mechanical tank vibration, partial discharge (PD), and dissolved gas concentrations (Acetylene $C_2H_2$, Ethylene $C_2H_4$).
2. **Health Index Calculation**: The risk engine evaluates internal physical degradation on a 0–100 scale based on weighted thermal, mechanical, dielectric, and chemical fault signatures.
3. **Severe Weather Fusion**: Real-time meteorological telemetry (wind gusts, ambient temperature heat indexes, lightning strikes within a 10km radius, precipitation) is processed through a weather stress weighting matrix.
4. **Outage Probability & Impact Scoring**: The engine correlates physical equipment vulnerability with weather threat vectors and evaluates downstream grid criticality (substation MVA capacity and downstream customer counts).
5. **AI Advisory Copilot & Pre-Positioning Dispatch**: Utilizing **IBM Bob** and **watsonx.ai**, GridPulse surfaces natural-language root-cause diagnostic assessments, recommends specific Corrective and Preventive Actions (CAPA), and constructs an optimal 24-to-72-hour mobile field crew pre-positioning itinerary before severe weather landfall.

## Architecture Flow

```
[ Substation Sensors ]       [ Meteorological Feeds ]
 (Temp, Vibration, DGA)        (Wind, Storm, Lightning)
           │                                │
           └───────────────┬────────────────┘
                           ▼
               [ GridPulse FastAPI Engine ]
               ├── Health Index (HI) Module
               ├── Weather Stress Correlator
               └── Risk Priority Index (RPI)
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
    [ IBM Bob / watsonx.ai ]    [ Operator Control Room ]
    (Diagnostics & Runbooks)     (Live Map & Crew Dispatch)
```

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Multi-Factor Risk Fusion Algorithm** | Rather than treating sensor alarms and weather advisories as disjointed alerts, compounding internal physical degradation with external meteorological load provides an accurate lead-time failure window. |
| **IEEE C57 Standard Aligned Heuristics** | Grounding Dissolved Gas Analysis (DGA) in electrical engineering standards guarantees high credibility and defensibility for utility operational leads. |
| **IBM Bob & watsonx Copilot Integration** | Translates complex sensor anomalies into clear natural-language incident summaries and step-by-step Standard Operating Procedures (SOPs) for dispatchers under high-stress conditions. |
| **FastAPI Microservice Backend** | Ensures high-throughput, low-latency processing of concurrent time-series telemetry with automated OpenAPI documentation. |

## IBM Technologies Used

- **IBM Bob**: Used as the AI SDLC partner to architect, scaffold, develop, and review code implementations, manage development workflows, and structure standard operational runbooks.
- **watsonx.ai / Granite**: Powers natural language root cause explanation, synthesizes multi-modal telemetry into concise BLUF (Bottom Line Up Front) operator briefs, and prescribes remediation actions based on utility maintenance manuals.
