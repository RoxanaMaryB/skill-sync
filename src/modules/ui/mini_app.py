from __future__ import annotations

import os
import sys
from pathlib import Path
import pandas as pd
import streamlit as st

# ============================================================
# Ensure "cv-sage/src" is on sys.path so "modules.*" imports work
# ============================================================
ROOT = Path(__file__).resolve().parents[3]  # -> cv-sage/
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# ============================================================
# Imports
# ============================================================
from modules.json_explainer.proj_extractor import (  # noqa: E402
    ProjectSchemaExtractor,
    ProjectExtractorConfig,
)

from modules.json_explainer.extractor import (  # noqa: E402
    CandidateProfileExtractor,
    ExtractorConfig,
    OPENROUTER_BASE_URL,
)

# ============================================================
# Page config
# ============================================================
st.set_page_config(page_title="SkillSync - Project Setup", layout="wide")

st.title("SkillSync — Project Setup")
st.caption(
    "Upload candidates → extract N candidate profiles → describe the project → extract requirements."
)

# ============================================================
# 0) Upload candidate CSV
# ============================================================
st.subheader("0) Upload candidate CSV")
uploaded_csv = st.file_uploader("Upload CSV", type=["csv"])

df_candidates = None
if uploaded_csv is not None:
    try:
        df_candidates = pd.read_csv(uploaded_csv)
        st.success("CSV loaded successfully.")
        st.write(f"Rows: {len(df_candidates)} • Columns: {len(df_candidates.columns)}")
        st.dataframe(df_candidates.head(8), use_container_width=True)
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")

# ============================================================
# Sidebar: API settings (OpenRouter)
# ============================================================
with st.sidebar:
    st.header("Model / API Settings (OpenRouter)")

    api_key = st.text_input(
        "API Key",
        value=os.getenv("OPENROUTER_API_KEY", ""),
        type="password",
        help="OpenRouter keys start with sk-or-...",
    )

    base_url = st.text_input(
        "Base URL",
        value=os.getenv("OPENAI_BASE_URL", OPENROUTER_BASE_URL),
    )

    model = st.text_input(
        "Model",
        value=os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini"),
    )

    temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.1)

st.divider()

# ============================================================
# 0.1) Extract N candidate profiles (ONLY ONE BAR)
# ============================================================
if df_candidates is not None:
    st.subheader("0.1) Extract candidate profiles")

    max_n = min(200, len(df_candidates))

    n_candidates = st.number_input(
        "How many candidates to extract (N)",
        min_value=1,
        max_value=max_n,
        value=min(20, max_n),
        step=1,
    )

    extract_candidates_btn = st.button(
        "Extract N candidates",
        type="primary",
        disabled=not api_key.strip(),
    )

    if extract_candidates_btn:
        if not api_key.strip():
            st.error("Missing API key. Add it in the sidebar.")
        else:
            # Set env vars for consistency
            os.environ["OPENROUTER_API_KEY"] = api_key
            os.environ["OPENAI_API_KEY"] = api_key
            os.environ["OPENAI_BASE_URL"] = base_url
            os.environ["OPENAI_MODEL"] = model

            cfg = ExtractorConfig(
                model=model,
                temperature=0.0,     # deterministic extraction
                limit=int(n_candidates),
                retries=1,
                request_timeout_s=60,
                sleep_between_calls_s=0.2,
                debug=False,
            )

            extractor = CandidateProfileExtractor(
                api_key=api_key,
                base_url=base_url,
                config=cfg,
            )

            out_dir = ROOT / "data" / "artifacts" / "extraction"
            out_dir.mkdir(parents=True, exist_ok=True)

            out_with_evidence = out_dir / "candidate_profiles_with_evidence.json"
            out_clean = out_dir / "candidate_profiles.json"
            out_inputs = out_dir / "candidate_inputs.json"

            limit = min(int(n_candidates), len(df_candidates))
            st.write(f"Extracting {limit} candidates...")

            progress = st.progress(0)
            status = st.empty()

            profiles = []
            inputs = {}

            for i in range(limit):
                row = df_candidates.iloc[i].to_dict()
                cid = str(row.get("Candidate ID", "Unknown"))

                status.write(f"Extracting {i + 1}/{limit} (Candidate ID={cid})")

                try:
                    text = extractor.build_profile_text(row)
                    inputs[cid] = text
                    prof = extractor.extract_one(row, i=i)
                    profiles.append(prof)
                except Exception as e:
                    profiles.append({"id": cid, "error": str(e)})

                progress.progress(int(((i + 1) / limit) * 100))

            CandidateProfileExtractor.save_json(profiles, str(out_with_evidence))
            CandidateProfileExtractor.save_json(
                [CandidateProfileExtractor.strip_evidence(p) for p in profiles],
                str(out_clean),
            )
            CandidateProfileExtractor.save_json(inputs, str(out_inputs))

            st.success("Candidate extraction finished ✅")
            st.write("Saved files:")
            st.code(str(out_clean))
            st.code(str(out_with_evidence))
            st.code(str(out_inputs))

            if profiles:
                st.subheader("Preview: first extracted profile")
                st.json(profiles[0])

st.divider()

# ============================================================
# 1) Project description (unchanged)
# ============================================================
st.subheader("1) Project description (unstructured)")
description = st.text_area(
    "Paste your project description here",
    height=180,
    placeholder="Example: Build a web app with a Python backend, React frontend, deploy on AWS, store data in PostgreSQL...",
)

# ============================================================
# 2) Constraints (unchanged)
# ============================================================
st.subheader("2) Constraints (structured)")

team_size = st.number_input(
    "Team size",
    min_value=2,
    max_value=10,
    value=4,
    step=1,
)

min_hours = st.number_input(
    "Minimum availability (hours/week per person)",
    min_value=0,
    max_value=80,
    value=10,
    step=1,
)

# ============================================================
# Project extraction
# ============================================================
def validate_extraction(obj: dict) -> dict:
    if not isinstance(obj, dict):
        raise ValueError("Output is not a JSON object.")
    if "technical_requirements" not in obj:
        raise ValueError("Missing 'technical_requirements'.")
    tr = obj["technical_requirements"]
    for k in ["skills", "tools", "roles"]:
        tr[k] = list(dict.fromkeys([x.strip() for x in tr.get(k, []) if isinstance(x, str)]))
    return {"technical_requirements": tr}

@st.cache_data(show_spinner=False)
def cached_extract(api_key, base_url, model, temperature, description):
    extractor = ProjectSchemaExtractor(
        api_key=api_key,
        base_url=base_url,
        config=ProjectExtractorConfig(model=model, temperature=temperature),
    )
    return validate_extraction(extractor.extract_requirements(description))

extract_btn = st.button(
    "Extract + Build Project Requirements JSON",
    type="primary",
    disabled=not description.strip(),
)

if extract_btn:
    if not api_key.strip():
        st.error("Missing API key.")
    else:
        with st.spinner("Extracting project requirements…"):
            extracted = cached_extract(api_key, base_url, model, temperature, description)

            project_requirements = {
                **extracted,
                "constraints": {
                    "team_size": int(team_size),
                    "min_availability_hours_per_week": int(min_hours),
                },
            }

            st.subheader("Final Project Requirements (JSON)")
            st.json(project_requirements)
