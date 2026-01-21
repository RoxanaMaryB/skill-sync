# SkillSync - System Documentation & Architecture Report

**Date**: January 21, 2026  
**Project**: SkillSync - AI-Powered Team Formation  
**Purpose**: Complete system overview, module responsibilities, data flow, and operational guide

---

## 1. 🎯 Project Overview

### What is SkillSync?

SkillSync is an intelligent team formation system that automatically creates balanced, diverse, and complementary teams by analyzing candidate skills, experience, and collaboration metrics against project requirements.

**Core Problem Solved**:
- **Input**: Large pool of candidates + project description
- **Process**: AI-powered analysis of skills, experience, and compatibility
- **Output**: Optimal team recommendations with explanations

### Use Cases

1. **HR Team Allocation**: Assign employees to projects
2. **Startup Hiring**: Form founding teams from pool of candidates
3. **Consultant Scheduling**: Match project requirements with available consultants
4. **Educational Groups**: Form study groups or project teams

---

## 2. 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    SkillSync Pipeline                        │
└─────────────────────────────────────────────────────────────┘

INPUT STAGE:
  ┌──────────────────┐         ┌──────────────────┐
  │ Candidate CVs    │         │ Project Brief    │
  │ (Raw Text/JSON)  │         │ (Requirements)   │
  └────────┬─────────┘         └────────┬─────────┘
           │                            │
           └──────────────┬─────────────┘
                          ▼
           ┌─────────────────────────┐
           │   M5: Extraction        │ Extract structured data
           │   JSON Processing       │
           └────────────┬────────────┘
                        ▼
        ┌──────────────────────────────────┐
        │  Structured Profiles & Reqs      │
        │  (JSON format)                   │
        └──────────┬───────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
   ┌─────────────┐    ┌──────────────────┐
   │ M1: Candidate│    │ M2: Project      │
   │ Embeddings   │    │ Embeddings       │
   │ (Skills)     │    │ (Requirements)   │
   └─────┬───────┘    └────────┬─────────┘
         │                     │
         └──────────┬──────────┘
                    ▼
        ┌───────────────────────────┐
        │ Similarity Matrices       │
        │ (Fit & Diversity)         │
        └──────────┬────────────────┘
                   ▼
        ┌───────────────────────────┐
        │ M3: Team Builder          │
        │ Greedy Algorithm          │
        │ (Optimization)            │
        └──────────┬────────────────┘
                   ▼
        ┌───────────────────────────┐
        │ Team Recommendations      │
        │ (Multiple options)        │
        └──────────┬────────────────┘
                   ▼
        ┌───────────────────────────┐
        │ M5: Explanation Report    │
        │ Human-readable reasons    │
        └──────────┬────────────────┘
                   ▼
        ┌───────────────────────────┐
        │ M4: UI Presentation       │
        │ Results & Visualization   │
        └───────────────────────────┘

OUTPUT STAGE:
  ┌────────────────────────────────┐
  │ Recommended Teams              │
  │ + Detailed Explanations        │
  │ + Confidence Metrics           │
  └────────────────────────────────┘
```

---

## 3. 📦 Module Responsibilities

### Module 1 (M1): Candidate Embeddings
**Owner**: Shahzad  
**Location**: `src/modules/candidate_embeddings/`

**Purpose**: Transform candidate profiles into numerical vectors for similarity analysis

**Responsibilities**:
- Convert candidate skills/experience to embeddings using SentenceTransformer
- Compute candidate-to-candidate similarity matrix (diversity)
- Store embeddings in FAISS vector database
- Handle embedding model updates and versioning

**Key Files**:
- `embedding_service.py` - Main embedding generation
- `repository.py` - Storage and retrieval
- `similarity.py` - Similarity matrix computation
- `text_encoder.py` - Profile text encoding

**Input**: `List[CandidateProfile]`
- id, name, skills, tools, experience_years, collaboration_style, etc.

**Output**: `EmbeddingResult`
```python
{
    "embeddings": np.ndarray,      # shape: (n_candidates, 384)
    "candidate_ids": List[str],
    "similarity_matrix": np.ndarray,  # (n_candidates, n_candidates)
    "metadata": dict
}
```

**Metrics Provided**:
- Skill overlap (similarity)
- Diversity score (dissimilarity)
- Coverage gaps

---

### Module 2 (M2): Project Embeddings
**Owner**: Roxana  
**Location**: `src/modules/project_embeddings/`

**Purpose**: Analyze project requirements and match against candidate skills

**Responsibilities**:
- Extract and embed project requirements
- Compute candidate-to-project similarity (fit)
- Rank candidates by project suitability
- Handle multi-language requirement descriptions

**Key Files**:
- `embeddings.py` - Project embedding generation
- `compute_similarity.py` - Candidate-project fit calculation
- `generate_embeddings.py` - Embedding pipeline
- `store_embeddings.py` - Persistence layer

**Input**: `ProjectDescription`
- title, description, required_roles, required_skills, team_size, duration

**Output**: `ProjectFitResult`
```python
{
    "project_embedding": np.ndarray,       # (384,)
    "candidate_fits": Dict[str, float],    # candidate_id -> fit_score
    "top_matches": List[Tuple[str, float]] # sorted by fit
}
```

**Metrics Provided**:
- Project-candidate fit (0.0-1.0)
- Skill coverage % 
- Role coverage %

---

### Module 3 (M3): Team Builder
**Owner**: Ana  
**Location**: `src/modules/team_builder/`

**Purpose**: Form optimal teams balancing fit, diversity, and constraints

**Responsibilities**:
- Implement team formation algorithm (greedy with heuristics)
- Balance multiple objectives: project fit, internal diversity, skill coverage
- Enforce team size and availability constraints
- Provide alternative team options

**Key Files**:
- `team_builder.py` - Main algorithm implementation
- `constraints.py` - Constraint validation
- `metrics.py` - Team quality metrics

**Input**:
```python
{
    "profiles": List[CandidateProfile],
    "project": ProjectDescription,
    "candidate_dissim": np.ndarray,  # From M1
    "project_fits": Dict[str, float], # From M2
    "team_size": int
}
```

**Output**: `List[Team]`
```python
[
    {
        "members": [CandidateProfile, ...],
        "metrics": {
            "project_fit": 0.85,
            "internal_diversity": 0.72,
            "skill_coverage": 0.95,
            "availability_hours": 160
        }
    }
]
```

**Algorithm**:
```
1. Start with candidate with highest project fit
2. Iteratively add candidates that maximize:
   score = α*fit + β*diversity + γ*skill_coverage
3. Stop when team_size reached
4. Validate constraints (availability, roles)
5. Return top K alternative teams
```

**Configuration**:
- `fitness_weights`: {fit: 0.5, diversity: 0.3, coverage: 0.2}
- `max_team_size`: 8
- `min_team_size`: 2

---

### Module 4 (M4): UI & Architecture
**Owner**: Șaban  
**Location**: `src/modules/ui/`

**Purpose**: Provide user interface and system orchestration

**Responsibilities**:
- Streamlit web application interface
- Data upload and validation
- Results visualization and presentation
- System integration and coordination

**Key Files**:
- `app.py` - Main Streamlit application
- `mini_app.py` - Lightweight alternative UI
- `components/` - Reusable UI components

**Pages**:
1. **📤 Upload Data**: Load candidate profiles (CSV/JSON)
2. **⚙️ Project Setup**: Define project requirements
3. **👥 Build Teams**: Visualize team formation process
4. **📊 Analytics**: Show metrics and comparisons
5. **📋 Results**: Display recommendations with explanations

**Features**:
- Real-time progress indication
- Interactive team customization
- Confidence metrics display
- Team comparison matrices

---

### Module 5 (M5): JSON Extraction & Explanations
**Owner**: Noor  
**Location**: `src/modules/json_extraction/` + `src/modules/EXPLANATION/`

**Purpose**: Convert raw CV text to structured data and generate human-readable reports

**Sub-modules**:

**5a. JSON Extraction** (`json_extraction/`)
- Extract structured profiles from raw CV text using OpenAI GPT
- Validate JSON schema compliance
- Extract evidence snippets for transparency
- Handle parsing errors and fallbacks

**Key Files**:
- `extractor.py` - LLM-based extraction logic
- `proj_extractor.py` - Project requirements extraction

**5b. Explanation Report Generation** (`EXPLANATION/`)
- Generate human-readable team reports
- Explain why teams are recommended
- Provide technical fit analysis
- Highlight team dynamics and compatibility

**Key Files**:
- `team_report.py` - Report generation from context
- `report_retrieve.py` - Context preparation
- `report_paths.py` - File organization

**Input** (5a): Raw CV text
```
"John Doe, Senior Python Developer with 5 years experience..."
```

**Output** (5a): Structured profile
```json
{
    "id": "candidate_1",
    "technical": {"skills": ["Python", "Django"], "tools": ["VS Code"]},
    "metadata": {"experience_years": 5, "industry": "tech"},
    "collaboration": {"communication_style": "direct"},
    "evidence": {...}
}
```

**Output** (5b): Human-readable report
```
# Team Recommendations

Team 1: Strong Technical Fit
- Led by John (5y Python) and Maria (React specialist)
- Coverage: 95% of required skills
- Dynamics: Complementary - John is systematic, Maria is creative
- Recommendation: EXCELLENT fit for timeline-critical work
```

---

### Module 6: Evaluation System
**Location**: `src/modules/evaluators/`

**Purpose**: Assess quality of extractions and team recommendations

**Components**:
- `profile_ex_eval.py` - Evaluate candidate profile extraction quality
- `project_ex_eval.py` - Evaluate project requirement extraction
- `team_eval.py` - Evaluate team recommendations
- `latency_logger.py` - Track performance metrics

**Metrics Tracked**:
- Schema validity (JSON structure)
- Grounding quality (evidence presence)
- Hallucination detection
- Team diversity metrics
- Constraint satisfaction

---

## 4. 📊 Data Models & Flow

### Candidate Profile Data Model

```python
@dataclass
class CandidateProfile:
    # Identification
    id: str                      # Unique identifier
    
    # Technical Skills
    technical: {
        "skills": ["Python", "React"],     # Skill names
        "tools": ["Docker", "Git"]         # Tools/frameworks
    }
    
    # Experience & Role
    metadata: {
        "dev_type": "Full Stack",          # Developer type
        "work_experience_years": 5,        # Total years
        "employment": "employed",          # Employment status
        "industry": "tech"                 # Industry background
    }
    
    # Collaboration Profile
    collaboration: {
        "communication_style": "direct",   # How they communicate
        "conflict_style": "collaborative", # Conflict resolution
        "leadership_preference": "shared", # Leadership style
        "deadline_discipline": "planned"   # Deadline approach
    }
    
    # Behavioral Profile
    personality: {
        "Belbin_team_role": "Coordinator" # Belbin role
    }
    
    # Learning & Growth
    learning_behavior: {
        "learning_orientation": "continuous",
        "knowledge_sharing": "collaborative"
    }
    
    # Constraints
    constraints: {
        "weekly_availability_hours": 40   # Available hours/week
    }
    
    # Evidence
    evidence: {
        "personality": {"team_role": "Found in: 'leads team meetings'"},
        "collaboration": {...}
    }
```

### Project Description Data Model

```python
@dataclass
class ProjectDescription:
    id: str                          # Project identifier
    title: str                       # Project name
    description: str                 # Detailed description
    
    # Requirements
    required_roles: ["Backend Dev", "QA"]
    required_skills: ["Python", "Docker", "SQL"]
    required_tools: ["AWS", "PostgreSQL"]
    
    # Constraints
    team_size: int                   # Number of team members
    duration_weeks: int              # Project duration
    min_availability_hours: int      # Minimum availability
    
    # Priority
    priority_skills: ["Python", "AWS"]  # Must-have skills
```

### Data Flow Through Pipeline

```
RAW CV TEXT
    ↓
[M5 EXTRACTION]
    ↓
CANDIDATE_PROFILES (JSON)
    ├─→ Stored: data/candidate_profiles.json
    ├─→ With evidence: data/candidate_profiles_with_evidence.json
    │
    └─→ [M1 EMBEDDING]
            ↓
        EMBEDDINGS (numerical vectors)
            ├─→ Stored: data/artifacts/candidate_embeddings.npy
            ├─→ Similarity matrix: data/artifacts/candidate_dissimilarity.npy
            │
            └─→ [Team Selection Process]
                    ↓
        PROJECT DESCRIPTION (raw text)
            ↓
        [M5 EXTRACTION]
            ↓
        PROJECT_REQUIREMENTS (JSON)
            │
            └─→ [M2 EMBEDDING]
                    ↓
                PROJECT_EMBEDDING (vector)
                    ├─→ Stored: data/artifacts/project_embeddings.npy
                    ├─→ Candidate-project fit scores
                    │
                    └─→ [M3 TEAM BUILDER]
                            ↓
                        CANDIDATE_DISSIMILARITY
                        (from M1)
                            │
                            ├─→ Fit scores (from M2)
                            ├─→ Team size constraints
                            │
                            └─→ BUILD TEAMS
                                ↓
                            TEAMS (multiple options)
                                ├─→ Stored: data/teams_ranking.json
                                │
                                └─→ [M5 EXPLANATION]
                                        ↓
                                    REPORT (human-readable)
                                        ├─→ Stored: data/team_report.json
                                        │
                                        └─→ [M4 UI]
                                                ↓
                                            VISUALIZE & PRESENT
```

---

## 5. 🔄 Complete Workflow

### Step-by-Step Process

#### **Phase 1: Data Preparation**
```
1. User uploads candidates (CSV or raw text)
2. M5 validates and extracts structured profiles
3. Profiles stored with evidence snippets
4. Quality checks performed
```

#### **Phase 2: Embedding & Matching**
```
1. M1 generates embeddings for all candidates
   - Encodes skills, experience, collaboration data
   - Computes similarity matrix (who works well together)
   - Stores embeddings for reuse

2. M2 generates project embedding
   - Analyzes project requirements
   - Computes fit scores for each candidate
   - Ranks candidates by suitability
```

#### **Phase 3: Team Formation**
```
1. M3 runs team building algorithm
   - Input: Candidate profiles, fit scores, diversity scores
   - Process: Greedy algorithm with weighted objectives
   - Output: Multiple team options (ranked)
   
2. Constraints validated
   - Team size
   - Availability hours
   - Required roles covered
```

#### **Phase 4: Explanation & Presentation**
```
1. M5 generates human-readable reports
   - Why each team is recommended
   - Technical fit analysis
   - Team dynamics assessment
   - Confidence metrics

2. M4 presents via UI
   - Display recommended teams
   - Show metrics and comparisons
   - Allow customization
   - Collect feedback
```

---

## 6. 🔧 Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Embeddings** | SentenceTransformer | Convert text to vectors |
| **LLM Processing** | OpenAI GPT-4 / OpenRouter | Extract structured data |
| **Vector DB** | FAISS | Similarity search |
| **Data Processing** | Pandas, NumPy | Data manipulation |
| **ML/Math** | SciPy, Scikit-learn | Matrix operations |
| **Visualization** | Plotly | Charts & graphs |
| **UI Framework** | Streamlit | Web interface |
| **Config** | YAML | Settings management |

---

## 7. 📁 Project Structure

```
skill-sync/
│
├── 📄 config.yaml                 # Configuration settings
├── 📄 main.py                     # Main pipeline orchestrator
├── 📄 requirements.txt            # Python dependencies
├── 📄 setup_skillsync.sh          # Setup script
│
├── 📁 src/                        # Source code
│   ├── main.py                    # Entry point
│   ├── test_team_builder.py       # Local testing
│   │
│   ├── 📁 shared/                 # Shared utilities
│   │   ├── interfaces.py          # Data contracts between modules
│   │   └── __pycache__/
│   │
│   └── 📁 modules/
│       │
│       ├── 📁 candidate_embeddings/  # [M1] Shahzad
│       │   ├── embedding_service.py
│       │   ├── repository.py
│       │   ├── similarity.py
│       │   ├── storage.py
│       │   ├── text_encoder.py
│       │   └── utils.py
│       │
│       ├── 📁 project_embeddings/    # [M2] Roxana
│       │   ├── compute_similarity.py
│       │   ├── embeddings.py
│       │   ├── generate_embeddings.py
│       │   ├── store_embeddings.py
│       │   └── ...
│       │
│       ├── 📁 team_builder/          # [M3] Ana
│       │   ├── team_builder.py
│       │   ├── constraints.py
│       │   ├── metrics.py
│       │   └── test_builder1_local.py
│       │
│       ├── 📁 ui/                    # [M4] Șaban
│       │   ├── app.py              # Main Streamlit app
│       │   └── mini_app.py
│       │
│       ├── 📁 json_extraction/       # [M5] Noor (Part A)
│       │   ├── extractor.py
│       │   ├── proj_extractor.py
│       │   └── __init__.py
│       │
│       ├── 📁 EXPLANATION/           # [M5] Noor (Part B)
│       │   ├── __init__.py
│       │   ├── team_report.py
│       │   ├── report_retrieve.py
│       │   └── report_paths.py
│       │
│       ├── 📁 evaluators/            # Quality evaluation
│       │   ├── latency_logger.py
│       │   ├── profile_ex_eval.py
│       │   ├── project_ex_eval.py
│       │   └── team_eval.py
│       │
│       ├── 📁 RAG/                   # RAG components
│       │   └── rag_retrieve.py
│       │
│       └── 📁 EXPLANATION/
│           └── ...
│
├── 📁 data/                       # Data storage
│   ├── candidate_profiles.json
│   ├── candidate_profiles_with_evidence.json
│   ├── skillsync_dataset_v1_draft.csv
│   │
│   └── 📁 artifacts/              # Generated outputs
│       ├── candidate_embeddings.npy
│       ├── candidate_dissimilarity.npy
│       ├── project_embeddings.npy
│       ├── teams_ranking.json
│       ├── team_report.json
│       │
│       └── 📁 evaluation/
│           ├── candidate_extraction_eval.json
│           ├── project_extraction_eval.json
│           └── latency_log.jsonl
│
├── 📁 docs/                       # Documentation
│   ├── architecture.md
│   └── development_guide.md
│
├── 📁 logs/                       # Application logs
│
├── 📁 notebooks/                  # Jupyter notebooks
│
├── 📁 outputs/                    # Final outputs
│   ├── embeddings/
│   ├── explanations/
│   └── teams/
│
├── 📁 tests/                      # Unit tests
│   └── integration_test.py
│
└── 📄 README.md                   # Project overview
```

---

## 8. 🚀 How to Run the System

### Installation

```bash
# Clone and navigate
git clone https://github.com/akaysaban/skill-sync.git
cd skill-sync

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export OPENROUTER_API_KEY="your_key_here"
```

### Running the Full Pipeline

```bash
# Start the UI
streamlit run src/modules/ui/app.py

# Or run individual components
python src/test_team_builder.py  # Test team builder locally
python tests/integration_test.py # Run integration test
```

### Running Specific Modules

```python
# M1: Generate candidate embeddings
from src.modules.candidate_embeddings.embedding_service import EmbeddingService
service = EmbeddingService()
embeddings = service.generate_embeddings(profiles)

# M2: Project matching
from src.modules.project_embeddings.embeddings import ProjectEmbedder
embedder = ProjectEmbedder()
fit_scores = embedder.compute_fit(project_desc, candidate_embeddings)

# M3: Team formation
from src.modules.team_builder.team_builder import build_team_greedy_refined
teams = build_team_greedy_refined(profiles, project, dissimilarity, fit_scores)

# M5: Generate report
from src.modules.EXPLANATION.team_report import generate_team_report
report = generate_team_report(teams, project)
```

---

## 9. 📊 Key Metrics & Success Criteria

### System Metrics

| Metric | Target | Current |
|--------|--------|---------|
| **Skill Coverage** | >85% | ✓ Working |
| **Team Diversity** | >0.7 | ✓ Working |
| **Processing Speed** | <30s | ✓ Typical |
| **Extraction Quality** | >90% | ⚠️ Depends on LLM |
| **User Satisfaction** | >4.0/5.0 | ? Not measured |

### Quality Checks

```python
# Validation pipeline
✓ JSON schema validation (extraction correctness)
✓ Embedding dimension check (384-dim vectors)
✓ Similarity matrix properties (symmetric, 0-1 range)
✓ Team constraint satisfaction (size, availability)
✓ Hallucination detection (LLM outputs grounded in input)
✓ Coverage calculation (skill/role matching)
```

---

## 10. 🔐 Security & Data Handling

**Data Security Level**: ⚠️ **REQUIRES ENHANCEMENT** (See COMPLIANCE_REPORT.md)

**Current Protections**:
- HTTPS for external API calls
- Data stored in JSON/NumPy files
- No authentication on local UI

**Needed Protections**:
- Encryption at rest
- Anonymization before LLM processing
- Access control & audit logging
- GDPR compliance measures

---

## 11. 🎓 Development Guidelines

### Adding a New Feature

1. **Plan**: Define purpose, inputs, outputs
2. **Design**: Create interface contract in `shared/interfaces.py`
3. **Implement**: Build in appropriate module
4. **Test**: Add unit tests
5. **Integrate**: Wire into pipeline
6. **Document**: Update this report
7. **Review**: Code review with team

### Module Communication

All modules communicate through defined interfaces:
```python
# src/shared/interfaces.py defines contracts
def extract_profiles_from_raw(...) -> List[CandidateProfile]
def generate_candidate_embeddings(...) -> EmbeddingResult
def generate_project_embedding(...) -> ProjectFitResult
def build_teams(...) -> List[Team]
def generate_explanations(...) -> List[Report]
```

### Testing

```bash
# Unit tests
pytest tests/ -v

# Integration test
python tests/integration_test.py

# Coverage
pytest --cov=src tests/
```

---

## 12. 📈 Future Enhancements

- [ ] Multi-project team assignment
- [ ] Learning from feedback
- [ ] Integration with HR systems
- [ ] Advanced visualization dashboards
- [ ] Real-time team performance tracking
- [ ] Diversity & inclusion metrics
- [ ] Automatic team rebalancing
- [ ] Predictive compatibility models

---

## Summary

**SkillSync** is a modular, AI-powered system that solves the complex problem of team formation by combining:

1. **Data Extraction** (M5): Unstructured CV text → Structured profiles
2. **Skill Analysis** (M1): Profiles → Embeddings & diversity scores
3. **Project Matching** (M2): Requirements → Fit scores for candidates
4. **Optimization** (M3): Best team selection using multiple objectives
5. **Explanation** (M5): Human-readable reasoning for recommendations
6. **Presentation** (M4): User interface with visualization

The system is ready for use but requires enhancements in error handling, security, privacy compliance, and operational monitoring as detailed in PROJECT_REVIEW.md and COMPLIANCE_REPORT.md.

---

**Document Version**: 1.0  
**Last Updated**: January 21, 2026  
**Maintained By**: Team SkillSync
