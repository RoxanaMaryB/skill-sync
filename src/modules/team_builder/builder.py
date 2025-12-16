
"""
Team Construction Module (M3 - Ana)
"""

import numpy as np
from typing import List, Dict, Any
import logging
from shared.interfaces import CandidateProfile, ProjectDescription

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TeamBuilder:
    """Greedy algorithm for team formation"""
    
    def __init__(self, alpha: float = 0.5, beta: float = 0.3, gamma: float = 0.2):
        """
        Initialize team builder with weights.
        
        Args:
            alpha: Weight for candidate-project fit
            beta: Weight for diversity (1 - similarity)
            gamma: Weight for skill coverage
        """
        self.alpha = alpha  # Fit weight
        self.beta = beta    # Diversity weight  
        self.gamma = gamma  # Coverage weight
        
    def calculate_skill_coverage(self, team: List[CandidateProfile], 
                               required_skills: List[str]) -> float:
        """
        Calculate what percentage of required skills are covered by the team.
        
        Args:
            team: List of candidate profiles
            required_skills: List of skills required for the project
            
        Returns:
            Coverage score between 0 and 1
        """
        if not required_skills:
            return 1.0
            
        # Get all unique skills from team members
        team_skills = set()
        for member in team:
            team_skills.update(member.skills)
        
        # Calculate coverage
        covered_skills = set(required_skills) & team_skills
        coverage = len(covered_skills) / len(required_skills)
        
        return coverage
    
    def calculate_team_diversity(self, team: List[CandidateProfile],
                               candidate_sim_matrix: np.array,
                               candidate_ids: List[str]) -> float:
        """
        Calculate diversity score for a team (1 - average similarity).
        
        Args:
            team: List of candidate profiles
            candidate_sim_matrix: Precomputed similarity matrix
            candidate_ids: List of candidate IDs in order of matrix
            
        Returns:
            Diversity score between 0 and 1 (higher = more diverse)
        """
        if len(team) <= 1:
            return 1.0
            
        # Get indices of team members in similarity matrix
        team_indices = []
        for member in team:
            if member.id in candidate_ids:
                idx = candidate_ids.index(member.id)
                team_indices.append(idx)
        
        if len(team_indices) <= 1:
            return 1.0
            
        # Calculate average similarity between team members
        total_similarity = 0
        count = 0
        
        for i in range(len(team_indices)):
            for j in range(i + 1, len(team_indices)):
                idx_i = team_indices[i]
                idx_j = team_indices[j]
                total_similarity += candidate_sim_matrix[idx_i, idx_j]
                count += 1
        
        if count == 0:
            return 1.0
            
        avg_similarity = total_similarity / count
        
        # Diversity is inverse of similarity
        diversity = 1 - avg_similarity
        
        return max(0, min(1, diversity))
    
    def calculate_team_fit(self, team: List[CandidateProfile],
                         project_similarities: Dict[str, float]) -> float:
        """
        Calculate average project fit for team members.
        
        Args:
            team: List of candidate profiles
            project_similarities: Dictionary of candidate_id -> similarity score
            
        Returns:
            Average fit score between 0 and 1
        """
        if not team:
            return 0.0
            
        total_fit = 0
        count = 0
        
        for member in team:
            if member.id in project_similarities:
                total_fit += project_similarities[member.id]
                count += 1
        
        if count == 0:
            return 0.0
            
        return total_fit / count
    
    def calculate_team_score(self, team: List[CandidateProfile],
                           candidate_sim_matrix: np.array,
                           candidate_ids: List[str],
                           project_similarities: Dict[str, float],
                           required_skills: List[str]) -> float:
        """
        Calculate overall team score using weighted combination.
        
        Args:
            team: List of candidate profiles
            candidate_sim_matrix: Precomputed similarity matrix
            candidate_ids: List of candidate IDs in order of matrix
            project_similarities: Dictionary of candidate_id -> similarity
            required_skills: List of required skills for project
            
        Returns:
            Overall team score
        """
        # Calculate individual components
        coverage = self.calculate_skill_coverage(team, required_skills)
        diversity = self.calculate_team_diversity(team, candidate_sim_matrix, candidate_ids)
        fit = self.calculate_team_fit(team, project_similarities)
        
        # Weighted combination
        score = (self.alpha * fit + 
                self.beta * diversity + 
                self.gamma * coverage)
        
        return score
    
    def build_team_greedy(self,
                         profiles: List[CandidateProfile],
                         project: ProjectDescription,
                         candidate_sim_matrix: np.array,
                         candidate_ids: List[str],
                         project_similarities: Dict[str, float]) -> List[CandidateProfile]:
        """
        Build a team using greedy algorithm.
        
        Args:
            profiles: List of all candidate profiles
            project: Project description
            candidate_sim_matrix: Precomputed similarity matrix
            candidate_ids: List of candidate IDs in order of matrix
            project_similarities: Dictionary of candidate_id -> similarity
            
        Returns:
            List of selected team members
        """
        logger.info(f"Building team of size {project.team_size}")
        
        # Filter out candidates with very low project similarity
        filtered_profiles = []
        for profile in profiles:
            if profile.id in project_similarities and project_similarities[profile.id] > 0.3:
                filtered_profiles.append(profile)
        
        if not filtered_profiles:
            filtered_profiles = profiles[:project.team_size]
            logger.warning("No candidates passed similarity filter, using first few")
        
        # Start with candidate with highest project fit
        sorted_by_fit = sorted(filtered_profiles, 
                             key=lambda p: project_similarities.get(p.id, 0), 
                             reverse=True)
        
        if not sorted_by_fit:
            return []
        
        team = [sorted_by_fit[0]]
        remaining = [p for p in filtered_profiles if p.id != sorted_by_fit[0].id]
        
        # Greedily add candidates until team size reached
        while len(team) < project.team_size and remaining:
            best_candidate = None
            best_score = -1
            
            for candidate in remaining:
                # Try adding this candidate
                potential_team = team + [candidate]
                
                # Calculate score for this potential team
                score = self.calculate_team_score(
                    potential_team,
                    candidate_sim_matrix,
                    candidate_ids,
                    project_similarities,
                    project.required_skills
                )
                
                if score > best_score:
                    best_score = score
                    best_candidate = candidate
            
            if best_candidate:
                team.append(best_candidate)
                remaining.remove(best_candidate)
            else:
                break
        
        logger.info(f"Team built with {len(team)} members. Score: {best_score:.3f}")
        return team

# Interface function
def build_teams(
    profiles: List[CandidateProfile],
    project: ProjectDescription,
    candidate_sim_matrix: np.array,
    candidate_ids: List[str],
    project_similarities: Dict[str, float]
) -> List[List[CandidateProfile]]:
    """
    Interface function for M3 module.
    
    Args:
        profiles: List of candidate profiles
        project: Project description
        candidate_sim_matrix: Precomputed similarity matrix
        candidate_ids: List of candidate IDs in order of matrix
        project_similarities: Dictionary of candidate_id -> similarity score
        
    Returns:
        List of teams (each team is list of CandidateProfile objects)
    """
    builder = TeamBuilder()
    
    # For now, return one team - can be extended to multiple teams
    team = builder.build_team_greedy(
        profiles, project, candidate_sim_matrix, candidate_ids, project_similarities
    )
    
    return [team] if team else []

if __name__ == "__main__":
    """Test the team builder with sample data"""
    # Create mock data for testing
    profiles = [
        CandidateProfile(
            id="1",
            name="Alice",
            skills=["Python", "ML"],
            skill_levels={"Python": "Advanced", "ML": "Intermediate"},
            role="Data Scientist",
            experience_years=3,
            collaboration_style="Analytical",
            availability_hours=40,
            tools=[],
            domains=[]
        ),
        CandidateProfile(
            id="2",
            name="Bob",
            skills=["React", "JavaScript"],
            skill_levels={"React": "Expert", "JavaScript": "Advanced"},
            role="Frontend Developer",
            experience_years=2,
            collaboration_style="Creative",
            availability_hours=35,
            tools=[],
            domains=[]
        )
    ]
    
    project = ProjectDescription(
        id="p1",
        title="Test Project",
        description="A test project",
        required_roles=["Data Scientist", "Frontend Developer"],
        required_skills=["Python", "React"],
        team_size=2,
        duration_weeks=4,
        priority_skills=[]
    )
    
    # Mock similarity data
    candidate_sim_matrix = np.array([[1.0, 0.2], [0.2, 1.0]])
    candidate_ids = ["1", "2"]
    project_similarities = {"1": 0.8, "2": 0.9}
    
    # Build team
    teams = build_teams(profiles, project, candidate_sim_matrix, candidate_ids, project_similarities)
    
    print(f"Built {len(teams)} team(s)")
    for i, team in enumerate(teams):
        print(f"Team {i+1} members: {[member.name for member in team]}")
