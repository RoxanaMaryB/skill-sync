
"""
Candidate Embeddings Module (M1 - Shahzad)
"""

import numpy as np
from typing import List, Dict, Any
import json
from pathlib import Path
import logging
from sentence_transformers import SentenceTransformer
import faiss

from shared.interfaces import CandidateProfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CandidateEmbedder:
    """Generates embeddings for candidate profiles"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedder.
        
        Args:
            model_name: Name of sentence transformer model
        """
        logger.info(f"Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.candidate_ids = []
        
    def profile_to_text(self, profile: CandidateProfile) -> str:
        """
        Convert candidate profile to canonical text for embedding.
        
        Args:
            profile: CandidateProfile object
            
        Returns:
            Text representation of profile
        """
        # Create canonical text template
        skills_text = ", ".join([f"{skill}" for skill in profile.skills])
        tools_text = ", ".join(profile.tools) if profile.tools else ""
        
        text_parts = [
            f"Role: {profile.role}",
            f"Skills: {skills_text}",
            f"Experience: {profile.experience_years} years",
            f"Collaboration style: {profile.collaboration_style}",
            f"Availability: {profile.availability_hours} hours/week"
        ]
        
        if tools_text:
            text_parts.append(f"Tools: {tools_text}")
            
        return ". ".join(text_parts)
    
    def generate_embeddings(self, profiles: List[CandidateProfile]) -> Dict[str, Any]:
        """
        Generate embeddings for all candidates and compute similarity matrix.
        
        Args:
            profiles: List of CandidateProfile objects
            
        Returns:
            Dictionary with embeddings, similarity matrix, and candidate IDs
        """
        logger.info(f"Generating embeddings for {len(profiles)} candidates")
        
        # Convert profiles to text
        texts = [self.profile_to_text(profile) for profile in profiles]
        self.candidate_ids = [profile.id for profile in profiles]
        
        # Generate embeddings
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Create FAISS index for efficient similarity search
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings.astype('float32'))
        
        # Compute similarity matrix (cosine similarity)
        # Normalize embeddings for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized_embeddings = embeddings / norms
        similarity_matrix = np.dot(normalized_embeddings, normalized_embeddings.T)
        
        # Store embeddings in dictionary
        embedding_dict = {
            profile.id: embedding for profile, embedding in zip(profiles, embeddings)
        }
        
        result = {
            'embeddings': embedding_dict,
            'similarity_matrix': similarity_matrix,
            'candidate_ids': self.candidate_ids,
            'faiss_index': self.index,
            'normalized_embeddings': normalized_embeddings
        }
        
        logger.info(f"Embeddings generated. Dimension: {embeddings.shape}")
        return result
    
    def get_similar_candidates(self, candidate_id: str, top_k: int = 5) -> List[Dict]:
        """
        Find candidates most similar to the given candidate.
        
        Args:
            candidate_id: ID of candidate to find similar ones for
            top_k: Number of similar candidates to return
            
        Returns:
            List of similar candidates with similarity scores
        """
        if self.index is None or candidate_id not in self.embeddings:
            raise ValueError("Embeddings not generated or candidate not found")
        
        # Get candidate embedding
        candidate_idx = self.candidate_ids.index(candidate_id)
        candidate_embedding = self.normalized_embeddings[candidate_idx].reshape(1, -1)
        
        # Search for similar candidates
        distances, indices = self.index.search(candidate_embedding.astype('float32'), top_k + 1)
        
        # Convert distances to similarities (cosine similarity from L2 distance)
        # For normalized vectors: similarity = 1 - distance^2 / 2
        similarities = 1 - (distances[0] ** 2) / 2
        
        # Prepare results (skip the first one as it's the candidate itself)
        results = []
        for i in range(1, min(top_k + 1, len(indices[0]))):
            idx = indices[0][i]
            if idx < len(self.candidate_ids):
                results.append({
                    'candidate_id': self.candidate_ids[idx],
                    'similarity': float(similarities[i])
                })
        
        return results

# Interface function
def generate_candidate_embeddings(profiles: List[CandidateProfile]) -> Dict[str, Any]:
    """
    Interface function for M1 module.
    
    Args:
        profiles: List of CandidateProfile objects
        
    Returns:
        Dictionary with embeddings and similarity data
    """
    embedder = CandidateEmbedder()
    return embedder.generate_embeddings(profiles)

if __name__ == "__main__":
    """Test the embedder with sample data"""
    # Load sample data
    sample_file = Path(__file__).parent.parent.parent.parent / "data" / "sample" / "sample_profiles.json"
    with open(sample_file) as f:
        profiles_data = json.load(f)
    
    # Convert to CandidateProfile objects (simplified)
    profiles = []
    for i, data in enumerate(profiles_data[:3]):
        profile = CandidateProfile(
            id=data.get("id", str(i)),
            name=data.get("name", ""),
            skills=data.get("skills", []),
            skill_levels=data.get("skill_levels", {}),
            role=data.get("role", ""),
            experience_years=data.get("experience_years", 0),
            collaboration_style=data.get("collaboration_style", ""),
            availability_hours=data.get("availability_hours", 40),
            tools=data.get("tools", []),
            domains=data.get("domains", [])
        )
        profiles.append(profile)
    
    # Generate embeddings
    result = generate_candidate_embeddings(profiles)
    print(f"Generated embeddings for {len(profiles)} candidates")
    print(f"Similarity matrix shape: {result['similarity_matrix'].shape}")
    print(f"Sample similarity between first two: {result['similarity_matrix'][0, 1]:.3f}")
