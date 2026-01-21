# tests/test_integration.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import tempfile
from src.modules import (
    embed_candidates,
    embed_project,
    build_teams,
    extract_candidates,
    extract_project_requirements
)

class TestIntegration:
    def test_full_pipeline(self):
        """Test complete pipeline from extraction to team building"""
        
        # 1. Create test CSV
        csv_content = """CandidateID,Name,DevType,WorkExp,WeeklyAvailabilityHours,LanguageHaveWorkedWith
1001,Test1,Developer, front-end,5,40,JavaScript;React
1002,Test2,Developer, back-end,8,35,Python;Docker"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_path = f.name
        
        try:
            # 2. Extract candidates
            profiles, _ = extract_candidates(csv_path, api_key="test_key")
            assert len(profiles) == 2
            
            # 3. Embed candidates
            embedding_result = embed_candidates(profiles)
            assert "embeddings" in embedding_result
            
            # 4. Create project requirements
            project_desc = "We need a web app with React frontend and Python backend"
            project_req = extract_project_requirements(project_desc, api_key="test_key")
            
            # 5. Embed project
            project_result = embed_project(project_req)
            assert "candidate_similarities" in project_result
            
            # 6. Build teams
            project_config = {
                "required_skills": ["React", "Python"],
                "team_size": 2
            }
            
            teams = build_teams(
                profiles=profiles,
                project=project_config,
                candidate_dissim_matrix=embedding_result.get('dissimilarity_matrix'),
                candidate_ids=embedding_result.get('candidate_ids'),
                project_similarities=project_result.get('candidate_similarities', {})
            )
            
            assert len(teams) > 0
            assert len(teams[0]) == 2
            
        finally:
            os.unlink(csv_path)
    
    def test_edge_cases(self):
        """Test edge cases"""
        
        # Empty profiles
        empty_result = embed_candidates([])
        assert empty_result["embeddings"] is None
        
        # Single profile team
        single_profile = [{
            "id": "1",
            "metadata": {"dev_type": "Developer"},
            "technical": {"skills": ["Python"]}
        }]
        
        project = {"required_skills": ["Python"], "team_size": 1}
        
        teams = build_teams(single_profile, project)
        assert len(teams) == 1
        assert len(teams[0]) == 1