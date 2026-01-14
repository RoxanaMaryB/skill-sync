
from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import streamlit as st
import pandas as pd



ROOT = Path(__file__).resolve().parents[3]  # -> cv-sage/
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

OPENROUTER_BASE_URL_DEFAULT = "https://openrouter.ai/api/v1"



from modules.json_explainer.proj_extractor import (  # noq
    ProjectSchemaExtractor,
    ProjectExtractorConfig,
)
from modules.json_explainer.extractor import (  # noqa: E402
    CandidateProfileExtractor,
    ExtractorConfig,
    OPENROUTER_BASE_URL,
)

from modules.evaluators.profile_ex_eval import CandidateProfileEvaluator  
from modules.evaluators.project_ex_eval import ProjectRequirementsEvaluator  



ARTIFACTS_DIR = DATA_DIR / "artifacts"
EXTRACTION_DIR = ARTIFACTS_DIR / "extraction"
PROJECT_DIR = ARTIFACTS_DIR / "project"
EVAL_DIR = ARTIFACTS_DIR / "eval"

EXTRACTION_DIR.mkdir(parents=True, exist_ok=True)
PROJECT_DIR.mkdir(parents=True, exist_ok=True)
EVAL_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = DATA_DIR / "uploaded_candidates.csv"

CANDIDATES_CLEAN = EXTRACTION_DIR / "candidate_profiles.json"
CANDIDATES_WITH_EVIDENCE = EXTRACTION_DIR / "candidate_profiles_with_evidence.json"
CANDIDATE_INPUTS = EXTRACTION_DIR / "candidate_inputs.json"

PROJECT_DESC_TXT = PROJECT_DIR / "project_description.txt"
PROJECT_REQ_JSON = PROJECT_DIR / "project_requirements.json"

CANDIDATE_EVAL_JSON = EVAL_DIR / "candidate_extraction_eval.json"
PROJECT_EVAL_JSON = EVAL_DIR / "project_extraction_eval.json"


def file_ok(p: Path) -> bool:
    return p.exists() and p.is_file() and p.stat().st_size > 0


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def save_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or "", encoding="utf-8")


def clear_outputs() -> None:
    for p in [
        CSV_PATH,
        CANDIDATES_CLEAN,
        CANDIDATES_WITH_EVIDENCE,
        CANDIDATE_INPUTS,
        PROJECT_DESC_TXT,
        PROJECT_REQ_JSON,
        CANDIDATE_EVAL_JSON,
        PROJECT_EVAL_JSON,
    ]:
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass


def validate_project_extraction(obj: dict) -> dict:
    """
    Ensure schema and de-duplicate (preserve order).
    """
    if not isinstance(obj, dict):
        raise ValueError("Output is not a JSON object.")
    if "technical_requirements" not in obj:
        raise ValueError("Missing 'technical_requirements'.")
    tr = obj["technical_requirements"]

    for k in ["skills", "tools", "roles"]:
        lst = tr.get(k, [])
        if not isinstance(lst, list):
            lst = []
        clean = []
        for x in lst:
            if isinstance(x, str):
                s = x.strip()
                if s:
                    clean.append(s)
        tr[k] = list(dict.fromkeys(clean))

    return {"technical_requirements": tr}


def set_openrouter_env(api_key: str, base_url: str, model: str) -> None:
    os.environ["OPENROUTER_API_KEY"] = api_key
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_BASE_URL"] = base_url
    os.environ["OPENAI_MODEL"] = model


def summarize_candidate_eval(summary: dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build two small tables:
    1) evidence errors table (first 50)
    2) label errors table (first 50)
    """
    rows_e = []
    rows_l = []

    for d in summary.get("details", []) or []:
        cid = d.get("id", "Unknown")
        for err in d.get("evidence_errors", []) or []:
            rows_e.append({"candidate_id": cid, "error": err})
        for err in d.get("label_errors", []) or []:
            rows_l.append({"candidate_id": cid, "error": err})

    df_e = pd.DataFrame(rows_e).head(50)
    df_l = pd.DataFrame(rows_l).head(50)
    return df_e, df_l


def top_n_error_counts(summary: dict, key: str, n: int = 8) -> pd.DataFrame:
    """
    key = 'evidence_errors' or 'label_errors'
    Returns a table: error -> count
    """
    from collections import Counter

    c = Counter()
    for d in summary.get("details", []) or []:
        for err in d.get(key, []) or []:
            c[str(err)] += 1

    items = c.most_common(n)
    return pd.DataFrame(items, columns=["error", "count"])



st.set_page_config(page_title="SkillSync", layout="wide")
st.title("SkillSync — Team Formation System")
st.caption("OpenRouter sidebar + Extractors + Evaluators (candidate + project)")

if "csv_saved" not in st.session_state:
    st.session_state.csv_saved = False
if "project_description" not in st.session_state:
    st.session_state.project_description = ""



st.sidebar.header("Settings (OpenRouter)")

api_key = st.sidebar.text_input(
    "OPENROUTER_API_KEY",
    value=os.getenv("OPENROUTER_API_KEY", ""),
    type="password",
)

base_url = st.sidebar.text_input(
    "Base URL",
    value=os.getenv("OPENAI_BASE_URL", OPENROUTER_BASE_URL or OPENROUTER_BASE_URL_DEFAULT),
)

model = st.sidebar.text_input(
    "Model",
    value=os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini"),
)

st.sidebar.divider()
n_extract = st.sidebar.number_input("Candidate extraction limit (N)", 1, 500, 30)
st.sidebar.caption("Candidate extraction runs deterministically at temperature=0.")

st.sidebar.divider()
if st.sidebar.button("🧹 Clear outputs (extraction/project/eval)"):
    clear_outputs()
    st.session_state.csv_saved = False
    st.sidebar.success("Cleared outputs")



tab_run, tab_eval, tab_raw = st.tabs(["Run Pipeline", "Evaluation", "Raw JSON"])



with tab_run:
    st.subheader("1) Upload Candidate CSV")

    csv_file = st.file_uploader("Upload CSV", type=["csv"])
    if csv_file:
        CSV_PATH.write_bytes(csv_file.getvalue())
        st.session_state.csv_saved = True
        st.success(f"CSV saved to: {CSV_PATH}")

        try:
            df_preview = pd.read_csv(CSV_PATH)
            df_preview = CandidateProfileExtractor.rename_columns(df_preview)
            st.write(f"Rows: {len(df_preview)} • Columns: {len(df_preview.columns)}")
            st.dataframe(df_preview.head(8), use_container_width=True)
        except Exception:
            st.info("CSV saved (preview failed to render).")

    st.markdown("### 2) Extract Candidate Profiles (N)")

    run_extract = st.button(
        "🚀 Run Extraction (Candidates)",
        type="primary",
        disabled=not st.session_state.csv_saved,
    )

    if run_extract:
        if not file_ok(CSV_PATH):
            st.error("Upload a CSV first.")
            st.stop()

        if not api_key.strip():
            st.error("Missing OPENROUTER_API_KEY in sidebar.")
            st.stop()

        set_openrouter_env(api_key, base_url, model)

        df = pd.read_csv(CSV_PATH)
        df = CandidateProfileExtractor.rename_columns(df)

        cfg = ExtractorConfig(
            model=model,
            temperature=0.0,
            limit=int(min(int(n_extract), len(df))),
            retries=1,
            request_timeout_s=60,
            sleep_between_calls_s=0.2,
            debug=False,
        )
        extractor = CandidateProfileExtractor(api_key=api_key, base_url=base_url, config=cfg)

        limit = cfg.limit
        st.write(f"Extracting {limit} candidates…")
        progress = st.progress(0.0)
        status = st.empty()

        profiles: List[Dict[str, Any]] = []
        inputs: Dict[str, str] = {}

        for i in range(limit):
            row = df.iloc[i].to_dict()
            cid = str(row.get("Candidate ID", "Unknown"))
            status.write(f"Extracting {i + 1}/{limit} (Candidate ID={cid})")

            try:
                text = extractor.build_profile_text(row)
                inputs[cid] = text
                prof = extractor.extract_one(row, i=i)
                profiles.append(prof)
            except Exception as e:
                profiles.append({"id": cid, "error": str(e)})

            progress.progress((i + 1) / limit)

        save_json(profiles, CANDIDATES_WITH_EVIDENCE)
        save_json([CandidateProfileExtractor.strip_evidence(p) for p in profiles], CANDIDATES_CLEAN)
        save_json(inputs, CANDIDATE_INPUTS)

        st.success("Candidate extraction completed ")
        st.caption("Saved artifacts:")
        st.code(str(CANDIDATES_CLEAN))
        st.code(str(CANDIDATES_WITH_EVIDENCE))
        st.code(str(CANDIDATE_INPUTS))

        if profiles:
            st.markdown("#### Preview (first extracted profile)")
            st.json(profiles[0])

    st.divider()

    st.subheader("3) Project Description → Extract Project Requirements")

    project_description = st.text_area(
        "Describe the project stack",
        value=st.session_state.project_description
        or "Build a React and Node.js web app using PostgreSQL on AWS. Use Docker for deployment.",
        height=140,
    )
    st.session_state.project_description = project_description

    team_size = st.number_input("Team size", min_value=2, max_value=10, value=4, step=1)
    min_hours = st.number_input(
        "Minimum availability (hours/week per person)", min_value=0, max_value=80, value=10, step=1
    )

    if st.button("Extract & Save Project Requirements", type="primary", disabled=not project_description.strip()):
        if not api_key.strip():
            st.error("Missing OPENROUTER_API_KEY in sidebar.")
            st.stop()

        set_openrouter_env(api_key, base_url, model)

        extractor = ProjectSchemaExtractor(
            api_key=api_key,
            base_url=base_url,
            config=ProjectExtractorConfig(model=model, temperature=0.0),
        )
        raw = extractor.extract_requirements(project_description)
        extracted = validate_project_extraction(raw)

        project = {
            **extracted,
            "constraints": {
                "team_size": int(team_size),
                "min_availability_hours_per_week": int(min_hours),
            },
        }

        save_text(project_description, PROJECT_DESC_TXT)
        save_json(project, PROJECT_REQ_JSON)

        st.success("Project requirements saved ✅")
        st.caption("Saved artifacts:")
        st.code(str(PROJECT_DESC_TXT))
        st.code(str(PROJECT_REQ_JSON))
        st.json(project)



with tab_eval:
    st.subheader("Candidate Profile Extraction Evaluation (LLM)")

    st.write("candidate_profiles_with_evidence.json:", "✅" if file_ok(CANDIDATES_WITH_EVIDENCE) else "❌ missing")
    st.write("candidate_inputs.json:", "✅" if file_ok(CANDIDATE_INPUTS) else "❌ missing")

    if st.button("🧪 Run Candidate Evaluator", type="primary"):
        if not file_ok(CANDIDATES_WITH_EVIDENCE) or not file_ok(CANDIDATE_INPUTS):
            st.error("Missing files. Run candidate extraction first.")
            st.stop()

        ev = CandidateProfileEvaluator()
        summary = ev.evaluate_files(
            profiles_path=str(CANDIDATES_WITH_EVIDENCE),
            inputs_path=str(CANDIDATE_INPUTS),
            out_path=str(CANDIDATE_EVAL_JSON),
        )

        st.success("✅ Candidate evaluation complete")
        st.caption(f"Saved to: {CANDIDATE_EVAL_JSON}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Schema OK rate", f"{summary.get('schema_ok_rate', 0.0) * 100:.2f}%")
        c2.metric("Avg label errors", f"{summary.get('avg_label_errors', 0.0):.2f}")
        c3.metric("Avg evidence errors", f"{summary.get('avg_evidence_errors', 0.0):.2f}")

 
        st.markdown("### What is failing the most?")
        left, right = st.columns(2)

        with left:
            st.markdown("**Top evidence error types**")
            st.dataframe(top_n_error_counts(summary, "evidence_errors", n=8), use_container_width=True)

        with right:
            st.markdown("**Top label error types**")
            st.dataframe(top_n_error_counts(summary, "label_errors", n=8), use_container_width=True)

        st.markdown("### Evidence errors (first 50)")
        df_e, df_l = summarize_candidate_eval(summary)
        if len(df_e) == 0:
            st.success("No evidence errors ✅")
        else:
            st.dataframe(df_e, use_container_width=True, hide_index=True)

  
        with st.expander("Show full candidate evaluation JSON"):
            st.json(summary)

    st.divider()
    st.subheader("Project Requirements Extraction Evaluation (LLM)")

    st.write("project_requirements.json:", "✅" if file_ok(PROJECT_REQ_JSON) else "❌ missing")
    st.write("project_description.txt:", "✅" if file_ok(PROJECT_DESC_TXT) else "❌ missing")

    if st.button("🧪 Run Project Evaluator", type="primary"):
        if not file_ok(PROJECT_REQ_JSON) or not file_ok(PROJECT_DESC_TXT):
            st.error("Missing project artifacts. Extract & save project requirements first.")
            st.stop()

        pev = ProjectRequirementsEvaluator()
        summary_proj = pev.evaluate_files(
            requirements_path=str(PROJECT_REQ_JSON),
            description_path=str(PROJECT_DESC_TXT),
            out_path=str(PROJECT_EVAL_JSON),
        )

        st.success("✅ Project evaluation complete")
        st.caption(f"Saved to: {PROJECT_EVAL_JSON}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Schema OK", "✅" if summary_proj.get("schema_ok") else "❌")
        c2.metric("Skills supported", f"{summary_proj.get('skills_supported_rate', 1.0) * 100:.1f}%")
        c3.metric("Tools supported", f"{summary_proj.get('tools_supported_rate', 1.0) * 100:.1f}%")
        c4.metric(
            "Unsupported total",
            len(summary_proj.get("skills_unsupported", [])) + len(summary_proj.get("tools_unsupported", [])),
        )

        st.markdown("### Unsupported items (what your extractor hallucinated / over-extracted)")
        colA, colB = st.columns(2)
        with colA:
            st.markdown("**Skills unsupported**")
            st.write(summary_proj.get("skills_unsupported", []))
        with colB:
            st.markdown("**Tools unsupported**")
            st.write(summary_proj.get("tools_unsupported", []))

        with st.expander("Show full project evaluation JSON"):
            st.json(summary_proj)


with tab_raw:
    st.subheader("Artifacts viewer")

    options: List[Tuple[str, Path]] = []

    def add_opt(label: str, path: Path) -> None:
        if file_ok(path):
            options.append((label, path))

    add_opt("candidate_profiles_with_evidence.json", CANDIDATES_WITH_EVIDENCE)
    add_opt("candidate_profiles.json", CANDIDATES_CLEAN)
    add_opt("candidate_inputs.json", CANDIDATE_INPUTS)
    add_opt("project_description.txt", PROJECT_DESC_TXT)
    add_opt("project_requirements.json", PROJECT_REQ_JSON)
    add_opt("candidate_extraction_eval.json", CANDIDATE_EVAL_JSON)
    add_opt("project_extraction_eval.json", PROJECT_EVAL_JSON)

    if not options:
        st.info("No artifacts found yet. Run extraction / project steps first.")
    else:
        labels = [x[0] for x in options]
        chosen = st.selectbox("Select an artifact", options=labels)
        p = dict(options)[chosen]

        if p.suffix.lower() == ".json":
            st.json(read_json(p))
        else:
            st.code(p.read_text(encoding="utf-8"), language="text")
