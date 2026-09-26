# PulseFlow

A single-file Streamlit demonstration of multi-agent hospital resource and
patient-flow optimization with authentication, role-based access control,
audit logging, seven-day forecasts, anomaly detection, and operational
recommendations.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The recommendation agent works without external services through its built-in
rules. To enable Groq recommendations, add `GROQ_API_KEY` to a local `.env`
file. You can optionally set `GROQ_MODEL`; it defaults to
`llama-3.1-8b-instant`.

## Demo users

| Username | Password | Role |
| --- | --- | --- |
| `admin` | `Admin@123` | ADMIN |
| `dr_sharma` | `Doctor@123` | DOCTOR |
| `nurse_priya` | `Nurse@123` | HEAD_NURSE |
| `viewer_01` | `View@123` | VIEWER |

All application state is intentionally session-local for this project demo.
Restarting the Streamlit session resets bed counts, roles, decisions, and the
audit log.
