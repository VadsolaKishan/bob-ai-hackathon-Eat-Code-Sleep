# Problem Statement: Power Outage Prediction & Grid Equipment Failure Advisor (U1)

## Background

Electrical power transmission and distribution (T&D) networks form the backbone of modern civilization. Within this complex infrastructure, high-voltage substations and power transformers are critical, capital-intensive nodes. When a primary 400kV or 220kV transformer catastrophically fails, the repercussions ripple instantly through interconnected feeders, causing widespread regional blackouts, disabling municipal water filtration plants, severing communications networks, and shutting down medical centers.

## The Problem

Electric utility operators currently face two compounding operational blind spots:
1. **Reliance on Static, Calendar-Based Maintenance**: Large transformers undergo visual checks and periodic oil testing every 6 to 12 months. However, internal insulation degradation, mechanical winding displacement, and contact overheating develop rapidly under dynamic grid stress.
2. **Siloed Sensor Data and Meteorological Weather Feeds**: Substation Supervisory Control and Data Acquisition (SCADA) telemetry—including oil temperatures, vibration sensors, and partial discharge monitors—operates completely detached from incoming severe weather warnings. When a severe windstorm, lightning barrage, or heatwave strikes, equipment with pre-existing latent mechanical or dielectric vulnerabilities suffers catastrophic burnouts that could have been predicted weeks or hours in advance.

## Who is Affected

- **Grid Dispatchers & Control Room Engineers**: Operating under severe cognitive overload during storm surges without real-time failure probability rankings across assets.
- **Utility Asset Health Managers**: Tasked with maintaining aging power transformer fleets (many older than 30 years) with limited maintenance budgets.
- **Emergency Field Response Crews**: Frequently dispatched reactively in treacherous weather after lines fail, leading to prolonged Mean Time to Recovery (MTTR) and crew safety hazards.
- **Commercial & Residential Consumers**: Millions of power customers who experience unexpected service interruptions.

## Why It Matters

- **Financial Impact**: Power transformer and substation failures cost utilities upwards of **$1M per hour** in outage penalties, lost revenue, and replacement costs (a high-voltage transformer costs between $3M–$8M with replacement lead times exceeding 24 months).
- **Societal & Safety Risk**: Cascading blackout events shut down hospitals, emergency dispatch centers, and public water supply systems.
- **Extreme Weather Amplification**: Climate change has increased the frequency of microburst winds, excessive heatwaves, and lightning storms, compounding the stress on degraded equipment.

## Why Existing Solutions Fall Short

- **Legacy SCADA Alarms**: Provide only binary trip threshold alarms (e.g., "Temperature > 95°C") when a catastrophic flashover or breakdown is already occurring, leaving zero lead time for mitigation.
- **Independent Weather Dashboards**: Show general regional weather forecasts without computing localized physical stresses on specific substation transformer components.
- **Lack of Actionable Crew Orchestration**: Existing systems do not translate predictive risk into prioritized emergency crew pre-positioning routes prior to storm landfall.
