# ✈️ Operational Airspace Monitoring Dashboard

An end-to-end aviation data pipeline and operational dashboard that tracks live flights, analyzes flight telemetry, flags operational anomalies, and retrieves spotter photography via external aviation APIs.

---

## 📌 Architecture & Features

1. **Ingestion & Data Normalization (`fetcher_py.ipynb` & `db.ipynb`):**
   - Ingests real-time state vectors from OpenSky Network API within Turkey's territorial airspace.
   - Cleans missing coordinates and applies standard aviation unit conversions:
     - Ground Speed: $m/s \rightarrow \text{knots}$ ($\times 1.94384$)
     - Barometric Altitude: $m \rightarrow \text{feet}$ ($\times 3.28084$)
     - Vertical Rate: $m/s \rightarrow \text{fpm}$ ($\times 196.85$)
   - Populates a normalized 3NF SQLite schema enforcing strict foreign key constraints across `aircraft`, `flights`, and `telemetry_logs`.

2. **Analytical Layer (`queries.sql` & `visualization.ipynb`):**
   - Common Table Expressions (CTE) and window functions partition aircraft behavior into operational phases (`Climb`, `Cruise`, `Descent`).
   - Spatial 1-degree coordinate rounding isolates regional airspace density clusters.
   - Flags vertical rate anomalies defined as $\vert{}V_{\text{rate}}\vert{} \ge 2500\text{ fpm}$.

3. **Interactive Visual Dashboard (`streamlit.py`):**
   - Real-time geospatial mapping via Plotly Express.
   - Fleet aggregation and operational anomaly inspection tables.
   - On-demand ICAO24 thumbnail extraction via the Planespotters.net API.

---

## 🛠️ Tech Stack

- **Core:** Python 3.12+
- **Database:** SQLite3
- **Data Engineering & Processing:** Pandas
- **Visualization:** Plotly Express
- **Dashboard Interface:** Streamlit
- **APIs:** OpenSky Network API, Planespotters API

---

## 📂 Project Structure

```text
.
├── airspace.db           # Normalized SQLite production database
├── fetcher_py.ipynb      # API ingestion and staging script
├── db.ipynb              # Relational schema definition & ingestion
├── visualization.ipynb   # Exploratory data visualization and prototyping
├── queries.sql           # Production SQL analytics queries
├── streamlit.py          # Interactive dashboard application
├── temp_flights.csv      # Staged flight telemetry sample
├── requirements.txt      # Production dependencies
└── .gitignore            # Version control exclusions