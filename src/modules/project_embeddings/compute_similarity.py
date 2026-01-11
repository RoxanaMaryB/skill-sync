import os
from sklearn.metrics.pairwise import cosine_similarity

from store_similarity import save_similarity

from store_embeddings import load_candidate_embeddings, load_project_embeddings

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    data_dir = os.path.join(root_dir, "data")

    candidate_embeddings, candidate_ids = load_candidate_embeddings()

    project_embeddings, project_ids = load_project_embeddings()

    sim_matrix = cosine_similarity(candidate_embeddings, project_embeddings)

    save_similarity(sim_matrix, candidate_ids, project_ids)

    print("Candidate-project similarity matrix saved.")
    print(f"Matrix shape: {sim_matrix.shape} (candidates x projects)")


if __name__ == "__main__":
    main()
