
# Continuing from where the file left off...
"""
JSON Extraction Module (M5 - Noor)
"""

import json
from typing import List, Dict, Any
import logging
from openai import OpenAI
import os
from dotenv import load_dotenv
import re
from pathlib import Path

from shared.interfaces import CandidateProfile

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONExtractor:
    """Extract structured JSON from raw text using ChatGPT API"""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize the JSON extractor.
        
        Args:
            model: OpenAI model to use
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
    def create_extraction_prompt(self, raw_text: str) -> str:
        """
        Create prompt for extracting structured data from raw profiles.
        
        Args:
            raw_text: Raw text containing one or more profiles
            
        Returns:
            Prompt for ChatGPT
        """
        prompt = f"""Extract structured information from the following candidate profiles. 
        For each candidate, extract:
        1. Name
        2. Role/title
        3. List of skills with levels (beginner, intermediate, advanced, expert)
        4. Years of experience (extract numeric value)
        5. Tools/technologies used
        6. Collaboration style/preferences
        7. Availability (hours per week, extract numeric value)
        8. Timezone (if mentioned)
        
        Return the data as a JSON array of objects with this structure:
        [
          {{
            "id": "unique_id_1",
            "name": "Full Name",
            "role": "Job Role",
            "skills": ["Skill1", "Skill2", "Skill3"],
            "skill_levels": {{"Skill1": "advanced", "Skill2": "intermediate"}},
            "experience_years": 5,
            "tools": ["Tool1", "Tool2"],
            "collaboration_style": "description",
            "availability_hours": 40,
            "timezone": "UTC+1",
            "domains": ["Domain1", "Domain2"] if mentioned
          }}
        ]
        
        IMPORTANT RULES:
        - Generate unique sequential IDs starting from "1"
        - If skill levels are not mentioned, use "intermediate" as default
        - If availability is not mentioned, use 40 as default
        - If experience is not mentioned, use 0
        - Extract only the information explicitly mentioned
        - Do not make up or infer information
        
        Profiles to process:
        {raw_text}
        """
        return prompt
    
    def extract_profiles(self, raw_text: str) -> List[Dict[str, Any]]:
        """
        Extract structured profiles from raw text using OpenAI API.
        
        Args:
            raw_text: Raw text containing candidate profiles
            
        Returns:
            List of structured profile dictionaries
        """
        logger.info("Extracting structured profiles from raw text")
        
        try:
            # Create prompt
            prompt = self.create_extraction_prompt(raw_text)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data from text. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent output
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Extract profiles array
            profiles = result.get("profiles", result)  # Handle different response formats
            
            if not isinstance(profiles, list):
                profiles = [profiles]
            
            logger.info(f"Successfully extracted {len(profiles)} profiles")
            return profiles
            
        except Exception as e:
            logger.error(f"Error extracting profiles: {e}")
            # Fallback to simple parsing
            return self._fallback_extraction(raw_text)
    
    def _fallback_extraction(self, raw_text: str) -> List[Dict[str, Any]]:
        """
        Fallback extraction method if API call fails.
        Uses simple regex patterns to extract basic information.
        
        Args:
            raw_text: Raw text containing candidate profiles
            
        Returns:
            List of basic profile dictionaries
        """
        logger.warning("Using fallback extraction method")
        
        # Split text into candidate sections
        sections = re.split(r'\n\s*\n', raw_text.strip())
        profiles = []
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
                
            profile = {
                "id": str(i + 1),
                "name": "",
                "role": "",
                "skills": [],
                "skill_levels": {},
                "experience_years": 0,
                "tools": [],
                "collaboration_style": "",
                "availability_hours": 40,
                "timezone": "",
                "domains": []
            }
            
            # Extract name (first line)
            lines = section.strip().split('\n')
            if lines:
                profile["name"] = lines[0].strip()
            
            # Extract skills (simplified)
            for line in lines:
                line_lower = line.lower()
                if 'skill' in line_lower:
                    # Simple skill extraction - in real implementation, use more sophisticated parsing
                    pass
            
            profiles.append(profile)
        
        return profiles
    
    def validate_profile(self, profile: Dict[str, Any]) -> bool:
        """
        Validate extracted profile against schema.
        
        Args:
            profile: Profile dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["id", "name", "role", "skills"]
        
        for field in required_fields:
            if field not in profile:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate types
        if not isinstance(profile.get("skills", []), list):
            logger.warning("Skills should be a list")
            return False
        
        if not isinstance(profile.get("experience_years", 0), (int, float)):
            logger.warning("experience_years should be a number")
            return False
        
        return True

# Interface function
def extract_profiles_from_raw(raw_text: str) -> List[CandidateProfile]:
    """
    Interface function for M5 module.
    
    Args:
        raw_text: Raw text containing candidate profiles
        
    Returns:
        List of CandidateProfile objects
    """
    extractor = JSONExtractor()
    
    # Extract structured data
    profile_dicts = extractor.extract_profiles(raw_text)
    
    # Convert to CandidateProfile objects
    profiles = []
    for profile_dict in profile_dicts:
        # Validate profile
        if not extractor.validate_profile(profile_dict):
            logger.warning(f"Skipping invalid profile: {profile_dict.get('name', 'Unknown')}")
            continue
        
        try:
            profile = CandidateProfile(
                id=profile_dict.get("id", ""),
                name=profile_dict.get("name", ""),
                skills=profile_dict.get("skills", []),
                skill_levels=profile_dict.get("skill_levels", {}),
                role=profile_dict.get("role", ""),
                experience_years=profile_dict.get("experience_years", 0),
                collaboration_style=profile_dict.get("collaboration_style", ""),
                availability_hours=profile_dict.get("availability_hours", 40),
                tools=profile_dict.get("tools", []),
                domains=profile_dict.get("domains", [])
            )
            profiles.append(profile)
        except Exception as e:
            logger.error(f"Error converting profile: {e}")
    
    return profiles

if __name__ == "__main__":
    """Test the JSON extractor with sample data"""
    # Load sample data
    sample_file = Path(__file__).parent.parent.parent.parent / "data" / "sample" / "sample_profiles_raw.txt"
    with open(sample_file, 'r') as f:
        raw_text = f.read()
    
    # Extract profiles
    profiles = extract_profiles_from_raw(raw_text)
    
    print(f"Extracted {len(profiles)} profiles:")
    for i, profile in enumerate(profiles[:3]):  # Show first 3
        print(f"\nProfile {i+1}:")
        print(f"  Name: {profile.name}")
        print(f"  Role: {profile.role}")
        print(f"  Skills: {', '.join(profile.skills[:5])}")
        print(f"  Experience: {profile.experience_years} years")
