# src/modules/__init__.py
"""
SkillSync Modules - Consolidated Interface
"""
from .candidate_embeddings import embed_candidates, get_candidate_similarity
from .project_embeddings import embed_project, get_project_similarities
from .team_builder import build_teams, build_greedy_team, TeamBuilderConfig
from .json_extraction import extract_candidates, extract_project_requirements, ExtractorConfig
from .EXPLANATION import generate_team_report, explain_team, ExplanationConfig

__all__ = [
    # Candidate Embeddings
    "embed_candidates",
    "get_candidate_similarity",
    
    # Project Embeddings
    "embed_project",
    "get_project_similarities",
    
    # Team Builder
    "build_teams",
    "build_greedy_team",
    "TeamBuilderConfig",
    
    # JSON Extraction
    "extract_candidates",
    "extract_project_requirements",
    "ExtractorConfig",
    
    # Explanation
    "generate_team_report",
    "explain_team",
    "ExplanationConfig",
]