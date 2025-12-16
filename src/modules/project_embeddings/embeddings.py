
"""
Project Embeddings Module (M2 - Roxana)
"""

import numpy as np
from typing import List, Dict, Any
import json
from pathlib import Path
import logging
from sentence_transformers import SentenceTransformer

from shared.interfaces import ProjectDescription, CandidateProfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectEmbedder:
    """Generates embeddings for project descriptions"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the project embedder.
        
        Args:
            model_name: Name of sentence transformer model
        """
        logger.info(f"Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
    def project_to_text(self, project: ProjectDescription) -> str:
        """
        Convert project description to canonical text for embedding.
        
        Args:
            project: ProjectDescription object
            
        Returns:
            Text representation of project
        """
        # Create canonical text template
        roles_text = ", ".join(project.required_roles)
        skills_text = ", ".join(project.required_skills)
        
        text_parts = [
            f"Project: {project.title}",
            f"Description: {project.description}",
            f"Required roles: {roles_text}",
            f"Required skills: {skills_text}",
            f"Team size: {project.team_size}",
            f"Duration: {project.duration_weeks} weeks"
        ]
        
        if project.priority_skills:
            priority_text = ", ".join(project.priority_skills)
            text_parts.append(f"Priority skills: {priority_text}")
            
        return ". ".join(text_parts)
    
    def generate_project_embedding(self, project: ProjectDescription) -> np.array:
        """
        Generate embedding for a project description.
        
        Args:
            project: ProjectDescription object
            
        Returns:
            Project embedding vector
        """
        logger.info(f"Generating embedding for project: {project.title}")
        
        # Convert project to text
        text = self.project_to_text(project)
        
        # Generate embedding
        embedding = self.model.encode(text, show_progress_bar=False)
        
        logger.info(f"Project embedding generated. Dimension: {embedding.shape}")
        return embedding
    
    def compute_candidate_project_similarities(
        self, 
        project_embedding: np.array,
        candidate_embeddings: Dict[str, np.array]
    ) -> Dict[str, float]:
        """
        Compute cosine similarity between project and all candidates.
        
        Args:
            project_embedding: Project embedding vector
            candidate_embeddings: Dictionary of candidate_id -> embedding
            
        Returns:
            Dictionary of candidate_id -> similarity score
        """
        logger.info(f"Computing candidate-project similarities for {len(candidate_embeddings)} candidates")
        
        # Normalize project embedding
        project_norm = np.linalg.norm(project_embedding)
        if project_norm == 0:
            project_normalized = project_embedding
        else:
            project_normalized = project_embedding / project_norm
        
        similarities = {}
        
        for candidate_id, candidate_embedding in candidate_embeddings.items():
            # Normalize candidate embedding
            candidate_norm = np.linalg.norm(candidate_embedding)
            if candidate_norm == 0:
                candidate_normalized = candidate_embedding
            else:
                candidate_normalized = candidate_embedding / candidate_norm
            
            # Compute cosine similarity
            similarity = float(np.dot(project_normalized, candidate_normalized))
            similarities[candidate_id] = similarity
        
        logger.info(f"Similarities computed. Range: [{min(similarities.values()):.3f}, {max(similarities.values()):.3f}]")
        return similarities
    
    def get_top_candidates(
        self, 
        similarities: Dict[str, float], 
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top-k candidates by project similarity.
        
        Args:
            similarities: Dictionary of candidate_id -> similarity
            top_k: Number of top candidates to return
            
        Returns:
            List of top candidates with scores, sorted descending
        """
        # Sort candidates by similarity
        sorted_candidates = sorted(
            similarities.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:top_k]
        
        # Format results
        results = [
            {"candidate_id": cand_id, "similarity": score}
            for cand_id, score in sorted_candidates
        ]
        
        return results

# Interface function
def generate_project_embedding(project: ProjectDescription) -> Dict[str, Any]:
    """
    Interface function for M2 module.
    
    Args:
        project: ProjectDescription object
        
    Returns:
        Dictionary with project embedding (placeholder - will be extended)
    """
    embedder = ProjectEmbedder()
    project_embedding = embedder.generate_project_embedding(project)
    
    return {
        'project_embedding': project_embedding,
        'project_id': project.id,
        'project_title': project.title
    }

if __name__ == "__main__":
    """Test the project embedder with sample data"""
    # Load sample data
    sample_file = Path(__file__).parent.parent.parent.parent / "data" / "sample" / "sample_projects.json"
    with open(sample_file) as f:
        projects_data = json.load(f)
    
    # Convert to ProjectDescription object
    project_data = projects_data[0]
    project = ProjectDescription(
        id=project_data["id"],
        title=project_data["title"],
        description=project_data["description"],
        required_roles=project_data["required_roles"],
        required_skills=project_data["required_skills"],
        team_size=project_data["team_size"],
        duration_weeks=project_data["duration_weeks"],
        priority_skills=project_data["priority_skills"]
    )
    
    # Generate project embedding
    result = generate_project_embedding(project)
    print(f"Generated embedding for project: {project.title}")
    print(f"Embedding shape: {result['project_embedding'].shape}")
