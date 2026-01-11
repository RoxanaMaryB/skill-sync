import os
from utils import load_projects
from embeddings import embed_projects
from store_embeddings import save_project_embeddings

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Move up 3 levels
# (src/modules/project_embeddings -> src/modules -> src -> root)
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

# Combine with the data path
data_path = os.path.join(root_dir, "data", "sample", "sample_projects.json")

projects = load_projects(data_path)

embeddings = embed_projects(projects)

project_ids = [p["id"] for p in projects]

save_project_embeddings(embeddings, project_ids)

print("Project embeddings generated and stored.")
