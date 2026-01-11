from sentence_transformers import SentenceTransformer

def project_to_text(project):
    description = project.get("description", "")
    required_roles = project.get("required_roles", [])
    required_skills = project.get("required_skills", [])
    priority_skills = project.get("priority_skills", [])
    team_size = project.get("team_size", "")
    duration = project.get("duration_weeks", "")

    return (
        f"Project description: {description}. "
        f"Required roles: {', '.join(required_roles)}. "
        f"Required skills: {', '.join(required_skills)}. "
        f"Priority skills: {', '.join(priority_skills)}. "
        f"Team size: {team_size}. "
        f"Duration: {duration} weeks."
    )

_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_projects(projects):
    texts = [project_to_text(p) for p in projects]
    embeddings = _model.encode(texts, normalize_embeddings=True)
    return embeddings