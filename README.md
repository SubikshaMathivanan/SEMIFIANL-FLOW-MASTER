# Multi-Agent Hospital Resource & Patient-Flow Optimization System

An AI-driven forecasting and decision-support pipeline that predicts hospital bed shortages before they happen, and recommends actionable patient transfers between departments — built with a 4-agent architecture, Prophet time-series forecasting, and an interactive dashboard.

> This is **not** a hospital management/ERP system. There is no manual data entry, login, or record-keeping CRUD anywhere in this project — every output (forecasts, anomaly flags, urgency scores, transfer recommendations) is computed by a model or algorithm.

---

## The Problem

Hospitals typically track bed occupancy manually and reactively. By the time a shortage in a department (say, ICU during a seasonal outbreak) becomes visible, it's already too late to plan ahead — leading to delayed transfers, overcrowding, and poor patient outcomes. There is no predictive lead time for administrators to reallocate resources in advance.

## The Solution

A sequential 4-agent AI pipeline that:
1. **Forecasts** department-wise bed occupancy 14 days ahead
2. **Tracks** real-time bed availability against that forecast
3. **Detects anomalies** and ranks departments by urgency
4. **Recommends** specific, explainable patient transfers between departments

---

## The Four Agents

### 1. Forecasting Agent
Trains a separate **Prophet** time-series model per department on historical daily occupancy and forecasts the next 14 days. Forecasts are clipped to each department's physical bed capacity so predictions never exceed what's physically possible.

### 2. Bed Availability Agent
Converts the forecast into operational numbers: `available_beds = total_beds − forecast_occupied_beds` and `occupancy_rate`, grounded against the latest real snapshot of each department.

### 3. Anomaly & Priority Agent
Flags a day as anomalous when occupancy crosses an **85% threshold**, or when it's a statistical spike (**z-score ≥ 1.5** above that department's historical mean). Computes a weighted 0–100 urgency score per department:
- 50% — peak forecasted occupancy
- 30% — frequency of anomaly days
- 20% — bed margin pressure

Departments are then ranked by this score.

### 4. Recommendation & Transfer Agent
For every department predicted to be short on beds, finds the department with the most spare capacity on that same day as the "donor," and recommends transferring `min(shortage, donor_slack × 0.4)` patients — capped at 40% of the donor's slack so no other department gets overloaded. Explanations are rule-based (templated) by default for reliability, with an optional LLM mode (via LangChain + Groq/OpenAI) for richer, AI-generated explanations — automatically falling back to rule-based text if no API key is set or the call fails.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Forecasting | Prophet |
| Data handling | Pandas, NumPy |
| Backend API | FastAPI |
| Frontend dashboard | Streamlit |
| Optional LLM explanations | LangChain + Groq / OpenAI |
| Orchestration | Python (sequential pipeline) |

---

## Project Structure

hospital-mas/
├── agents/
│ ├── forecasting_agent.py
│ ├── bed_availability_agent.py
│ ├── anomaly_priority_agent.py
│ └── recommendation_agent.py
├── backend/
│ └── app.py # FastAPI server
├── dashboard/
│ └── streamlit_app.py # Streamlit frontend
├── data/
│ └── generate_data.py # Synthetic dataset generator
├── orchestrator.py # Runs all 4 agents in sequence
├── requirements.txt
├── .env.example
└── README.md


---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/SubikshaMathivanan/Hospital-Mas.git
cd Hospital-Mas
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate the dataset
```bash
python data/generate_data.py
```

### 4. Run the full pipeline standalone
```bash
python orchestrator.py
```

### 5. Start the backend API
```bash
uvicorn backend.app:app --reload
```

### 6. Launch the dashboard
```bash
streamlit run dashboard/streamlit_app.py
```

### (Optional) Enable LLM-generated explanations
Copy `.env.example` to `.env` and add your Groq or OpenAI API key. If skipped, the system automatically uses rule-based explanations instead — no functionality is lost.

---

## Why Synthetic Data?

Public hospital datasets rarely provide clean, daily, department-level bed occupancy — most are aggregated or one-time snapshots. `generate_data.py` produces 18 months of realistic daily data across 5 departments (ICU, Surgery, Pediatrics, Emergency, General Medicine), with a deliberately injected demand surge so the forecasting and anomaly-detection agents have something meaningful to catch. The generator can be swapped for real hospital data as long as the same 6 columns (date, department, total_beds, occupied_beds, admissions, discharges) are matched.

---

## Expected Outcome

A working demonstration where a user can view historical occupancy trends, receive AI-generated shortage forecasts and anomaly alerts, and get explainable, actionable recommendations for resource reallocation — showcasing the practical integration of agentic AI and data science in healthcare resource management.

---

## Future Scope

- Integrate real hospital datasets via a hospital's own data pipeline
- Move from a sequential pipeline to a true decentralized multi-agent system with agent-to-agent negotiation
- Add authentication and role-based views for different hospital staff
- Extend forecasting to include staffing and equipment resources, not just beds

---

## Author

**M. Subiksha**
B.Tech (AI & ML), Silver Oak University