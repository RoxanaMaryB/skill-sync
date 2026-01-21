# src/modules/EXPLANATION/__init__.py
"""
Consolidated Explanation Module (M5 Part B)
Provides: generate_team_report(), explain_team()
"""
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import os

@dataclass
class ExplanationConfig:
    """Configuration for explanation generation"""
    model: str = "openai/gpt-4o-mini"
    temperature: float = 0.0
    base_url: str = "https://openrouter.ai/api/v1"

class TeamExplainer:
    """Generate explanations for team formations"""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[ExplanationConfig] = None):
        self.config = config or ExplanationConfig()
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
    
    def generate_team_report(self, teams: List[List[Dict[str, Any]]], 
                           project: Dict[str, Any],
                           candidate_inputs: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate a comprehensive team report"""
        
        if not self.api_key:
            # Generate simple report without LLM
            return self._generate_simple_report(teams, project)
        
        # In production, this would call an LLM via the RAG module
        # For now, return a simple report
        
        return self._generate_simple_report(teams, project)
    
    def _generate_simple_report(self, teams: List[List[Dict[str, Any]]], 
                              project: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a simple report without LLM"""
        
        report = {
            "project": {
                "title": project.get("title", "Untitled Project"),
                "required_skills": project.get("required_skills", []),
                "required_roles": project.get("required_roles", []),
                "team_size": project.get("team_size", 4)
            },
            "teams": []
        }
        
        for i, team in enumerate(teams):
            team_report = {
                "team_number": i + 1,
                "size": len(team),
                "members": [],
                "summary": {},
                "strengths": [],
                "recommendations": []
            }
            
            # Analyze team composition
            roles = []
            skills = []
            experience_years = []
            
            for member in team:
                # Add member info
                member_info = {
                    "id": member.get("id", ""),
                    "role": member.get("metadata", {}).get("dev_type", "Unknown"),
                    "skills": member.get("technical", {}).get("skills", []),
                    "experience": member.get("metadata", {}).get("work_experience_years", "0"),
                    "availability": member.get("constraints", {}).get("weekly_availability_hours", "20")
                }
                team_report["members"].append(member_info)
                
                # Collect stats
                roles.append(member_info["role"])
                skills.extend(member_info["skills"])
                exp = member_info["experience"]
                if exp.isdigit():
                    experience_years.append(int(exp))
            
            # Calculate team summary
            team_report["summary"] = {
                "unique_roles": len(set(roles)),
                "unique_skills": len(set(skills)),
                "avg_experience": sum(experience_years) / max(1, len(experience_years)),
                "role_distribution": {role: roles.count(role) for role in set(roles)}
            }
            
            # Generate strengths
            unique_skill_count = len(set(skills))
            if unique_skill_count > 15:
                team_report["strengths"].append("High skill diversity")
            elif unique_skill_count > 10:
                team_report["strengths"].append("Good skill coverage")
            
            if len(set(roles)) >= 2:
                team_report["strengths"].append("Cross-functional composition")
            
            avg_exp = team_report["summary"]["avg_experience"]
            if avg_exp > 5:
                team_report["strengths"].append("Experienced team members")
            
            # Check project requirements coverage
            required_skills = project.get("required_skills", [])
            if required_skills:
                covered = len(set(required_skills) & set(skills))
                coverage_percent = (covered / len(required_skills)) * 100
                team_report["summary"]["skill_coverage_percent"] = coverage_percent
                
                if coverage_percent > 80:
                    team_report["strengths"].append(f"Excellent skill coverage ({coverage_percent:.0f}%)")
                elif coverage_percent > 60:
                    team_report["strengths"].append(f"Good skill coverage ({coverage_percent:.0f}%)")
            
            # Recommendations
            if len(set(roles)) < 2:
                team_report["recommendations"].append("Consider adding more role diversity")
            
            if avg_exp < 3:
                team_report["recommendations"].append("Team lacks senior experience")
            
            report["teams"].append(team_report)
        
        return {
            "report": report,
            "markdown_summary": self._report_to_markdown(report),
            "recommended_team": 1 if len(teams) > 0 else None
        }
    
    def _report_to_markdown(self, report: Dict[str, Any]) -> str:
        """Convert report to markdown format"""
        project = report["project"]
        teams = report["teams"]
        
        markdown = f"# Team Formation Report\n\n"
        markdown += f"## Project: {project['title']}\n\n"
        markdown += f"**Required Skills:** {', '.join(project['required_skills'][:10])}\n\n"
        markdown += f"**Team Size:** {project['team_size']}\n\n"
        
        markdown += "---\n\n"
        
        for team in teams:
            markdown += f"## Team {team['team_number']}\n\n"
            markdown += f"**Size:** {team['size']} members\n"
            markdown += f"**Avg Experience:** {team['summary']['avg_experience']:.1f} years\n"
            markdown += f"**Unique Skills:** {team['summary']['unique_skills']}\n\n"
            
            if team['strengths']:
                markdown += "### Strengths\n"
                for strength in team['strengths']:
                    markdown += f"- {strength}\n"
                markdown += "\n"
            
            if team['recommendations']:
                markdown += "### Recommendations\n"
                for rec in team['recommendations']:
                    markdown += f"- {rec}\n"
                markdown += "\n"
            
            markdown += "### Team Members\n"
            for member in team['members'][:5]:  # Limit to first 5
                markdown += f"- **{member['role']}**: {len(member['skills'])} skills, {member['experience']} years exp\n"
            
            markdown += "\n---\n\n"
        
        return markdown
    
    def explain_team(self, team: List[Dict[str, Any]], project: Dict[str, Any]) -> str:
        """Generate a concise explanation for a single team"""
        roles = [m.get("metadata", {}).get("dev_type", "Unknown") for m in team]
        skills = []
        for member in team:
            skills.extend(member.get("technical", {}).get("skills", []))
        
        unique_roles = len(set(roles))
        unique_skills = len(set(skills))
        
        explanation = f"This team of {len(team)} has {unique_roles} unique roles "
        explanation += f"and covers {unique_skills} unique skills. "
        
        if unique_roles >= 3:
            explanation += "The diverse role composition enables cross-functional collaboration. "
        elif unique_roles == 2:
            explanation += "The team has complementary role specialization. "
        
        if unique_skills > 20:
            explanation += "Strong technical breadth across multiple domains. "
        elif unique_skills > 10:
            explanation += "Good technical coverage of essential skills. "
        
        # Check coverage
        required = set(project.get("required_skills", []))
        team_skills = set(skills)
        coverage = len(required & team_skills)
        
        if required:
            coverage_pct = (coverage / len(required)) * 100
            explanation += f"Covers {coverage} of {len(required)} required skills ({coverage_pct:.0f}%)."
        
        return explanation

# Public API functions
def generate_team_report(teams: List[List[Dict[str, Any]]], 
                        project: Dict[str, Any],
                        api_key: Optional[str] = None,
                        config: Optional[ExplanationConfig] = None) -> Dict[str, Any]:
    """Generate a comprehensive team report"""
    explainer = TeamExplainer(api_key, config)
    return explainer.generate_team_report(teams, project)

def explain_team(team: List[Dict[str, Any]], project: Dict[str, Any],
                api_key: Optional[str] = None) -> str:
    """Generate a concise explanation for a team"""
    explainer = TeamExplainer(api_key)
    return explainer.explain_team(team, project)