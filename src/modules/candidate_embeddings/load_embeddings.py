from storage import load_embeddings

embeddings, candidate_ids = load_embeddings()

print(f"Loaded {len(candidate_ids)} candidate embeddings.")