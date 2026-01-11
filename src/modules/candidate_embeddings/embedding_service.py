from pathlib import Path
from .utils import load_profiles
from .text_encoder import embed_profiles
from .similarity import cosine_dissimilarity_matrix
from .repository import (
    save_embeddings,
    save_dissimilarity
)

def generate_embeddings_and_dissimilarity(profile_path: Path) -> dict:
    profiles = load_profiles(profile_path)

    embeddings = embed_profiles(profiles)
    candidate_ids = [p["id"] for p in profiles]

    save_embeddings(embeddings, candidate_ids)

    dissimilarity = cosine_dissimilarity_matrix(embeddings)
    save_dissimilarity(dissimilarity)

    return {
        "num_candidates": len(candidate_ids),
        "artifacts": [
            "candidate_embeddings.npy",
            "candidate_dissimilarity.npy",
            "candidate_ids.json"
        ]
    }