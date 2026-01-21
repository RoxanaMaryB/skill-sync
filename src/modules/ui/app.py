# src/modules/ui/app.py
import streamlit as st
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys
import os
import time
import plotly.colors as pc
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.interfaces import CandidateProfile, ProjectDescription

# Page configuration
st.set_page_config(
    page_title="SkillSync - AI Team Formation",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    /* Sidebar */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1E3A8A 0%, #3B82F6 100%);
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
    
    /* Grid layout */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 1.5rem 0;
    }
    
    /* Table styling */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

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
        st.image("https://img.icons8.com/color/96/000000/teamwork.png", width=60)
    with col2:
        st.markdown("### **SkillSync**")
        st.caption("v2.0 • Professional Edition")
    
    st.markdown("---")
    
    # Navigation with icons
    st.markdown("### 📍 Navigation")
    page_options = {
        "📤 Upload Data": "Upload candidate profiles and project data",
        "⚙️ Project Setup": "Define project requirements and constraints",
        "🔍 Candidate Analysis": "Explore candidate skills and compatibility",
        "👥 Team Formation": "Build and visualize optimal teams",
        "📊 Analytics Dashboard": "View metrics and insights",
        "📋 Results & Export": "Review and export team configurations"
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
        profile_count = len(st.session_state.profiles) if st.session_state.profiles else 0
        st.metric("👤 Candidates", profile_count, 
                 delta="+{}".format(profile_count) if profile_count > 0 else None)
    
    with status_cols[1]:
        team_count = len(st.session_state.teams)
        st.metric("👥 Teams", team_count,
                 delta="+{}".format(team_count) if team_count > 0 else None)
    
    # Progress bar for data completeness
    if st.session_state.project and st.session_state.profiles:
        completeness = min(100, (len(st.session_state.profiles) / 50) * 100)
        st.progress(completeness / 100, text=f"Data Completeness: {completeness:.0f}%")
    
    st.markdown("---")
    
    # Team member display with avatars
    st.markdown("### 👨‍💻 Development Team")
    team_members = [
        {"name": "Shahzad", "role": "M1: Candidate Embeddings", "emoji": "🎯"},
        {"name": "Roxana", "role": "M2: Project Embeddings", "emoji": "📊"},
        {"name": "Ana", "role": "M3: Team Algorithm", "emoji": "🤖"},
        {"name": "Saban", "role": "M4: Architecture & UI", "emoji": "💻"},
        {"name": "Noor", "role": "M5: JSON & Explanations", "emoji": "📝"}
    ]
    
    for member in team_members:
        with st.container():
            cols = st.columns([1, 4])
            with cols[0]:
                st.markdown(f"<div style='font-size: 1.5rem;'>{member['emoji']}</div>", unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"**{member['name']}**")
                st.caption(member['role'])
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    if st.button("🔄 Reset All Data", use_container_width=True):
        for key in ['profiles', 'project', 'teams', 'explanations']:
            st.session_state[key] = [] if key != 'project' else None
        st.rerun()
    
    if st.button("📥 Export Session", use_container_width=True):
        st.info("Export functionality coming soon!")

# Page 1: Upload Data
if st.session_state.page == "📤 Upload Data":
    st.header("📤 Data Import Hub")
    
    tab1, tab2, tab3 = st.tabs(["📁 Upload JSON", "📝 Raw Text Input", "🔄 Sample Data"])
    
    with tab1:
        st.markdown("### Upload Structured Data")
        st.markdown("Upload candidate profiles in JSON format (output from M5 extraction)")
        
        uploaded_file = st.file_uploader(
            "Drag and drop JSON file here",
            type=['json'],
            help="Expected format: Array of candidate profile objects"
        )
        
        if uploaded_file is not None:
            try:
                data = json.load(uploaded_file)
                st.session_state.profiles = data
                
                # Success animation
                st.success(f"✅ Successfully loaded {len(data)} candidate profiles")
                
                # Display stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Profiles", len(data))
                with col2:
                    avg_skills = np.mean([len(p.get('skills', [])) for p in data]) if data else 0
                    st.metric("Avg Skills/Profile", f"{avg_skills:.1f}")
                with col3:
                    roles = set(p.get('role', '') for p in data)
                    st.metric("Unique Roles", len(roles))
                
                # Preview with expandable sections
                with st.expander("🔍 Preview Profiles (First 5)", expanded=True):
                    df = pd.DataFrame(data[:5])
                    st.dataframe(df, use_container_width=True)
                
                # Skills cloud visualization
                with st.expander("☁️ Skills Distribution", expanded=False):
                    all_skills = []
                    for profile in data:
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
    
    with tab2:
        st.markdown("### Process Raw Text")
        st.markdown("Paste raw candidate profiles for automatic extraction")
        
        raw_text = st.text_area(
            "Enter candidate profiles (one per candidate):",
            height=250,
            placeholder="""Example format:
John Doe
Role: Full Stack Developer
Skills: Python, React, SQL, Docker
Experience: 5 years
Tools: VS Code, Git, JIRA

Jane Smith
Role: UX Designer
Skills: Figma, Adobe XD, User Research
Experience: 3 years
Tools: Sketch, Miro"""
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            extract_btn = st.button("🔧 Extract Profiles", type="primary", use_container_width=True)
        with col2:
            st.caption("This will call M5's JSON extraction module")
        
        if extract_btn:
            if raw_text.strip():
                with st.spinner("🔄 Extracting profiles from text..."):
                    # Placeholder for actual extraction
                    st.session_state.profiles = [
                        {
                            "id": "sample_1",
                            "name": "Sample Candidate",
                            "role": "Developer",
                            "skills": ["Python", "React"],
                            "experience_years": 3,
                            "tools": ["Git", "VS Code"]
                        }
                    ]
                    time.sleep(1)  # Simulate processing
                    
                    st.success("✅ Profiles extracted successfully!")
                    st.balloons()
            else:
                st.warning("⚠️ Please enter some profile text")
    
    with tab3:
        st.markdown("### Load Sample Data")
        st.markdown("Quickly get started with sample candidate profiles")
        
        sample_options = {
            "Small Team (5 candidates)": 5,
            "Medium Team (15 candidates)": 15,
            "Large Team (30 candidates)": 30
        }
        
        selected_sample = st.selectbox("Choose sample size:", list(sample_options.keys()))
        
        if st.button("📥 Load Sample Data", type="primary", use_container_width=True):
            with st.spinner(f"Loading {selected_sample}..."):
                # Generate sample data
                sample_data = []
                roles = ["Frontend Developer", "Backend Developer", "UX Designer", "Data Scientist", "DevOps Engineer"]
                skills_pool = ["Python", "JavaScript", "React", "Node.js", "SQL", "Docker", "AWS", "Figma", "ML", "Agile"]
                
                for i in range(sample_options[selected_sample]):
                    sample_data.append({
                        "id": f"candidate_{i+1}",
                        "name": f"Candidate {chr(65 + i)}",
                        "role": roles[i % len(roles)],
                        "skills": np.random.choice(skills_pool, size=np.random.randint(3, 7), replace=False).tolist(),
                        "experience_years": np.random.randint(1, 10),
                        "tools": np.random.choice(["Git", "VS Code", "JIRA", "Docker", "AWS"], size=3, replace=False).tolist(),
                        "availability_hours": np.random.randint(20, 40)
                    })
                
                st.session_state.profiles = sample_data
                st.success(f"✅ Loaded {len(sample_data)} sample profiles!")
                st.rerun()

# Page 2: Project Setup
elif st.session_state.page == "⚙️ Project Setup":
    st.header("⚙️ Project Configuration")
    
    # Project header with timeline
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Define Your Project Requirements")
        st.caption("Configure the project that needs team formation")
    with col2:
        st.metric("Current Step", "2/6", "Setup")
    
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
• Mobile-responsive design""",
            help="Detailed description helps AI understand project needs better"
        )
        
        st.markdown("#### 🎯 Key Objectives")
        objectives = st.text_area(
            "Primary Goals & Success Metrics",
            height=100,
            placeholder="• Improve user conversion rate by 20%\n• Reduce page load time to under 2 seconds\n• Increase mobile traffic engagement\n• Implement scalable architecture"
        )
    
    with config_col2:
        st.markdown("#### ⚙️ Project Parameters")
        
        team_size = st.slider(
            "Team Size",
            2, 10, 4,
            help="Number of team members needed"
        )
        
        duration = st.selectbox(
            "Project Duration",
            ["2 weeks", "1 month", "2 months", "3 months", "6 months", "6 months+"],
            index=2
        )
        
        urgency = st.select_slider(
            "Urgency Level",
            options=["Low", "Medium", "High", "Critical"],
            value="Medium"
        )
        
        budget_tier = st.selectbox(
            "Budget Tier",
            ["Basic", "Standard", "Premium", "Enterprise"]
        )
    
    st.markdown("---")
    
    # Skills and Roles Configuration
    st.markdown("### 🛠️ Required Expertise")
    
    roles_col, skills_col = st.columns(2)
    
    with roles_col:
        st.markdown("#### 👥 Required Roles")
        required_roles = st.multiselect(
            "Select essential roles",
            ["Frontend Developer", "Backend Developer", "Full Stack Developer", 
             "UX/UI Designer", "Data Scientist", "Machine Learning Engineer",
             "DevOps Engineer", "QA Engineer", "Project Manager", 
             "Product Owner", "Scrum Master", "Business Analyst"],
            default=["Frontend Developer", "Backend Developer", "UX/UI Designer"],
            help="Select roles crucial for project success"
        )
        
        # Role priority
        if required_roles:
            st.markdown("##### 🎯 Role Priority")
            for role in required_roles:
                priority = st.slider(f"Priority for {role}", 1, 5, 3, key=f"priority_{role}")
    
    with skills_col:
        st.markdown("#### 💡 Required Skills")
        required_skills = st.multiselect(
            "Select required skills",
            ["Python", "JavaScript", "TypeScript", "React", "Vue.js", "Angular",
             "Node.js", "Django", "Flask", "FastAPI", "Figma", "Adobe XD",
             "SQL", "NoSQL", "MongoDB", "PostgreSQL", "Docker", "Kubernetes",
             "AWS", "Azure", "GCP", "CI/CD", "Git", "Agile", "Scrum",
             "Machine Learning", "Data Analysis", "TensorFlow", "PyTorch"],
            default=["Python", "React", "SQL", "Docker"],
            help="Technical skills needed for the project"
        )
        
        # Skill level requirements
        if required_skills:
            st.markdown("##### 📊 Minimum Skill Levels")
            for skill in required_skills[:5]:  # Limit to first 5 for UI
                level = st.select_slider(
                    f"{skill} level",
                    options=["Basic", "Intermediate", "Advanced", "Expert"],
                    value="Intermediate",
                    key=f"level_{skill}"
                )
    
    st.markdown("---")
    
    # Advanced Settings
    with st.expander("⚙️ Advanced Settings", expanded=False):
        adv_col1, adv_col2 = st.columns(2)
        
        with adv_col1:
            st.markdown("#### 🎭 Team Dynamics")
            communication_style = st.selectbox(
                "Preferred Communication Style",
                ["Async Preferred", "Sync Required", "Hybrid", "Flexible"]
            )
            
            collaboration_tools = st.multiselect(
                "Required Collaboration Tools",
                ["Slack", "Microsoft Teams", "Zoom", "JIRA", "Trello", "Asana", "Confluence", "Notion"]
            )
        
        with adv_col2:
            st.markdown("#### 📅 Timeline Constraints")
            start_date = st.date_input("Project Start Date")
            milestone_frequency = st.selectbox(
                "Milestone Frequency",
                ["Weekly", "Bi-weekly", "Monthly", "Quarterly"]
            )
            
            timezone_preference = st.selectbox(
                "Timezone Overlap Required",
                ["Flexible", "±2 hours", "±4 hours", "Same timezone"]
            )
    
    st.markdown("---")
    
    # Generate button with confirmation
    generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])
    
    with generate_col2:
        if st.button("🚀 Generate Team Recommendations", type="primary", use_container_width=True):
            if not project_desc:
                st.warning("⚠️ Please enter a project description")
            else:
                # Create project object
                project = {
                    "title": project_title or "Untitled Project",
                    "description": project_desc,
                    "objectives": objectives,
                    "required_roles": required_roles,
                    "required_skills": required_skills,
                    "team_size": team_size,
                    "duration": duration,
                    "urgency": urgency,
                    "budget_tier": budget_tier,
                    "timestamp": datetime.now().isoformat()
                }
                
                st.session_state.project = project
                
                # Show processing animation
                with st.status("🚀 Building optimal teams...", expanded=True) as status:
                    steps = [
                        ("📊 Analyzing candidate profiles", 0.5),
                        ("🎯 Calculating project-candidate fit", 1.0),
                        ("🤖 Running AI optimization algorithms", 1.5),
                        ("👥 Forming balanced teams", 1.0),
                        ("💡 Generating recommendations", 0.5),
                        ("✅ Finalizing results", 0.5)
                    ]
                    
                    progress_bar = st.progress(0)
                    for i, (step_text, step_time) in enumerate(steps):
                        status.write(f"{step_text}...")
                        time.sleep(step_time)
                        progress_bar.progress((i + 1) / len(steps))
                    
                    # Placeholder teams
                    st.session_state.teams = [
                        [
                            {"id": "1", "name": "Alex Chen", "role": "Frontend Lead", "skills": ["React", "TypeScript", "UI/UX"], "fit_score": 0.92},
                            {"id": "2", "name": "Maria Rodriguez", "role": "Backend Architect", "skills": ["Python", "Django", "AWS"], "fit_score": 0.88},
                            {"id": "3", "name": "James Wilson", "role": "UX Designer", "skills": ["Figma", "User Research", "Prototyping"], "fit_score": 0.85},
                            {"id": "4", "name": "Sarah Johnson", "role": "DevOps Engineer", "skills": ["Docker", "Kubernetes", "CI/CD"], "fit_score": 0.90}
                        ],
                        [
                            {"id": "5", "name": "David Kim", "role": "Full Stack", "skills": ["React", "Node.js", "MongoDB"], "fit_score": 0.87},
                            {"id": "6", "name": "Lisa Wang", "role": "Backend Developer", "skills": ["Python", "FastAPI", "PostgreSQL"], "fit_score": 0.89},
                            {"id": "7", "name": "Tom Baker", "role": "Frontend Developer", "skills": ["Vue.js", "JavaScript", "CSS"], "fit_score": 0.84},
                            {"id": "8", "name": "Emma Davis", "role": "UI Designer", "skills": ["Adobe XD", "Prototyping", "Design Systems"], "fit_score": 0.86}
                        ]
                    ]
                    
                    st.session_state.explanations = [
                        "**Team Alpha**: High-performing team with clear role specialization. Excellent for complex projects requiring deep expertise in each domain. Strong leadership structure.",
                        "**Team Beta**: Versatile team with overlapping skills. Ideal for agile projects requiring flexibility and cross-functional collaboration. Good for fast-paced environments."
                    ]
                    
                    status.update(label="✅ Team formation complete!", state="complete")
                    st.balloons()
                
                st.success(f"✨ Generated {len(st.session_state.teams)} team configurations!")
                st.session_state.page = "📋 Results & Export"
                st.rerun()

# Page 3: Candidate Analysis
elif st.session_state.page == "🔍 Candidate Analysis":
    st.header("🔍 Candidate Intelligence Hub")
    
    if not st.session_state.profiles:
        st.warning("📭 No candidate profiles found. Please upload data first.")
        if st.button("📤 Go to Upload Data"):
            st.session_state.page = "📤 Upload Data"
            st.rerun()
        st.stop()
    
    # Metrics dashboard
    st.markdown("### 📊 Candidate Pool Overview")
    
    metrics_cols = st.columns(5)
    with metrics_cols[0]:
        st.metric("Total Candidates", len(st.session_state.profiles))
    with metrics_cols[1]:
        avg_exp = np.mean([p.get('experience_years', 0) for p in st.session_state.profiles])
        st.metric("Avg Experience", f"{avg_exp:.1f} yrs")
    with metrics_cols[2]:
        total_skills = len(set([skill for p in st.session_state.profiles for skill in p.get('skills', [])]))
        st.metric("Unique Skills", total_skills)
    with metrics_cols[3]:
        roles = set(p.get('role', 'Unknown') for p in st.session_state.profiles)
        st.metric("Unique Roles", len(roles))
    with metrics_cols[4]:
        avg_availability = np.mean([p.get('availability_hours', 0) for p in st.session_state.profiles])
        st.metric("Avg Availability", f"{avg_availability:.0f}h/wk")
    
    tab1, tab2, tab3 = st.tabs(["📋 Candidate Directory", "📈 Skills Analysis", "🎯 Compatibility Matrix"])
    
    with tab1:
        st.markdown("#### Browse Candidate Profiles")
        
        # Filters
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            role_filter = st.multiselect(
                "Filter by Role",
                list(roles),
                placeholder="All roles"
            )
        
        with filter_col2:
            min_exp = st.slider("Min Experience (years)", 0, 20, 0)
        
        with filter_col3:
            skill_filter = st.multiselect(
                "Filter by Skill",
                sorted(set([skill for p in st.session_state.profiles for skill in p.get('skills', [])])),
                placeholder="Any skill"
            )
        
        # Filter logic
        filtered_profiles = st.session_state.profiles
        if role_filter:
            filtered_profiles = [p for p in filtered_profiles if p.get('role') in role_filter]
        if min_exp > 0:
            filtered_profiles = [p for p in filtered_profiles if p.get('experience_years', 0) >= min_exp]
        if skill_filter:
            filtered_profiles = [p for p in filtered_profiles 
                               if any(skill in p.get('skills', []) for skill in skill_filter)]
        
        st.markdown(f"**Showing {len(filtered_profiles)} of {len(st.session_state.profiles)} candidates**")
        
        # Display profiles in cards
        for i, profile in enumerate(filtered_profiles[:20]):  # Limit display
            with st.container():
                cols = st.columns([1, 4, 1])
                with cols[0]:
                    # Avatar placeholder
                    st.markdown(f"<div style='font-size: 2rem; text-align: center;'>👤</div>", 
                               unsafe_allow_html=True)
                
                with cols[1]:
                    st.markdown(f"##### {profile.get('name', 'Unknown')}")
                    st.markdown(f"**{profile.get('role', 'No role specified')}** • {profile.get('experience_years', 0)} years experience")
                    
                    # Skills badges
                    skills = profile.get('skills', [])[:8]
                    if skills:
                        badges_html = " ".join([f"<span class='skill-badge'>{skill}</span>" for skill in skills])
                        st.markdown(badges_html, unsafe_allow_html=True)
                    
                    # Tools
                    tools = profile.get('tools', [])
                    if tools:
                        st.caption(f"🛠️ Tools: {', '.join(tools[:5])}")
                
                with cols[2]:
                    availability = profile.get('availability_hours', 0)
                    if availability >= 30:
                        st.metric("Availability", f"{availability}h", "High")
                    elif availability >= 20:
                        st.metric("Availability", f"{availability}h", "Medium")
                    else:
                        st.metric("Availability", f"{availability}h", "Limited")
                
                st.markdown("---")
    
    with tab2:
        st.markdown("#### Skills Distribution & Analysis")
        
        # Extract all skills
        all_skills = []
        for profile in st.session_state.profiles:
            all_skills.extend(profile.get('skills', []))
        
        if all_skills:
            skill_series = pd.Series(all_skills)
            skill_counts = skill_series.value_counts()
            
            # Top skills chart
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig1 = px.bar(
                    x=skill_counts.head(15).values,
                    y=skill_counts.head(15).index,
                    orientation='h',
                    title="Top 15 Most Common Skills",
                    labels={'x': 'Number of Candidates', 'y': 'Skill'},
                    color=skill_counts.head(15).values,
                    color_continuous_scale='Viridis'
                )
                fig1.update_layout(height=500)
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Skill combinations
                st.markdown("##### 🔗 Skill Co-occurrence")
                # Simple co-occurrence example
                common_pairs = [
                    ("Python", "Django"),
                    ("React", "JavaScript"),
                    ("AWS", "Docker"),
                    ("SQL", "Python"),
                    ("Figma", "UI/UX")
                ]
                
                for skill1, skill2 in common_pairs[:5]:
                    count1 = skill_counts.get(skill1, 0)
                    count2 = skill_counts.get(skill2, 0)
                    if count1 and count2:
                        overlap = len([p for p in st.session_state.profiles 
                                     if skill1 in p.get('skills', []) and skill2 in p.get('skills', [])])
                        st.metric(f"{skill1} + {skill2}", overlap, 
                                 f"{overlap/min(count1, count2)*100:.0f}% overlap")
            
            # Role-skill matrix
            st.markdown("##### 🎯 Skills by Role")
            roles_list = list(roles)
            if len(roles_list) > 0:
                role_skill_data = []
                for role in roles_list[:10]:  # Limit to first 10 roles
                    role_profiles = [p for p in st.session_state.profiles if p.get('role') == role]
                    role_skills = [skill for p in role_profiles for skill in p.get('skills', [])]
                    top_skills = pd.Series(role_skills).value_counts().head(5).index.tolist()
                    for skill in top_skills:
                        role_skill_data.append({"Role": role, "Skill": skill, "Count": role_skills.count(skill)})
                
                if role_skill_data:
                    df_role_skill = pd.DataFrame(role_skill_data)
                    fig2 = px.density_heatmap(
                        df_role_skill,
                        x="Role",
                        y="Skill",
                        z="Count",
                        title="Role-Skill Heatmap",
                        color_continuous_scale="Blues"
                    )
                    fig2.update_layout(height=400)
                    st.plotly_chart(fig2, use_container_width=True)
    
    with tab3:
        st.markdown("#### Candidate Compatibility Matrix")
        st.info("👆 This visualization shows similarity between candidates. Hover to see details.")
        
        # Generate sample similarity matrix
        n = min(15, len(st.session_state.profiles))
        sample_profiles = st.session_state.profiles[:n]
        names = [p.get('name', f"Candidate {i}") for i, p in enumerate(sample_profiles)]
        
        # Create synthetic similarity matrix
        np.random.seed(42)
        sim_matrix = np.random.rand(n, n) * 0.4 + 0.3
        np.fill_diagonal(sim_matrix, 1.0)
        sim_matrix = (sim_matrix + sim_matrix.T) / 2  # Make symmetric
        
        fig = go.Figure(data=go.Heatmap(
            z=sim_matrix,
            x=names,
            y=names,
            colorscale='RdBu',
            zmin=0,
            zmax=1,
            hoverongaps=False,
            text=np.round(sim_matrix, 2),
            texttemplate='%{text}',
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title="Candidate Similarity Matrix",
            xaxis_title="Candidates",
            yaxis_title="Candidates",
            height=600,
            xaxis_tickangle=45
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Clusters visualization
        st.markdown("##### 🎨 Candidate Clusters")
        if n >= 5:
            from sklearn.decomposition import PCA
            
            # Dimensionality reduction for visualization
            pca = PCA(n_components=2)
            coords = pca.fit_transform(sim_matrix)
            
            fig_cluster = px.scatter(
                x=coords[:, 0],
                y=coords[:, 1],
                text=names,
                title="Candidate Clusters (PCA Projection)",
                labels={'x': 'PC1', 'y': 'PC2'}
            )
            
            fig_cluster.update_traces(
                textposition='top center',
                marker=dict(size=12, color=np.arange(n), colorscale='Viridis', showscale=True)
            )
            
            fig_cluster.update_layout(height=400)
            st.plotly_chart(fig_cluster, use_container_width=True)

# Page 4: Team Formation
elif st.session_state.page == "👥 Team Formation":
    st.header("👥 Intelligent Team Formation")
    
    if not st.session_state.project:
        st.warning("📋 Please set up a project first")
        if st.button("⚙️ Go to Project Setup"):
            st.session_state.page = "⚙️ Project Setup"
            st.rerun()
        st.stop()
    
    st.markdown(f"### Building teams for: **{st.session_state.project.get('title', 'Untitled Project')}**")
    
    # Algorithm visualization section
    st.markdown("#### 🤖 Team Formation Algorithm")
    
    # Algorithm steps with visualization
    steps = [
        {
            "step": 1,
            "title": "Candidate Filtering",
            "description": "Filter candidates by availability, skills, and role requirements",
            "icon": "🔍"
        },
        {
            "step": 2,
            "title": "Fit Scoring",
            "description": "Calculate project-candidate fit scores using embeddings",
            "icon": "🎯"
        },
        {
            "step": 3,
            "title": "Diversity Analysis",
            "description": "Analyze team diversity across skills, experience, and collaboration styles",
            "icon": "🌈"
        },
        {
            "step": 4,
            "title": "Optimization",
            "description": "Use greedy algorithm to maximize team effectiveness",
            "icon": "⚡"
        },
        {
            "step": 5,
            "title": "Team Assembly",
            "description": "Form balanced teams based on optimization results",
            "icon": "👥"
        }
    ]
    
    # Display steps as timeline
    st.markdown("##### 📋 Algorithm Pipeline")
    for i, step in enumerate(steps):
        cols = st.columns([1, 10])
        with cols[0]:
            st.markdown(f"<div style='font-size: 2rem; text-align: center;'>{step['icon']}</div>", 
                       unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"**Step {step['step']}: {step['title']}**")
            st.caption(step['description'])
            if i < len(steps) - 1:
                st.markdown("↓")
    
    st.markdown("---")
    
    # Algorithm parameters control
    st.markdown("#### ⚙️ Algorithm Parameters")
    
    param_col1, param_col2, param_col3 = st.columns(3)
    
    with param_col1:
        st.markdown("##### 🎯 Fit Weight (α)")
        alpha = st.slider("Project-Skill Fit Importance", 0.0, 1.0, 0.5, 0.1,
                         help="Higher values prioritize candidates with better skill match")
        st.metric("Current Weight", f"{alpha:.2f}")
    
    with param_col2:
        st.markdown("##### 🌈 Diversity Weight (β)")
        beta = st.slider("Team Diversity Importance", 0.0, 1.0, 0.3, 0.1,
                        help="Higher values prioritize diverse skill sets and backgrounds")
        st.metric("Current Weight", f"{beta:.2f}")
    
    with param_col3:
        st.markdown("##### ⚖️ Balance Weight (γ)")
        gamma = st.slider("Team Balance Importance", 0.0, 1.0, 0.2, 0.1,
                         help="Higher values prioritize balanced team composition")
        st.metric("Current Weight", f"{gamma:.2f}")
    
    # Show total
    total_weight = alpha + beta + gamma
    if abs(total_weight - 1.0) > 0.01:
        st.warning(f"Weights sum to {total_weight:.2f} (should be 1.0)")
    
    # Visualize weight distribution
    weights = [alpha, beta, gamma]
    labels = ['Fit', 'Diversity', 'Balance']
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
        height=300
    )
    
    st.plotly_chart(fig_weights, use_container_width=True)
    
    st.markdown("---")
    
    # Team building action
    st.markdown("#### 🚀 Build Teams")
    
    build_col1, build_col2, build_col3 = st.columns([1, 2, 1])
    
    with build_col2:
        if st.button("🏗️ Construct Optimal Teams", type="primary", use_container_width=True):
            if not st.session_state.profiles:
                st.error("❌ No candidate profiles available")
            else:
                with st.spinner("Building teams with optimized parameters..."):
                    # Simulate team building
                    time.sleep(2)
                    
                    # Generate sample teams if none exist
                    if not st.session_state.teams:
                        st.session_state.teams = [
                            [
                                {"id": "1", "name": "Alex Chen", "role": "Frontend Lead", "fit": 0.92, "diversity": 0.85},
                                {"id": "2", "name": "Maria Rodriguez", "role": "Backend Architect", "fit": 0.88, "diversity": 0.78},
                                {"id": "3", "name": "James Wilson", "role": "UX Designer", "fit": 0.85, "diversity": 0.92},
                                {"id": "4", "name": "Sarah Johnson", "role": "DevOps Engineer", "fit": 0.90, "diversity": 0.80}
                            ],
                            [
                                {"id": "5", "name": "David Kim", "role": "Full Stack", "fit": 0.87, "diversity": 0.88},
                                {"id": "6", "name": "Lisa Wang", "role": "Backend Developer", "fit": 0.89, "diversity": 0.82},
                                {"id": "7", "name": "Tom Baker", "role": "Frontend Developer", "fit": 0.84, "diversity": 0.90},
                                {"id": "8", "name": "Emma Davis", "role": "UI Designer", "fit": 0.86, "diversity": 0.85}
                            ]
                        ]
                    
                    st.success(f"✅ Built {len(st.session_state.teams)} teams!")
                    st.balloons()
                    
                    # Show quick results
                    st.markdown("##### 📊 Quick Results")
                    results_cols = st.columns(3)
                    with results_cols[0]:
                        avg_fit = np.mean([member.get('fit', 0) for team in st.session_state.teams 
                                         for member in team])
                        st.metric("Avg Team Fit", f"{avg_fit:.2f}")
                    with results_cols[1]:
                        avg_div = np.mean([member.get('diversity', 0) for team in st.session_state.teams 
                                         for member in team])
                        st.metric("Avg Diversity", f"{avg_div:.2f}")
                    with results_cols[2]:
                        st.metric("Total Members", 
                                 sum(len(team) for team in st.session_state.teams))

# Page 5: Analytics Dashboard
elif st.session_state.page == "📊 Analytics Dashboard":
    st.header("📊 Analytics & Insights Dashboard")
    
    if not st.session_state.project or not st.session_state.teams:
        st.warning("📈 No team data available. Please generate teams first.")
        st.stop()
    
    # Top-level KPIs
    st.markdown("### 📈 Key Performance Indicators")
    
    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.metric("Team Effectiveness", "87%", "+12% vs baseline")
    with kpi_cols[1]:
        st.metric("Skill Coverage", "92%", "+24% vs random")
    with kpi_cols[2]:
        st.metric("Diversity Score", "0.78", "+0.18 vs industry avg")
    with kpi_cols[3]:
        st.metric("Cost Efficiency", "94%", "Optimal")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Team Analysis", "📊 Skill Coverage", "👥 Role Distribution", "📈 Performance Trends"])
    
    with tab1:
        st.markdown("#### Team Composition Analysis")
        
        # Team comparison metrics
        team_metrics = []
        for i, team in enumerate(st.session_state.teams):
            avg_fit = np.mean([m.get('fit', 0.5) for m in team])
            avg_exp = np.mean([m.get('experience_years', 3) for m in team])
            unique_skills = len(set([skill for m in team for skill in m.get('skills', [])]))
            team_metrics.append({
                "Team": f"Team {i+1}",
                "Size": len(team),
                "Avg Fit": avg_fit,
                "Avg Exp (yrs)": avg_exp,
                "Unique Skills": unique_skills,
                "Balance Score": avg_fit * 0.6 + (unique_skills/20) * 0.4
            })
        
        df_team_metrics = pd.DataFrame(team_metrics)
        
        # Display metrics
        st.dataframe(
            df_team_metrics.style.background_gradient(subset=['Avg Fit', 'Balance Score'], cmap='Blues'),
            use_container_width=True
        )
        
        # Visualization
        fig = go.Figure(data=[
            go.Bar(name='Avg Fit', x=df_team_metrics['Team'], y=df_team_metrics['Avg Fit']),
            go.Bar(name='Balance Score', x=df_team_metrics['Team'], y=df_team_metrics['Balance Score']),
            go.Scatter(name='Unique Skills', x=df_team_metrics['Team'], 
                      y=df_team_metrics['Unique Skills']/10, mode='lines+markers', yaxis='y2')
        ])
        
        fig.update_layout(
            title="Team Performance Metrics",
            yaxis=dict(title="Score (0-1)"),
            yaxis2=dict(title="Unique Skills", overlaying='y', side='right'),
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("#### Skill Coverage Analysis")
        
        # Get all required skills from project
        required_skills = st.session_state.project.get('required_skills', [])
        
        if required_skills:
            # Calculate coverage per team
            coverage_data = []
            for i, team in enumerate(st.session_state.teams):
                team_skills = set()
                for member in team:
                    team_skills.update(member.get('skills', []))
                
                coverage = len(set(required_skills) & team_skills) / len(required_skills) * 100
                coverage_data.append({
                    "Team": f"Team {i+1}",
                    "Coverage %": coverage,
                    "Covered Skills": len(set(required_skills) & team_skills),
                    "Missing Skills": len(set(required_skills) - team_skills)
                })
            
            df_coverage = pd.DataFrame(coverage_data)
            
            # Display coverage
            st.dataframe(df_coverage, use_container_width=True)
            
            # Coverage visualization
            fig = px.bar(
                df_coverage,
                x='Team',
                y='Coverage %',
                title="Required Skill Coverage by Team",
                color='Coverage %',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Missing skills analysis
            st.markdown("##### 🔍 Missing Skills Analysis")
            for i, team in enumerate(st.session_state.teams):
                team_skills = set()
                for member in team:
                    team_skills.update(member.get('skills', []))
                
                missing = set(required_skills) - team_skills
                if missing:
                    with st.expander(f"Team {i+1} - Missing Skills ({len(missing)})"):
                        for skill in missing:
                            st.markdown(f"- {skill}")
    
    with tab3:
        st.markdown("#### Role Distribution Analysis")
        
        # Get all roles from teams
        all_roles = []
        for team in st.session_state.teams:
            for member in team:
                all_roles.append(member.get('role', 'Unknown'))
        
        if all_roles:
            role_counts = pd.Series(all_roles).value_counts()
            
            # Pie chart
            fig = px.pie(
                values=role_counts.values,
                names=role_counts.index,
                title="Role Distribution Across All Teams",
                hole=0.3,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Role by team matrix
            st.markdown("##### 👥 Role Distribution by Team")
            role_by_team = []
            for i, team in enumerate(st.session_state.teams):
                team_roles = [m.get('role', 'Unknown') for m in team]
                for role in set(team_roles):
                    role_by_team.append({
                        "Team": f"Team {i+1}",
                        "Role": role,
                        "Count": team_roles.count(role)
                    })
            
            if role_by_team:
                df_role_team = pd.DataFrame(role_by_team)
                fig_heatmap = px.density_heatmap(
                    df_role_team,
                    x="Team",
                    y="Role",
                    z="Count",
                    title="Role Distribution Heatmap",
                    color_continuous_scale="Blues"
                )
                fig_heatmap.update_layout(height=400)
                st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with tab4:
        st.markdown("#### Historical Performance Trends")
        st.info("📈 Historical data will appear here after multiple team formations")
        
        # Sample trend data
        dates = pd.date_range(start='2024-01-01', periods=12, freq='M')
        trend_data = {
            'Date': dates,
            'Team Effectiveness': np.random.uniform(0.7, 0.95, 12),
            'Diversity Score': np.random.uniform(0.6, 0.85, 12),
            'Skill Coverage': np.random.uniform(0.75, 0.98, 12)
        }
        
        df_trend = pd.DataFrame(trend_data)
        
        fig = px.line(
            df_trend,
            x='Date',
            y=['Team Effectiveness', 'Diversity Score', 'Skill Coverage'],
            title="Performance Trends Over Time",
            markers=True
        )
        
        fig.update_layout(
            height=500,
            yaxis_title="Score",
            xaxis_title="Date"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics
        st.markdown("##### 📊 Summary Statistics")
        summary_cols = st.columns(3)
        with summary_cols[0]:
            st.metric("Avg Effectiveness", f"{df_trend['Team Effectiveness'].mean():.2%}")
        with summary_cols[1]:
            st.metric("Avg Diversity", f"{df_trend['Diversity Score'].mean():.2%}")
        with summary_cols[2]:
            st.metric("Avg Coverage", f"{df_trend['Skill Coverage'].mean():.2%}")

# Page 6: Results & Export
elif st.session_state.page == "📋 Results & Export":
    st.header("📋 Team Recommendations & Export")
    
    if not st.session_state.teams:
        st.warning("👥 No teams generated yet. Please generate teams first.")
        if st.button("👥 Go to Team Formation"):
            st.session_state.page = "👥 Team Formation"
            st.rerun()
        st.stop()
    
    st.markdown(f"### Project: **{st.session_state.project.get('title', 'Untitled Project')}**")
    st.markdown(f"*{st.session_state.project.get('description', '')[:200]}...*")
    
    # Team selection with visual indicators
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
            avg_div = np.mean([m.get('diversity', 0.5) for m in team])
            st.metric("Diversity", f"{avg_div:.2f}")
        with metrics_cols[2]:
            unique_skills = len(set([skill for m in team for skill in m.get('skills', [])]))
            st.metric("Unique Skills", unique_skills)
        with metrics_cols[3]:
            avg_exp = np.mean([m.get('experience_years', 3) for m in team])
            st.metric("Avg Experience", f"{avg_exp:.1f} yrs")
        
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
        
        action_cols = st.columns(5)
        
        with action_cols[0]:
            if st.button("✅ Select This Team", type="primary", use_container_width=True):
                st.success(f"✅ Team {team_idx + 1} selected! 🎉")
                st.balloons()
        
        with action_cols[1]:
            if st.button("🔄 Regenerate", use_container_width=True):
                st.info("🔄 Regenerating team configuration...")
                time.sleep(1)
                st.rerun()
        
        with action_cols[2]:
            if st.button("📊 Compare", use_container_width=True):
                st.session_state.page = "📊 Analytics Dashboard"
                st.rerun()
        
        with action_cols[3]:
            # Export as JSON
            json_data = {
                "team_id": team_idx + 1,
                "project": st.session_state.project.get('title'),
                "members": team,
                "metrics": {
                    "avg_fit": avg_fit,
                    "avg_diversity": avg_div,
                    "unique_skills": unique_skills,
                    "avg_experience": avg_exp
                },
                "generated_at": datetime.now().isoformat()
            }
            
            st.download_button(
                label="📥 JSON",
                data=json.dumps(json_data, indent=2),
                file_name=f"team_{team_idx + 1}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with action_cols[4]:
            # Export as CSV
            csv_data = []
            for member in team:
                csv_data.append({
                    "name": member.get('name'),
                    "role": member.get('role'),
                    "skills": ", ".join(member.get('skills', [])),
                    "fit_score": member.get('fit', 0.5),
                    "experience_years": member.get('experience_years', 0)
                })
            
            df_csv = pd.DataFrame(csv_data)
            csv_string = df_csv.to_csv(index=False)
            
            st.download_button(
                label="📊 CSV",
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
                        expanded=(i == 0)):
            
            # Quick stats
            stats_cols = st.columns(4)
            with stats_cols[0]:
                st.metric("Fit", f"{np.mean([m.get('fit', 0.5) for m in team]):.2f}")
            with stats_cols[1]:
                st.metric("Diversity", f"{np.mean([m.get('diversity', 0.5) for m in team]):.2f}")
            with stats_cols[2]:
                unique_skills = len(set([skill for m in team for skill in m.get('skills', [])]))
                st.metric("Unique Skills", unique_skills)
            with stats_cols[3]:
                st.metric("Avg Exp", f"{np.mean([m.get('experience_years', 3) for m in team]):.1f}y")
            
            # Members grid
            member_cols = st.columns(min(4, len(team)))
            for idx, member in enumerate(team):
                col_idx = idx % 4
                with member_cols[col_idx]:
                    # Mini card
                    st.markdown(f"""
                    <div style='
                        padding: 12px;
                        border-radius: 10px;
                        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                        border: 1px solid #e2e8f0;
                        margin-bottom: 10px;
                    '>
                        <div style='font-weight: bold; font-size: 1.1rem;'>{member.get('name', 'Member')}</div>
                        <div style='color: #64748b; font-size: 0.9rem;'>{member.get('role', 'Role')}</div>
                        <div style='margin-top: 8px;'>
                            <span style='
                                display: inline-block;
                                padding: 2px 8px;
                                background: #3B82F6;
                                color: white;
                                border-radius: 12px;
                                font-size: 0.8rem;
                                margin-top: 4px;
                            '>Fit: {member.get('fit', 0.5):.2f}</span>
                        </div>
                        <div style='margin-top: 8px; font-size: 0.85rem; color: #475569;'>
                            {', '.join(member.get('skills', [])[:3])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

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
        v2.0 Professional Edition • Last updated: """ + datetime.now().strftime("%Y-%m-%d") + """
    </div>
</div>
""", unsafe_allow_html=True)

# Add some JavaScript for smooth scrolling
st.markdown("""
<script>
// Smooth scrolling for anchor links
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});
</script>
""", unsafe_allow_html=True)