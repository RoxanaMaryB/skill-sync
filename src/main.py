from pathlib import Path
from modules.candidate_embeddings.embedding_service import (
    generate_embeddings_and_dissimilarity
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


if __name__ == "__main__":
    profile_path = PROJECT_ROOT / "data" / "candidate_profiles_with_evidence.json"

    result = generate_embeddings_and_dissimilarity(profile_path)
    print(result)
