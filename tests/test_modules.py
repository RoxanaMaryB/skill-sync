# tests/test_modules.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
from src.modules.candidate_embeddings import CandidateEmbeddings
from src.modules.project_embeddings import ProjectEmbeddings
from src.modules.team_builder import TeamBuilder, TeamBuilderConfig
from src.modules.json_extraction import CandidateExtractor, ProjectExtractor

class TestCandidateEmbeddings:
    def test_profile_to_text(self):
        service = CandidateEmbeddings()
        profile = {
            "metadata": {"dev_type": "Frontend Developer"},
            "technical": {"skills": ["React", "JavaScript"], "tools": ["VS Code"]},
            "collaboration": {"communication_style": "Direct"}
        }
        text = service.profile_to_text(profile)
        assert "Frontend Developer" in text
        assert "React" in text
        assert "JavaScript" in text
    
    def test_embed_candidates_empty(self):
        service = CandidateEmbeddings()
        result = service.embed_candidates([])
        assert result["embeddings"] is None
        assert result["candidate_ids"] == []

class TestTeamBuilder:
    def setup_method(self):
        self.profiles = [
            {
                "id": "1",
                "technical": {"skills": ["Python", "SQL"]},
                "metadata": {"dev_type": "Backend"},
                "constraints": {"weekly_availability_hours": "40"}
            },
            {
                "id": "2", 
                "technical": {"skills": ["React", "JavaScript"]},
                "metadata": {"dev_type": "Frontend"},
                "constraints": {"weekly_availability_hours": "35"}
            }
        ]
        
        self.project = {
            "required_skills": ["Python", "React", "SQL"],
            "team_size": 2
        }
        
        self.config = TeamBuilderConfig()
        self.builder = TeamBuilder(self.config)
    
    def test_coverage_gain(self):
        team = [self.profiles[0]]
        candidate = self.profiles[1]
        gain = self.builder.coverage_gain(team, candidate, ["Python", "React", "SQL"])
        assert 0 <= gain <= 1.0
    
    def test_build_greedy_team(self):
        dissim_matrix = np.array([[0, 0.5], [0.5, 0]])
        candidate_ids = ["1", "2"]
        project_similarities = {"1": 0.8, "2": 0.9}
        
        team = self.builder.build_greedy_team(
            self.profiles, self.project, dissim_matrix,
            candidate_ids, project_similarities
        )
        
        assert len(team) <= self.config.team_size
        assert all("id" in member for member in team)

class TestJSONExtraction:
    @patch('pandas.read_csv')
    def test_candidate_extraction(self, mock_read_csv):
        # Mock CSV data
        mock_data = {
            'Candidate ID': ['1001', '1002'],
            'DevType': ['Frontend Developer', 'Backend Developer'],
            'WorkExp': ['5', '3'],
            'WeeklyAvailabilityHours': ['40', '35'],
            'LanguageHaveWorkedWith': ['JavaScript;TypeScript', 'Python;Java']
        }
        mock_df = pd.DataFrame(mock_data)
        mock_read_csv.return_value = mock_df
        
        extractor = CandidateExtractor(api_key="test_key")
        profiles, inputs = extractor.extract_from_csv("dummy.csv")
        
        assert len(profiles) == 2
        assert profiles[0]["id"] == "1001"
        assert "JavaScript" in profiles[0]["technical"]["skills"]

# Run with: pytest tests/test_modules.py -v