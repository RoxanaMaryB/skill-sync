# src/modules/team_builder/__init__.py
"""
Consolidated Team Builder Module (M3)
Provides: build_teams(), build_greedy_team()
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class TeamBuilderConfig:
    """Configuration for team building algorithm"""
    alpha: float = 0.55      # Fit weight
    beta: float = 0.25       # Diversity weight
    gamma: float = 0.20      # Coverage weight
    team_size: int = 4
    n_teams: int = 1
    min_fit: float = 0.0

class TeamBuilder:
    """Unified team building service with multiple algorithms"""
    
    def __init__(self, config: Optional[TeamBuilderConfig] = None):
        self.config = config or TeamBuilderConfig()
    
    @staticmethod
    def _norm_skill(s: str) -> str:
        return (s or "").strip().lower()
    
    @staticmethod
    def _team_skill_set(team: List[Dict[str, Any]]) -> set:
        s = set()
        for m in team:
            tech = m.get("technical", {})
            skills = tech.get("skills", [])
            s.update([TeamBuilder._norm_skill(x) for x in skills if x])
        return s
    
    @staticmethod
    def _candidate_skill_set(candidate: Dict[str, Any]) -> set:
        tech = candidate.get("technical", {})
        skills = tech.get("skills", [])
        return set([TeamBuilder._norm_skill(x) for x in skills if x])
    
    @staticmethod
    def coverage_gain(team: List[Dict[str, Any]], candidate: Dict[str, Any], required_skills: List[str]) -> float:
        """Marginal gain in required skill coverage"""
        req = {TeamBuilder._norm_skill(x) for x in (required_skills or []) if x}
        if not req:
            return 0.0
        
        team_sk = TeamBuilder._team_skill_set(team)
        cand_sk = TeamBuilder._candidate_skill_set(candidate)
        
        before = len(req & team_sk)
        after = len(req & (team_sk | cand_sk))
        return (after - before) / max(1, len(req))
    
    @staticmethod
    def avg_dissimilarity_to_team(candidate_id: str, team: List[Dict[str, Any]], 
                                 dissim_matrix: np.ndarray, id_to_idx: Dict[str, int]) -> float:
        """Average dissimilarity between candidate and team members"""
        if not team or candidate_id not in id_to_idx:
            return 0.0
        
        ci = id_to_idx[candidate_id]
        vals = [
            float(dissim_matrix[ci, id_to_idx[m["id"]]])
            for m in team
            if m["id"] in id_to_idx
        ]
        return float(sum(vals) / len(vals)) if vals else 0.0
    
    def score_candidate(self, team: List[Dict[str, Any]], candidate: Dict[str, Any],
                       project: Dict[str, Any], dissim_matrix: np.ndarray,
                       id_to_idx: Dict[str, int], project_similarities: Dict[str, float]) -> float:
        """Score a candidate for team inclusion"""
        fit = project_similarities.get(candidate["id"], 0.0)
        coverage = self.coverage_gain(team, candidate, project.get("required_skills", []))
        diversity = self.avg_dissimilarity_to_team(candidate["id"], team, dissim_matrix, id_to_idx)
        
        return (self.config.alpha * fit) + (self.config.gamma * coverage) + (self.config.beta * diversity)
    
    def build_greedy_team(self, profiles: List[Dict[str, Any]], project: Dict[str, Any],
                         candidate_dissim_matrix: np.ndarray, candidate_ids: List[str],
                         project_similarities: Dict[str, float]) -> List[Dict[str, Any]]:
        """Build a single team using greedy algorithm"""
        id_to_idx = {cid: i for i, cid in enumerate(candidate_ids)}
        
        # Filter by minimum fit
        filtered = [p for p in profiles if project_similarities.get(p["id"], 0.0) >= self.config.min_fit]
        if not filtered:
            filtered = profiles
        
        # Sort by fit
        filtered.sort(key=lambda p: project_similarities.get(p["id"], 0.0), reverse=True)
        
        team = [filtered[0]] if filtered else []
        remaining = filtered[1:] if len(filtered) > 1 else []
        
        while len(team) < self.config.team_size and remaining:
            scored = []
            for cand in remaining:
                score = self.score_candidate(team, cand, project, candidate_dissim_matrix, 
                                           id_to_idx, project_similarities)
                scored.append((score, cand))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            chosen = scored[0][1]
            
            team.append(chosen)
            remaining = [c for c in remaining if c["id"] != chosen["id"]]
        
        return team
    
    def build_multiple_teams(self, profiles: List[Dict[str, Any]], project: Dict[str, Any],
                           candidate_dissim_matrix: np.ndarray, candidate_ids: List[str],
                           project_similarities: Dict[str, float]) -> List[List[Dict[str, Any]]]:
        """Build multiple teams using round-robin assignment"""
        teams = [[] for _ in range(self.config.n_teams)]
        remaining_profiles = profiles.copy()
        
        for round_num in range(self.config.team_size):
            for team_idx in range(self.config.n_teams):
                if not remaining_profiles:
                    break
                
                # Score remaining candidates for this team
                scored = []
                for cand in remaining_profiles:
                    score = self.score_candidate(teams[team_idx], cand, project, 
                                               candidate_dissim_matrix, {}, project_similarities)
                    scored.append((score, cand))
                
                scored.sort(key=lambda x: x[0], reverse=True)
                if scored:
                    chosen = scored[0][1]
                    teams[team_idx].append(chosen)
                    remaining_profiles = [p for p in remaining_profiles if p["id"] != chosen["id"]]
        
        # Filter out incomplete teams
        return [team for team in teams if len(team) == self.config.team_size]
    
    def build_teams(self, profiles: List[Dict[str, Any]], project: Dict[str, Any],
                   candidate_dissim_matrix: Optional[np.ndarray] = None,
                   candidate_ids: Optional[List[str]] = None,
                   project_similarities: Optional[Dict[str, float]] = None) -> List[List[Dict[str, Any]]]:
        """Main team building interface"""
        # Default values
        if candidate_dissim_matrix is None:
            n = len(profiles)
            candidate_dissim_matrix = np.ones((n, n))
            np.fill_diagonal(candidate_dissim_matrix, 0)
        
        if candidate_ids is None:
            candidate_ids = [p["id"] for p in profiles]
        
        if project_similarities is None:
            project_similarities = {p["id"]: 0.8 for p in profiles}
        
        if self.config.n_teams == 1:
            team = self.build_greedy_team(profiles, project, candidate_dissim_matrix,
                                        candidate_ids, project_similarities)
            return [team] if team else []
        else:
            return self.build_multiple_teams(profiles, project, candidate_dissim_matrix,
                                           candidate_ids, project_similarities)

# Public API functions
def build_teams(profiles: List[Dict[str, Any]], 
                project: Dict[str, Any],
                config: Optional[TeamBuilderConfig] = None,
                **kwargs) -> List[List[Dict[str, Any]]]:
    """Build teams based on profiles and project requirements"""
    builder = TeamBuilder(config)
    return builder.build_teams(profiles, project, **kwargs)

def build_greedy_team(profiles: List[Dict[str, Any]],
                     project: Dict[str, Any],
                     candidate_dissim_matrix: np.ndarray,
                     candidate_ids: List[str],
                     project_similarities: Dict[str, float],
                     alpha: float = 0.55,
                     beta: float = 0.25,
                     gamma: float = 0.20) -> List[Dict[str, Any]]:
    """Build a single team using greedy algorithm"""
    config = TeamBuilderConfig(alpha=alpha, beta=beta, gamma=gamma, team_size=project.get("team_size", 4))
    builder = TeamBuilder(config)
    return builder.build_greedy_team(profiles, project, candidate_dissim_matrix,
                                   candidate_ids, project_similarities)