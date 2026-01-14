from pathlib import Path
from .utils import load_projects
from .embeddings import embed_projects
from .store_embeddings import save_project_embeddings
from .compute_similarity import compute_store_similarity

def gen_poj_emb_sim(projects_path: Path):


    projects = load_projects(projects_path)

    embeddings = embed_projects(projects)

    project_ids = [p["id"] for p in projects]

    save_project_embeddings(embeddings, project_ids)    
    print("Project embeddings and similarity matrix generated and saved successfully.")

    compute_store_similarity()