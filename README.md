# SkillSync - AI-Powered Team Formation



## 🚀 Quick Start
1. Install: `pip install -r requirements.txt`
2. Run UI: `streamlit run src/modules/member4_ui/app.py`
3. Test: `python tests/integration_test.py`

## 📁 Project Structure
See `docs/architecture.md` for detailed architecture.

## 🔧 Development
- Each member works in their `src/modules/memberX_*` directory
- Use `shared/interfaces.py` for module communication
- Create PRs for integration


-------------------------------------------------------------------------------------

# SkillSync — GenAI Team Formation Pipeline

SkillSync is a hybrid GenAI + deterministic pipeline that forms balanced teams from candidate data and a project description.  
It uses LLM-based structured extraction, embedding similarity, a team-building heuristic, and an LLM-generated explanation report.

## What problem does it solve?
Given:
- a list of candidates (skills, tools, experience, collaboration signals)
- an unstructured project description (requirements, constraints)

The system:
1) extracts structured profiles and requirements  
2) computes similarity and diversity  
3) builds candidate teams  
4) generates an explanation report grounded in extracted artifacts  
5) evaluates quality using automatic checks (without needing ground-truth labels)

---

## Pipeline Overview

### 1) Candidate Profile Extraction (GenAI)
- Input: candidate rows (CSV)
- Output: structured JSON profiles:
  - technical (skills, tools)
  - metadata (dev_type, industry, experience)
  - collaboration (communication/conflict/leadership/deadline)
  - personality (Belbin role)
  - constraints (availability)
- Also saves: `candidate_profiles_with_evidence.json` (evidence snippets)

### 2) Candidate Embeddings + Diversity (Non-GenAI)
- Encodes candidate profiles to embeddings (SentenceTransformer)
- Computes cosine dissimilarity matrix (candidate–candidate) for diversity

### 3) Project Requirements Extraction (GenAI)
- Input: free-text project description
- Output: `project_requirements.json` with:
  - required roles / skills / tools
  - constraints (team size, min availability)

### 4) Candidate–Project Similarity (Non-GenAI)
- Embeds project requirements
- Computes cosine similarity between candidate embeddings and project embedding

### 5) Team Builder (Non-GenAI)
- Builds teams using:
  - fit to project (candidate–project similarity)
  - internal diversity (candidate–candidate dissimilarity)
  - constraints (availability, team size)

### 6) Explanation Report (GenAI)
- Generates a structured team report:
  - project requirements
  - per-team technical fit
  - per-team dynamics summary
  - recommended team + reasons
- Hard safety rules: uses only provided context JSON (no invented facts)

### 7) Evaluation (No Ground Truth Required)
There is no human-labeled ground truth for “correct” skills/roles in this dataset, so traditional precision/recall is not used.
Instead, we evaluate quality via:
- schema validity checks (JSON structure)
- grounding checks (evidence correctness / missing evidence)
- hallucination checks (project requirements supported by description)
- deterministic team metrics (coverage %, internal diversity, constraints satisfaction)

---

## GenAI Components
- Candidate profile extraction (LLM → structured JSON + evidence)
- Project requirements extraction (LLM → structured JSON)
- Explanation report generation (LLM → grounded report)

## Non-GenAI Components
- Embeddings (SentenceTransformer)
- Team-building heuristic


---

## How to Run

### 1) Install
```bash
pip install -r requirements.txt






set your API open router key 

      export OPENROUTER_API_KEY="your_key_here"


start the app 

      streamlit run src/modules/ui/mini_app.py
