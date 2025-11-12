<div style="display:flex; align-items:center; justify-content:space-between;">
  <h1 style="margin:0">CV-Sage: Intelligent CV Analysis & Enhancement Assistant</h1>
  <img src="assets/tu.png" alt="logo" style="height:100px;">
</div>

## Table of contents
- [1. Project Overview](#overview)
- [2. Target Users](#target-users)
  - [2.1 Job Seekers](#job-seekers)
  - [2.2 Recruiters/Hiring Managers](#recruiters-hiring-managers)
- [3. Data Sources & Characteristics](#data-sources)
- [4. Core Problems Addressed](#core-problems)
- [5. Solution Components](#solution-components)
- [6. Evaluation Plan](#evaluation-plan)
- [Development Timeline](#development-timeline)
- [Next Steps for Discussion](#next-steps)
- [Resources Needed](#resources-needed)

<a id="overview"></a>
## 1. Project Overview
CV-Sage is a generative AI application that helps both job seekers and recruiters work more effectively with CV/resume data and job descriptions. The system provides intelligent matching, analysis, and actionable suggestions to streamline the job application and recruitment processes.

<a id="target-users"></a>
## 2. Target Users

<a id="job-seekers"></a>
### 2.1 Job Seekers
- **Goals**: Create effective, tailored CVs; understand how their CV is perceived; quickly adapt CVs for new applications
- **Workflow**: Start with master CV → manually tailor for each job → guess important keywords → struggle to articulate skills effectively

<a id="recruiters-hiring-managers"></a>
### 2.2 Recruiters/Hiring Managers
- **Goals**: Quickly screen large volumes of CVs; identify best-fit candidates; reduce unconscious bias; analyze applicant pool strengths
- **Workflow**: Post job description → receive hundreds of CVs → time-consuming manual screening → inconsistent matching

<a id="data-sources"></a>
## 3. Data Sources & Characteristics

### 3.1 Data Types
- **CVs/Resumes**: Semi-structured documents (Work Experience, Education, Skills, Projects)
- **Job Descriptions**: Unstructured text describing role requirements

### 3.2 Data Characteristics
- **Granularity**: Mixed (atomic skills vs. narrative paragraphs)
- **Connections**: Largely implicit (must be inferred)
- **Completeness**: Highly variable
- **Heterogeneity**: High (different formats, layouts, writing styles)

### 3.3 Dataset Strategy
- **Size**: 200-500 CVs + 50-100 Job Descriptions
- **Sources**: 
  - Public datasets (Kaggle Resume Dataset, Job Description datasets)
  - Synthetic data generation using LLMs
  - Justification: Large enough for meaningful testing, manageable for scope


<a id="core-problems"></a>
## 4. Core Problems Addressed

### 4.1 For Job Seekers: "Tailoring Friction"
"I have to spend 30+ minutes manually comparing my CV to each job description and guessing what to highlight."

### 4.2 For Recruiters: "Information Overload & Matching"
"Manually reading and matching hundreds of CVs is slow, inconsistent, and I might miss great candidates."

<a id="solution-components"></a>
## 5. Solution Components

### 5.1 Core Tasks
1. **Understand**: Parse CVs/JDs to extract structured information
2. **Retrieve & Match**: Rank relevant CVs for JDs and match CV sections to requirements
3. **Generate & Augment**: 
   - **Tailoring Report**: Suggestions for job seekers to improve CV for specific JD
   - **Candidate Match Report**: Match score + breakdown for recruiters

### 5.2 User Interface
**Web Application** - Accessible for both user groups, easy file upload, interactive reports

### 5.3 Technical Challenges
1. **Structured Information Extraction**: Using LLMs to consistently extract entities from heterogeneous CV formats
2. **Semantic Matching**: Hybrid approach combining dense vector embeddings + keyword matching
3. **Actionable Insight Generation**: LLM-powered suggestions grounded in CV/JD data

<a id="evaluation-plan"></a>
## 6. Evaluation Plan

### 6.1 CV Parser (Understanding)
- **Metric**: F1-score for entities (Skill, Job Title, Company)
- **Method**: Compare against manually annotated gold-standard set (20-30 CVs)

### 6.2 Matching System (Retrieval)
- **Metrics**: Mean Reciprocal Rank (MRR), Precision@K (P@5)
- **Method**: Test on dataset with known "ground truth" matches

### 6.3 Report Generation
- **Method**: Human evaluation with scoring rubric
- **Criteria**: Relevance, Actionability, Accuracy (1-5 scale)


<a id="development-timeline"></a>
## Development Timeline

### Phase 1: Foundation
1. Data collection & cleaning
2. CV parsing prototype with LLM API
3. Basic embedding & semantic search

### Phase 2: Core System 
4. Hybrid matching engine development
5. Report generation with LLM prompts
6. Backend API (FastAPI)

### Phase 3: Integration & Evaluation
7. Frontend web app (Streamlit/React)
8. Formal evaluation on test set
9. Technical report writing

<a id="next-steps"></a>
## Next Steps for Discussion
1. Refine technical approach priorities
2. Identify specific datasets to use
3. Assign initial responsibilities
4. Discuss implementation details for parsing and matching
5. Plan evaluation methodology in more detail

<a id="resources-needed"></a>
## Resources Needed
- LLM API access (OpenAI/Anthropic/etc.)
- Embedding models (sentence-transformers)
- Web framework (Streamlit recommended for prototype)
- Evaluation datasets

Let's use this as our starting point for discussion and refinement!

_Not: emotional damage is incoming!_