
"""
Team Explanations Module (M5 - Noor)
"""

import json
from typing import List, Dict, Any
import logging
from openai import OpenAI
import os
from dotenv import load_dotenv

from shared.interfaces import CandidateProfile, ProjectDescription

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExplanationGenerator:
    """Generate human-readable explanations for teams using ChatGPT"""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize the explanation generator.
        
        Args:
            model: OpenAI model to use
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def create_team_summary(self, team: List[CandidateProfile]) -> str:
        """
        Create a textual summary of the team for the prompt.
        
        Args:
            team: List of team members
            
        Returns:
            Textual summary of the team
        """
        summary_parts = []
        
        for member in team:
            member_summary = f"{member.name} ({member.role}):"
            member_summary += f"\n  - Skills: {', '.join(member.skills[:5])}"
            if member.skill_levels:
                top_skills = list(member.skill_levels.items())[:3]
                member_summary += f"\n  - Top skill levels: {', '.join([f'{k}: {v}' for k, v in top_skills])}"
            member_summary += f"\n  - Experience: {member.experience_years} years"
            member_summary += f"\n  - Collaboration style: {member.collaboration_style}"
            member_summary += f"\n  - Availability: {member.availability_hours} hours/week"
            summary_parts.append(member_summary)
        
        return "\n\n".join(summary_parts)
    
    def create_explanation_prompt(self, team: List[CandidateProfile], 
                                project: ProjectDescription) -> str:
        """
        Create prompt for generating team explanations.
        
        Args:
            team: List of team members
            project: Project description
            
        Returns:
            Prompt for ChatGPT
        """
        team_summary = self.create_team_summary(team)
        
        prompt = f"""Analyze the following team composition for the given project and provide a comprehensive explanation.

PROJECT:
Title: {project.title}
Description: {project.description}
Required Roles: {', '.join(project.required_roles)}
Required Skills: {', '.join(project.required_skills)}
Team Size: {project.team_size}
Duration: {project.duration_weeks} weeks

TEAM COMPOSITION:
{team_summary}

Please provide a detailed explanation covering:

1. **Overall Assessment**: How well does this team match the project requirements?

2. **Strengths**: 
   - Skill coverage for required skills
   - Role fulfillment
   - Complementary expertise
   - Collaboration potential

3. **Potential Gaps or Risks**:
   - Missing skills or roles
   - Possible collaboration challenges
   - Availability constraints
   - Experience level considerations

4. **Recommendations**:
   - Suggestions for team success
   - Areas to monitor
   - Potential need for additional support

Guidelines:
- Be specific and data-driven
- Reference actual skills and experience mentioned
- Avoid generic statements
- Focus on factual analysis based on provided data
- Keep explanation concise but comprehensive
- Do not make up information not provided

Format the response as a clear, well-structured paragraph suitable for a project manager.
"""
        
        return prompt
    
    def generate_explanation(self, team: List[CandidateProfile], 
                           project: ProjectDescription) -> str:
        """
        Generate explanation for a single team.
        
        Args:
            team: List of team members
            project: Project description
            
        Returns:
            Human-readable explanation
        """
        logger.info(f"Generating explanation for team with {len(team)} members")
        
        try:
            prompt = self.create_explanation_prompt(team, project)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert team composition analyst. Provide insightful, data-driven analysis of team formations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            explanation = response.choices[0].message.content.strip()
            logger.info("Explanation generated successfully")
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            return self._generate_fallback_explanation(team, project)
    
    def _generate_fallback_explanation(self, team: List[CandidateProfile],
                                     project: ProjectDescription) -> str:
        """
        Generate a simple fallback explanation without API.
        
        Args:
            team: List of team members
            project: Project description
            
        Returns:
            Basic explanation
        """
        # Calculate basic metrics
        all_skills = []
        for member in team:
            all_skills.extend(member.skills)
        
        unique_skills = set(all_skills)
        required_skills = set(project.required_skills)
        covered_skills = required_skills.intersection(unique_skills)
        
        coverage_percentage = len(covered_skills) / len(required_skills) * 100 if required_skills else 100
        
        # Create simple explanation
        explanation = f"This team consists of {len(team)} members covering {len(covered_skills)} out of {len(required_skills)} required skills ({coverage_percentage:.1f}%). "
        explanation += f"Team includes: {', '.join([member.role for member in team])}. "
        
        if coverage_percentage > 80:
            explanation += "The team has strong skill coverage for this project."
        elif coverage_percentage > 60:
            explanation += "The team covers most required skills, but some gaps may need attention."
        else:
            explanation += "The team has significant skill gaps that should be addressed."
        
        return explanation

# Interface function
def generate_explanations(
    teams: List[List[CandidateProfile]],
    project: ProjectDescription
) -> List[Dict[str, Any]]:
    """
    Interface function for M5 module.
    
    Args:
        teams: List of teams (each team is list of CandidateProfile)
        project: Project description
        
    Returns:
        List of explanation objects for each team
    """
    generator = ExplanationGenerator()
    explanations = []
    
    for i, team in enumerate(teams):
        explanation_text = generator.generate_explanation(team, project)
        
        explanation_obj = {
            "team_id": i + 1,
            "team_members": [member.name for member in team],
            "explanation": explanation_text,
            "summary": f"Team {i+1}: {', '.join([member.role for member in team])}"
        }
        
        explanations.append(explanation_obj)
    
    return explanations

if __name__ == "__main__":
    """Test the explanation generator with sample data"""
    import sys
    from pathlib import Path
    
    # Add parent directory to path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    
    from shared.interfaces import CandidateProfile, ProjectDescription
    
    # Create sample team
    team = [
        CandidateProfile(
            id="1",
            name="John Doe",
            skills=["Python", "Django", "PostgreSQL"],
            skill_levels={"Python": "Expert", "Django": "Advanced"},
            role="Backend Developer",
            experience_years=5,
            collaboration_style="Agile, mentoring",
            availability_hours=40,
            tools=["Git", "Docker"],
            domains=[]
        ),
        CandidateProfile(
            id="2",
            name="Jane Smith",
            skills=["React", "JavaScript", "Figma"],
            skill_levels={"React": "Expert", "Figma": "Advanced"},
            role="Frontend Developer",
            experience_years=3,
            collaboration_style="Creative, communicative",
            availability_hours=35,
            tools=["VS Code", "Git"],
            domains=[]
        )
    ]
    
    # Create sample project
    project = ProjectDescription(
        id="p1",
        title="Web Application Development",
        description="Build a modern web application with frontend and backend components",
        required_roles=["Backend Developer", "Frontend Developer"],
        required_skills=["Python", "Django", "React", "JavaScript"],
        team_size=2,
        duration_weeks=8,
        priority_skills=["Python", "React"]
    )
    
    # Generate explanation
    explanations = generate_explanations([team], project)
    
    print("Generated Explanation:")
    print("=" * 50)
    print(explanations[0]["explanation"])
    print("=" * 50)
