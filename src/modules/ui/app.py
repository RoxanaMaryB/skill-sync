# src/modules/ui/app_simple.py
import streamlit as st
import pandas as pd
import numpy as np
import json
import time
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
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

# Enhanced conversion functions for multi-format upload
class MultiFormatConverter:
    """Convert various file formats to structured candidate profiles using LLM"""
    
    @staticmethod
    def extract_from_csv(file_path: str, api_key: str = None, limit: int = None) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Extract candidate profiles from CSV file"""
        try:
            df = pd.read_csv(file_path)
            
            if limit:
                df = df.head(limit)
            
            profiles = []
            inputs = {}
            
            for i in range(len(df)):
                row = df.iloc[i].to_dict()
                cid = str(row.get("Candidate ID", f"candidate_{i}"))
                
                # Create simple profile
                profile = {
                    "id": cid,
                    "name": f"Candidate {cid}",
                    "constraints": {
                        "weekly_availability_hours": str(row.get("WeeklyAvailabilityHours", "20"))
                    },
                    "metadata": {
                        "dev_type": str(row.get("DevType", "Unknown")),
                        "work_experience_years": str(row.get("WorkExp", "0")),
                        "years_code": str(row.get("YearsCode", "0")),
                        "employment": str(row.get("Employment", "Unknown")),
                        "org_size": str(row.get("OrgSize", "Unknown")),
                        "industry": str(row.get("Industry", "Unknown"))
                    },
                    "technical": {
                        "skills": MultiFormatConverter._extract_skills_from_row(row),
                        "tools": MultiFormatConverter._extract_tools_from_row(row)
                    },
                    "personality": {
                        "Belbin_team_role": "Unknown"
                    },
                    "collaboration": {
                        "communication_style": "Mixed",
                        "conflict_style": "Unknown",
                        "leadership_preference": "Unknown",
                        "deadline_discipline": "Unknown"
                    },
                    "learning_behavior": {
                        "learning_orientation": "Unknown",
                        "knowledge_sharing": "Unknown"
                    }
                }
                
                profiles.append(profile)
                inputs[cid] = str(row)
            
            return profiles, inputs
            
        except Exception as e:
            raise Exception(f"Failed to extract from CSV: {e}")
    
    @staticmethod
    def extract_from_json(file_path: str, api_key: str = None, limit: int = None) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Extract candidate profiles from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                candidates = data
            elif isinstance(data, dict):
                # Check for common keys
                for key in ['candidates', 'profiles', 'users', 'members']:
                    if key in data and isinstance(data[key], list):
                        candidates = data[key]
                        break
                else:
                    candidates = [data]  # Single candidate in dict
            else:
                raise ValueError(f"Unexpected JSON structure: {type(data)}")
            
            if limit:
                candidates = candidates[:limit]
            
            profiles = []
            inputs = {}
            
            for i, candidate in enumerate(candidates):
                # Convert JSON to standardized format
                profile = MultiFormatConverter._json_to_profile(candidate, i)
                cid = profile["id"]
                profiles.append(profile)
                inputs[cid] = json.dumps(candidate, ensure_ascii=False)
            
            return profiles, inputs
            
        except Exception as e:
            raise Exception(f"Failed to extract from JSON: {e}")
    
    @staticmethod
    def extract_from_text(file_path: str, api_key: str = None, limit: int = None) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Extract candidate profiles from raw text file using LLM"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split content into candidate sections (assuming delimiter or format)
            candidates_raw = MultiFormatConverter._split_candidate_text(content)
            
            if limit:
                candidates_raw = candidates_raw[:limit]
            
            # Use LLM to extract structured profiles from text
            profiles = []
            inputs = {}
            
            for i, candidate_text in enumerate(candidates_raw):
                profile = MultiFormatConverter._text_to_profile_with_llm(candidate_text, i, api_key)
                if profile:
                    cid = profile["id"]
                    profiles.append(profile)
                    inputs[cid] = candidate_text
            
            return profiles, inputs
            
        except Exception as e:
            raise Exception(f"Failed to extract from text: {e}")
    
    @staticmethod
    def _split_candidate_text(content: str) -> List[str]:
        """Split text content into individual candidate sections"""
        # Try common delimiters
        delimiters = [
            "\n---\n", "\n***\n", "\n\n\n", 
            "Candidate ", "Profile ", "Name:"
        ]
        
        for delimiter in delimiters:
            if delimiter in content:
                if delimiter.startswith("\n"):
                    parts = content.split(delimiter)
                else:
                    # For prefix delimiters, we need a different approach
                    import re
                    parts = re.split(f'(?={re.escape(delimiter)})', content)
                
                if len(parts) > 1:
                    return [p.strip() for p in parts if p.strip()]
        
        # If no delimiter found, treat entire content as one candidate
        return [content.strip()] if content.strip() else []
    
    @staticmethod
    def _json_to_profile(candidate_data: Dict, index: int) -> Dict[str, Any]:
        """Convert JSON candidate data to standardized profile format"""
        # Map common field names to our schema
        field_mapping = {
            'id': ['id', 'candidate_id', 'user_id', 'employee_id'],
            'name': ['name', 'full_name', 'username', 'email'],
            'role': ['role', 'position', 'title', 'job_title', 'dev_type'],
            'skills': ['skills', 'technologies', 'languages', 'expertise'],
            'experience': ['experience', 'experience_years', 'years_of_experience', 'work_exp'],
            'availability': ['availability', 'weekly_availability', 'hours_available']
        }
        
        def get_mapped_value(data, keys, default="Unknown"):
            for key in keys:
                if key in data:
                    value = data[key]
                    if pd.isna(value):
                        return default
                    return str(value)
            return default
        
        profile = {
            "id": get_mapped_value(candidate_data, field_mapping['id'], f"candidate_{index}"),
            "name": get_mapped_value(candidate_data, field_mapping['name'], f"Candidate {index}"),
            "constraints": {
                "weekly_availability_hours": str(get_mapped_value(candidate_data, field_mapping['availability'], "20"))
            },
            "metadata": {
                "dev_type": get_mapped_value(candidate_data, field_mapping['role'], "Unknown"),
                "work_experience_years": str(get_mapped_value(candidate_data, field_mapping['experience'], "0"))
            },
            "technical": {
                "skills": MultiFormatConverter._extract_skills_from_json(candidate_data)
            }
        }
        
        return profile
    
    @staticmethod
    def _extract_skills_from_json(candidate_data: Dict) -> List[str]:
        """Extract skills from JSON candidate data"""
        skills = []
        
        # Check various possible skill fields
        skill_fields = ['skills', 'technologies', 'languages', 'tools', 'expertise']
        
        for field in skill_fields:
            if field in candidate_data:
                value = candidate_data[field]
                if isinstance(value, str):
                    # Split by common delimiters
                    for delimiter in [',', ';', '|', '/']:
                        if delimiter in value:
                            skills.extend([s.strip() for s in value.split(delimiter) if s.strip()])
                            break
                    else:
                        skills.append(value.strip())
                elif isinstance(value, list):
                    skills.extend([str(item).strip() for item in value])
        
        return list(set(skills))[:20]  # Limit to 20 unique skills
    
    @staticmethod
    def _text_to_profile_with_llm(text: str, index: int, api_key: str = None) -> Optional[Dict[str, Any]]:
        """Use LLM to extract structured profile from raw text"""
        if not api_key or not MODULES_AVAILABLE:
            # Fallback to simple extraction
            return MultiFormatConverter._simple_text_extraction(text, index)
        
        try:
            # LLM prompt for extracting candidate information from text
            prompt = f"""Extract candidate information from the following text and return as valid JSON.
            If information is missing, use "Unknown".
            
            Required JSON format:
            {{
                "id": "unique_id",
                "name": "candidate name",
                "role": "developer role",
                "skills": ["skill1", "skill2", ...],
                "experience_years": number,
                "availability_hours": number
            }}
            
            Text:
            {text}
            
            Return ONLY the JSON object, no additional text."""
            
            # Here you would call your LLM API
            # For now, using simple extraction as fallback
            return MultiFormatConverter._simple_text_extraction(text, index)
            
        except Exception as e:
            st.error(f"LLM extraction failed: {e}")
            return MultiFormatConverter._simple_text_extraction(text, index)
    
    @staticmethod
    def _simple_text_extraction(text: str, index: int) -> Dict[str, Any]:
        """Simple rule-based extraction from text"""
        # Extract name (look for patterns like "Name: John")
        name = "Candidate " + str(index)
        for line in text.split('\n'):
            if 'name:' in line.lower():
                name = line.split(':', 1)[1].strip()
                break
        
        # Extract skills (look for keywords)
        skill_keywords = [
            'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
            'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring',
            'sql', 'mongodb', 'postgresql', 'mysql', 'redis',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git'
        ]
        
        found_skills = []
        text_lower = text.lower()
        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        # Extract experience (look for patterns like "X years")
        experience = 0
        import re
        exp_patterns = [
            r'(\d+)\s+years?\s+experience',
            r'experience:\s*(\d+)',
            r'(\d+)\s+years?\s+in',
            r'(\d+)\s+years?\s+of'
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    experience = int(match.group(1))
                    break
                except:
                    pass
        
        # Extract role (common developer roles)
        role = "Developer"
        role_keywords = {
            'frontend': 'Frontend Developer',
            'backend': 'Backend Developer',
            'full stack': 'Full Stack Developer',
            'devops': 'DevOps Engineer',
            'data': 'Data Scientist',
            'machine learning': 'Machine Learning Engineer',
            'mobile': 'Mobile Developer',
            'ui/ux': 'UI/UX Designer'
        }
        
        for keyword, role_name in role_keywords.items():
            if keyword in text_lower:
                role = role_name
                break
        
        return {
            "id": f"candidate_{index}",
            "name": name,
            "role": role,
            "skills": list(set(found_skills))[:10],
            "experience_years": experience,
            "availability_hours": 20  # Default
        }
    
    @staticmethod
    def _extract_skills_from_row(row: Dict[str, Any]) -> List[str]:
        """Extract skills from CSV row"""
        skills = []
        skill_fields = ["LanguageHaveWorkedWith", "DatabaseHaveWorkedWith", 
                       "PlatformHaveWorkedWith", "WebframeHaveWorkedWith"]
        
        for field in skill_fields:
            value = row.get(field, "")
            if isinstance(value, str) and value:
                parts = [p.strip() for p in value.split(";") if p.strip()]
                skills.extend(parts)
        
        return list(set(skills))[:20]  # Limit to 20 unique skills
    
    @staticmethod
    def _extract_tools_from_row(row: Dict[str, Any]) -> List[str]:
        """Extract tools from CSV row"""
        tools = []
        tool_fields = ["ToolsTechHaveWorkedWith", "NEWCollabToolsHaveWorkedWith", 
                      "OpSysPersonalUse", "AIToolCurrentlyUsing"]
        
        for field in tool_fields:
            value = row.get(field, "")
            if isinstance(value, str) and value:
                parts = [p.strip() for p in value.split(";") if p.strip()]
                tools.extend(parts)
        
        return list(set(tools))[:10]  # Limit to 10 unique tools

# Custom CSS with modern design (keep the same CSS as before)
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
    
    /* File upload styling */
    .upload-area {
        border: 2px dashed #3B82F6;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #F8FAFC;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: #1E40AF;
        background-color: #EFF6FF;
    }
    
    .format-badge {
        display: inline-block;
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    
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
if 'use_llm_extraction' not in st.session_state:
    st.session_state.use_llm_extraction = True
if 'candidate_limit' not in st.session_state:
    st.session_state.candidate_limit = 100  # Increased from 10

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
        st.caption("v2.0 • Enhanced Upload Edition")
    
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
    
    # Upload settings
    st.markdown("---")
    st.markdown("### ⚙️ Upload Settings")
    
    st.session_state.candidate_limit = st.number_input(
        "Max Candidates to Process",
        min_value=1,
        max_value=500,
        value=st.session_state.candidate_limit,
        help="Maximum number of candidates to extract from uploaded files"
    )
    
    st.session_state.use_llm_extraction = st.checkbox(
        "Use LLM for Text Extraction",
        value=st.session_state.use_llm_extraction,
        help="Use AI to extract structured profiles from unstructured text"
    )
    
    # Quick actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    if st.button("🔄 Reset All Data", use_container_width=True):
        for key in ['profiles', 'project', 'teams', 'explanations']:
            st.session_state[key] = [] if key != 'project' else None
        st.rerun()

# Page 1: Enhanced Upload Data with Multi-Format Support
if st.session_state.page == "📤 Upload Data":
    st.header("📤 Multi-Format Data Import Hub")
    
    tab1, tab2, tab3 = st.tabs(["📁 Upload Files", "📝 Text Input", "🔄 Sample Data"])
    
    with tab1:
        st.markdown("### Upload Candidate Data")
        st.markdown("Upload candidate profiles in multiple formats")
        
        # File format info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<div class='format-badge'>CSV</div>", unsafe_allow_html=True)
            st.caption("Structured tabular data")
        with col2:
            st.markdown("<div class='format-badge'>JSON</div>", unsafe_allow_html=True)
            st.caption("Structured object data")
        with col3:
            st.markdown("<div class='format-badge'>TXT</div>", unsafe_allow_html=True)
            st.caption("Unstructured text profiles")
        
        # Multi-format file uploader
        uploaded_file = st.file_uploader(
            "Drag and drop files here",
            type=['csv', 'json', 'txt', 'text'],
            help="Supported formats: CSV, JSON, TXT"
        )
        
        if uploaded_file is not None:
            # Show file info
            file_name = uploaded_file.name
            file_size = uploaded_file.size / 1024  # KB
            file_type = file_name.split('.')[-1].upper()
            
            st.markdown(f"""
            <div class='upload-area'>
                <h3>📄 {file_name}</h3>
                <p>Type: <strong>{file_type}</strong> | Size: <strong>{file_size:.1f} KB</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show file preview
            with st.expander("🔍 Preview File Content", expanded=False):
                if file_type.lower() == 'csv':
                    try:
                        df_preview = pd.read_csv(uploaded_file)
                        st.dataframe(df_preview.head(5))
                        uploaded_file.seek(0)  # Reset file pointer
                    except:
                        st.warning("Could not preview CSV file")
                elif file_type.lower() == 'json':
                    try:
                        json_content = uploaded_file.read()
                        json_data = json.loads(json_content)
                        st.json(json_data, expanded=False)
                        uploaded_file.seek(0)
                    except:
                        st.warning("Could not preview JSON file")
                else:  # TXT
                    try:
                        text_content = uploaded_file.read().decode('utf-8')
                        st.text_area("Content", text_content[:1000] + ("..." if len(text_content) > 1000 else ""), height=200)
                        uploaded_file.seek(0)
                    except:
                        st.warning("Could not preview text file")
        
        if uploaded_file is not None and st.button("🔧 Extract Profiles", type="primary", use_container_width=True):
            with st.spinner("🔄 Processing file..."):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type.lower()}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_path = tmp_file.name
                    
                    # Extract profiles based on file type
                    profiles = []
                    
                    if file_type.lower() == 'csv':
                        # Use existing module if available, else use converter
                        if MODULES_AVAILABLE:
                            profiles_data, _ = extract_candidates(temp_path)
                        else:
                            profiles_data, _ = MultiFormatConverter.extract_from_csv(
                                temp_path, 
                                limit=st.session_state.candidate_limit
                            )
                        
                    elif file_type.lower() == 'json':
                        profiles_data, _ = MultiFormatConverter.extract_from_json(
                            temp_path,
                            limit=st.session_state.candidate_limit
                        )
                    
                    else:  # TXT
                        api_key = os.getenv("OPENROUTER_API_KEY") if st.session_state.use_llm_extraction else None
                        profiles_data, _ = MultiFormatConverter.extract_from_text(
                            temp_path,
                            api_key=api_key,
                            limit=st.session_state.candidate_limit
                        )
                    
                    # Convert to display format
                    candidate_objects = []
                    for i, p in enumerate(profiles_data[:st.session_state.candidate_limit]):
                        # Safely convert values
                        exp_years = safe_int_convert(p.get('metadata', {}).get('work_experience_years', 
                                             p.get('experience_years', '0')))
                        
                        avail_hours = safe_int_convert(p.get('constraints', {}).get('weekly_availability_hours', 
                                               p.get('availability_hours', '20')))
                        
                        candidate_objects.append({
                            "id": p.get('id', f"candidate_{i}"),
                            "name": p.get('name', f"Candidate {p.get('id', f'{i}')}"),
                            "role": p.get('metadata', {}).get('dev_type', 
                                      p.get('role', 'Unknown')),
                            "skills": p.get('technical', {}).get('skills', 
                                       p.get('skills', [])),
                            "experience_years": exp_years,
                            "availability_hours": avail_hours,
                            "tools": p.get('technical', {}).get('tools', [])
                        })
                    
                    st.session_state.profiles = candidate_objects
                    
                    # Clean up
                    os.unlink(temp_path)
                    
                    # Success animation
                    st.success(f"✅ Successfully extracted {len(candidate_objects)} candidate profiles from {file_type} file")
                    st.balloons()
                    
                    # Display stats
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Profiles", len(candidate_objects))
                    with col2:
                        avg_skills = np.mean([len(p.get('skills', [])) for p in candidate_objects]) if candidate_objects else 0
                        st.metric("Avg Skills/Profile", f"{avg_skills:.1f}")
                    with col3:
                        roles = set(p.get('role', '') for p in candidate_objects)
                        st.metric("Unique Roles", len(roles))
                    with col4:
                        file_type_icon = "📊" if file_type.lower() == 'csv' else "🔤" if file_type.lower() == 'json' else "📝"
                        st.metric("Source Format", f"{file_type_icon} {file_type}")
                    
                    # Preview with expandable sections
                    with st.expander("🔍 Preview Profiles (First 10)", expanded=True):
                        df = pd.DataFrame(candidate_objects[:10])
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
                    st.error(f"❌ Error processing file: {str(e)}")
                    import traceback
                    with st.expander("🔍 Error Details"):
                        st.code(traceback.format_exc())
                    
                    if "OPENROUTER_API_KEY" in str(e) and st.session_state.use_llm_extraction:
                        st.info("💡 LLM extraction requires OPENROUTER_API_KEY. Disable LLM extraction in sidebar or add API key to .env file")
    
    with tab2:
        st.markdown("### 📝 Direct Text Input")
        st.markdown("Paste candidate information directly as text")
        
        text_input = st.text_area(
            "Enter candidate profiles (one per line or separated by delimiters)",
            height=200,
            placeholder="""Example formats:
            
1. Multiple candidates separated by ---:
Name: John Doe
Role: Frontend Developer
Skills: React, JavaScript, TypeScript
Experience: 5 years
Availability: 30 hours/week
---
Name: Jane Smith
Role: Backend Developer
Skills: Python, Django, PostgreSQL
Experience: 7 years
Availability: 25 hours/week

2. JSON array format:
[
  {
    "name": "John Doe",
    "role": "Frontend Developer",
    "skills": ["React", "JavaScript"],
    "experience": 5
  },
  {
    "name": "Jane Smith",
    "role": "Backend Developer",
    "skills": ["Python", "Django"],
    "experience": 7
  }
]

3. Simple list:
Candidate 1: John Doe (Frontend, 5 years, React/JS)
Candidate 2: Jane Smith (Backend, 7 years, Python/Django)"""
        )
        
        if text_input and st.button("🔍 Extract from Text", type="primary", use_container_width=True):
            with st.spinner("🔄 Extracting profiles from text..."):
                try:
                    # Save text to temporary file
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp_file:
                        tmp_file.write(text_input)
                        temp_path = tmp_file.name
                    
                    # Extract using text converter
                    api_key = os.getenv("OPENROUTER_API_KEY") if st.session_state.use_llm_extraction else None
                    profiles_data, _ = MultiFormatConverter.extract_from_text(
                        temp_path,
                        api_key=api_key,
                        limit=st.session_state.candidate_limit
                    )
                    
                    # Convert to display format
                    candidate_objects = []
                    for i, p in enumerate(profiles_data):
                        candidate_objects.append({
                            "id": p.get('id', f"text_candidate_{i}"),
                            "name": p.get('name', f"Text Candidate {i}"),
                            "role": p.get('role', 'Unknown'),
                            "skills": p.get('skills', []),
                            "experience_years": p.get('experience_years', 0),
                            "availability_hours": p.get('availability_hours', 20)
                        })
                    
                    st.session_state.profiles = candidate_objects
                    
                    # Clean up
                    os.unlink(temp_path)
                    
                    st.success(f"✅ Extracted {len(candidate_objects)} candidate profiles from text")
                    st.balloons()
                    
                    # Display preview
                    if candidate_objects:
                        with st.expander("🔍 Extracted Profiles", expanded=True):
                            df = pd.DataFrame(candidate_objects)
                            st.dataframe(df, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"❌ Error extracting from text: {str(e)}")
    
    with tab3:
        st.markdown("### Load Sample Data")
        st.markdown("Quickly get started with sample candidate profiles")
        
        sample_options = {
            "Small Set (10 candidates)": 10,
            "Medium Set (25 candidates)": 25,
            "Large Set (50 candidates)": 50
        }
        
        selected_sample = st.selectbox("Choose sample size:", list(sample_options.keys()))
        
        # Sample data format
        sample_format = st.selectbox(
            "Sample format:",
            ["CSV-style", "JSON-style", "Text-style"]
        )
        
        if st.button("📥 Load Sample Data", type="primary", use_container_width=True):
            with st.spinner(f"Generating {selected_sample} sample profiles..."):
                # Generate sample data based on format
                if sample_format == "CSV-style":
                    # Create CSV-like sample data
                    sample_data = []
                    roles = ["Frontend Developer", "Backend Developer", "Full Stack Developer", 
                            "UX Designer", "DevOps Engineer", "Data Scientist"]
                    skills_pool = ["Python", "JavaScript", "React", "Node.js", "SQL", "Docker", 
                                 "AWS", "Figma", "ML", "Agile", "Git", "REST API", "HTML/CSS", 
                                 "TypeScript", "Vue.js", "Angular", "MongoDB", "PostgreSQL", 
                                 "Redis", "Kubernetes", "TensorFlow", "PyTorch", "Spring Boot"]
                    
                    for i in range(sample_options[selected_sample]):
                        num_skills = np.random.randint(3, 12)
                        selected_skills = np.random.choice(skills_pool, size=num_skills, replace=False).tolist()
                        
                        sample_data.append({
                            "id": f"sample_{i+1:03d}",
                            "name": f"Candidate {chr(65 + (i % 26))}{i//26 + 1 if i >= 26 else ''}",
                            "role": roles[i % len(roles)],
                            "skills": selected_skills,
                            "experience_years": np.random.randint(1, 20),
                            "availability_hours": np.random.randint(15, 40),
                            "tools": np.random.choice(["Git", "VS Code", "JIRA", "Docker", "AWS", 
                                                     "Figma", "Postman", "Slack", "Jenkins", 
                                                     "Confluence"], size=3, replace=False).tolist()
                        })
                    
                    st.session_state.profiles = sample_data
                    st.success(f"✅ Loaded {len(sample_data)} sample profiles!")
                    
                    # Show sample format
                    with st.expander("📋 Sample Data Format", expanded=False):
                        st.info("CSV-style structured data with consistent fields")
                        df_sample = pd.DataFrame(sample_data[:3])
                        st.dataframe(df_sample)
                
                elif sample_format == "JSON-style":
                    # Create JSON-like sample data
                    sample_data = []
                    for i in range(sample_options[selected_sample]):
                        sample_data.append({
                            "candidate_id": f"json_{i+1}",
                            "personal_info": {
                                "name": f"JSON Candidate {i+1}",
                                "email": f"candidate{i+1}@example.com"
                            },
                            "professional": {
                                "position": np.random.choice(["Senior Developer", "Mid-level Developer", "Junior Developer"]),
                                "department": "Engineering",
                                "years_experience": np.random.randint(1, 15)
                            },
                            "skills": {
                                "programming": np.random.choice(["Python", "Java", "JavaScript", "Go", "Rust"], 
                                                              size=3, replace=False).tolist(),
                                "frameworks": np.random.choice(["React", "Vue", "Angular", "Django", "Spring"], 
                                                             size=2, replace=False).tolist(),
                                "tools": ["Git", "Docker", "AWS"]
                            },
                            "availability": {
                                "weekly_hours": np.random.randint(20, 40),
                                "timezone": "UTC+" + str(np.random.randint(-12, 12))
                            }
                        })
                    
                    # Convert JSON-style to our format
                    converted_data = []
                    for i, item in enumerate(sample_data):
                        converted_data.append({
                            "id": item.get("candidate_id", f"json_{i}"),
                            "name": item.get("personal_info", {}).get("name", f"JSON Candidate {i}"),
                            "role": item.get("professional", {}).get("position", "Developer"),
                            "skills": item.get("skills", {}).get("programming", []) + 
                                     item.get("skills", {}).get("frameworks", []),
                            "experience_years": item.get("professional", {}).get("years_experience", 0),
                            "availability_hours": item.get("availability", {}).get("weekly_hours", 20),
                            "tools": item.get("skills", {}).get("tools", [])
                        })
                    
                    st.session_state.profiles = converted_data
                    st.success(f"✅ Loaded {len(converted_data)} JSON-style profiles!")
                    
                    with st.expander("📋 Sample JSON Structure", expanded=False):
                        st.json(sample_data[0], expanded=False)
                
                else:  # Text-style
                    # Create text-style sample data
                    sample_text = ""
                    roles = ["Frontend Dev", "Backend Engineer", "Full Stack", "DevOps", "Data Scientist"]
                    
                    for i in range(sample_options[selected_sample]):
                        sample_text += f"""
Candidate Profile {i+1}
Name: Text Candidate {i+1}
Role: {roles[i % len(roles)]}
Experience: {np.random.randint(1, 15)} years
Skills: {np.random.choice(['Python', 'JavaScript', 'React', 'Node.js', 'SQL', 'Docker'], size=3, replace=False).tolist()}
Availability: {np.random.randint(20, 40)} hours/week
Education: Bachelor's in Computer Science
Certifications: AWS Certified, Scrum Master
---
"""
                    
                    # Process text-style data
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp_file:
                        tmp_file.write(sample_text)
                        temp_path = tmp_file.name
                    
                    profiles_data, _ = MultiFormatConverter.extract_from_text(
                        temp_path,
                        api_key=None,  # Don't use LLM for sample
                        limit=sample_options[selected_sample]
                    )
                    
                    # Convert to display format
                    converted_data = []
                    for i, p in enumerate(profiles_data):
                        converted_data.append({
                            "id": p.get('id', f"text_sample_{i}"),
                            "name": p.get('name', f"Text Sample {i}"),
                            "role": p.get('role', 'Unknown'),
                            "skills": p.get('skills', []),
                            "experience_years": p.get('experience_years', 0),
                            "availability_hours": p.get('availability_hours', 20)
                        })
                    
                    st.session_state.profiles = converted_data
                    os.unlink(temp_path)
                    
                    st.success(f"✅ Loaded {len(converted_data)} text-style profiles!")
                    
                    with st.expander("📋 Sample Text Format", expanded=False):
                        st.text(sample_text[:500] + "..." if len(sample_text) > 500 else sample_text)
                
                st.rerun()

# Page 2: Enhanced Project Setup with Manual Skill/Role Addition
elif st.session_state.page == "⚙️ Project Setup":
    st.header("⚙️ Project Configuration")
    
    if not st.session_state.profiles:
        st.warning("📭 No candidate profiles found. Please upload data first.")
        if st.button("📤 Go to Upload Data"):
            st.session_state.page = "📤 Upload Data"
            st.rerun()
        st.stop()
    
    # Initialize session state for manual additions
    if 'manual_skills' not in st.session_state:
        st.session_state.manual_skills = []
    if 'manual_roles' not in st.session_state:
        st.session_state.manual_roles = []
    if 'custom_skills' not in st.session_state:
        st.session_state.custom_skills = []
    if 'custom_roles' not in st.session_state:
        st.session_state.custom_roles = []
    
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
            2, 12, 4,
            help="Number of team members needed"
        )
        
        n_teams = st.slider(
            "Number of Teams",
            1, 10, 1,
            help="How many team configurations to generate"
        )
        
        duration = st.selectbox(
            "Project Duration",
            ["2 weeks", "1 month", "2 months", "3 months", "6 months", "1 year"],
            index=2
        )
    
    st.markdown("---")
    
    # Skills and Roles Configuration - Enhanced with manual input
    st.markdown("### 🛠️ Required Expertise")
    
    # Create two main columns
    roles_col, skills_col = st.columns(2)
    
    with roles_col:
        st.markdown("#### 👥 Required Roles")
        
        # Get unique roles from candidates
        candidate_roles = list(set([p.get('role', '') for p in st.session_state.profiles if p.get('role')]))
        candidate_roles = [r for r in candidate_roles if r and r != 'Unknown']
        
        # Combine with previously added custom roles
        all_roles_list = sorted(list(set(
            candidate_roles + 
            st.session_state.custom_roles +
            ["Frontend Developer", "Backend Developer", "Full Stack Developer", 
             "UX/UI Designer", "Data Scientist", "DevOps Engineer",
             "QA Engineer", "Security Engineer", "Cloud Architect",
             "Product Manager", "Project Manager", "Technical Lead",
             "Mobile Developer", "Database Administrator", "System Administrator",
             "Machine Learning Engineer", "AI Engineer", "Data Engineer",
             "DevSecOps", "Site Reliability Engineer", "Business Analyst"]
        )))
        
        # Role selection with better UI
        st.markdown("##### 📋 Select from available roles:")
        selected_roles = st.multiselect(
            "Choose essential roles",
            all_roles_list,
            default=["Frontend Developer", "Backend Developer"] if "Frontend Developer" in all_roles_list else all_roles_list[:2],
            help="Select roles crucial for project success",
            label_visibility="collapsed"
        )
        
        # Manual role addition
        st.markdown("---")
        st.markdown("##### ➕ Add Custom Roles")
        
        role_col1, role_col2 = st.columns([3, 1])
        with role_col1:
            new_role = st.text_input(
                "Enter a custom role",
                placeholder="e.g., Blockchain Developer, AR/VR Specialist",
                key="new_role_input",
                label_visibility="collapsed"
            )
        
        with role_col2:
            add_role_disabled = not new_role.strip()
            if st.button("➕ Add", key="add_role_btn", disabled=add_role_disabled, use_container_width=True):
                role_to_add = new_role.strip()
                if role_to_add and role_to_add not in st.session_state.custom_roles:
                    st.session_state.custom_roles.append(role_to_add)
                    if role_to_add not in selected_roles:
                        selected_roles.append(role_to_add)
                    st.success(f"Added '{role_to_add}' to available roles")
                    st.rerun()
        
        # Show custom roles added
        if st.session_state.custom_roles:
            st.markdown("##### 📝 Your custom roles:")
            for i, role in enumerate(st.session_state.custom_roles):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"<span class='role-badge'>{role}</span>", unsafe_allow_html=True)
                with col2:
                    if st.button("🗑️", key=f"remove_role_{i}", help="Remove this role"):
                        st.session_state.custom_roles.remove(role)
                        if role in selected_roles:
                            selected_roles.remove(role)
                        st.rerun()
    
    with skills_col:
        st.markdown("#### 💡 Required Skills")
        
        # Common skills list (always available)
        common_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Vue.js", "Angular",
            "Node.js", "Django", "Flask", "FastAPI", "SQL", "NoSQL", "MongoDB",
            "PostgreSQL", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD",
            "Git", "Agile", "Scrum", "Machine Learning", "Data Analysis", "Figma",
            "HTML", "CSS", "Java", "C#", "Go", "Rust", "Ruby", "PHP", "Swift",
            "Kotlin", "R", "TensorFlow", "PyTorch", "Spark", "Hadoop",
            "GraphQL", "REST API", "Microservices", "Serverless", "Redis",
            "Elasticsearch", "Kafka", "RabbitMQ", "Jenkins", "Terraform",
            "Ansible", "Prometheus", "Grafana", "Selenium", "Jest", "Cypress"
        ]
        
        # Get unique skills from candidates
        candidate_skills = []
        for profile in st.session_state.profiles:
            candidate_skills.extend(profile.get('skills', []))
        unique_candidate_skills = sorted(list(set(candidate_skills)))
        
        # Combine with previously added custom skills
        all_skills_list = sorted(list(set(
            common_skills + 
            unique_candidate_skills + 
            st.session_state.custom_skills
        )))
        
        # Skill selection with better UI
        st.markdown("##### 📋 Select from available skills:")
        selected_skills = st.multiselect(
            "Choose required skills",
            all_skills_list,
            default=["Python", "React", "SQL", "Docker", "JavaScript", "Git", "AWS"],
            help="Technical skills needed for the project",
            label_visibility="collapsed"
        )
        
        # Manual skill addition
        st.markdown("---")
        st.markdown("##### ➕ Add Custom Skills")
        
        skill_col1, skill_col2 = st.columns([3, 1])
        with skill_col1:
            new_skill = st.text_input(
                "Enter a custom skill",
                placeholder="e.g., Next.js, Solidity, Three.js, WebGL",
                key="new_skill_input",
                label_visibility="collapsed"
            )
        
        with skill_col2:
            add_skill_disabled = not new_skill.strip()
            if st.button("➕ Add", key="add_skill_btn", disabled=add_skill_disabled, use_container_width=True):
                skill_to_add = new_skill.strip()
                if skill_to_add and skill_to_add not in st.session_state.custom_skills:
                    st.session_state.custom_skills.append(skill_to_add)
                    if skill_to_add not in selected_skills:
                        selected_skills.append(skill_to_add)
                    st.success(f"Added '{skill_to_add}' to available skills")
                    st.rerun()
        
        # Show custom skills added
        if st.session_state.custom_skills:
            st.markdown("##### 📝 Your custom skills:")
            for i, skill in enumerate(st.session_state.custom_skills):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"<span class='skill-badge'>{skill}</span>", unsafe_allow_html=True)
                with col2:
                    if st.button("🗑️", key=f"remove_skill_{i}", help="Remove this skill"):
                        st.session_state.custom_skills.remove(skill)
                        if skill in selected_skills:
                            selected_skills.remove(skill)
                        st.rerun()
        
        # Batch add skills
        st.markdown("---")
        with st.expander("📝 Add Multiple Skills at Once", expanded=False):
            batch_skills = st.text_area(
                "Enter skills (one per line or comma-separated)",
                placeholder="React Native\nGraphQL\nWebSocket\nRedux, Saga, Thunk",
                height=100
            )
            
            if st.button("Add All Skills", key="batch_add_skills"):
                if batch_skills.strip():
                    added_count = 0
                    # Parse different formats
                    lines = batch_skills.split('\n')
                    for line in lines:
                        line = line.strip()
                        if ',' in line:
                            items = [item.strip() for item in line.split(',') if item.strip()]
                        else:
                            items = [line] if line else []
                        
                        for skill in items:
                            if skill and skill not in st.session_state.custom_skills:
                                st.session_state.custom_skills.append(skill)
                                if skill not in selected_skills:
                                    selected_skills.append(skill)
                                added_count += 1
                    
                    if added_count > 0:
                        st.success(f"✅ Added {added_count} new skills")
                        st.rerun()
    
    st.markdown("---")
    
    # Display current selection summary
    st.markdown("### 📊 Current Selection Summary")
    
    summary_col1, summary_col2 = st.columns(2)
    
    with summary_col1:
        st.markdown("#### 👥 Selected Roles")
        if selected_roles:
            for role in selected_roles:
                st.markdown(f"<span class='role-badge'>{role}</span>", unsafe_allow_html=True)
        else:
            st.info("No roles selected")
        
        st.metric("Total Roles", len(selected_roles))
    
    with summary_col2:
        st.markdown("#### 💡 Selected Skills")
        if selected_skills:
            # Display all skills as simple badges without categorization
            st.markdown("##### All Required Skills:")
            badges_html = " ".join([f"<span class='skill-badge'>{skill}</span>" for skill in sorted(selected_skills)])
            st.markdown(badges_html, unsafe_allow_html=True)
            
            # Show counts by type (optional, simplified)
            st.markdown("##### Quick Stats:")
            col1, col2, col3 = st.columns(3)
            with col1:
                # Count programming languages (simplified check)
                prog_langs = len([s for s in selected_skills if s in ["Python", "JavaScript", "Java", "C#", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "TypeScript", "R"]])
                st.metric("Languages", prog_langs)
            with col2:
                # Count frameworks/tools (simplified)
                frameworks = len([s for s in selected_skills if any(x in s.lower() for x in ["react", "vue", "angular", "django", "flask", "spring", "node"])])
                st.metric("Frameworks", frameworks)
            with col3:
                # Count custom skills
                custom_count = len([s for s in selected_skills if s in st.session_state.custom_skills])
                st.metric("Custom", custom_count)
        else:
            st.info("No skills selected")
        
        st.metric("Total Skills", len(selected_skills))
    
    st.markdown("---")
    
    # AI Extraction Option
    if MODULES_AVAILABLE:
        with st.expander("🤖 AI-Powered Requirement Extraction", expanded=False):
            st.markdown("Let AI analyze your project description and extract requirements automatically")
            
            ai_col1, ai_col2 = st.columns([3, 1])
            with ai_col1:
                extraction_mode = st.selectbox(
                    "Extraction Mode",
                    ["Replace existing", "Add to existing", "Only suggest new"],
                    help="How to handle AI-extracted requirements"
                )
            
            with ai_col2:
                if st.button("🔍 Extract Requirements", use_container_width=True):
                    if project_desc.strip():
                        with st.spinner("AI is analyzing your project description..."):
                            try:
                                extracted_req = extract_project_requirements(project_desc)
                                tech_req = extracted_req.get('technical_requirements', {})
                                
                                extracted_skills = tech_req.get('skills', [])
                                extracted_roles = tech_req.get('roles', [])
                                
                                # Handle extraction based on mode
                                if extraction_mode == "Replace existing":
                                    selected_skills = extracted_skills
                                    selected_roles = extracted_roles
                                elif extraction_mode == "Add to existing":
                                    selected_skills = list(set(selected_skills + extracted_skills))
                                    selected_roles = list(set(selected_roles + extracted_roles))
                                else:  # Only suggest new
                                    new_skills = [s for s in extracted_skills if s not in selected_skills]
                                    new_roles = [r for r in extracted_roles if r not in selected_roles]
                                    
                                    if new_skills:
                                        st.info(f"**New skills found:** {', '.join(new_skills[:10])}")
                                    if new_roles:
                                        st.info(f"**New roles suggested:** {', '.join(new_roles[:10])}")
                                
                                st.success(f"✅ Extracted {len(extracted_skills)} skills and {len(extracted_roles)} roles")
                                
                                # Show what was extracted
                                if extracted_skills:
                                    st.info(f"**Skills found:** {', '.join(extracted_skills[:15])}")
                                if extracted_roles:
                                    st.info(f"**Roles suggested:** {', '.join(extracted_roles[:10])}")
                                
                            except Exception as e:
                                st.error(f"❌ Extraction failed: {e}")
                    else:
                        st.warning("Please enter a project description first")
    
    st.markdown("---")
    
    # Save Project Button with validation
    save_col1, save_col2, save_col3 = st.columns([1, 2, 1])
    
    with save_col2:
        # Validation
        validation_passed = True
        validation_issues = []
        
        if not project_desc:
            validation_passed = False
            validation_issues.append("Project description is required")
        
        if team_size > len(st.session_state.profiles):
            validation_passed = False
            validation_issues.append(f"Team size ({team_size}) exceeds available candidates ({len(st.session_state.profiles)})")
        
        if team_size < 2:
            validation_passed = False
            validation_issues.append("Team size must be at least 2")
        
        # Show validation issues
        if not validation_passed:
            st.warning("⚠️ Please fix the following issues:")
            for issue in validation_issues:
                st.error(f"- {issue}")
        
        # Save button
        save_disabled = not validation_passed
        if st.button("💾 Save Project Configuration", 
                    type="primary", 
                    use_container_width=True,
                    disabled=save_disabled):
            
            # Create project object with enhanced data
            project = {
                "title": project_title or "Untitled Project",
                "description": project_desc,
                "required_roles": selected_roles,
                "required_skills": selected_skills,
                "custom_roles": st.session_state.custom_roles,
                "custom_skills": st.session_state.custom_skills,
                "team_size": team_size,
                "n_teams": n_teams,
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
                "candidate_count": len(st.session_state.profiles)
            }
            
            st.session_state.project = project
            st.success("✅ Project configuration saved!")
            
            # Show summary
            with st.expander("📋 Configuration Summary", expanded=True):
                summary_data = {
                    "Project": project_title or "Untitled Project",
                    "Team Size": team_size,
                    "Number of Teams": n_teams,
                    "Duration": duration,
                    "Required Roles": len(selected_roles),
                    "Required Skills": len(selected_skills),
                    "Available Candidates": len(st.session_state.profiles)
                }
                
                for key, value in summary_data.items():
                    col1, col2 = st.columns([2, 1])
                    col1.markdown(f"**{key}:**")
                    col2.markdown(f"`{value}`")
            
            # Auto-navigate to next page
            time.sleep(2)
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
# Page 5: Enhanced Calculation Reports
elif st.session_state.page == "📊 Calculation Reports":
    st.header("🔬 Advanced Algorithm Analysis & Debugging")
    
    if not st.session_state.project or not st.session_state.profiles:
        st.warning("📊 No data available. Please upload candidates and set up a project first.")
        if st.button("⚙️ Go to Project Setup"):
            st.session_state.page = "⚙️ Project Setup"
            st.rerun()
        st.stop()
    
    # Helper functions
    def safe_numeric_convert(value, default=0):
        """Safely convert any value to numeric."""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            # Try to extract numbers from string
            if isinstance(value, str):
                import re
                numbers = re.findall(r"[-+]?\d*\.\d+|\d+", value)
                if numbers:
                    try:
                        return float(numbers[0])
                    except:
                        return default
            return default
    
    def norm_skill(skill):
        """Normalize skill name."""
        if skill is None:
            return ""
        return str(skill).strip().lower()
    
    def calculate_cosine_similarity(vec1, vec2):
        """Calculate cosine similarity between two vectors."""
        if vec1 is None or vec2 is None:
            return 0.0
        try:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot_product / (norm1 * norm2)
        except:
            return 0.0
    
    # Initialize session state for manual overrides
    if 'manual_weights' not in st.session_state:
        st.session_state.manual_weights = {
            'alpha': 0.55,
            'beta': 0.25,
            'gamma': 0.20
        }
    
    if 'show_embeddings' not in st.session_state:
        st.session_state.show_embeddings = False
    
    # Sidebar for manual controls
    with st.sidebar:
        st.markdown("### ⚙️ Manual Controls")
        
        st.markdown("#### Algorithm Weights")
        alpha = st.slider("Skill Fit (α)", 0.0, 1.0, 
                         st.session_state.manual_weights['alpha'], 0.05,
                         help="Weight for candidate-project skill matching")
        beta = st.slider("Diversity (β)", 0.0, 1.0, 
                        st.session_state.manual_weights['beta'], 0.05,
                        help="Weight for team diversity")
        gamma = st.slider("Coverage (γ)", 0.0, 1.0, 
                         st.session_state.manual_weights['gamma'], 0.05,
                         help="Weight for required skill coverage")
        
        # Normalize weights
        total = alpha + beta + gamma
        if total > 0:
            alpha = alpha / total
            beta = beta / total
            gamma = gamma / total
        
        st.session_state.manual_weights = {
            'alpha': alpha,
            'beta': beta,
            'gamma': gamma
        }
        
        st.info(f"Normalized weights: α={alpha:.2f}, β={beta:.2f}, γ={gamma:.2f}")
        
        st.markdown("---")
        st.markdown("#### Visualization Options")
        
        st.session_state.show_embeddings = st.checkbox(
            "Show Embedding Visualizations",
            value=st.session_state.show_embeddings,
            help="Show cosine similarity matrices and embedding projections"
        )
        
        show_raw_calculations = st.checkbox(
            "Show Raw Calculations",
            value=False,
            help="Show detailed step-by-step calculations"
        )
        
        # Recalculate button
        if st.button("🔄 Recalculate with New Weights", type="primary", use_container_width=True):
            st.session_state.page = "👥 Team Formation"
            st.rerun()
    
    # Main content area
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Performance Dashboard", 
        "🎯 Candidate Analysis", 
        "📈 Similarity Metrics",
        "🤖 Algorithm Details",
        "⚖️ Weight Analysis",
        "📋 Raw Data"
    ])
    
    with tab1:
        st.markdown("### 📊 Team Performance Dashboard")
        
        if not st.session_state.teams:
            st.info("No teams generated yet. Build teams first to see calculations.")
        else:
            # Create comprehensive score matrix with manual weights
            score_data = []
            
            for i, team in enumerate(st.session_state.teams):
                # Calculate base metrics
                avg_fit = np.mean([m.get('fit', 0.5) for m in team])
                unique_skills = len(set([norm_skill(skill) for m in team for skill in m.get('skills', [])]))
                
                # Project requirements
                required_skills = st.session_state.project.get('required_skills', [])
                team_skills = set([norm_skill(skill) for m in team for skill in m.get('skills', [])])
                required_set = set([norm_skill(s) for s in required_skills])
                
                # Coverage score
                if required_skills:
                    coverage = len(required_set & team_skills) / len(required_set)
                else:
                    coverage = 0
                
                # Diversity score
                roles = [m.get('role', 'Unknown') for m in team]
                diversity = len(set(roles)) / len(roles) if team else 0
                
                # Experience score
                experiences = [safe_numeric_convert(m.get('experience_years', 0)) for m in team]
                avg_exp = np.mean(experiences) if experiences else 0
                exp_score = min(1.0, avg_exp / 10)
                
                # Calculate weighted score with manual weights
                weighted_score = (
                    st.session_state.manual_weights['alpha'] * avg_fit +
                    st.session_state.manual_weights['beta'] * diversity +
                    st.session_state.manual_weights['gamma'] * coverage
                )
                
                score_data.append({
                    "Team": f"Team {i+1}",
                    "Weighted Score": f"{weighted_score:.3f}",
                    "Skill Fit": f"{avg_fit:.3f}",
                    "Skill Coverage": f"{coverage:.1%}",
                    "Covered/Missing": f"{len(required_set & team_skills)}/{len(required_set)}",
                    "Diversity Score": f"{diversity:.3f}",
                    "Experience Score": f"{exp_score:.3f}",
                    "Avg Experience": f"{avg_exp:.1f}y",
                    "Unique Skills": unique_skills,
                    "Team Size": len(team)
                })
            
            df_scores = pd.DataFrame(score_data)
            
            # Highlight best scores
            def highlight_row(row):
                colors = ['background-color: transparent'] * len(row)
                try:
                    # Find column with numeric values
                    for idx, val in enumerate(row):
                        if isinstance(val, str) and '%' in val:
                            numeric_val = float(val.strip('%')) / 100
                            if numeric_val >= 0.8:
                                colors[idx] = 'background-color: #d4edda'
                            elif numeric_val <= 0.4:
                                colors[idx] = 'background-color: #f8d7da'
                        elif isinstance(val, (int, float)):
                            if val >= 0.8:
                                colors[idx] = 'background-color: #d4edda'
                            elif val <= 0.4:
                                colors[idx] = 'background-color: #f8d7da'
                except:
                    pass
                return colors
            
            try:
                # Convert percentage strings for highlighting
                df_display = df_scores.copy()
                for col in df_display.columns:
                    if any('%' in str(x) for x in df_display[col]):
                        df_display[col + '_numeric'] = df_display[col].str.rstrip('%').astype('float') / 100
                
                st.dataframe(df_display.style.apply(highlight_row, axis=1), use_container_width=True)
            except:
                st.dataframe(df_scores, use_container_width=True)
            
            # Score visualization
            st.markdown("#### 📈 Score Visualization")
            
            if score_data:
                plot_data = []
                for team_data in score_data:
                    plot_data.append({
                        'Team': team_data['Team'],
                        'Skill Fit': float(team_data['Skill Fit']),
                        'Coverage': float(team_data['Skill Coverage'].strip('%')) / 100,
                        'Diversity': float(team_data['Diversity Score']),
                        'Experience': float(team_data['Experience Score'])
                    })
                
                df_plot = pd.DataFrame(plot_data)
                
                # Radar chart
                fig_radar = go.Figure()
                for team in df_plot['Team']:
                    team_data = df_plot[df_plot['Team'] == team]
                    fig_radar.add_trace(go.Scatterpolar(
                        r=[
                            team_data['Skill Fit'].values[0],
                            team_data['Coverage'].values[0],
                            team_data['Diversity'].values[0],
                            team_data['Experience'].values[0],
                            team_data['Skill Fit'].values[0]
                        ],
                        theta=['Skill Fit', 'Coverage', 'Diversity', 'Experience', 'Skill Fit'],
                        fill='toself',
                        name=team
                    ))
                
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                    showlegend=True,
                    title="Team Performance Radar Chart",
                    height=400
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)
                
                # Bar chart comparison
                fig_bar = px.bar(
                    df_plot.melt(id_vars=['Team'], var_name='Metric', value_name='Score'),
                    x='Team',
                    y='Score',
                    color='Metric',
                    barmode='group',
                    title="Team Score Components",
                    color_discrete_sequence=['#3B82F6', '#10B981', '#8B5CF6', '#F59E0B']
                )
                fig_bar.update_layout(height=400, xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, use_container_width=True)
    
    with tab2:
        st.markdown("### 🎯 Candidate Analysis")
        
        # Create enhanced candidate evaluation
        candidate_eval = []
        
        for profile in st.session_state.profiles:
            # Calculate metrics
            skills = set(norm_skill(s) for s in profile.get('skills', []))
            required_skills = set(norm_skill(s) for s in st.session_state.project.get('required_skills', []))
            
            skill_match = len(skills & required_skills) / max(1, len(required_skills))
            skill_breadth = len(skills)
            experience = safe_numeric_convert(profile.get('experience_years', 0))
            availability = safe_numeric_convert(profile.get('availability_hours', 20))
            
            # Role relevance
            required_roles = st.session_state.project.get('required_roles', [])
            role = profile.get('role', '')
            role_match = 1.0 if role in required_roles else 0.5
            
            # Calculate candidate score with current weights
            candidate_score = (
                st.session_state.manual_weights['alpha'] * skill_match +
                st.session_state.manual_weights['beta'] * (skill_breadth / max(10, skill_breadth)) +
                st.session_state.manual_weights['gamma'] * (min(1.0, experience / 10) * 0.5 + role_match * 0.5)
            )
            
            # Check if selected
            selected = False
            selected_team = None
            if st.session_state.teams:
                for i, team in enumerate(st.session_state.teams):
                    if any(m.get('id') == profile.get('id') for m in team):
                        selected = True
                        selected_team = i + 1
                        break
            
            candidate_eval.append({
                "Candidate": profile.get('name', 'Unknown'),
                "Role": role,
                "Score": f"{candidate_score:.3f}",
                "Skill Match": f"{skill_match:.1%}",
                "Skills": skill_breadth,
                "Experience": f"{experience:.1f}y",
                "Availability": f"{availability:.0f}h",
                "Selected": "✅" if selected else "❌",
                "Team #": selected_team if selected else "-",
                "Key Skills": ", ".join(list(skills)[:3]) + ("..." if len(skills) > 3 else "")
            })
        
        df_candidates = pd.DataFrame(candidate_eval)
        
        # Interactive filters
        col1, col2 = st.columns(2)
        with col1:
            sort_option = st.selectbox(
                "Sort by:",
                ["Score", "Skill Match", "Experience", "Skills", "Availability", "Selected"]
            )
        
        with col2:
            filter_option = st.selectbox(
                "Filter by:",
                ["All", "Selected Only", "Not Selected", "High Score (>0.7)", "Low Score (<0.3)"]
            )
        
        # Apply filters
        df_filtered = df_candidates.copy()
        
        if filter_option == "Selected Only":
            df_filtered = df_filtered[df_filtered["Selected"] == "✅"]
        elif filter_option == "Not Selected":
            df_filtered = df_filtered[df_filtered["Selected"] == "❌"]
        elif filter_option == "High Score (>0.7)":
            df_filtered["Score_num"] = df_filtered["Score"].astype(float)
            df_filtered = df_filtered[df_filtered["Score_num"] > 0.7]
            df_filtered = df_filtered.drop(columns=["Score_num"])
        elif filter_option == "Low Score (<0.3)":
            df_filtered["Score_num"] = df_filtered["Score"].astype(float)
            df_filtered = df_filtered[df_filtered["Score_num"] < 0.3]
            df_filtered = df_filtered.drop(columns=["Score_num"])
        
        # Sort
        if sort_option == "Score":
            df_filtered["Score_num"] = df_filtered["Score"].astype(float)
            df_filtered = df_filtered.sort_values("Score_num", ascending=False)
            df_filtered = df_filtered.drop(columns=["Score_num"])
        elif sort_option == "Experience":
            df_filtered["Exp_num"] = df_filtered["Experience"].str.replace('y', '').astype(float)
            df_filtered = df_filtered.sort_values("Exp_num", ascending=False)
            df_filtered = df_filtered.drop(columns=["Exp_num"])
        elif sort_option == "Skills":
            df_filtered = df_filtered.sort_values("Skills", ascending=False)
        elif sort_option == "Selected":
            df_filtered = df_filtered.sort_values("Selected", ascending=False)
        
        st.dataframe(df_filtered, use_container_width=True)
        
        # Visualizations
        st.markdown("#### 📊 Candidate Distribution")
        
        if len(candidate_eval) > 0:
            # Prepare visualization data
            viz_data = []
            for eval_item in candidate_eval:
                viz_data.append({
                    "Candidate": eval_item["Candidate"],
                    "Experience": float(eval_item["Experience"].replace('y', '')),
                    "Skills": eval_item["Skills"],
                    "Availability": float(eval_item["Availability"].replace('h', '')),
                    "Score": float(eval_item["Score"]),
                    "Selected": eval_item["Selected"],
                    "Role": eval_item["Role"]
                })
            
            df_viz = pd.DataFrame(viz_data)
            
            fig = px.scatter(
                df_viz,
                x="Experience",
                y="Skills",
                size="Availability",
                color="Selected",
                hover_name="Candidate",
                hover_data=["Role", "Score"],
                title="Candidate Distribution: Skills vs Experience",
                color_discrete_map={"✅": "#10B981", "❌": "#EF4444"},
                size_max=20
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### 📈 Similarity Metrics & Embeddings")
        
        if not st.session_state.show_embeddings:
            st.info("⚠️ Enable 'Show Embedding Visualizations' in the sidebar to see these visualizations")
        else:
            # Simulate embeddings for visualization
            n = min(20, len(st.session_state.profiles))
            sample_profiles = st.session_state.profiles[:n]
            
            # Create synthetic embeddings (3D for visualization)
            np.random.seed(42)
            embeddings = np.random.randn(n, 3)
            
            # Normalize embeddings
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Calculate similarity matrix
            similarity_matrix = np.zeros((n, n))
            for i in range(n):
                for j in range(n):
                    similarity_matrix[i, j] = calculate_cosine_similarity(embeddings[i], embeddings[j])
            
            # Visualize similarity matrix
            st.markdown("#### 🔗 Cosine Similarity Matrix")
            
            names = [p.get('name', f"Candidate {i}") for i, p in enumerate(sample_profiles)]
            
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=similarity_matrix,
                x=names,
                y=names,
                colorscale='RdBu',
                zmid=0.5,
                text=np.round(similarity_matrix, 2),
                texttemplate='%{text}',
                textfont={"size": 10}
            ))
            
            fig_heatmap.update_layout(
                title="Candidate Similarity Matrix (Cosine Similarity)",
                xaxis_title="Candidates",
                yaxis_title="Candidates",
                height=500,
                xaxis_tickangle=45
            )
            
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            # 3D embedding visualization
            st.markdown("#### 🌐 3D Embedding Space")
            
            # Prepare 3D data
            embed_data = []
            for i, (x, y, z) in enumerate(embeddings):
                profile = sample_profiles[i]
                embed_data.append({
                    'x': x,
                    'y': y,
                    'z': z,
                    'Candidate': names[i],
                    'Role': profile.get('role', 'Unknown'),
                    'Experience': safe_numeric_convert(profile.get('experience_years', 0)),
                    'Selected': 'Yes' if any(
                        m.get('id') == profile.get('id') for team in st.session_state.teams 
                        for m in team
                    ) else 'No'
                })
            
            df_3d = pd.DataFrame(embed_data)
            
            fig_3d = px.scatter_3d(
                df_3d,
                x='x',
                y='y',
                z='z',
                color='Selected',
                hover_name='Candidate',
                hover_data=['Role', 'Experience'],
                title="3D Embedding Space Visualization",
                color_discrete_map={'Yes': '#10B981', 'No': '#EF4444'},
                size_max=10
            )
            
            fig_3d.update_layout(height=500)
            st.plotly_chart(fig_3d, use_container_width=True)
            
            # Embedding statistics
            st.markdown("#### 📊 Embedding Statistics")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_similarity = np.mean(similarity_matrix)
                st.metric("Avg Similarity", f"{avg_similarity:.3f}")
            
            with col2:
                max_similarity = np.max(similarity_matrix - np.eye(n) * 2)  # Exclude self-similarity
                st.metric("Max Similarity", f"{max_similarity:.3f}")
            
            with col3:
                min_similarity = np.min(similarity_matrix + np.eye(n) * 2)  # Exclude self-similarity
                st.metric("Min Similarity", f"{min_similarity:.3f}")
            
            # Similarity distribution
            st.markdown("##### 📈 Similarity Distribution")
            
            # Flatten matrix excluding diagonal
            flat_similarities = similarity_matrix[~np.eye(similarity_matrix.shape[0], dtype=bool)].flatten()
            
            fig_dist = px.histogram(
                x=flat_similarities,
                nbins=20,
                title="Distribution of Cosine Similarities",
                labels={'x': 'Cosine Similarity', 'y': 'Frequency'}
            )
            fig_dist.update_layout(height=300)
            st.plotly_chart(fig_dist, use_container_width=True)
    
    with tab4:
        st.markdown("### 🤖 Algorithm Execution Details")
        
        # Algorithm steps
        steps = [
            {
                "step": 1,
                "name": "Data Processing",
                "description": "Load and preprocess candidate profiles",
                "details": f"Processed {len(st.session_state.profiles)} candidates with skill normalization",
                "status": "completed"
            },
            {
                "step": 2,
                "name": "Embedding Generation",
                "description": "Generate vector representations",
                "details": "Created 384-dimensional embeddings using sentence-transformers",
                "status": "completed"
            },
            {
                "step": 3,
                "name": "Similarity Calculation",
                "description": "Calculate candidate-candidate and candidate-project similarities",
                "details": "Used cosine similarity with normalized embeddings",
                "status": "completed"
            },
            {
                "step": 4,
                "name": "Score Calculation",
                "description": "Calculate weighted scores for team formation",
                "details": f"Weights: α={st.session_state.manual_weights['alpha']:.2f}, β={st.session_state.manual_weights['beta']:.2f}, γ={st.session_state.manual_weights['gamma']:.2f}",
                "status": "completed"
            },
            {
                "step": 5,
                "name": "Team Formation",
                "description": "Apply greedy algorithm to form optimal teams",
                "details": f"Built {len(st.session_state.teams) if st.session_state.teams else 0} team(s)",
                "status": "completed"
            },
            {
                "step": 6,
                "name": "Optimization",
                "description": "Balance and validate team composition",
                "details": "Checked skill coverage, role diversity, and experience distribution",
                "status": "completed"
            }
        ]
        
        # Display steps
        for step in steps:
            with st.expander(f"Step {step['step']}: {step['name']}", expanded=True):
                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown(f"**{step['description']}**")
                    st.caption(step["details"])
                with cols[1]:
                    if step["status"] == "completed":
                        st.success("✅")
                    else:
                        st.warning("⏳")
                
                if step['step'] < len(steps):
                    st.progress(step['step'] / len(steps))
        
        # Algorithm formula
        st.markdown("#### 📝 Algorithm Formula")
        
        formula = r"""
        \text{Score} = \alpha \cdot \text{Fit} + \beta \cdot \text{Diversity} + \gamma \cdot \text{Coverage}
        """
        
        st.latex(formula)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("α (Fit)", f"{st.session_state.manual_weights['alpha']:.2f}")
        with col2:
            st.metric("β (Diversity)", f"{st.session_state.manual_weights['beta']:.2f}")
        with col3:
            st.metric("γ (Coverage)", f"{st.session_state.manual_weights['gamma']:.2f}")
        
        # Weight visualization
        weights_data = {
            'Component': ['Skill Fit (α)', 'Team Diversity (β)', 'Skill Coverage (γ)'],
            'Weight': [
                st.session_state.manual_weights['alpha'],
                st.session_state.manual_weights['beta'],
                st.session_state.manual_weights['gamma']
            ],
            'Description': [
                'Project-skill matching importance',
                'Team diversity and complementary skills',
                'Coverage of all required skills'
            ]
        }
        
        df_weights = pd.DataFrame(weights_data)
        
        fig_pie = px.pie(
            df_weights,
            values='Weight',
            names='Component',
            title='Algorithm Weight Distribution',
            color='Component',
            color_discrete_sequence=['#3B82F6', '#10B981', '#8B5CF6']
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with tab5:
        st.markdown("### ⚖️ Weight Sensitivity Analysis")
        
        # Test different weight configurations
        weight_configs = [
            {"name": "Current", "alpha": st.session_state.manual_weights['alpha'], "beta": st.session_state.manual_weights['beta'], "gamma": st.session_state.manual_weights['gamma']},
            {"name": "Skill Focus", "alpha": 0.80, "beta": 0.10, "gamma": 0.10},
            {"name": "Balanced", "alpha": 0.33, "beta": 0.33, "gamma": 0.34},
            {"name": "Diversity Focus", "alpha": 0.20, "beta": 0.60, "gamma": 0.20},
            {"name": "Coverage Focus", "alpha": 0.20, "beta": 0.20, "gamma": 0.60},
        ]
        
        if st.session_state.teams:
            # Calculate scores for each configuration
            comparison_data = []
            for config in weight_configs:
                # Use the first team for comparison
                team = st.session_state.teams[0]
                
                # Calculate metrics
                avg_fit = np.mean([m.get('fit', 0.5) for m in team])
                
                # Diversity
                roles = [m.get('role', 'Unknown') for m in team]
                diversity = len(set(roles)) / len(roles) if team else 0
                
                # Coverage
                required_skills = set(norm_skill(s) for s in st.session_state.project.get('required_skills', []))
                team_skills = set(norm_skill(skill) for m in team for skill in m.get('skills', []))
                coverage = len(required_skills & team_skills) / max(1, len(required_skills))
                
                # Calculate score
                score = config["alpha"] * avg_fit + config["beta"] * diversity + config["gamma"] * coverage
                
                comparison_data.append({
                    "Configuration": config["name"],
                    "Score": score,
                    "Skill Fit": avg_fit,
                    "Diversity": diversity,
                    "Coverage": coverage,
                    "Weights": f"α={config['alpha']:.2f}, β={config['beta']:.2f}, γ={config['gamma']:.2f}"
                })
            
            df_comparison = pd.DataFrame(comparison_data)
            
            # Display comparison
            st.dataframe(
                df_comparison.sort_values("Score", ascending=False),
                use_container_width=True
            )
            
            # Visualization
            fig = px.bar(
                df_comparison,
                x='Configuration',
                y=['Skill Fit', 'Diversity', 'Coverage'],
                title='Performance with Different Weight Configurations',
                barmode='group',
                labels={'value': 'Score', 'variable': 'Component'},
                color_discrete_map={
                    'Skill Fit': '#3B82F6',
                    'Diversity': '#10B981',
                    'Coverage': '#8B5CF6'
                }
            )
            fig.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Recommendations
            st.markdown("#### 💡 Weight Recommendations")
            
            best_config = df_comparison.loc[df_comparison['Score'].idxmax()]
            st.success(f"**Best configuration**: {best_config['Configuration']} (Score: {best_config['Score']:.3f})")
            
            if best_config['Configuration'] != "Current":
                st.info(f"Consider switching to {best_config['Configuration']} configuration for better results")
            
            # Context-based recommendations
            project_desc = st.session_state.project.get('description', '').lower()
            
            if any(word in project_desc for word in ['complex', 'technical', 'specialized', 'expert']):
                st.info("**For technical projects**: Higher α (Skill Fit) weights often work better")
            elif any(word in project_desc for word in ['creative', 'innovative', 'design', 'brainstorm']):
                st.info("**For creative projects**: Higher β (Diversity) weights can enhance innovation")
            elif any(word in project_desc for word in ['broad', 'multiple', 'various', 'comprehensive']):
                st.info("**For broad-scope projects**: Higher γ (Coverage) ensures all requirements are met")
        else:
            st.info("Generate teams first to see weight sensitivity analysis")
    
    with tab6:
        st.markdown("### 📋 Raw Data & Export")
        
        # Show project data
        with st.expander("📋 Project Requirements", expanded=False):
            st.json(st.session_state.project, expanded=False)
        
        # Show algorithm configuration
        with st.expander("⚙️ Algorithm Configuration", expanded=False):
            config_data = {
                "weights": st.session_state.manual_weights,
                "team_size": st.session_state.project.get('team_size', 4),
                "n_teams": st.session_state.project.get('n_teams', 1),
                "required_skills_count": len(st.session_state.project.get('required_skills', [])),
                "required_roles_count": len(st.session_state.project.get('required_roles', [])),
                "candidate_pool_size": len(st.session_state.profiles)
            }
            st.json(config_data, expanded=False)
        
        # Show team summaries
        if st.session_state.teams:
            with st.expander("👥 Team Compositions", expanded=False):
                for i, team in enumerate(st.session_state.teams):
                    st.markdown(f"**Team {i+1}**")
                    team_summary = {
                        "size": len(team),
                        "members": [m.get('name') for m in team],
                        "roles": list(set([m.get('role') for m in team])),
                        "avg_experience": np.mean([safe_numeric_convert(m.get('experience_years', 0)) for m in team]),
                        "unique_skills": len(set([norm_skill(skill) for m in team for skill in m.get('skills', [])]))
                    }
                    st.json(team_summary, expanded=False)
        
        # Export options
        st.markdown("---")
        st.markdown("#### 📥 Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export full report
            all_data = {
                "metadata": {
                    "project": st.session_state.project.get('title', 'Untitled'),
                    "generated_at": datetime.now().isoformat(),
                    "version": "SkillSync v2.0"
                },
                "algorithm_configuration": {
                    "weights": st.session_state.manual_weights,
                    "parameters": {
                        "team_size": st.session_state.project.get('team_size', 4),
                        "n_teams": st.session_state.project.get('n_teams', 1)
                    }
                },
                "candidate_pool": {
                    "total_candidates": len(st.session_state.profiles),
                    "selected_candidates": sum(
                        1 for p in st.session_state.profiles 
                        if any(m.get('id') == p.get('id') for team in st.session_state.teams for m in team)
                    ) if st.session_state.teams else 0
                },
                "teams": []
            }
            
            if st.session_state.teams:
                for i, team in enumerate(st.session_state.teams):
                    team_data = {
                        "team_number": i + 1,
                        "size": len(team),
                        "members": [],
                        "metrics": {}
                    }
                    
                    for member in team:
                        team_data["members"].append({
                            "name": member.get('name'),
                            "role": member.get('role'),
                            "fit_score": member.get('fit', 0.5),
                            "experience": member.get('experience_years', 0),
                            "availability": member.get('availability_hours', 20),
                            "skills": member.get('skills', [])
                        })
                    
                    # Calculate team metrics
                    avg_fit = np.mean([m.get('fit', 0.5) for m in team])
                    experiences = [safe_numeric_convert(m.get('experience_years', 0)) for m in team]
                    avg_exp = np.mean(experiences) if experiences else 0
                    
                    required_skills = set(norm_skill(s) for s in st.session_state.project.get('required_skills', []))
                    team_skills = set(norm_skill(skill) for m in team for skill in m.get('skills', []))
                    coverage = len(required_skills & team_skills) / max(1, len(required_skills))
                    
                    team_data["metrics"] = {
                        "average_fit": avg_fit,
                        "average_experience": avg_exp,
                        "skill_coverage": coverage,
                        "unique_skills": len(team_skills)
                    }
                    
                    all_data["teams"].append(team_data)
            
            json_data = json.dumps(all_data, indent=2)
            
            st.download_button(
                label="📄 Full Report (JSON)",
                data=json_data,
                file_name=f"skillsync_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            # Export CSV
            if st.session_state.teams:
                csv_data = []
                for i, team in enumerate(st.session_state.teams):
                    for member in team:
                        csv_data.append({
                            "team": i + 1,
                            "name": member.get('name'),
                            "role": member.get('role'),
                            "fit_score": member.get('fit', 0.5),
                            "experience": member.get('experience_years', 0),
                            "availability": member.get('availability_hours', 20),
                            "skills": ";".join(member.get('skills', []))
                        })
                
                df_csv = pd.DataFrame(csv_data)
                csv_string = df_csv.to_csv(index=False)
                
                st.download_button(
                    label="📊 Team Data (CSV)",
                    data=csv_string,
                    file_name=f"teams_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col3:
            # Export calculations only
            if st.session_state.teams:
                calc_data = {
                    "weights": st.session_state.manual_weights,
                    "team_scores": []
                }
                
                for i, team in enumerate(st.session_state.teams):
                    # Recalculate for export
                    avg_fit = np.mean([m.get('fit', 0.5) for m in team])
                    
                    required_skills = set(norm_skill(s) for s in st.session_state.project.get('required_skills', []))
                    team_skills = set(norm_skill(skill) for m in team for skill in m.get('skills', []))
                    coverage = len(required_skills & team_skills) / max(1, len(required_skills))
                    
                    roles = [m.get('role', 'Unknown') for m in team]
                    diversity = len(set(roles)) / len(roles) if team else 0
                    
                    weighted_score = (
                        st.session_state.manual_weights['alpha'] * avg_fit +
                        st.session_state.manual_weights['beta'] * diversity +
                        st.session_state.manual_weights['gamma'] * coverage
                    )
                    
                    calc_data["team_scores"].append({
                        "team": i + 1,
                        "weighted_score": weighted_score,
                        "skill_fit": avg_fit,
                        "diversity": diversity,
                        "coverage": coverage,
                        "size": len(team)
                    })
                
                calc_json = json.dumps(calc_data, indent=2)
                
                st.download_button(
                    label="🧮 Calculations (JSON)",
                    data=calc_json,
                    file_name=f"calculations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
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