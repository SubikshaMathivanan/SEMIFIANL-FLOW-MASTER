"""
PulseFlow — Multi-Agent Hospital Resource & Patient-Flow Optimization System

Run with: streamlit run app.py

╔══════════════╦══════════╦═══════════╦════════════╦══════════╗
║ Feature      ║ ADMIN    ║ DOCTOR    ║ HEAD_NURSE ║ VIEWER   ║
╠══════════════╬══════════╬═══════════╬════════════╬══════════╣
║ Overview     ║ R/W      ║ R         ║ R/W        ║ R        ║
║ Forecasts    ║ R        ║ R         ║ R          ║ R        ║
║ Anomalies    ║ R        ║ R         ║ R          ║ ✖        ║
║ Recommen.    ║ R        ║ R/Approve ║ R          ║ ✖        ║
║ Admin Panel  ║ ✔        ║ ✖         ║ ✖          ║ ✖        ║
║ Audit Log    ║ ✔        ║ ✖         ║ ✖          ║ ✖        ║
╚══════════════╩══════════╩═══════════╩════════════╩══════════╝

Demo credentials:
    admin / Admin@123
    dr_sharma / Doctor@123
    nurse_priya / Nurse@123
    viewer_01 / View@123
"""

# 2. ALL IMPORTS
from __future__ import annotations

import html
import io
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from statsmodels.tsa.holtwinters import ExponentialSmoothing

try:
    from prophet import Prophet
except ImportError:
    Prophet = None

try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None


# 3. LOAD ENVIRONMENT
load_dotenv()


# ── 4. CONFIG ─────────────────────────────────────────────────────────────────
APP_NAME = "PulseFlow"
HOSPITAL_NAME = "CityCare Medical Center"
DEPARTMENTS = ["ICU", "ER", "General", "Pediatrics", "Oncology"]
TOTAL_BEDS = {"ICU": 32, "ER": 48, "General": 128, "Pediatrics": 44, "Oncology": 36}
DEFAULT_OCCUPIED = {"ICU": 26, "ER": 42, "General": 94, "Pediatrics": 31, "Oncology": 25}
CONFIDENCE_GATE = 0.60
ANOMALY_Z_THRESHOLD = 1.8
SESSION_TIMEOUT = timedelta(minutes=30)
LOCKOUT_DURATION = timedelta(minutes=5)
MAX_FAILED_ATTEMPTS = 3
HISTORY_DAYS = 90

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "ADMIN": {
        "view_overview",
        "view_forecasts",
        "view_anomalies",
        "view_recommendations",
        "update_beds",
        "run_pipeline",
        "manage_users",
        "view_audit_log",
    },
    "DOCTOR": {
        "view_overview",
        "view_forecasts",
        "view_anomalies",
        "view_recommendations",
        "review_recommendations",
    },
    "HEAD_NURSE": {
        "view_overview",
        "view_forecasts",
        "view_anomalies",
        "view_recommendations",
        "update_beds",
    },
    "VIEWER": {"view_overview", "view_forecasts"},
}

ROLE_COLORS = {
    "ADMIN": ("#9f2f26", "#fee9e7"),
    "DOCTOR": ("#2559a7", "#eaf2ff"),
    "HEAD_NURSE": ("#187665", "#e6f6f1"),
    "VIEWER": ("#5d6472", "#edf0f3"),
}


# ── 5. SECURITY CONFIG ────────────────────────────────────────────────────────
# These are bcrypt hashes only; plaintext passwords are never stored in the app.
INITIAL_USERS: dict[str, dict[str, Any]] = {
    "admin": {
        "password_hash": "$2b$12$PY7/HzA7knLTxBzeu.FSFOewx8JPrm4uj0ZFdOxKdkUml9unjWo.G",
        "role": "ADMIN",
        "last_login": None,
    },
    "dr_sharma": {
        "password_hash": "$2b$12$0zabsNGFFjiubvXItEtl.eY2PVlVO6Ldt1MYFn6vmjKCt4bpuCxSy",
        "role": "DOCTOR",
        "last_login": None,
    },
    "nurse_priya": {
        "password_hash": "$2b$12$6v1W92v958mnpKXu9kgakuvXJ4g5LqGCgn9n8p2YzGamWScU.BF7O",
        "role": "HEAD_NURSE",
        "last_login": None,
    },
    "viewer_01": {
        "password_hash": "$2b$12$FuUEk1wkGxOdqbey.aVSqeeBaXFlZgL32.aa9MaMlT78btwLzIXPq",
        "role": "VIEWER",
        "last_login": None,
    },
}


# ── 6. DATA GENERATOR ─────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def generate_historical_data(days: int = HISTORY_DAYS) -> pd.DataFrame:
    """Generate deterministic demo occupancy history for every department."""
    rng = np.random.default_rng(42)
    dates = pd.date_range(
        end=pd.Timestamp.now(tz="UTC").normalize() - pd.Timedelta(days=1),
        periods=days,
        freq="D",
    ).tz_localize(None)
    rows: list[dict[str, Any]] = []
    base_rates = {"ICU": 0.78, "ER": 0.76, "General": 0.71, "Pediatrics": 0.65, "Oncology": 0.69}

    for department in DEPARTMENTS:
        total = TOTAL_BEDS[department]
        for index, date in enumerate(dates):
            weekly = 0.06 * np.sin(2 * np.pi * index / 7)
            trend = 0.0007 * index
            noise = rng.normal(0, 0.045)
            rate = np.clip(base_rates[department] + weekly + trend + noise, 0.35, 0.98)
            occupied = int(round(rate * total))
            rows.append(
                {
                    "date": date,
                    "department": department,
                    "occupied": occupied,
                    "total_beds": total,
                    "occupancy_rate": occupied / total,
                }
            )
    return pd.DataFrame(rows)


# ── 7. AGENT 1: BED AVAILABILITY AGENT ───────────────────────────────────────
@dataclass
class BedAvailabilityAgent:
    """Reads current bed occupancy and derives capacity metrics."""

    def run(self, occupied_beds: dict[str, int]) -> pd.DataFrame:
        rows = []
        for department in DEPARTMENTS:
            occupied = int(occupied_beds[department])
            total = TOTAL_BEDS[department]
            rows.append(
                {
                    "department": department,
                    "occupied": occupied,
                    "total_beds": total,
                    "available": total - occupied,
                    "occupancy_rate": occupied / total,
                }
            )
        return pd.DataFrame(rows)


# ── 8. AGENT 2: FORECASTING AGENT ─────────────────────────────────────────────
@dataclass
class ForecastingAgent:
    """Creates a seven-day Prophet forecast, with ETS as a reliable fallback."""

    horizon: int = 7

    @staticmethod
    def _confidence(actual: np.ndarray, fitted: np.ndarray) -> float:
        mae = float(np.mean(np.abs(actual - fitted)))
        scale = max(float(np.mean(actual)), 1.0)
        return float(np.clip(1.0 - (mae / scale), 0.0, 0.99))

    def _prophet_forecast(self, values: pd.DataFrame) -> tuple[pd.DataFrame, float]:
        model_data = values[["date", "occupied"]].rename(columns={"date": "ds", "occupied": "y"})
        model = Prophet(
            weekly_seasonality=True,
            daily_seasonality=False,
            yearly_seasonality=False,
            interval_width=0.80,
        )
        model.fit(model_data)
        future = model.make_future_dataframe(periods=self.horizon, freq="D")
        prediction = model.predict(future)
        history_prediction = prediction.iloc[: len(model_data)]["yhat"].to_numpy()
        confidence = self._confidence(model_data["y"].to_numpy(), history_prediction)
        result = prediction.tail(self.horizon)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
        return result.rename(columns={"ds": "date"}), confidence

    def _ets_forecast(self, values: pd.DataFrame) -> tuple[pd.DataFrame, float]:
        series = values["occupied"].astype(float).to_numpy()
        model = ExponentialSmoothing(
            series,
            trend="add",
            seasonal="add",
            seasonal_periods=7,
            initialization_method="estimated",
        ).fit(optimized=True)
        predicted = np.asarray(model.forecast(self.horizon), dtype=float)
        residuals = series - np.asarray(model.fittedvalues, dtype=float)
        spread = max(float(np.std(residuals)), 1.0)
        future_dates = pd.date_range(
            start=values["date"].max() + pd.Timedelta(days=1),
            periods=self.horizon,
            freq="D",
        )
        result = pd.DataFrame(
            {
                "date": future_dates,
                "yhat": predicted,
                "yhat_lower": predicted - (1.28 * spread),
                "yhat_upper": predicted + (1.28 * spread),
            }
        )
        confidence = self._confidence(series, np.asarray(model.fittedvalues, dtype=float))
        return result, confidence

    def run(self, history: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float], str]:
        forecasts: list[pd.DataFrame] = []
        confidence_scores: dict[str, float] = {}
        engine = "Prophet" if Prophet is not None else "ETS"

        for department in DEPARTMENTS:
            values = history[history["department"] == department].sort_values("date")
            try:
                result, confidence = (
                    self._prophet_forecast(values) if Prophet is not None else self._ets_forecast(values)
                )
            except (ValueError, RuntimeError, np.linalg.LinAlgError):
                result, confidence = self._ets_forecast(values)
                engine = "ETS"

            total = TOTAL_BEDS[department]
            for column in ("yhat", "yhat_lower", "yhat_upper"):
                result[column] = result[column].clip(lower=0, upper=total).round(1)
            result["department"] = department
            result["occupancy_rate"] = result["yhat"] / total
            forecasts.append(result)
            confidence_scores[department] = round(confidence, 3)

        return pd.concat(forecasts, ignore_index=True), confidence_scores, engine


# ── 9. AGENT 3: ANOMALY PRIORITY AGENT ───────────────────────────────────────
@dataclass
class AnomalyPriorityAgent:
    """Detects unusual current occupancy and ranks operational priority."""

    threshold: float = ANOMALY_Z_THRESHOLD

    def run(
        self,
        history: pd.DataFrame,
        availability: pd.DataFrame,
        confidence_scores: dict[str, float],
    ) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []
        for current in availability.to_dict("records"):
            department = current["department"]
            values = history[history["department"] == department]["occupancy_rate"]
            std = max(float(values.std()), 0.01)
            z_score = (float(current["occupancy_rate"]) - float(values.mean())) / std
            confidence = confidence_scores[department]
            gated = confidence < CONFIDENCE_GATE

            if current["occupancy_rate"] >= 0.90 or z_score >= 2.5:
                priority = "Critical"
            elif current["occupancy_rate"] >= 0.80 or z_score >= self.threshold:
                priority = "High"
            elif current["occupancy_rate"] >= 0.70:
                priority = "Moderate"
            else:
                priority = "Low"

            rows.append(
                {
                    "department": department,
                    "z_score": round(z_score, 2),
                    "occupancy_rate": float(current["occupancy_rate"]),
                    "priority": priority,
                    "forecast_confidence": confidence,
                    "confidence_gate": "Review required" if gated else "Passed",
                    "is_anomaly": abs(z_score) >= self.threshold,
                }
            )

        order = {"Critical": 0, "High": 1, "Moderate": 2, "Low": 3}
        result = pd.DataFrame(rows)
        result["sort_order"] = result["priority"].map(order)
        return result.sort_values(["sort_order", "occupancy_rate"], ascending=[True, False]).drop(
            columns="sort_order"
        )


# ── 10. AGENT 4: RECOMMENDATION AGENT ────────────────────────────────────────
@dataclass
class RecommendationAgent:
    """Produces concise, actionable recommendations from pipeline findings."""

    def _llm_recommendation(
        self,
        department: str,
        priority: str,
        occupancy_rate: float,
        forecast_peak: float,
        available: int,
        confidence: float,
    ) -> str | None:
        """Use Groq when configured; return None so rules can safely take over."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or ChatGroq is None:
            return None
        try:
            model = ChatGroq(
                api_key=api_key,
                model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
                temperature=0.1,
                max_tokens=140,
            )
            response = model.invoke(
                "You are a hospital capacity operations advisor. Give one concise, actionable "
                "recommendation in no more than 55 words. Do not diagnose or recommend clinical "
                "treatment. Use these facts only: "
                f"department={department}, priority={priority}, current occupancy={occupancy_rate:.1%}, "
                f"seven-day peak={forecast_peak:.1%}, available beds={available}, "
                f"forecast confidence={confidence:.1%}."
            )
            text = sanitize_text(str(response.content), 500)
            return text or None
        except Exception:
            # Network, quota, and provider failures must not stop the safety-rule fallback.
            return None

    def _rule_based(
        self,
        anomaly: dict[str, Any],
        forecast_peak: float,
        available: int,
    ) -> str:
        department = anomaly["department"]
        rate = anomaly["occupancy_rate"]
        if anomaly["confidence_gate"] != "Passed":
            return (
                f"Validate the {department} census manually before reallocating resources; "
                "forecast confidence is below the operational threshold."
            )
        if rate >= 0.90:
            return (
                f"Activate the {department} surge plan, expedite discharge reviews, and reserve "
                f"step-down capacity. Only {available} beds are currently available."
            )
        if forecast_peak >= 0.85:
            return (
                f"Prepare additional {department} coverage before the forecast peak of "
                f"{forecast_peak:.0%}; review transfers and elective admissions."
            )
        if anomaly["is_anomaly"]:
            return (
                f"Review the unexpected {department} occupancy pattern with the charge team and "
                "confirm staffing alignment for the next shift."
            )
        return (
            f"Maintain the current {department} allocation and repeat capacity review at the next "
            "shift handover."
        )

    def run(
        self,
        anomalies: pd.DataFrame,
        forecasts: pd.DataFrame,
        availability: pd.DataFrame,
    ) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []
        for anomaly in anomalies.to_dict("records"):
            department = anomaly["department"]
            department_forecast = forecasts[forecasts["department"] == department]
            peak = float(department_forecast["occupancy_rate"].max())
            available = int(
                availability.loc[availability["department"] == department, "available"].iloc[0]
            )
            llm_text = self._llm_recommendation(
                department,
                anomaly["priority"],
                float(anomaly["occupancy_rate"]),
                peak,
                available,
                float(anomaly["forecast_confidence"]),
            )
            recommendations.append(
                {
                    "id": f"{department.lower()}-capacity",
                    "department": department,
                    "priority": anomaly["priority"],
                    "recommendation": llm_text or self._rule_based(anomaly, peak, available),
                    "forecast_peak": peak,
                    "confidence": float(anomaly["forecast_confidence"]),
                    "source": "Groq operations advisor" if llm_text else "Rule-based clinical operations engine",
                }
            )
        return recommendations


# ── 11. PIPELINE ORCHESTRATOR ─────────────────────────────────────────────────
def run_pipeline() -> dict[str, Any]:
    """Run all four agents sequentially and persist the latest result."""
    history = generate_historical_data()
    availability = BedAvailabilityAgent().run(st.session_state["occupied_beds"])
    forecasts, confidence, engine = ForecastingAgent().run(history)
    anomalies = AnomalyPriorityAgent().run(history, availability, confidence)
    recommendations = RecommendationAgent().run(anomalies, forecasts, availability)
    result = {
        "history": history,
        "availability": availability,
        "forecasts": forecasts,
        "confidence": confidence,
        "forecast_engine": engine,
        "anomalies": anomalies,
        "recommendations": recommendations,
        "run_at": utc_now(),
    }
    st.session_state["pipeline_result"] = result
    return result


# ── 12. AUTH FUNCTIONS ────────────────────────────────────────────────────────
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def sanitize_text(value: str, max_length: int = 100) -> str:
    return " ".join(value.strip().split())[:max_length]


def format_timestamp(value: datetime | pd.Timestamp | None) -> str:
    if value is None or pd.isna(value):
        return "Never"

    try:
        dt = value.to_pydatetime() if isinstance(value, pd.Timestamp) else value
    except AttributeError:
        dt = pd.Timestamp(value).to_pydatetime()

    if not isinstance(dt, datetime):
        return "Never"

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone().strftime("%d %b %Y, %H:%M")


def initialize_session_state() -> None:
    defaults: dict[str, Any] = {
        "authenticated": False,
        "username": None,
        "role": None,
        "login_time": None,
        "last_activity_time": None,
        "auth_message": None,
        "audit_log": [],
        "failed_attempts": {},
        "locked_until": {},
        "users": {username: dict(data) for username, data in INITIAL_USERS.items()},
        "occupied_beds": dict(DEFAULT_OCCUPIED),
        "pipeline_result": None,
        "recommendation_status": {},
        "audit_clear_pending": False,
        "denied_tabs_logged": set(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def log_action(
    action: str,
    details: str = "",
    *,
    username: str | None = None,
    role: str | None = None,
) -> None:
    """Append a security event without exposing private request information."""
    st.session_state["audit_log"].append(
        {
            "timestamp": utc_now(),
            "username": username or st.session_state.get("username") or "anonymous",
            "role": role or st.session_state.get("role") or "UNAUTHENTICATED",
            "action": action,
            "details": sanitize_text(details, 500),
            "ip_placeholder": "session-local",
        }
    )


def check_permission(role: str | None, action: str) -> bool:
    return action in ROLE_PERMISSIONS.get(role or "", set())


def logout(action: str = "LOGOUT", message: str | None = None) -> None:
    if st.session_state.get("authenticated"):
        log_action(action, "User session ended")
    for key in ("authenticated", "username", "role", "login_time", "last_activity_time"):
        st.session_state[key] = False if key == "authenticated" else None
    st.session_state["pipeline_result"] = None
    st.session_state["denied_tabs_logged"] = set()
    st.session_state["auth_message"] = message


def check_session_timeout() -> None:
    """End an authenticated session after 30 minutes without a Streamlit interaction."""
    if not st.session_state.get("authenticated"):
        return
    now = utc_now()
    last_activity = st.session_state.get("last_activity_time")
    if last_activity and now - last_activity > SESSION_TIMEOUT:
        logout("SESSION_TIMEOUT", "Session expired due to inactivity")
        st.rerun()
    st.session_state["last_activity_time"] = now


def _locked_seconds(username: str) -> int:
    locked_until = st.session_state["locked_until"].get(username)
    if not locked_until:
        return 0
    remaining = int((locked_until - utc_now()).total_seconds())
    if remaining <= 0:
        st.session_state["locked_until"].pop(username, None)
        st.session_state["failed_attempts"][username] = 0
        return 0
    return remaining


def authenticate(username: str, password: str) -> bool:
    user = st.session_state["users"].get(username)
    attempt = st.session_state["failed_attempts"].get(username, 0) + 1
    valid = bool(
        user
        and bcrypt.checkpw(
            password.encode("utf-8"),
            user["password_hash"].encode("utf-8"),
        )
    )
    if not valid:
        st.session_state["failed_attempts"][username] = attempt
        if attempt >= MAX_FAILED_ATTEMPTS:
            st.session_state["locked_until"][username] = utc_now() + LOCKOUT_DURATION
        log_action(
            "LOGIN_FAILED",
            f"Failed authentication attempt {attempt}",
            username=username or "anonymous",
            role=user["role"] if user else "UNKNOWN",
        )
        return False

    now = utc_now()
    st.session_state["authenticated"] = True
    st.session_state["username"] = username
    st.session_state["role"] = user["role"]
    st.session_state["login_time"] = now
    st.session_state["last_activity_time"] = now
    st.session_state["failed_attempts"][username] = 0
    st.session_state["locked_until"].pop(username, None)
    st.session_state["users"][username]["last_login"] = now
    st.session_state["auth_message"] = None
    log_action("LOGIN_SUCCESS", "Authentication successful")
    return True


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
        :root {
            --pf-primary: #5d50d2;
            --pf-primary-dark: #4036a2;
            --pf-ink: #25243a;
            --pf-muted: #74758a;
            --pf-border: #e7e7ef;
        }
        html, body, [class*="css"] { font-family: "DM Sans", sans-serif; }
        .stApp { background: #f7f8fb; color: var(--pf-ink); }
        h1, h2, h3 { font-family: "Manrope", sans-serif !important; letter-spacing: -.035em; }
        [data-testid="stHeader"] { background: rgba(247, 248, 251, .82); backdrop-filter: blur(12px); }
        [data-testid="stSidebar"] {
            border-right: 1px solid var(--pf-border);
            background: rgba(255, 255, 255, .96);
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { line-height: 1.35; }
        .block-container { max-width: 1360px; padding-top: 2.2rem; padding-bottom: 3rem; }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255,255,255,.92);
            border-color: var(--pf-border) !important;
            border-radius: 14px !important;
            box-shadow: 0 5px 20px rgba(40,39,70,.035);
        }
        div[data-testid="stButton"] > button {
            color: #fff;
            background: linear-gradient(180deg, rgba(124,108,235,.94), rgba(83,68,199,.96));
            border: 1px solid rgba(255,255,255,.28);
            border-radius: .7rem;
            box-shadow: 0 6px 0 var(--pf-primary-dark), 0 11px 22px rgba(75,61,182,.22),
                        inset 0 1px 1px rgba(255,255,255,.35);
            backdrop-filter: blur(12px);
            font-weight: 700;
            transform: translateY(0);
            transition: transform 110ms ease, box-shadow 110ms ease, filter 180ms ease;
        }
        div[data-testid="stButton"] > button:hover {
            color: #fff;
            border-color: rgba(255,255,255,.38);
            filter: brightness(1.06);
        }
        div[data-testid="stButton"] > button:active {
            transform: translateY(5px);
            box-shadow: 0 1px 0 var(--pf-primary-dark), 0 4px 8px rgba(75,61,182,.15),
                        inset 0 2px 4px rgba(45,35,130,.22);
        }
        div[data-testid="stButton"] > button[kind="secondary"] {
            color: #4e4d61; background: rgba(255,255,255,.82);
            border: 1px solid #dddde8; box-shadow: 0 3px 0 #d8d8e3, 0 6px 13px rgba(40,39,70,.06);
        }
        div[data-testid="stButton"] > button[kind="secondary"]:active {
            box-shadow: 0 1px 0 #d8d8e3; transform: translateY(2px);
        }
        button[data-baseweb="tab"] { font-weight: 700; }
        [data-testid="stMetric"] {
            background: #fff; border: 1px solid var(--pf-border); border-radius: 13px;
            padding: 1rem 1.1rem; box-shadow: 0 4px 16px rgba(40,39,70,.035);
        }
        [data-testid="stMetricValue"] { font-family: "Manrope", sans-serif; letter-spacing: -.04em; }
        .pf-brand { display:flex; align-items:center; gap:.7rem; font:800 1.18rem "Manrope"; margin:.15rem 0 1.35rem; }
        .pf-mark {
            display:inline-grid; place-items:center; width:2rem; height:2rem; color:white;
            border-radius:.55rem; background:#5d50d2; box-shadow:0 5px 12px rgba(93,80,210,.28);
        }
        .pf-brand em { color:#5d50d2; font-style:normal; }
        .pf-kicker { color:#5d50d2; font-size:.7rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; }
        .pf-subtle { color:#797a8d; font-size:.88rem; }
        .pf-role { display:inline-flex; padding:.26rem .52rem; border-radius:.4rem; font-size:.68rem; font-weight:800; letter-spacing:.04em; }
        .pf-security {
            border:1px solid #e7e4f8; background:#f6f4fd; border-radius:.75rem;
            padding:.8rem .9rem; margin:.75rem 0 1rem;
        }
        .pf-security strong { font-size:.78rem; }
        .pf-security small { color:#77788a; }
        .pf-lock {
            background:#fff; border:1px solid #ececf2; border-radius:1rem; padding:2.2rem;
            text-align:center; margin-top:1rem;
        }
        .pf-lock-symbol { width:2.8rem; height:2.8rem; display:grid; place-items:center; border-radius:.8rem; margin:0 auto .8rem; background:#f0eefc; color:#5d50d2; font-weight:800; }
        .pf-rec { border-left:4px solid #5d50d2; padding:.2rem 0 .2rem .9rem; }
        .pf-rec p { color:#67687a; }
        .pf-status { display:inline-block; padding:.22rem .55rem; border-radius:99px; font-size:.68rem; font-weight:800; }
        .pf-status-pending { color:#8b6918; background:#fff4d9; }
        .pf-status-approved { color:#187665; background:#e6f6f1; }
        .pf-status-rejected { color:#9f2f26; background:#fee9e7; }
        .pf-footer { color:#a0a1af; text-align:center; font-size:.72rem; padding-top:2rem; }
        .pf-login-note { color:#8a8b9b; text-align:center; font-size:.75rem; margin-top:1.5rem; }
        @media (prefers-reduced-motion: reduce) {
            div[data-testid="stButton"] > button { transition:none; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_login_page() -> None:
    inject_styles()
    left, center, right = st.columns([1, 1.05, 1])
    with center:
        st.markdown(
            """
            <div style="height:5vh"></div>
            <div class="pf-brand" style="justify-content:center">
                <span class="pf-mark">+</span><span>Pulse<em>Flow</em></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="pf-kicker">Hospital operations intelligence</div>
                <h1 style="margin:.45rem 0 .3rem">Welcome back.</h1>
                <p class="pf-subtle" style="margin-bottom:1.5rem">
                    Sign in to {html.escape(HOSPITAL_NAME)}'s secure operations dashboard.
                </p>
                """,
                unsafe_allow_html=True,
            )
            message = st.session_state.get("auth_message")
            if message:
                st.warning(message)
                st.session_state["auth_message"] = None

            with st.form("login_form", clear_on_submit=False):
                username_raw = st.text_input("Username", max_chars=100, placeholder="Enter your username")
                password_raw = st.text_input(
                    "Password",
                    type="password",
                    max_chars=100,
                    placeholder="Enter your password",
                )
                submitted = st.form_submit_button("Sign in to dashboard", use_container_width=True)

            if submitted:
                username = sanitize_text(username_raw).lower()
                password = password_raw[:100]
                remaining = _locked_seconds(username)
                if remaining:
                    minutes, seconds = divmod(remaining, 60)
                    st.error(f"Account temporarily locked. Try again in {minutes}m {seconds:02d}s.")
                elif authenticate(username, password):
                    st.rerun()
                else:
                    remaining = _locked_seconds(username)
                    if remaining:
                        minutes, seconds = divmod(remaining, 60)
                        st.error(
                            f"Invalid credentials. Account locked for {minutes}m {seconds:02d}s."
                        )
                    else:
                        st.error("Invalid credentials")

            st.markdown(
                '<p class="pf-login-note">Protected by bcrypt password hashing and role-based access control</p>',
                unsafe_allow_html=True,
            )
    st.markdown(
        '<div class="pf-footer">PulseFlow Health Systems · Secure demonstration environment</div>',
        unsafe_allow_html=True,
    )


def render_access_restricted(tab_name: str) -> None:
    key = f"{st.session_state['username']}:{tab_name}"
    if key not in st.session_state["denied_tabs_logged"]:
        log_action("TAB_ACCESS_DENIED", f"Access denied to {tab_name} tab")
        st.session_state["denied_tabs_logged"].add(key)
    role = html.escape(st.session_state["role"])
    st.markdown(
        f"""
        <div class="pf-lock">
            <div class="pf-lock-symbol">LOCK</div>
            <h3>Access Restricted</h3>
            <p class="pf-subtle">Your role ({role}) does not have permission to view this section.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    role = st.session_state["role"]
    foreground, background = ROLE_COLORS[role]
    expires_at = st.session_state["last_activity_time"] + SESSION_TIMEOUT
    remaining = max(int((expires_at - utc_now()).total_seconds()), 0)
    minutes, seconds = divmod(remaining, 60)

    with st.sidebar:
        st.markdown(
            """
            <div class="pf-brand">
                <span class="pf-mark">+</span><span>Pulse<em>Flow</em></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Log out", use_container_width=True, type="secondary"):
            logout()
            st.rerun()

        st.markdown(
            f"""
            <div class="pf-security">
                <strong>Secure session</strong><br>
                <small>User</small><br>
                <b>{html.escape(st.session_state["username"])}</b><br><br>
                <span class="pf-role" style="color:{foreground};background:{background}">{role}</span>
                <br><br><small>Session expires in</small><br>
                <b>{minutes} min {seconds:02d} sec</b>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if role == "ADMIN":
            st.caption("Active Sessions: 1")
        st.divider()
        st.caption("PIPELINE")
        result = st.session_state.get("pipeline_result")
        if result:
            st.write(f"Last run: {format_timestamp(result['run_at'])}")
            st.write(f"Forecast engine: {result['forecast_engine']}")
        else:
            st.write("Pipeline awaiting first run")


def page_heading(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="pf-kicker">{html.escape(kicker)}</div>
        <h1 style="margin:.35rem 0 .2rem">{html.escape(title)}</h1>
        <p class="pf-subtle" style="margin:0 0 1.4rem">{html.escape(subtitle)}</p>
        """,
        unsafe_allow_html=True,
    )


def render_overview(result: dict[str, Any]) -> None:
    page_heading(
        datetime.now().strftime("%A, %d %B"),
        f"Good day, {st.session_state['username'].replace('_', ' ').title()}.",
        "Live capacity, patient-flow signals, and operational readiness.",
    )

    availability = result["availability"]
    total_occupied = int(availability["occupied"].sum())
    total_capacity = int(availability["total_beds"].sum())
    critical_count = int(availability["occupancy_rate"].ge(0.85).sum())
    metric_columns = st.columns(4)
    metric_columns[0].metric("Hospital occupancy", f"{total_occupied}/{total_capacity}", f"{total_occupied / total_capacity:.1%}")
    metric_columns[1].metric("Available beds", int(availability["available"].sum()), "Live capacity")
    metric_columns[2].metric("Units above 85%", critical_count, "Needs attention" if critical_count else "Stable")
    metric_columns[3].metric("Forecast confidence", f"{np.mean(list(result['confidence'].values())):.0%}", result["forecast_engine"])

    st.markdown("### Department capacity")
    st.caption("Current occupied beds and live availability by department")
    columns = st.columns(len(DEPARTMENTS))
    for column, row in zip(columns, availability.to_dict("records")):
        rate = row["occupancy_rate"]
        with column:
            with st.container(border=True):
                st.markdown(f"**{row['department']}**")
                st.markdown(
                    f"<h2 style='margin:.25rem 0'>{row['occupied']} <small style='font-size:.75rem;color:#898a99'>/ {row['total_beds']}</small></h2>",
                    unsafe_allow_html=True,
                )
                st.progress(min(rate, 1.0))
                st.caption(f"{rate:.0%} occupied · {row['available']} available")

    if check_permission(st.session_state["role"], "update_beds"):
        st.markdown("### Update bed count")
        with st.form("bed_update_form"):
            first, second, third = st.columns([1.2, 1, 0.8])
            with first:
                department = st.selectbox("Department", DEPARTMENTS, key="bed_department")
            with second:
                new_value = st.number_input(
                    "Occupied beds",
                    min_value=0,
                    max_value=TOTAL_BEDS[department],
                    value=st.session_state["occupied_beds"][department],
                    step=1,
                    key=f"bed_value_{department}",
                )
            with third:
                st.write("")
                st.write("")
                update_submitted = st.form_submit_button("Update", use_container_width=True)
            if update_submitted:
                old_value = st.session_state["occupied_beds"][department]
                validated = int(new_value)
                if not 0 <= validated <= TOTAL_BEDS[department]:
                    st.error(f"Enter a whole number from 0 to {TOTAL_BEDS[department]}.")
                elif validated == old_value:
                    st.info("The occupied bed count is unchanged.")
                else:
                    st.session_state["occupied_beds"][department] = validated
                    log_action(
                        "BED_UPDATE",
                        f"{department}: occupied beds changed from {old_value} to {validated}",
                    )
                    run_pipeline()
                    st.toast(f"{department} bed count updated")
                    st.rerun()

    left, right = st.columns([1.45, 0.8])
    with left:
        with st.container(border=True):
            st.markdown("#### 30-day occupancy trend")
            recent = result["history"].groupby("date", as_index=False)["occupancy_rate"].mean().tail(30)
            chart = px.area(
                recent,
                x="date",
                y="occupancy_rate",
                color_discrete_sequence=["#6558d9"],
            )
            chart.update_traces(line={"width": 2}, fillcolor="rgba(101,88,217,.12)")
            chart.update_layout(
                height=290,
                margin=dict(l=10, r=10, t=10, b=10),
                yaxis_tickformat=".0%",
                xaxis_title=None,
                yaxis_title=None,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified",
            )
            chart.update_xaxes(showgrid=False)
            chart.update_yaxes(gridcolor="#eeeeF3")
            st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})

    with right:
        with st.container(border=True):
            st.markdown("#### Priority signals")
            for anomaly in result["anomalies"].head(4).to_dict("records"):
                st.markdown(
                    f"**{anomaly['department']} · {anomaly['priority']}**  \n"
                    f"<span class='pf-subtle'>{anomaly['occupancy_rate']:.0%} occupied · "
                    f"z-score {anomaly['z_score']:+.2f}</span>",
                    unsafe_allow_html=True,
                )
                st.divider()


def render_forecasts(result: dict[str, Any]) -> None:
    page_heading(
        "Agent 2 · Forecasting",
        "Seven-day capacity forecast",
        f"Forecasts generated with {result['forecast_engine']} and guarded by a {CONFIDENCE_GATE:.0%} confidence threshold.",
    )
    selected = st.selectbox("Department", DEPARTMENTS, key="forecast_department")
    historical = result["history"][result["history"]["department"] == selected].tail(30)
    forecast = result["forecasts"][result["forecasts"]["department"] == selected]
    confidence = result["confidence"][selected]

    first, second, third = st.columns(3)
    first.metric("Model confidence", f"{confidence:.1%}", "Gate passed" if confidence >= CONFIDENCE_GATE else "Manual review")
    third.metric("Capacity", TOTAL_BEDS[selected], "beds")
    second.metric("Forecast peak", f"{forecast['yhat'].max():.1f}", f"{forecast['occupancy_rate'].max():.0%} occupied")

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=historical["date"],
            y=historical["occupied"],
            mode="lines",
            name="Actual",
            line=dict(color="#279f91", width=2),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=forecast["date"],
            y=forecast["yhat_upper"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=forecast["date"],
            y=forecast["yhat_lower"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(101,88,217,.13)",
            name="80% interval",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=forecast["date"],
            y=forecast["yhat"],
            mode="lines+markers",
            name="Forecast",
            line=dict(color="#6558d9", width=3, dash="dot"),
        )
    )
    figure.add_hline(
        y=TOTAL_BEDS[selected] * 0.85,
        line_dash="dash",
        line_color="#e1644f",
        annotation_text="85% threshold",
    )
    figure.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title=None,
        yaxis_title="Occupied beds",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend_orientation="h",
        hovermode="x unified",
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(gridcolor="#ededf2")
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})

    forecast_table = forecast[["date", "yhat", "yhat_lower", "yhat_upper", "occupancy_rate"]].copy()
    forecast_table.columns = ["Date", "Expected", "Low", "High", "Occupancy"]
    st.dataframe(
        forecast_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Date": st.column_config.DateColumn(format="ddd, DD MMM"),
            "Expected": st.column_config.NumberColumn(format="%.1f beds"),
            "Low": st.column_config.NumberColumn(format="%.1f"),
            "High": st.column_config.NumberColumn(format="%.1f"),
            "Occupancy": st.column_config.ProgressColumn(format="%.0%%", min_value=0, max_value=1),
        },
    )


def render_anomalies(result: dict[str, Any]) -> None:
    if not check_permission(st.session_state["role"], "view_anomalies"):
        render_access_restricted("Anomalies")
        return
    page_heading(
        "Agent 3 · Anomaly & Priority",
        "Operational anomalies",
        "Current occupancy is compared with each department's historical baseline and ranked by urgency.",
    )
    anomalies = result["anomalies"].copy()
    critical = int(anomalies["priority"].isin(["Critical", "High"]).sum())
    flagged = int(anomalies["is_anomaly"].sum())
    low_confidence = int(anomalies["forecast_confidence"].lt(CONFIDENCE_GATE).sum())
    one, two, three = st.columns(3)
    one.metric("High priority", critical)
    two.metric("Statistical anomalies", flagged)
    three.metric("Confidence holds", low_confidence)

    display = anomalies.copy()
    display["occupancy_rate"] = display["occupancy_rate"].map(lambda value: f"{value:.1%}")
    display["forecast_confidence"] = display["forecast_confidence"].map(lambda value: f"{value:.1%}")
    display["is_anomaly"] = display["is_anomaly"].map({True: "Flagged", False: "Within baseline"})
    display.columns = [
        "Department",
        "Z-score",
        "Occupancy",
        "Priority",
        "Forecast confidence",
        "Confidence gate",
        "Detection",
    ]
    st.dataframe(display, use_container_width=True, hide_index=True)

    figure = px.scatter(
        anomalies,
        x="z_score",
        y="occupancy_rate",
        size="forecast_confidence",
        color="priority",
        text="department",
        color_discrete_map={
            "Critical": "#d95343",
            "High": "#ed815c",
            "Moderate": "#d9a23b",
            "Low": "#279f91",
        },
    )
    figure.add_vline(x=ANOMALY_Z_THRESHOLD, line_dash="dash", line_color="#9797a5")
    figure.update_traces(textposition="top center")
    figure.update_layout(
        height=400,
        xaxis_title="Z-score from historical baseline",
        yaxis_title="Current occupancy",
        yaxis_tickformat=".0%",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=30, b=10),
    )
    figure.update_xaxes(gridcolor="#ededf2")
    figure.update_yaxes(gridcolor="#ededf2")
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})


def render_recommendations(result: dict[str, Any]) -> None:
    if not check_permission(st.session_state["role"], "view_recommendations"):
        render_access_restricted("Recommendations")
        return
    page_heading(
        "Agent 4 · Recommendations",
        "Capacity actions",
        "Prioritized operational guidance generated from live capacity, forecast, and anomaly signals.",
    )
    can_review = check_permission(st.session_state["role"], "review_recommendations")
    for recommendation in result["recommendations"]:
        recommendation_id = recommendation["id"]
        state = st.session_state["recommendation_status"].get(
            recommendation_id,
            {"status": "Pending", "reason": "", "reviewer": None},
        )
        status_class = f"pf-status-{state['status'].lower()}"
        with st.container(border=True):
            top_left, top_right = st.columns([5, 1])
            with top_left:
                st.markdown(
                    f"""
                    <div class="pf-rec">
                        <div class="pf-kicker">{html.escape(recommendation['priority'])} priority · {html.escape(recommendation['department'])}</div>
                        <h3 style="margin:.35rem 0">Recommended capacity action</h3>
                        <p>{html.escape(recommendation['recommendation'])}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with top_right:
                st.markdown(
                    f'<span class="pf-status {status_class}">{state["status"]}</span>',
                    unsafe_allow_html=True,
                )
            st.caption(
                f"Forecast peak: {recommendation['forecast_peak']:.0%} · "
                f"Confidence: {recommendation['confidence']:.0%} · {recommendation['source']}"
            )

            if can_review and state["status"] == "Pending":
                reason = st.text_area(
                    "Rejection reason",
                    key=f"reason_{recommendation_id}",
                    max_chars=100,
                    placeholder="Required only when rejecting (minimum 10 characters)",
                )
                approve_column, reject_column, spacer = st.columns([1, 1, 3])
                with approve_column:
                    approve = st.button(
                        "Approve",
                        key=f"approve_{recommendation_id}",
                        use_container_width=True,
                    )
                with reject_column:
                    reject = st.button(
                        "Reject",
                        key=f"reject_{recommendation_id}",
                        use_container_width=True,
                        type="secondary",
                    )
                if approve:
                    st.session_state["recommendation_status"][recommendation_id] = {
                        "status": "Approved",
                        "reason": "",
                        "reviewer": st.session_state["username"],
                    }
                    log_action(
                        "RECOMMENDATION_APPROVED",
                        f"{recommendation['department']}: recommendation approved",
                    )
                    st.toast(f"{recommendation['department']} recommendation approved")
                    st.rerun()
                if reject:
                    clean_reason = sanitize_text(reason)
                    if len(clean_reason) < 10:
                        st.error("Please provide a rejection reason of at least 10 characters.")
                    else:
                        st.session_state["recommendation_status"][recommendation_id] = {
                            "status": "Rejected",
                            "reason": clean_reason,
                            "reviewer": st.session_state["username"],
                        }
                        log_action(
                            "RECOMMENDATION_REJECTED",
                            f"{recommendation['department']}: {clean_reason}",
                        )
                        st.toast(f"{recommendation['department']} recommendation rejected")
                        st.rerun()
            elif state["status"] != "Pending":
                review_text = f"Reviewed by {state['reviewer']}"
                if state["reason"]:
                    review_text += f" · Reason: {state['reason']}"
                st.info(review_text)


def render_user_management() -> None:
    st.markdown("### User management")
    st.caption("Demo accounts, current roles, latest successful login, and lock status")
    rows = []
    for username, user in st.session_state["users"].items():
        rows.append(
            {
                "Username": username,
                "Role": user["role"],
                "Last Login": format_timestamp(user["last_login"]),
                "Status": "Locked" if _locked_seconds(username) else "Active",
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.form("role_change_form"):
        first, second, third = st.columns([1, 1, 0.75])
        with first:
            username = st.selectbox(
                "Username",
                list(st.session_state["users"].keys()),
                key="role_username",
            )
        with second:
            roles = list(ROLE_PERMISSIONS.keys())
            current_role = st.session_state["users"][username]["role"]
            new_role = st.selectbox(
                "New role",
                roles,
                index=roles.index(current_role),
                key="role_new_value",
            )
        with third:
            st.write("")
            st.write("")
            submitted = st.form_submit_button("Update role", use_container_width=True)
        if submitted:
            old_role = st.session_state["users"][username]["role"]
            if new_role == old_role:
                st.info("The selected user already has that role.")
            else:
                st.session_state["users"][username]["role"] = new_role
                log_action("ROLE_UPDATED", f"{username}: role changed from {old_role} to {new_role}")
                if username == st.session_state["username"]:
                    st.session_state["role"] = new_role
                st.toast(f"{username}'s role updated to {new_role}")
                st.rerun()


def render_audit_log() -> None:
    st.markdown("### Audit log")
    st.caption("Session-local security and operational events")
    log_frame = pd.DataFrame(st.session_state["audit_log"])
    if log_frame.empty:
        st.info("No audit events have been recorded.")
        return

    action_options = sorted(log_frame["action"].unique())
    selected_actions = st.multiselect(
        "Filter by action",
        action_options,
        default=action_options,
        key="audit_actions",
    )
    filtered = log_frame[log_frame["action"].isin(selected_actions)].copy()
    filtered = filtered.sort_values("timestamp", ascending=False)
    filtered["timestamp"] = filtered["timestamp"].map(format_timestamp)
    display = filtered[["timestamp", "username", "role", "action", "details"]].copy()
    display.columns = ["Time", "User", "Role", "Action", "Details"]
    st.dataframe(display, use_container_width=True, hide_index=True)

    csv_buffer = io.StringIO()
    display.to_csv(csv_buffer, index=False)
    download_column, clear_column = st.columns([1, 1])
    with download_column:
        st.download_button(
            "Download as CSV",
            data=csv_buffer.getvalue(),
            file_name=f"pulseflow-audit-{datetime.now():%Y%m%d-%H%M}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with clear_column:
        if not st.session_state["audit_clear_pending"]:
            if st.button("Clear audit log", type="secondary", use_container_width=True):
                st.session_state["audit_clear_pending"] = True
                st.rerun()
        else:
            st.warning("This removes all existing session audit entries.")
            confirm, cancel = st.columns(2)
            if confirm.button("Confirm clear", use_container_width=True):
                st.session_state["audit_log"] = []
                st.session_state["audit_clear_pending"] = False
                log_action("AUDIT_LOG_CLEARED", "Audit log cleared by administrator")
                st.rerun()
            if cancel.button("Cancel", type="secondary", use_container_width=True):
                st.session_state["audit_clear_pending"] = False
                st.rerun()


def render_admin_panel() -> None:
    if not check_permission(st.session_state["role"], "manage_users"):
        render_access_restricted("Admin Panel")
        return
    page_heading(
        "Administration",
        "Security & access control",
        "Manage demo user roles and review the complete session audit trail.",
    )
    users_tab, audit_tab = st.tabs(["User Management", "Audit Log"])
    with users_tab:
        render_user_management()
    with audit_tab:
        render_audit_log()


# ── 13. DASHBOARD ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{APP_NAME} · Hospital Operations",
    page_icon="+",
    layout="wide",
    initial_sidebar_state="expanded",
)
initialize_session_state()

# Check auth FIRST — before any dashboard renders
if not st.session_state.get("authenticated"):
    show_login_page()
    st.stop()

check_session_timeout()  # call this right after auth check

if not st.session_state.get("authenticated"):
    show_login_page()
    st.stop()

inject_styles()
render_sidebar()

if st.session_state["pipeline_result"] is None:
    with st.spinner("Running hospital intelligence pipeline..."):
        run_pipeline()
    log_action("PIPELINE_RUN", "Initial pipeline run completed")

role = st.session_state["role"]
header_left, header_right = st.columns([4, 1])
with header_left:
    st.markdown(
        f"""
        <div class="pf-brand" style="margin-bottom:.15rem">
            <span class="pf-mark">+</span><span>{html.escape(HOSPITAL_NAME)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with header_right:
    if check_permission(role, "run_pipeline"):
        if st.button("Run AI pipeline", use_container_width=True):
            with st.spinner("Refreshing all four agents..."):
                run_pipeline()
            log_action("PIPELINE_RUN", "Manual pipeline run completed")
            st.toast("Pipeline refreshed")
            st.rerun()

result = st.session_state["pipeline_result"]
role_label = role.replace("_", " ")
tab_names = [
    f"Overview · {role_label}",
    f"Forecasts · {role_label}",
    f"Anomalies · {role_label}",
    f"Recommendations · {role_label}",
]
if role == "ADMIN":
    tab_names.append(f"Admin Panel · {role_label}")

tabs = st.tabs(tab_names)
with tabs[0]:
    render_overview(result)
with tabs[1]:
    render_forecasts(result)
with tabs[2]:
    render_anomalies(result)
with tabs[3]:
    render_recommendations(result)
if role == "ADMIN":
    with tabs[4]:
        render_admin_panel()

st.markdown(
    '<div class="pf-footer">PulseFlow · Hospital resource and patient-flow intelligence</div>',
    unsafe_allow_html=True,
)
