# src/modules/candidate_embeddings/__init__.py
"""
Consolidated Candidate Embeddings Module (M1)
Provides: embed_candidates(), get_candidate_similarity()
"""
import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️ sentence-transformers not available, using mock embeddings")

class CandidateEmbeddings:
    """Unified candidate embeddings service"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.project_root = Path(__file__).resolve().parents[3]
        self.artifact_dir = self.project_root / "data" / "artifacts"
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception as e:
                print(f"⚠️ Failed to load sentence transformer: {e}")
                self.model = None
    
    def profile_to_text(self, profile: Dict[str, Any]) -> str:
        """Convert profile to text for embedding"""
        tech = profile.get("technical", {}) or {}
        meta = profile.get("metadata", {}) or {}
        collab = profile.get("collaboration", {}) or {}
        
        def clean_str(v):
            if v is None:
                return ""
            return str(v).strip()
        
        def clean_list(values):
            if not values:
                return []
            out = []
            seen = set()
            for v in values:
                if v is None:
                    continue
                s = str(v).strip()
                if not s:
                    continue
                key = s.lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(s)
            return sorted(out, key=lambda x: x.lower())
        
        skills = clean_list(tech.get("skills", []))
        tools = clean_list(tech.get("tools", []))
        dev_type = clean_str(meta.get("dev_type"))
        comms = clean_str(collab.get("communication_style"))
        
        parts = []
        if dev_type:
            parts.append(f"Developer type: {dev_type}")
        if skills:
            parts.append("Skills: " + ", ".join(skills))
        if tools:
            parts.append("Tools: " + ", ".join(tools))
        if comms:
            parts.append(f"Communication style: {comms}")
        
        return ". ".join(parts) + "." if parts else "Candidate profile: Unknown."
    
    def embed_candidates(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate embeddings for candidate profiles"""
        if not profiles:
            return {"embeddings": None, "candidate_ids": [], "similarity_matrix": None}
        
        candidate_ids = [p.get("id", f"candidate_{i}") for i, p in enumerate(profiles)]
        
        if self.model and SENTENCE_TRANSFORMERS_AVAILABLE:
            # Use real embeddings
            texts = [self.profile_to_text(p) for p in profiles]
            embeddings = self.model.encode(texts, normalize_embeddings=True)
            
            # Calculate similarity matrix
            similarity = cosine_similarity(embeddings)
            np.fill_diagonal(similarity, 1.0)
            
            # Save to artifacts
            np.save(self.artifact_dir / "candidate_embeddings.npy", embeddings)
            with open(self.artifact_dir / "candidate_ids.json", "w") as f:
                json.dump(candidate_ids, f)
            np.save(self.artifact_dir / "candidate_similarity.npy", similarity)
            
        else:
            # Generate mock embeddings
            n = len(profiles)
            embeddings = np.random.randn(n, 384)
            similarity = np.random.rand(n, n) * 0.4 + 0.3
            np.fill_diagonal(similarity, 1.0)
            similarity = (similarity + similarity.T) / 2
        
        return {
            "embeddings": embeddings if 'embeddings' in locals() else None,
            "candidate_ids": candidate_ids,
            "similarity_matrix": similarity,
            "dissimilarity_matrix": 1 - similarity if 'similarity' in locals() else None
        }
    
    def get_candidate_similarity(self) -> Tuple[Optional[np.ndarray], Optional[List[str]]]:
        """Load existing candidate similarity matrix"""
        emb_path = self.artifact_dir / "candidate_embeddings.npy"
        ids_path = self.artifact_dir / "candidate_ids.json"
        sim_path = self.artifact_dir / "candidate_similarity.npy"
        
        if emb_path.exists() and ids_path.exists():
            embeddings = np.load(emb_path)
            with open(ids_path, "r") as f:
                candidate_ids = json.load(f)
            
            if sim_path.exists():
                similarity = np.load(sim_path)
            else:
                similarity = cosine_similarity(embeddings)
                np.save(sim_path, similarity)
            
            return similarity, candidate_ids
        
        return None, None

# Singleton instance
embeddings_service = CandidateEmbeddings()

# Public API
def embed_candidates(profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate embeddings for candidate profiles"""
    return embeddings_service.embed_candidates(profiles)

def get_candidate_similarity() -> Tuple[Optional[np.ndarray], Optional[List[str]]]:
    """Get existing candidate similarity matrix"""
    return embeddings_service.get_candidate_similarity()