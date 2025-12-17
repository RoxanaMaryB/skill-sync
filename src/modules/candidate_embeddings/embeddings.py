from sentence_transformers import SentenceTransformer

def profile_to_text(profile):
    return (
        f"Technical skills: {', '.join(profile['technical_skills'])}. "
        f"Soft skills: {', '.join(profile['soft_skills'])}. "
        f"Preferred roles: {', '.join(profile['preferred_roles'])}. "
        f"Experience: {', '.join(profile['experience_tags'])}."
    )


_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_profiles(profiles):
    texts = [profile_to_text(p) for p in profiles]
    embeddings = _model.encode(texts, normalize_embeddings=True)
    return embeddings
