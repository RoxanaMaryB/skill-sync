# SkillSync Module Usage Guide

## Overview

This guide explains how to properly import and use modules in the SkillSync application. The project follows a modular architecture with clear separation of concerns.

## Project Structure

```
src/
├── main.py                    # Entry point
├── shared/                    # Shared utilities and interfaces
│   └── interfaces.py          # Common data structures
└── modules/                   # Core modules
    ├── __init__.py            # Package initialization
    ├── candidate_embeddings/  # Candidate profile embeddings
    ├── project_embeddings/    # Project embeddings
    ├── team_builder/          # Team formation algorithm
    ├── json_extraction/       # Text-to-JSON extraction
    ├── EXPLANATION/           # Report and explanation generation
    ├── RAG/                   # Retrieval-augmented generation
    ├── evaluators/            # Evaluation and metrics
    └── ui/                    # Streamlit UI application
```

## Correct Import Patterns

### From Within the Application

When importing from within the app (e.g., from `src/modules/ui/app.py`):

```python
from pathlib import Path
import sys

# Add src directory to path
src_dir = Path(__file__).parent.parent.parent  # From ui/ → modules/ → src/
sys.path.insert(0, str(src_dir))

# Now import from shared and modules
from shared.interfaces import CandidateProfile, ProjectDescription
from modules.team_builder.builder import build_teams
from modules.candidate_embeddings.embedding_service import gen_cand_emb_dissim
```

### From Different Module Levels

**From `src/main.py`:**
```python
from pathlib import Path
from modules.candidate_embeddings.embedding_service import gen_cand_emb_dissim
from modules.project_embeddings.generate_embeddings import gen_poj_emb_sim
```

**From `src/modules/team_builder/test_builder1_local.py`:**
```python
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]  # skill-sync root
sys.path.append(str(ROOT / "src"))

from shared.interfaces import CandidateProfile, ProjectDescription
from modules.team_builder.builder import build_teams
```

## Key Patterns

### 1. Path Calculation

Always calculate paths relative to your file location:

```python
from pathlib import Path

# For files in src/modules/ui/:
src_dir = Path(__file__).parent.parent.parent

# For files in src/modules/team_builder/:
src_dir = Path(__file__).parent.parent

# For files in src/:
src_dir = Path(__file__).parent
```

### 2. sys.path Manipulation

**Always use `insert(0, ...)` instead of `append(...)`** to ensure your paths take priority:

```python
# ✅ Correct
sys.path.insert(0, str(src_dir))

# ❌ Avoid
sys.path.append(str(src_dir))  # May conflict with other paths
```

### 3. Imports Organization

Group imports in this order:
1. Standard library (sys, os, json, pathlib, etc.)
2. Third-party packages (streamlit, pandas, numpy, etc.)
3. Local modules

```python
import sys
from pathlib import Path
import json

import streamlit as st
import pandas as pd
import numpy as np

src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

from shared.interfaces import CandidateProfile, ProjectDescription
from modules.team_builder.builder import build_teams
```

## Module Reference

### `shared.interfaces`
Common data structures used across the application.

```python
from shared.interfaces import CandidateProfile, ProjectDescription

# Use these classes for type hints and data validation
def process_candidate(profile: CandidateProfile) -> dict:
    ...
```

### `modules.candidate_embeddings`
Generates embeddings for candidate profiles.

```python
from modules.candidate_embeddings.embedding_service import gen_cand_emb_dissim
from modules.candidate_embeddings.repository import store_embeddings

# Generate embeddings and save
gen_cand_emb_dissim(profiles_path)
```

### `modules.project_embeddings`
Generates embeddings for project descriptions.

```python
from modules.project_embeddings.generate_embeddings import gen_poj_emb_sim

# Generate project embeddings
gen_poj_emb_sim(projects_path)
```

### `modules.team_builder`
Core team formation algorithms.

```python
from modules.team_builder.builder import build_teams
from modules.team_builder.team_builder import TeamBuilder

# Build optimal teams
teams = build_teams(profiles, project, constraints)
```

### `modules.json_extraction`
Extracts structured data from raw text.

```python
from modules.json_extraction.extractor import extract_profiles
from modules.json_extraction.proj_extractor import extract_project

# Extract profiles from text
profiles = extract_profiles(raw_text)
```

### `modules.EXPLANATION`
Generates team formation explanations and reports.

```python
from modules.EXPLANATION.team_report import generate_team_report
from modules.EXPLANATION.report_retrieve import retrieve_report

# Generate explanation report
report = generate_team_report(teams, profiles, project)
```

### `modules.RAG`
Retrieval-augmented generation for context.

```python
from modules.RAG.retrieval import retrieve_context

# Retrieve context for decisions
context = retrieve_context(query, candidate_pool)
```

### `modules.evaluators`
Evaluation metrics and logging.

```python
from modules.evaluators.team_eval import evaluate_teams
from modules.evaluators.latency_logger import log_latency

# Evaluate team quality
metrics = evaluate_teams(teams, profiles, project)

# Log performance metrics
log_latency("team_formation", elapsed_time)
```

## Common Import Mistakes

### ❌ Mistake 1: Incorrect Path Calculation
```python
# Wrong - points to wrong directory
sys.path.append(str(Path(__file__).parent.parent))

# Correct - verify the path goes to src/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

### ❌ Mistake 2: Using Absolute Paths
```python
# Wrong - not portable
sys.path.append("/Users/saban.akay/Desktop/TU/7_ws_25/GenAI/skill-sync/src")

# Correct - works on any machine
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

### ❌ Mistake 3: Missing Package Initialization
```python
# Module directories MUST have __init__.py files
# All modules now have __init__.py for proper package structure
```

### ❌ Mistake 4: Late Path Setup
```python
# Wrong - imports before path is set
from modules.team_builder import build_teams
sys.path.insert(0, str(src_dir))

# Correct - set path first
sys.path.insert(0, str(src_dir))
from modules.team_builder import build_teams
```

## Lazy Loading for UI Performance

In the Streamlit UI (`src/modules/ui/app.py`), use lazy imports for expensive operations:

```python
# At the top (light imports only)
from shared.interfaces import CandidateProfile, ProjectDescription

# Later, when actually needed (inside callbacks/buttons)
def on_build_teams_click():
    from modules.team_builder.builder import build_teams
    teams = build_teams(st.session_state.profiles, st.session_state.project)
    st.session_state.teams = teams
```

## Testing Module Imports

To verify your module structure is correct:

```bash
# From project root, test basic imports
python3 -c "from pathlib import Path; import sys; sys.path.insert(0, str(Path('src'))); from modules.team_builder.builder import build_teams; print('✅ Import successful')"

# Or run the integration test
python3 tests/integration_test.py
```

## Dependencies and Compatibility

Ensure all modules are compatible with:
- Python 3.9+
- Dependencies listed in `requirements.txt`

When adding new modules:
1. Create a new directory under `modules/`
2. Add an `__init__.py` file
3. Update this guide with the module reference
4. Ensure imports follow the patterns above

## Summary

✅ **Do:**
- Use `Path(...).parent` to calculate relative paths
- Use `sys.path.insert(0, str(src_dir))` for path setup
- Group imports (standard → third-party → local)
- Put `__init__.py` in all module directories
- Set up paths BEFORE importing local modules

❌ **Don't:**
- Use absolute paths in imports
- Use `sys.path.append()` for local modules
- Create circular dependencies
- Import before path is configured
- Forget `__init__.py` files

