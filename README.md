# Project: SkillSync

## 🚀 Overview

SkillSync is an intelligent team formation system that uses AI and machine learning to build optimal teams based on candidate profiles and project requirements. The system analyzes skills, experience, roles, and collaboration preferences to form balanced, high-performing teams.

## 📁 Project Structure

skill-sync-project/
├── .env                         # API keys and configuration
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── src/
│   ├── modules/                 # Consolidated modules (M1-M5)
│   │   ├── __init__.py          # Main module interface
│   │   ├── candidate_embeddings/  # M1: Candidate embeddings
│   │   ├── project_embeddings/    # M2: Project embeddings
│   │   ├── team_builder/          # M3: Team building algorithms
│   │   ├── json_extraction/       # M4: JSON extraction from text/CSV
│   │   ├── EXPLANATION/           # M5: Team explanations and reports
│   │   └── ui/
│   │       ├── app_simple.py     # Main Streamlit UI application
│   │       └── app.py           # Advanced UI (if available)
│   └── shared/                  # Shared interfaces
└── data/
    └── artifacts/              # Saved embeddings and calculations

## 🛠️ Installation & Setup

### 1. Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```
If requirements.txt doesn't exist, install manually:

```bash
pip install streamlit pandas numpy plotly scikit-learn sentence-transformers python-dotenv
```

### 4. API Key Setup
Create **.env** file in the project root:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

**How to get an API key:**
1. Sign up at [OpenRouter](https://openrouter.ai/).
2. Create an API key in your account settings.
3. Copy the key (starts with sk-or-v1-)
4. Paste it in the .env file

**Location of .env file:**

Place the **.env** file in the project root directory (same level as src/ folder)

### 5. Sample Data

Create a CSV file with candidate data (use the provided sample format). Place it anywhere on your system - the app will let you upload it.

## 🏃‍♂️ Running the Application

**Start the Streamlit App:**

From project root:

```bash
streamlit run src/modules/ui/app.py
```

The app will open in your browser at http://localhost:8501

## 🧭 UI Navigation Guide

### 1. 📤 Upload Data Page

Purpose: Import candidate profiles
Options:

- Upload CSV: Upload your candidate data file
- Sample Data: Load pre-generated sample candidates (for testing)

How to use CSV:

- Use the provided sample CSV format
- Make sure columns match the expected names
- File should have .csv extension
- Click "Extract Profiles" to process

### 2. ⚙️ Project Setup Page

Purpose: Define your project requirements

Configuration sections:

- Project Details: Title and description
- Project Parameters: Team size, duration, urgency
- Required Roles: Select needed roles from dropdown
- Required Skills: Select or type skills (you can add custom skills)
- AI Extraction: Optional - let AI extract requirements from description

Important: You can type ANY skill, not just those from candidates!

### 3. 👥 Team Formation Page

Purpose: Build teams using AI algorithm

Key sections:

- Algorithm Visualization: See how the algorithm works step-by-step
- Parameter Controls: Adjust weights (α, β, γ)
  - α (Alpha): Project-skill fit importance (default: 0.55)
  - β (Beta): Team diversity importance (default: 0.25)
  - γ (Gamma): Skill coverage importance (default: 0.20)
- Build Teams: Click to generate team recommendations

### 4. 📊 Calculation Reports Page

Purpose: View detailed algorithm calculations and insights

Tabs available:

- Score Calculations: See how each team was scored
- Candidate Rankings: View individual candidate evaluations
- Algorithm Steps: Detailed breakdown of the algorithm process
- Raw Data: Exportable calculation data

### 5. 📋 Results & Export Page

Purpose: Review and export formed teams

Features:

- Team selection dropdown
- Team member details with skills and scores
- AI-generated explanations
- Export options (JSON, CSV)
- Team comparison

## 🔧 Key Features Explained

### 1. Candidate Extraction (M5)

- Extracts structured profiles from CSV/text
- Handles multiple skills formats (semicolon-separated)
- Converts experience years and availability hours
- Supports float values (e.g., "4.0" becomes 4)

### 2. Embeddings (M1 & M2)

- Uses sentence-transformers for text embeddings
- Calculates similarity between candidates and projects
- Falls back to mock embeddings if model unavailable

### 3. Team Building Algorithm (M3)

- Greedy algorithm with configurable weights
- Three factors:
  - Fit: Candidate-project skill match
  - Diversity: Complementary skills and roles
  - Coverage: Coverage of all required skills
- Supports multiple team generation

### 4. Explanations (M5)

- AI-generated team explanations
- Markdown report generation
- Strength and recommendation analysis

### 5. Calculation Reports

- New feature: Shows algorithm internals
- Score breakdowns: Fit, coverage, diversity, experience
- Visualizations: Radar charts, bar graphs
- Exportable: JSON reports for analysis

## 🐛 Troubleshooting

### Common Issues:

**"Modules not available" error**

- Check Python path is set correctly
- Make sure you're running from project root
- Verify all dependencies are installed

**API Key not loading**

- Check .env file location (should be in project root)
- Verify API key format (should start with sk-or-v1-)
- Restart the app after adding API key

**CSV extraction errors**

- Ensure CSV format matches sample
- Check for special characters or quotes
- Try the sample data first

**No skills showing in dropdown**

- The new version allows typing ANY skill
- Use "Add Custom Skill" feature
- Or type directly in the multiselect

**Slow performance**

- Limit candidate count to 20-30 for testing
- Sample data is optimized for performance
- Algorithm complexity increases with candidate count

### Debug Mode:

To see what's happening:

- Check terminal output when starting Streamlit
- Look for API key loading messages
- Check for import errors

## 📊 Sample Project Setup for Testing

Use this configuration for quick testing:

**Project Title:** E-commerce Platform Redesign

**Description:**

```text
We need to redesign our e-commerce platform with React frontend and Python backend. 
The project requires:
- Modern UI with React and TypeScript
- REST API with Python FastAPI
- PostgreSQL database
- Docker containerization
- AWS deployment
- Git version control
```

**Parameters:**

- Team Size: 4
- Number of Teams: 1
- Duration: 2 months

**Required Skills (type these):**

- React
- Python
- SQL
- Docker
- AWS
- Git
- JavaScript/TypeScript

## 💡 Tips for Best Results

- Start with sample data to understand the system
- Use clear project descriptions for better AI extraction
- Adjust algorithm weights based on your priorities
- Check calculation reports to understand team selection
- Export results for further analysis
- Experiment with different team sizes and requirements

## 🔗 Useful Links

- OpenRouter API: https://openrouter.ai/
- Streamlit Documentation: https://docs.streamlit.io/
- Sample CSV Format: Provided in the project
- Algorithm Details: See calculation reports in the app

## 👥 Development Team

- M1: Candidate Embeddings
- M2: Project Embeddings
- M3: Team Building Algorithms
- M4: Architecture & UI
- M5: JSON Extraction & Explanations

Group 45 • TU Wien • 2025

## 📄 License

Educational project for TU Wien course. Not for commercial use.