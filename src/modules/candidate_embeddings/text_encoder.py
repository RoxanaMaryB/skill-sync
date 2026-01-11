from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("all-MiniLM-L6-v2")

def profile_to_text(profile: dict) -> str:
    # Extracting data from nested dictionaries
    tech = profile.get("technical", {})
    meta = profile.get("metadata", {})
    collab = profile.get("collaboration", {})

    # Formatting lists into strings
    skills = ", ".join(tech.get("skills", []))
    tools = ", ".join(tech.get("tools", []))

    return (
        f"{meta.get('dev_type')} with {meta.get('work_experience_years')} years "
        f"in {meta.get('industry')}. "
        f"Skills: {skills}. "
        f"Tools: {tools}. "
        f"Belbin role: {profile.get('personality', {}).get('Belbin_team_role')}. "
        f"Communication style: {collab.get('communication_style')}. "
        f"Availability: {profile.get('constraints', {}).get('weekly_availability_hours')} hours/week."
    )

def embed_profiles(profiles: list[dict]):
    texts = [profile_to_text(p) for p in profiles]
    return _model.encode(texts, normalize_embeddings=True)
