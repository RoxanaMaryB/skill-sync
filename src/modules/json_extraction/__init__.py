# src/modules/json_extraction/__init__.py
"""
Consolidated JSON Extraction Module (M5)
Provides: extract_candidates(), extract_project_requirements()
"""
import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ExtractorConfig:
    """Configuration for extraction"""
    model: str = "openai/gpt-4o-mini"
    temperature: float = 0.0
    limit: int = 10
    base_url: str = "https://openrouter.ai/api/v1"

class CandidateExtractor:
    """Extract candidate profiles from text/CSV"""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[ExtractorConfig] = None):
        self.config = config or ExtractorConfig()
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        
    def extract_from_csv(self, csv_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Extract candidate profiles from CSV file"""
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        
        try:
            df = pd.read_csv(csv_path)
            # Simple extraction for demo (replace with actual LLM calls)
            profiles = []
            inputs = {}
            
            limit = min(self.config.limit, len(df))
            for i in range(limit):
                row = df.iloc[i].to_dict()
                cid = str(row.get("Candidate ID", f"candidate_{i}"))
                
                # Create simple profile
                profile = {
                    "id": cid,
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
                        "skills": self._extract_skills_from_row(row),
                        "tools": self._extract_tools_from_row(row)
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
    
    def _extract_skills_from_row(self, row: Dict[str, Any]) -> List[str]:
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
    
    def _extract_tools_from_row(self, row: Dict[str, Any]) -> List[str]:
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

class ProjectExtractor:
    """Extract project requirements from text"""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[ExtractorConfig] = None):
        self.config = config or ExtractorConfig()
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
    
    def extract_requirements(self, description: str) -> Dict[str, Any]:
        """Extract technical requirements from project description"""
        if not self.api_key:
            # Return default structure if no API key
            return {
                "technical_requirements": {
                    "skills": [],
                    "tools": [],
                    "roles": []
                }
            }
        
        # Simple keyword-based extraction for demo
        # In production, this would call an LLM
        
        skills_keywords = ["python", "javascript", "react", "node", "sql", "docker", 
                          "aws", "java", "c++", "typescript", "vue", "angular", "django", "flask"]
        tools_keywords = ["git", "jira", "confluence", "slack", "figma", "vscode", 
                         "intellij", "docker", "kubernetes", "jenkins"]
        roles_keywords = ["frontend", "backend", "full stack", "developer", "designer",
                         "devops", "data scientist", "engineer", "architect"]
        
        description_lower = description.lower()
        
        skills = [kw.title() for kw in skills_keywords if kw in description_lower]
        tools = [kw.title() for kw in tools_keywords if kw in description_lower]
        roles = []
        
        # Extract roles based on keywords
        if any(kw in description_lower for kw in ["frontend", "ui", "ux", "react", "angular", "vue"]):
            roles.append("Developer, front-end")
        if any(kw in description_lower for kw in ["backend", "server", "api", "database", "sql"]):
            roles.append("Developer, back-end")
        if "full stack" in description_lower:
            roles.append("Developer, full-stack")
        if any(kw in description_lower for kw in ["devops", "deployment", "container", "docker"]):
            roles.append("DevOps specialist")
        if any(kw in description_lower for kw in ["data", "machine learning", "ai", "analytics"]):
            roles.append("Data scientist or machine learning specialist")
        
        return {
            "technical_requirements": {
                "skills": list(set(skills)),
                "tools": list(set(tools)),
                "roles": list(set(roles))
            }
        }

# Public API functions
def extract_candidates(csv_path: str, api_key: Optional[str] = None, 
                      config: Optional[ExtractorConfig] = None) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Extract candidate profiles from CSV"""
    extractor = CandidateExtractor(api_key, config)
    return extractor.extract_from_csv(csv_path)

def extract_project_requirements(description: str, api_key: Optional[str] = None,
                               config: Optional[ExtractorConfig] = None) -> Dict[str, Any]:
    """Extract project requirements from description"""
    extractor = ProjectExtractor(api_key, config)
    return extractor.extract_requirements(description)