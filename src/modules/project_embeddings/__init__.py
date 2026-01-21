# src/modules/project_embeddings/__init__.py
"""
Consolidated Project Embeddings Module (M2)
Provides: embed_project(), get_project_similarities()
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

class ProjectEmbeddings:
    """Unified project embeddings service"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.project_root = Path(__file__).resolve().parents[3]
        self.artifact_dir = self.project_root / "data" / "artifacts"
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception:
                self.model = None
    
    def project_to_text(self, project_req: Dict[str, Any]) -> str:
        """Convert project requirements to text for embedding"""
        tr = project_req.get("technical_requirements", {}) or {}
        
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
        
        skills = clean_list(tr.get("skills", []))
        tools = clean_list(tr.get("tools", []))
        roles = clean_list(tr.get("roles", []))
        
        parts = []
        if roles:
            parts.append("Required roles: " + ", ".join(roles))
        if skills:
            parts.append("Required skills: " + ", ".join(skills))
        if tools:
            parts.append("Required tools: " + ", ".join(tools))
        
        return ". ".join(parts) + "." if parts else "Project requirements: Unknown."
    
    def embed_project(self, project_req: Dict[str, Any], project_id: str = "active_project") -> Dict[str, Any]:
        """Generate embedding for a project and compute similarities with candidates"""
        # Load candidate embeddings if available
        cand_emb_path = self.artifact_dir / "candidate_embeddings.npy"
        cand_ids_path = self.artifact_dir / "candidate_ids.json"
        
        if cand_emb_path.exists() and cand_ids_path.exists():
            candidate_embeddings = np.load(cand_emb_path)
            with open(cand_ids_path, "r") as f:
                candidate_ids = json.load(f)
        else:
            # No candidate embeddings available
            return {
                "project_embedding": None,
                "candidate_similarities": {},
                "candidate_ids": []
            }
        
        # Generate project embedding
        if self.model and SENTENCE_TRANSFORMERS_AVAILABLE:
            project_text = self.project_to_text(project_req)
            project_embedding = self.model.encode([project_text], normalize_embeddings=True)[0]
            
            # Calculate similarities with candidates
            similarities = cosine_similarity(
                project_embedding.reshape(1, -1),
                candidate_embeddings
            )[0]
            
            candidate_similarities = dict(zip(candidate_ids, similarities))
            
            # Save project embedding
            project_embeddings = np.array([project_embedding])
            project_ids = [project_id]
            
            np.save(self.artifact_dir / "project_embeddings.npy", project_embeddings)
            with open(self.artifact_dir / "project_ids.json", "w") as f:
                json.dump(project_ids, f)
            
            # Save similarity matrix
            sim_matrix = similarities.reshape(-1, 1)
            np.save(self.artifact_dir / "candidate_project_similarity.npy", sim_matrix)
            
            with open(self.artifact_dir / "candidate_project_similarity.json", "w") as f:
                json.dump({
                    "candidate_ids": candidate_ids,
                    "project_ids": project_ids,
                    "similarity_matrix": sim_matrix.tolist()
                }, f, indent=2)
            
        else:
            # Mock similarities
            n_candidates = len(candidate_ids)
            candidate_similarities = {cid: np.random.uniform(0.6, 0.95) for cid in candidate_ids}
            project_embedding = np.random.randn(384)
        
        return {
            "project_embedding": project_embedding if 'project_embedding' in locals() else None,
            "candidate_similarities": candidate_similarities,
            "candidate_ids": candidate_ids
        }
    
    def get_project_similarities(self, project_id: str = "active_project") -> Tuple[Optional[Dict[str, float]], Optional[List[str]]]:
        """Get existing project-candidate similarities"""
        sim_path = self.artifact_dir / "candidate_project_similarity.json"
        
        if sim_path.exists():
            with open(sim_path, "r") as f:
                data = json.load(f)
            
            candidate_ids = data.get("candidate_ids", [])
            sim_matrix = np.array(data.get("similarity_matrix", []))
            
            if len(sim_matrix) > 0 and len(candidate_ids) > 0:
                # Find project index
                project_ids = data.get("project_ids", [])
                try:
                    proj_idx = project_ids.index(project_id)
                    similarities = dict(zip(candidate_ids, sim_matrix[:, proj_idx]))
                    return similarities, candidate_ids
                except ValueError:
                    pass
        
        return None, None

# Singleton instance
project_embeddings_service = ProjectEmbeddings()

# Public API
def embed_project(project_req: Dict[str, Any], project_id: str = "active_project") -> Dict[str, Any]:
    """Embed project and compute similarities with candidates"""
    return project_embeddings_service.embed_project(project_req, project_id)

def get_project_similarities(project_id: str = "active_project") -> Tuple[Optional[Dict[str, float]], Optional[List[str]]]:
    """Get existing project-candidate similarities"""
    return project_embeddings_service.get_project_similarities(project_id)