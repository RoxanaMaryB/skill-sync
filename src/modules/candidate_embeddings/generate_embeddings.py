import os
from utils import load_profiles
from embeddings import embed_profiles
from storage import save_embeddings

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Move up 3 levels
# (src/modules/candidate_embeddings -> src/modules -> src -> root)
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

# Combine with the data path
data_path = os.path.join(root_dir, "data", "candidate_profiles.json")

profiles = load_profiles(data_path)

embeddings = embed_profiles(profiles)

candidate_ids = [p["id"] for p in profiles]

save_embeddings(embeddings, candidate_ids)

print("Candidate embeddings generated and stored.")
