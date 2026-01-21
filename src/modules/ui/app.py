# src/modules/ui/app_simple.py
import streamlit as st
import pandas as pd
import numpy as np
import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Try to load .env file from project root
env_path = project_root / ".env"
if env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        # Manual load if dotenv not available
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Safe conversion helper
def safe_int_convert(value, default=0):
    """Safely convert value to int, handling float strings."""
    if value is None:
        return default
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return default

# Import consolidated modules
try:
    from modules import (
        embed_candidates,
        embed_project,
        build_teams,
        extract_candidates,
        extract_project_requirements,
        generate_team_report,
        explain_team,
        TeamBuilderConfig
    )
    MODULES_AVAILABLE = True
except ImportError as e:
    MODULES_AVAILABLE = False
    st.error(f"Failed to import modules: {e}")

# Custom CSS with modern design
st.markdown("""
<style>
    /* Main styles */
    .main-header {
        font-size: 3rem;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #4B5563;
        margin-bottom: 2rem;
        text-align: center;
        font-weight: 300;
    }
    
    /* Cards */
    .team-card {
        border-radius: 16px;
        padding: 1.8rem;
        margin: 1.2rem 0;
        background: linear-gradient(145deg, #ffffff, #f8fafc);
        border: 1px solid #E5E7EB;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
    }
    
    .team-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #3B82F6 0%, #1E3A8A 100%);
        border-radius: 12px;
        padding: 1.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.2);
    }
    
    /* Skill badges */
    .skill-badge {
        background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%);
        color: #1E40AF;
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.3rem;
        display: inline-block;
        border: 1px solid #93C5FD;
        transition: all 0.2s ease;
    }
    
    .skill-badge:hover {
        transform: scale(1.05);
        box-shadow: 0 2px 4px rgba(30, 64, 175, 0.2);
    }
    
    .role-badge {
        background: linear-gradient(135deg, #F3E8FF 0%, #E9D5FF 100%);
        color: #7C3AED;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 0.2rem;
        display: inline-block;
        border: 1px solid #C4B5FD;
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3B82F6 0%, #1E3A8A 100%);
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #F8FAFC;
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3B82F6 !important;
        color: white !important;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-active { background-color: #10B981; }
    .status-warning { background-color: #F59E0B; }
    .status-inactive { background-color: #9CA3AF; }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="SkillSync - AI Team Formation",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'profiles' not in st.session_state:
    st.session_state.profiles = []
if 'project' not in st.session_state:
    st.session_state.project = None
if 'teams' not in st.session_state:
    st.session_state.teams = []
if 'explanations' not in st.session_state:
    st.session_state.explanations = []
if 'page' not in st.session_state:
    st.session_state.page = "📤 Upload Data"

# Main title with animation
st.markdown("""
<div class="fade-in">
    <h1 class="main-header">🚀 SkillSync</h1>
    <p class="sub-header">AI-Powered Team Formation System • Build Better Teams Faster</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with improved design
with st.sidebar:
    # Logo and title
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("<div style='font-size: 2rem;'>🚀</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("### **SkillSync**")
        st.caption("v2.0 • Modular Edition")
    
    st.markdown("---")
    
    # Navigation with icons
    st.markdown("### 📍 Navigation")
    page_options = {
        "📤 Upload Data": "Upload candidate profiles",
        "⚙️ Project Setup": "Define project requirements",
        "👥 Team Formation": "Build optimal teams",
        "📊 Calculation Reports": "View detailed algorithm calculations", 
        "📋 Results & Export": "Review and export teams"
    }
    
    selected_page = st.radio(
        "Select Page",
        list(page_options.keys()),
        index=list(page_options.keys()).index(st.session_state.page) if st.session_state.page in page_options else 0,
        label_visibility="collapsed"
    )
    
    st.session_state.page = selected_page
    
    # Display page description
    st.info(page_options[selected_page])
    
    st.markdown("---")
    
    # System status
    st.markdown("### 📈 System Status")
    
    status_cols = st.columns(2)
    with status_cols[0]:
        profile_count = len(st.session_state.profiles)
        st.metric("👤 Candidates", profile_count, 
                 delta="+{}".format(profile_count) if profile_count > 0 else None)
    
    with status_cols[1]:
        team_count = len(st.session_state.teams)
        st.metric("👥 Teams", team_count,
                 delta="+{}".format(team_count) if team_count > 0 else None)
    
    # Module availability
    st.markdown("---")
    st.markdown("### 🛠️ Module Status")
    if MODULES_AVAILABLE:
        st.success("✅ All modules available")
    else:
        st.error("❌ Modules not available")
    
    # Quick actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    if st.button("🔄 Reset All Data", use_container_width=True):
        for key in ['profiles', 'project', 'teams', 'explanations']:
            st.session_state[key] = [] if key != 'project' else None
        st.rerun()

# Page 1: Upload Data
if st.session_state.page == "📤 Upload Data":
    st.header("📤 Data Import Hub")
    
    tab1, tab2 = st.tabs(["📁 Upload CSV", "🔄 Sample Data"])
    
    with tab1:
        st.markdown("### Upload Candidate Data")
        st.markdown("Upload candidate profiles in CSV format (e.g., StackOverflow survey data)")
        
        uploaded_file = st.file_uploader(
            "Drag and drop CSV file here",
            type=['csv'],
            help="Expected format: CSV with candidate information"
        )
        
        if uploaded_file is not None and MODULES_AVAILABLE:
            if st.button("🔧 Extract Profiles", type="primary", use_container_width=True):
                with st.spinner("🔄 Extracting profiles from CSV..."):
                    try:
                        # Save uploaded file temporarily
                        temp_path = "temp_upload.csv"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getvalue())
                        
                        # Extract candidates using module
                        profiles, _ = extract_candidates(temp_path)
                        
                        if profiles:
                            # Convert to consistent format
                            candidate_objects = []
                            for i, p in enumerate(profiles[:20]):  # Limit to 20 for performance
                                # Safely convert values
                                exp_years = safe_int_convert(p.get('metadata', {}).get('work_experience_years', '0'))
                                avail_hours = safe_int_convert(p.get('constraints', {}).get('weekly_availability_hours', '20'))
                                
                                candidate_objects.append({
                                    "id": p.get('id', f"candidate_{i}"),
                                    "name": f"Candidate {p.get('id', f'{i}')}",
                                    "role": p.get('metadata', {}).get('dev_type', 'Unknown'),
                                    "skills": p.get('technical', {}).get('skills', []),
                                    "experience_years": exp_years,
                                    "availability_hours": avail_hours,
                                    "tools": p.get('technical', {}).get('tools', [])
                                })
                            
                            st.session_state.profiles = candidate_objects
                            
                            # Clean up
                            os.remove(temp_path)
                            
                            # Success animation
                            st.success(f"✅ Successfully loaded {len(candidate_objects)} candidate profiles")
                            st.balloons()
                            
                            # Display stats
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Profiles", len(candidate_objects))
                            with col2:
                                avg_skills = np.mean([len(p.get('skills', [])) for p in candidate_objects]) if candidate_objects else 0
                                st.metric("Avg Skills/Profile", f"{avg_skills:.1f}")
                            with col3:
                                roles = set(p.get('role', '') for p in candidate_objects)
                                st.metric("Unique Roles", len(roles))
                            
                            # Preview with expandable sections
                            with st.expander("🔍 Preview Profiles (First 5)", expanded=True):
                                df = pd.DataFrame(candidate_objects[:5])
                                st.dataframe(df, use_container_width=True)
                            
                            # Skills cloud visualization
                            with st.expander("☁️ Skills Distribution", expanded=False):
                                all_skills = []
                                for profile in candidate_objects:
                                    all_skills.extend(profile.get('skills', []))
                                
                                if all_skills:
                                    skill_counts = pd.Series(all_skills).value_counts().head(20)
                                    fig = px.bar(
                                        x=skill_counts.values,
                                        y=skill_counts.index,
                                        orientation='h',
                                        title="Top 20 Skills",
                                        labels={'x': 'Frequency', 'y': 'Skill'},
                                        color=skill_counts.values,
                                        color_continuous_scale='Blues'
                                    )
                                    fig.update_layout(height=400)
                                    st.plotly_chart(fig, use_container_width=True)
                    
                    except Exception as e:
                        st.error(f"❌ Error loading file: {str(e)}")
                        if "OPENROUTER_API_KEY" in str(e):
                            st.info("💡 Please set your OPENROUTER_API_KEY in the .env file")
    
    with tab2:
        st.markdown("### Load Sample Data")
        st.markdown("Quickly get started with sample candidate profiles")
        
        sample_options = {
            "Small Team (5 candidates)": 5,
            "Medium Team (10 candidates)": 10,
            "Large Team (20 candidates)": 20
        }
        
        selected_sample = st.selectbox("Choose sample size:", list(sample_options.keys()))
        
        if st.button("📥 Load Sample Data", type="primary", use_container_width=True):
            with st.spinner(f"Generating {selected_sample} sample profiles..."):
                # Generate sample data
                sample_data = []
                roles = ["Frontend Developer", "Backend Developer", "Full Stack Developer", "UX Designer", "DevOps Engineer"]
                skills_pool = ["Python", "JavaScript", "React", "Node.js", "SQL", "Docker", "AWS", "Figma", "ML", "Agile", "Git", "REST API", "HTML/CSS", "TypeScript", "Vue.js", "Angular", "MongoDB", "PostgreSQL", "Redis", "Kubernetes"]
                
                for i in range(sample_options[selected_sample]):
                    sample_data.append({
                        "id": f"sample_{i+1}",
                        "name": f"Candidate {chr(65 + i)}",
                        "role": roles[i % len(roles)],
                        "skills": np.random.choice(skills_pool, size=np.random.randint(3, 8), replace=False).tolist(),
                        "experience_years": np.random.randint(1, 15),
                        "availability_hours": np.random.randint(20, 40),
                        "tools": np.random.choice(["Git", "VS Code", "JIRA", "Docker", "AWS", "Figma", "Postman", "Slack"], size=3, replace=False).tolist()
                    })
                
                st.session_state.profiles = sample_data
                st.success(f"✅ Loaded {len(sample_data)} sample profiles!")
                st.rerun()

# Page 2: Project Setup
elif st.session_state.page == "⚙️ Project Setup":
    st.header("⚙️ Project Configuration")
    
    if not st.session_state.profiles:
        st.warning("📭 No candidate profiles found. Please upload data first.")
        if st.button("📤 Go to Upload Data"):
            st.session_state.page = "📤 Upload Data"
            st.rerun()
        st.stop()
    
    # Project header with timeline
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Define Your Project Requirements")
        st.caption("Configure the project that needs team formation")
    with col2:
        st.metric("Candidates", len(st.session_state.profiles))
    
    # Main configuration area
    config_col1, config_col2 = st.columns([2, 1])
    
    with config_col1:
        st.markdown("#### 📝 Project Details")
        project_title = st.text_input(
            "Project Title *",
            placeholder="E-commerce Platform Redesign",
            help="Enter a descriptive title for your project"
        )
        
        project_desc = st.text_area(
            "Project Description *",
            height=150,
            placeholder="""We need to redesign our e-commerce platform with new features including:
• Modern UI/UX redesign
• Recommendation engine integration
• Performance optimization
• Mobile-responsive design

Technical requirements:
- Frontend: React/TypeScript
- Backend: Python/FastAPI
- Database: PostgreSQL
- DevOps: Docker/Kubernetes""",
            help="Detailed description helps AI understand project needs better"
        )
    
    with config_col2:
        st.markdown("#### ⚙️ Project Parameters")
        
        team_size = st.slider(
            "Team Size",
            2, 8, 4,
            help="Number of team members needed"
        )
        
        n_teams = st.slider(
            "Number of Teams",
            1, 5, 1,
            help="How many team configurations to generate"
        )
        
        duration = st.selectbox(
            "Project Duration",
            ["2 weeks", "1 month", "2 months", "3 months", "6 months"],
            index=2
        )
    
    st.markdown("---")
    
    # Skills and Roles Configuration
    st.markdown("### 🛠️ Required Expertise")
    
    roles_col, skills_col = st.columns(2)
    
    with roles_col:
        st.markdown("#### 👥 Required Roles")
        # Get unique roles from candidates
        candidate_roles = list(set([p.get('role', '') for p in st.session_state.profiles if p.get('role')]))
        candidate_roles = [r for r in candidate_roles if r and r != 'Unknown']
        
        required_roles = st.multiselect(
            "Select essential roles",
            candidate_roles + ["Frontend Developer", "Backend Developer", "Full Stack Developer", 
                             "UX/UI Designer", "Data Scientist", "DevOps Engineer"],
            default=["Frontend Developer", "Backend Developer"] if "Frontend Developer" in candidate_roles else candidate_roles[:2],
            help="Select roles crucial for project success"
        )
    
    with skills_col:
        st.markdown("#### 💡 Required Skills")
        
        # Common skills list (always available)
        common_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Vue.js", "Angular",
            "Node.js", "Django", "Flask", "FastAPI", "SQL", "NoSQL", "MongoDB",
            "PostgreSQL", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD",
            "Git", "Agile", "Scrum", "Machine Learning", "Data Analysis", "Figma",
            "HTML", "CSS", "Java", "C#", "Go", "Rust", "Ruby", "PHP", "Swift",
            "Kotlin", "R", "TensorFlow", "PyTorch", "Spark", "Hadoop"
        ]
        
        # Get unique skills from candidates
        candidate_skills = []
        for profile in st.session_state.profiles:
            candidate_skills.extend(profile.get('skills', []))
        unique_candidate_skills = sorted(list(set(candidate_skills)))
        
        # Combine lists and remove duplicates
        all_available_skills = sorted(list(set(common_skills + unique_candidate_skills)))
        
        # Create two columns for better organization
        skill_col1, skill_col2 = st.columns(2)
        
        with skill_col1:
            required_skills = st.multiselect(
                "Select required skills",
                all_available_skills,
                default=["Python", "React", "SQL", "Docker", "JavaScript", "Git", "AWS"],
                help="Technical skills needed for the project. You can select any skill."
            )
        
        with skill_col2:
            # Allow manual skill entry
            st.markdown("##### ➕ Add Custom Skill")
            custom_skill = st.text_input(
                "Enter a skill not in the list",
                placeholder="e.g., Next.js, GraphQL, Redis",
                key="custom_skill_input"
            )
            
            if custom_skill and st.button("Add Skill", key="add_skill_btn"):
                if custom_skill.strip() and custom_skill not in required_skills:
                    required_skills.append(custom_skill.strip())
                    st.success(f"Added '{custom_skill}' to required skills")
                    st.rerun()
    
    st.markdown("---")
    
    # AI Extraction Option
    if MODULES_AVAILABLE:
        with st.expander("🤖 AI-Powered Requirement Extraction", expanded=False):
            st.markdown("Let AI analyze your project description and extract requirements automatically")
            
            if st.button("🔍 Extract Requirements from Description"):
                if project_desc.strip():
                    with st.spinner("AI is analyzing your project description..."):
                        try:
                            extracted_req = extract_project_requirements(project_desc)
                            tech_req = extracted_req.get('technical_requirements', {})
                            
                            # Update the multiselects
                            extracted_skills = tech_req.get('skills', [])
                            extracted_roles = tech_req.get('roles', [])
                            
                            st.success(f"✅ Extracted {len(extracted_skills)} skills and {len(extracted_roles)} roles")
                            
                            # Show what was extracted
                            if extracted_skills:
                                st.info(f"**Skills found:** {', '.join(extracted_skills[:10])}")
                            if extracted_roles:
                                st.info(f"**Roles suggested:** {', '.join(extracted_roles[:10])}")
                            
                        except Exception as e:
                            st.error(f"❌ Extraction failed: {e}")
                else:
                    st.warning("Please enter a project description first")
    
    st.markdown("---")
    
    # Save Project Button
    save_col1, save_col2, save_col3 = st.columns([1, 2, 1])
    
    with save_col2:
        if st.button("💾 Save Project Configuration", type="primary", use_container_width=True):
            if not project_desc:
                st.warning("⚠️ Please enter a project description")
            else:
                # Create project object
                project = {
                    "title": project_title or "Untitled Project",
                    "description": project_desc,
                    "required_roles": required_roles,
                    "required_skills": required_skills,
                    "team_size": team_size,
                    "n_teams": n_teams,
                    "duration": duration,
                    "timestamp": datetime.now().isoformat()
                }
                
                st.session_state.project = project
                st.success("✅ Project configuration saved!")
                
                # Auto-navigate to next page
                st.session_state.page = "👥 Team Formation"
                st.rerun()

# Page 3: Team Formation
elif st.session_state.page == "👥 Team Formation":
    st.header("👥 Intelligent Team Formation")
    
    if not st.session_state.project or not st.session_state.profiles:
        st.warning("📋 Please set up a project and upload candidates first")
        if st.button("⚙️ Go to Project Setup"):
            st.session_state.page = "⚙️ Project Setup"
            st.rerun()
        st.stop()
    
    st.markdown(f"### Building teams for: **{st.session_state.project.get('title', 'Untitled Project')}**")
    
    # Algorithm visualization section
    st.markdown("#### 🤖 Team Formation Algorithm")
    
    # Algorithm steps
    steps = [
        {"step": 1, "title": "Candidate Embeddings", "description": "Convert profiles to vector embeddings", "icon": "🔍"},
        {"step": 2, "title": "Project Embeddings", "description": "Convert project requirements to vectors", "icon": "🎯"},
        {"step": 3, "title": "Similarity Calculation", "description": "Calculate candidate-project fit scores", "icon": "📊"},
        {"step": 4, "title": "Team Optimization", "description": "Use greedy algorithm to form teams", "icon": "⚡"},
        {"step": 5, "title": "Team Assembly", "description": "Finalize balanced teams", "icon": "👥"}
    ]
    
    # Display steps
    cols = st.columns(len(steps))
    for i, step in enumerate(steps):
        with cols[i]:
            st.markdown(f"<div style='text-align: center; font-size: 2rem;'>{step['icon']}</div>", unsafe_allow_html=True)
            st.markdown(f"**Step {step['step']}**")
            st.caption(step['title'])
    
    st.markdown("---")
    
    # Algorithm parameters control
    st.markdown("#### ⚙️ Algorithm Parameters")
    
    param_col1, param_col2, param_col3 = st.columns(3)
    
    with param_col1:
        st.markdown("##### 🎯 Fit Weight (α)")
        alpha = st.slider("Project-Skill Fit Importance", 0.0, 1.0, 0.55, 0.05,
                         help="Higher values prioritize candidates with better skill match")
    
    with param_col2:
        st.markdown("##### 🌈 Diversity Weight (β)")
        beta = st.slider("Team Diversity Importance", 0.0, 1.0, 0.25, 0.05,
                        help="Higher values prioritize diverse skill sets")
    
    with param_col3:
        st.markdown("##### ⚖️ Coverage Weight (γ)")
        gamma = st.slider("Skill Coverage Importance", 0.0, 1.0, 0.20, 0.05,
                         help="Higher values prioritize covering all required skills")
    
    # Visualize weight distribution
    weights = [alpha, beta, gamma]
    labels = ['Fit', 'Diversity', 'Coverage']
    colors = ['#3B82F6', '#10B981', '#8B5CF6']
    
    fig_weights = go.Figure(data=[
        go.Bar(
            x=labels,
            y=weights,
            marker_color=colors,
            text=[f"{w:.2f}" for w in weights],
            textposition='auto'
        )
    ])
    
    fig_weights.update_layout(
        title="Algorithm Weight Distribution",
        yaxis_title="Weight",
        yaxis_range=[0, 1],
        height=300
    )
    
    st.plotly_chart(fig_weights, use_container_width=True)
    
    st.markdown("---")
    
    # Team building action
    st.markdown("#### 🚀 Build Teams")
    
    if not MODULES_AVAILABLE:
        st.error("❌ Modules not available. Please check your installation.")
        st.stop()
    
    build_col1, build_col2, build_col3 = st.columns([1, 2, 1])
    
    with build_col2:
        if st.button("🏗️ Construct Optimal Teams", type="primary", use_container_width=True):
            with st.status("🚀 Building optimal teams...", expanded=True) as status:
                try:
                    # Step 1: Convert profiles to module format
                    status.write("📊 Converting profiles to module format...")
                    profiles_dict = []
                    for p in st.session_state.profiles:
                        profiles_dict.append({
                            "id": p.get('id', ''),
                            "metadata": {
                                "dev_type": p.get('role', 'Unknown'),
                                "work_experience_years": str(p.get('experience_years', 0))
                            },
                            "technical": {
                                "skills": p.get('skills', [])
                            },
                            "constraints": {
                                "weekly_availability_hours": str(p.get('availability_hours', 20))
                            }
                        })
                    
                    # Step 2: Convert project to module format
                    status.write("🎯 Converting project requirements...")
                    project_dict = {
                        "title": st.session_state.project.get('title', ''),
                        "required_skills": st.session_state.project.get('required_skills', []),
                        "team_size": st.session_state.project.get('team_size', 4)
                    }
                    
                    # Step 3: Generate embeddings
                    status.write("🔍 Generating candidate embeddings...")
                    embedding_result = embed_candidates(profiles_dict)
                    
                    # Step 4: Generate project embeddings
                    status.write("📈 Calculating project-candidate fit...")
                    project_req = {
                        "technical_requirements": {
                            "skills": st.session_state.project.get('required_skills', []),
                            "roles": st.session_state.project.get('required_roles', [])
                        }
                    }
                    project_sim_result = embed_project(project_req)
                    
                    # Step 5: Build teams
                    status.write("🤖 Running optimization algorithm...")
                    config = TeamBuilderConfig(
                        alpha=alpha,
                        beta=beta,
                        gamma=gamma,
                        team_size=st.session_state.project.get('team_size', 4),
                        n_teams=st.session_state.project.get('n_teams', 1)
                    )
                    
                    teams = build_teams(
                        profiles=profiles_dict,
                        project=project_dict,
                        config=config,
                        candidate_dissim_matrix=embedding_result.get('dissimilarity_matrix'),
                        candidate_ids=embedding_result.get('candidate_ids'),
                        project_similarities=project_sim_result.get('candidate_similarities', {})
                    )
                    
                    # Step 6: Convert teams back to display format
                    status.write("👥 Assembling final teams...")
                    teams_objects = []
                    for team in teams:
                        team_objects = []
                        for member in team:
                            # Find original profile
                            orig_profile = next((p for p in st.session_state.profiles 
                                               if p.get('id') == member.get("id")), None)
                            if orig_profile:
                                # Add fit score from project similarities
                                fit_score = project_sim_result.get('candidate_similarities', {}).get(member.get("id"), 0.5)
                                team_member = orig_profile.copy()
                                team_member['fit'] = float(fit_score)
                                team_objects.append(team_member)
                        if team_objects:
                            teams_objects.append(team_objects)
                    
                    st.session_state.teams = teams_objects
                    
                    # Step 7: Generate explanations
                    status.write("💡 Generating team explanations...")
                    explanations = []
                    for team in teams_objects:
                        team_dict = [{
                            "id": p.get('id'),
                            "metadata": {"dev_type": p.get('role')},
                            "technical": {"skills": p.get('skills', [])}
                        } for p in team]
                        
                        explanation = explain_team(team_dict, project_dict)
                        explanations.append(explanation)
                    
                    st.session_state.explanations = explanations
                    
                    status.update(label="✅ Team formation complete!", state="complete")
                    
                    st.success(f"✨ Generated {len(teams_objects)} team configurations!")
                    st.balloons()
                    
                    # Auto-navigate to results
                    st.session_state.page = "📋 Results & Export"
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error building teams: {e}")
                    status.update(label="❌ Team formation failed", state="error")

# Page 4: Results & Export
elif st.session_state.page == "📋 Results & Export":
    st.header("📋 Team Recommendations & Export")
    
    if not st.session_state.teams:
        st.warning("👥 No teams generated yet. Please generate teams first.")
        if st.button("👥 Go to Team Formation"):
            st.session_state.page = "👥 Team Formation"
            st.rerun()
        st.stop()
    
    st.markdown(f"### Project: **{st.session_state.project.get('title', 'Untitled Project')}**")
    
    # Team selection
    st.markdown("#### 🎯 Select Team to Review")
    
    team_options = [f"Team {i+1} • Score: {np.mean([m.get('fit', 0.5) for m in team]):.2f}" 
                   for i, team in enumerate(st.session_state.teams)]
    
    selected_team_str = st.selectbox(
        "Choose a team:",
        team_options,
        index=0,
        label_visibility="collapsed"
    )
    
    team_idx = int(selected_team_str.split()[1]) - 1
    
    if team_idx < len(st.session_state.teams):
        team = st.session_state.teams[team_idx]
        explanation = (st.session_state.explanations[team_idx] 
                      if team_idx < len(st.session_state.explanations) 
                      else "No explanation available")
        
        # Team card with enhanced design
        st.markdown("<div class='team-card'>", unsafe_allow_html=True)
        
        # Team header
        header_cols = st.columns([3, 1])
        with header_cols[0]:
            st.markdown(f"### 👥 Team {team_idx + 1}")
            st.caption(f"{len(team)} members • Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        with header_cols[1]:
            avg_fit = np.mean([m.get('fit', 0.5) for m in team])
            if avg_fit >= 0.85:
                st.markdown(f"<div style='text-align: center;'><h1 style='color: #10B981;'>⭐</h1><h4>Excellent Fit</h4></div>", 
                           unsafe_allow_html=True)
            elif avg_fit >= 0.7:
                st.markdown(f"<div style='text-align: center;'><h1 style='color: #F59E0B;'>✨</h1><h4>Good Fit</h4></div>", 
                           unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align: center;'><h1 style='color: #EF4444;'>⚡</h1><h4>Needs Review</h4></div>", 
                           unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Team metrics
        metrics_cols = st.columns(4)
        with metrics_cols[0]:
            st.metric("Project Fit", f"{avg_fit:.2f}")
        with metrics_cols[1]:
            unique_skills = len(set([skill for m in team for skill in m.get('skills', [])]))
            st.metric("Unique Skills", unique_skills)
        with metrics_cols[2]:
            avg_exp = np.mean([m.get('experience_years', 0) for m in team])
            st.metric("Avg Experience", f"{avg_exp:.1f} yrs")
        with metrics_cols[3]:
            # Skill coverage
            if st.session_state.project:
                required = set(st.session_state.project.get('required_skills', []))
                team_skills = set([skill for m in team for skill in m.get('skills', [])])
                coverage = len(required & team_skills)
                total = len(required)
                if total > 0:
                    st.metric("Skill Coverage", f"{coverage}/{total}", 
                             f"{coverage/max(total,1)*100:.0f}%")
                else:
                    st.metric("Required Skills", "Not specified")
        
        st.markdown("---")
        
        # Team members
        st.markdown("#### 👨‍💻 Team Members")
        
        for i, member in enumerate(team):
            with st.container():
                cols = st.columns([1, 3, 1, 1])
                
                with cols[0]:
                    # Avatar with color based on fit
                    fit_score = member.get('fit', 0.5)
                    if fit_score >= 0.85:
                        color = "#10B981"
                    elif fit_score >= 0.7:
                        color = "#F59E0B"
                    else:
                        color = "#EF4444"
                    
                    st.markdown(f"""
                    <div style='
                        width: 50px; 
                        height: 50px; 
                        background: linear-gradient(135deg, {color} 0%, {color}80 100%);
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 1.5rem;
                        font-weight: bold;
                        margin: auto;
                    '>
                        {member.get('name', '?')[0]}
                    </div>
                    """, unsafe_allow_html=True)
                
                with cols[1]:
                    st.markdown(f"**{member.get('name', 'Unknown Member')}**")
                    st.markdown(f"*{member.get('role', 'No role specified')}*")
                    
                    # Skills badges
                    skills = member.get('skills', [])[:6]
                    if skills:
                        badges_html = " ".join([f"<span class='skill-badge'>{skill}</span>" for skill in skills])
                        st.markdown(badges_html, unsafe_allow_html=True)
                
                with cols[2]:
                    st.metric("Fit", f"{member.get('fit', 0.5):.2f}")
                
                with cols[3]:
                    exp = member.get('experience_years', 0)
                    st.metric("Exp", f"{exp} yrs")
                
                if i < len(team) - 1:
                    st.markdown("---")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # AI Explanation
        st.markdown("#### 💡 AI Explanation & Recommendations")
        st.info(explanation)
        
        # Action buttons
        st.markdown("#### ⚡ Actions")
        
        action_cols = st.columns(4)
        
        with action_cols[0]:
            if st.button("✅ Select This Team", type="primary", use_container_width=True):
                st.success(f"✅ Team {team_idx + 1} selected! 🎉")
                st.balloons()
        
        with action_cols[1]:
            if st.button("🔄 Regenerate Teams", use_container_width=True):
                st.session_state.page = "👥 Team Formation"
                st.rerun()
        
        with action_cols[2]:
            # Export as JSON
            json_data = {
                "team_id": team_idx + 1,
                "project": st.session_state.project,
                "members": team,
                "metrics": {
                    "avg_fit": avg_fit,
                    "unique_skills": unique_skills,
                    "avg_experience": avg_exp,
                    "generated_at": datetime.now().isoformat()
                }
            }
            
            st.download_button(
                label="📥 Export JSON",
                data=json.dumps(json_data, indent=2),
                file_name=f"team_{team_idx + 1}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with action_cols[3]:
            # Export as CSV
            csv_data = []
            for member in team:
                csv_data.append({
                    "name": member.get('name'),
                    "role": member.get('role'),
                    "skills": ", ".join(member.get('skills', [])),
                    "fit_score": member.get('fit', 0.5),
                    "experience_years": member.get('experience_years', 0),
                    "availability_hours": member.get('availability_hours', 20)
                })
            
            df_csv = pd.DataFrame(csv_data)
            csv_string = df_csv.to_csv(index=False)
            
            st.download_button(
                label="📊 Export CSV",
                data=csv_string,
                file_name=f"team_{team_idx + 1}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    # All teams overview
    st.markdown("---")
    st.markdown("### 📋 All Generated Teams")
    
    for i, team in enumerate(st.session_state.teams):
        with st.expander(f"Team {i+1} • {len(team)} members • Score: {np.mean([m.get('fit', 0.5) for m in team]):.2f}", 
                        expanded=(i == team_idx)):
            
            # Quick stats
            stats_cols = st.columns(4)
            with stats_cols[0]:
                st.metric("Fit", f"{np.mean([m.get('fit', 0.5) for m in team]):.2f}")
            with stats_cols[1]:
                st.metric("Size", len(team))
            with stats_cols[2]:
                unique_skills = len(set([skill for m in team for skill in m.get('skills', [])]))
                st.metric("Unique Skills", unique_skills)
            with stats_cols[3]:
                st.metric("Avg Exp", f"{np.mean([m.get('experience_years', 3) for m in team]):.1f}y")
            
            # Brief explanation
            if i < len(st.session_state.explanations):
                st.caption(st.session_state.explanations[i][:200] + "...")
# Page 5: Calculation Reports
elif st.session_state.page == "📊 Calculation Reports":
    st.header("📊 Algorithm Calculation Reports")
    
    if not st.session_state.project or not st.session_state.profiles or not st.session_state.teams:
        st.warning("📊 No calculation data available. Please generate teams first.")
        if st.button("👥 Go to Team Formation"):
            st.session_state.page = "👥 Team Formation"
            st.rerun()
        st.stop()
    
    # Tab organization
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Score Calculations", "🎯 Candidate Rankings", "🤖 Algorithm Steps", "📋 Raw Data"])
    
    with tab1:
        st.markdown("### 📈 Team Score Calculations")
        
        # Create a DataFrame for score calculations
        score_data = []
        for i, team in enumerate(st.session_state.teams):
            # Calculate various scores
            avg_fit = np.mean([m.get('fit', 0.5) for m in team])
            unique_skills = len(set([skill for m in team for skill in m.get('skills', [])]))
            
            # Project requirements
            required_skills = st.session_state.project.get('required_skills', [])
            team_skills = set([skill for m in team for skill in m.get('skills', [])])
            
            # Coverage score
            if required_skills:
                coverage = len(set(required_skills) & team_skills) / len(required_skills)
            else:
                coverage = 0
            
            # Diversity score (simplified - based on unique roles)
            roles = [m.get('role', 'Unknown') for m in team]
            diversity = len(set(roles)) / len(roles) if team else 0
            
            # Experience score
            avg_exp = np.mean([m.get('experience_years', 0) for m in team])
            exp_score = min(1.0, avg_exp / 10)  # Normalize to 0-1
            
            score_data.append({
                "Team": f"Team {i+1}",
                "Fit Score": f"{avg_fit:.3f}",
                "Skill Coverage": f"{coverage:.1%}",
                "Diversity Score": f"{diversity:.3f}",
                "Experience Score": f"{exp_score:.3f}",
                "Unique Skills": unique_skills,
                "Team Size": len(team)
            })
        
        df_scores = pd.DataFrame(score_data)
        st.dataframe(df_scores, use_container_width=True)
        
        # Visualize scores
        if score_data:
            st.markdown("#### 📊 Score Visualization")
            metrics = ['Fit Score', 'Skill Coverage', 'Diversity Score', 'Experience Score']
            
            # Convert string percentages to float for plotting
            plot_data = []
            for team_data in score_data:
                team_name = team_data['Team']
                fit = float(team_data['Fit Score'])
                coverage = float(team_data['Skill Coverage'].strip('%')) / 100
                diversity = float(team_data['Diversity Score'])
                experience = float(team_data['Experience Score'])
                
                plot_data.append({
                    'Team': team_name,
                    'Fit': fit,
                    'Coverage': coverage,
                    'Diversity': diversity,
                    'Experience': experience
                })
            
            df_plot = pd.DataFrame(plot_data)
            
            fig = go.Figure()
            
            for team in df_plot['Team']:
                team_data = df_plot[df_plot['Team'] == team]
                fig.add_trace(go.Scatterpolar(
                    r=[team_data['Fit'].values[0], 
                       team_data['Coverage'].values[0],
                       team_data['Diversity'].values[0],
                       team_data['Experience'].values[0],
                       team_data['Fit'].values[0]],  # Close the shape
                    theta=['Fit', 'Coverage', 'Diversity', 'Experience', 'Fit'],
                    fill='toself',
                    name=team
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )),
                showlegend=True,
                title="Team Performance Radar Chart",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("### 🎯 Individual Candidate Rankings")
        
        # Collect all candidates with their scores
        candidate_scores = []
        for profile in st.session_state.profiles:
            # Find if candidate is in any team
            in_team = False
            team_found = None
            for i, team in enumerate(st.session_state.teams):
                if any(m.get('id') == profile.get('id') for m in team):
                    in_team = True
                    team_found = i + 1
                    break
            
            candidate_scores.append({
                "Name": profile.get('name', 'Unknown'),
                "Role": profile.get('role', 'Unknown'),
                "Experience": profile.get('experience_years', 0),
                "Skills Count": len(profile.get('skills', [])),
                "In Team": "✅ Yes" if in_team else "❌ No",
                "Team #": team_found if in_team else "-",
                "Fit Score": profile.get('fit', 'N/A')
            })
        
        df_candidates = pd.DataFrame(candidate_scores)
        
        # Sort by experience or fit score
        sort_by = st.selectbox("Sort by:", ["Experience", "Skills Count", "In Team"])
        if sort_by == "Experience":
            df_candidates = df_candidates.sort_values("Experience", ascending=False)
        elif sort_by == "Skills Count":
            df_candidates = df_candidates.sort_values("Skills Count", ascending=False)
        
        st.dataframe(df_candidates, use_container_width=True)
        
        # Statistics
        st.markdown("#### 📊 Candidate Pool Statistics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_candidates = len(st.session_state.profiles)
            selected_candidates = sum(1 for c in candidate_scores if c["In Team"] == "✅ Yes")
            st.metric("Selected", selected_candidates, 
                     f"{selected_candidates/total_candidates*100:.0f}%")
        with col2:
            avg_exp = np.mean([p.get('experience_years', 0) for p in st.session_state.profiles])
            st.metric("Avg Experience", f"{avg_exp:.1f} years")
        with col3:
            avg_skills = np.mean([len(p.get('skills', [])) for p in st.session_state.profiles])
            st.metric("Avg Skills", f"{avg_skills:.1f}")
        with col4:
            unique_roles = len(set([p.get('role', '') for p in st.session_state.profiles]))
            st.metric("Unique Roles", unique_roles)
    
    with tab3:
        st.markdown("### 🤖 Algorithm Execution Steps")
        
        steps = [
            {
                "step": 1,
                "name": "Data Preparation",
                "description": "Convert candidate profiles to vector embeddings",
                "details": f"Processed {len(st.session_state.profiles)} candidate profiles"
            },
            {
                "step": 2,
                "name": "Project Analysis",
                "description": "Extract and embed project requirements",
                "details": f"Extracted {len(st.session_state.project.get('required_skills', []))} skills and {len(st.session_state.project.get('required_roles', []))} roles"
            },
            {
                "step": 3,
                "name": "Similarity Calculation",
                "description": "Calculate candidate-project fit scores",
                "details": "Used cosine similarity on embeddings"
            },
            {
                "step": 4,
                "name": "Team Formation",
                "description": "Apply greedy algorithm with weights",
                "details": f"α={st.session_state.project.get('alpha', 0.55):.2f} (Fit), β={st.session_state.project.get('beta', 0.25):.2f} (Diversity), γ={st.session_state.project.get('gamma', 0.20):.2f} (Coverage)"
            },
            {
                "step": 5,
                "name": "Optimization",
                "description": "Balance team composition",
                "details": f"Generated {len(st.session_state.teams)} team configurations"
            },
            {
                "step": 6,
                "name": "Validation",
                "description": "Check constraints and requirements",
                "details": f"Team size: {st.session_state.project.get('team_size', 4)}, Duration: {st.session_state.project.get('duration', '2 months')}"
            }
        ]
        
        for step in steps:
            with st.expander(f"Step {step['step']}: {step['name']}", expanded=True):
                st.markdown(f"**{step['description']}**")
                st.markdown(f"*{step['details']}*")
                
                # Add progress bar for visual effect
                if step['step'] <= 6:
                    st.progress(step['step'] / 6)
        
        # Algorithm weights visualization
        st.markdown("#### ⚖️ Algorithm Weights Configuration")
        weights_data = {
            'Metric': ['Fit (α)', 'Diversity (β)', 'Coverage (γ)'],
            'Value': [
                st.session_state.project.get('alpha', 0.55),
                st.session_state.project.get('beta', 0.25),
                st.session_state.project.get('gamma', 0.20)
            ],
            'Description': [
                'Project-skill matching importance',
                'Team diversity and complementary skills',
                'Coverage of all required skills'
            ]
        }
        
        df_weights = pd.DataFrame(weights_data)
        st.dataframe(df_weights, use_container_width=True)
        
        # Pie chart of weights
        fig = px.pie(
            df_weights,
            values='Value',
            names='Metric',
            title='Algorithm Weight Distribution',
            color='Metric',
            color_discrete_sequence=['#3B82F6', '#10B981', '#8B5CF6']
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with tab4:
        st.markdown("### 📋 Raw Calculation Data")
        
        st.markdown("#### Project Requirements")
        st.json(st.session_state.project, expanded=False)
        
        st.markdown("#### Algorithm Configuration")
        config_data = {
            "team_size": st.session_state.project.get('team_size', 4),
            "n_teams": st.session_state.project.get('n_teams', 1),
            "alpha": st.session_state.project.get('alpha', 0.55),
            "beta": st.session_state.project.get('beta', 0.25),
            "gamma": st.session_state.project.get('gamma', 0.20),
            "required_skills_count": len(st.session_state.project.get('required_skills', [])),
            "required_roles_count": len(st.session_state.project.get('required_roles', [])),
            "candidate_pool_size": len(st.session_state.profiles)
        }
        st.json(config_data, expanded=False)
        
        st.markdown("#### Team Composition Summary")
        team_summary = []
        for i, team in enumerate(st.session_state.teams):
            team_summary.append({
                f"Team_{i+1}": {
                    "size": len(team),
                    "members": [m.get('name') for m in team],
                    "roles": list(set([m.get('role') for m in team])),
                    "avg_experience": np.mean([m.get('experience_years', 0) for m in team]),
                    "skill_coverage": len(set([skill for m in team for skill in m.get('skills', [])]))
                }
            })
        
        for summary in team_summary:
            st.json(summary, expanded=False)
        
        # Download raw data
        st.markdown("---")
        st.markdown("#### 📥 Download Calculation Data")
        
        all_data = {
            "project": st.session_state.project,
            "algorithm_config": config_data,
            "teams": team_summary,
            "generated_at": datetime.now().isoformat()
        }
        
        json_data = json.dumps(all_data, indent=2)
        
        st.download_button(
            label="📄 Download Full Calculation Report",
            data=json_data,
            file_name=f"calculation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
# Footer with enhanced design
st.markdown("""
<hr style='margin: 3rem 0; border: none; height: 2px; background: linear-gradient(90deg, transparent, #3B82F6, transparent);'>
<div style='
    text-align: center; 
    color: #64748b; 
    font-size: 0.9rem;
    padding: 2rem 0;
'>
    <div style='font-size: 1.5rem; margin-bottom: 1rem;'>
        🚀 <strong>SkillSync</strong> • AI-Powered Team Formation System
    </div>
    <div style='margin-bottom: 0.5rem;'>
        Group 45 • TU Wien • 2025
    </div>
    <div style='font-size: 0.8rem; color: #94a3b8;'>
        Using consolidated modules • Last updated: """ + datetime.now().strftime("%Y-%m-%d") + """
    </div>
</div>
""", unsafe_allow_html=True)