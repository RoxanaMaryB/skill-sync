import sys
from pathlib import Path
import json
from typing import List, Dict
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(ROOT / "src"))

from shared.interfaces import CandidateProfile, ProjectDescription
from modules.team_builder.builder import build_teams


def load_profiles() -> List[CandidateProfile]:
    raw = json.loads((ROOT / "data/candidate_profiles.json").read_text(encoding="utf-8"))
    profiles: List[CandidateProfile] = []

    for x in raw:
        technical = x.get("technical", {}) if isinstance(x, dict) else {}
        metadata = x.get("metadata", {}) if isinstance(x, dict) else {}
        constraints = x.get("constraints", {}) if isinstance(x, dict) else {}
        collaboration = x.get("collaboration", {}) if isinstance(x, dict) else {}

        skills = technical.get("skills", []) or []
        tools = technical.get("tools", []) or []

        # availability can be "10–20" or "Unknown"
        avail_raw = constraints.get("weekly_availability_hours", "Unknown")
        availability_hours = 0
        if isinstance(avail_raw, (int, float)):
            availability_hours = int(avail_raw)
        else:
            s = str(avail_raw)
            digits = "".join([c if c.isdigit() or c == " " else " " for c in s]).split()
            if digits:
                availability_hours = int(digits[0])

        exp_raw = metadata.get("work_experience_years", 0)
        try:
            experience_years = int(float(exp_raw))
        except Exception:
            experience_years = 0

        profiles.append(
            CandidateProfile(
                id=str(x.get("id", "Unknown")),
                name=str(x.get("name", "Unknown")),
                skills=list(skills),
                skill_levels={},
                role=str(metadata.get("dev_type", "Unknown")),
                experience_years=experience_years,
                collaboration_style=str(collaboration.get("communication_style", "Unknown")),
                availability_hours=availability_hours,
                tools=list(tools),
                domains=[],
            )
        )

    return profiles


def load_candidate_dissimilarity_and_ids():
    """
    From candidate_embeddings module artifacts:
      data/artifacts/candidate_dissimilarity.npy  (NxN)
      data/artifacts/candidate_ids.json           (length N)
    """
    dissim = np.load(ROOT / "data/artifacts/candidate_dissimilarity.npy") 
    candidate_ids = json.loads((ROOT / "data/artifacts/candidate_ids.json").read_text(encoding="utf-8"))
    return dissim, candidate_ids


def load_candidate_project_similarities(project_index: int = 0) -> Dict[str, float]:
    """
    From store_similarity.py payload:
    {
      candidate_ids: [...],
      project_ids: [...],
      similarity_matrix: [[...], ...]  # candidates x projects
    }
    Returns dict: candidate_id -> similarity_for_selected_project
    """
    payload = json.loads((ROOT / "data/artifacts/candidate_project_similarity.json").read_text(encoding="utf-8"))
    candidate_ids = payload["candidate_ids"]
    project_ids = payload["project_ids"]
    M = np.array(payload["similarity_matrix"], dtype=float)  # shape (C, P)

    if project_index < 0 or project_index >= M.shape[1]:
        raise ValueError(f"project_index {project_index} out of range. Matrix has {M.shape[1]} projects.")

    sims = {str(cid): float(M[i, project_index]) for i, cid in enumerate(candidate_ids)}
    return sims, project_ids[project_index]


def dissimilarity_to_similarity(dissim: np.ndarray) -> np.ndarray:
    # TeamBuilder expects similarity matrix; your artifacts are dissimilarity.
    sim = 1.0 - dissim
    sim[sim < 0.0] = 0.0
    return sim


def main():
    print("=== SkillSync: Local test for builder1 (fixed) ===")

    profiles = load_profiles()
    print(f"Loaded profiles: {len(profiles)}")

    # diversity inputs (from artifacts)
    dissim, cand_ids_from_artifacts = load_candidate_dissimilarity_and_ids()
    candidate_sim_matrix = dissimilarity_to_similarity(dissim)

    # fit inputs (from candidate_project_similarity payload)
    project_similarities, chosen_project_id = load_candidate_project_similarities(project_index=0)
    print(f"Loaded project fit for project_id={chosen_project_id}. Num scores: {len(project_similarities)}")

    # IMPORTANT: candidate_ids order must match similarity matrix order
    candidate_ids = [str(x) for x in cand_ids_from_artifacts]

    # Build a matching ProjectDescription (sample projects file used by M2)
    sample_projects = json.loads((ROOT / "data/sample/sample_projects.json").read_text(encoding="utf-8"))
    p0 = sample_projects[0]  # because we used project_index=0 above
    project = ProjectDescription(
        id=str(p0["id"]),
        title=str(p0["title"]),
        description=str(p0["description"]),
        required_roles=list(p0.get("required_roles", [])),
        required_skills=list(p0.get("required_skills", [])),
        team_size=int(p0.get("team_size", 4)),
        duration_weeks=int(p0.get("duration_weeks", 8)),
        priority_skills=list(p0.get("priority_skills", [])),
    )

    teams = build_teams(
        profiles=profiles,
        project=project,
        candidate_sim_matrix=candidate_sim_matrix,
        candidate_ids=candidate_ids,
        project_similarities=project_similarities,
    )

    print(f"\nBuilt teams: {len(teams)}")
    for i, team in enumerate(teams, 1):
        print(f"\nTeam {i} (size={len(team)}):")
        for m in team:
            fit = project_similarities.get(m.id, 0.0)
            print(f"- {m.id} | {m.name} | role={m.role} | fit={fit:.3f} | skills={m.skills[:6]}")

    out = [
        [{"id": m.id, "name": m.name, "role": m.role, "skills": m.skills} for m in team]
        for team in teams
    ]
    (ROOT / "data/teams_debug.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\nSaved -> data/teams_debug.json")


if __name__ == "__main__":
    main()