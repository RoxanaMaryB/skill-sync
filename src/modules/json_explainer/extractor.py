
# # Continuing from where the file left off...
# """
# JSON Extraction Module (M5 - Noor)
# """

# import json
# from typing import List, Dict, Any
# import logging
# from openai import OpenAI
# import os
# from dotenv import load_dotenv
# import re
# from pathlib import Path

# from shared.interfaces import CandidateProfile

# # Load environment variables
# load_dotenv()

# # Setup logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class JSONExtractor:
#     """Extract structured JSON from raw text using ChatGPT API"""
    
#     def __init__(self, model: str = "gpt-3.5-turbo"):
#         """
#         Initialize the JSON extractor.
        
#         Args:
#             model: OpenAI model to use
#         """
#         api_key = os.getenv("OPENAI_API_KEY")
#         if not api_key:
#             raise ValueError("OPENAI_API_KEY not found in environment variables")
        
#         self.client = OpenAI(api_key=api_key)
#         self.model = model
        
#     def create_extraction_prompt(self, raw_text: str) -> str:
#         """
#         Create prompt for extracting structured data from raw profiles.
        
#         Args:
#             raw_text: Raw text containing one or more profiles
            
#         Returns:
#             Prompt for ChatGPT
#         """
#         prompt = f"""Extract structured information from the following candidate profiles. 
#         For each candidate, extract:
#         1. Name
#         2. Role/title
#         3. List of skills with levels (beginner, intermediate, advanced, expert)
#         4. Years of experience (extract numeric value)
#         5. Tools/technologies used
#         6. Collaboration style/preferences
#         7. Availability (hours per week, extract numeric value)
#         8. Timezone (if mentioned)
        
#         Return the data as a JSON array of objects with this structure:
#         [
#           {{
#             "id": "unique_id_1",
#             "name": "Full Name",
#             "role": "Job Role",
#             "skills": ["Skill1", "Skill2", "Skill3"],
#             "skill_levels": {{"Skill1": "advanced", "Skill2": "intermediate"}},
#             "experience_years": 5,
#             "tools": ["Tool1", "Tool2"],
#             "collaboration_style": "description",
#             "availability_hours": 40,
#             "timezone": "UTC+1",
#             "domains": ["Domain1", "Domain2"] if mentioned
#           }}
#         ]
        
#         IMPORTANT RULES:
#         - Generate unique sequential IDs starting from "1"
#         - If skill levels are not mentioned, use "intermediate" as default
#         - If availability is not mentioned, use 40 as default
#         - If experience is not mentioned, use 0
#         - Extract only the information explicitly mentioned
#         - Do not make up or infer information
        
#         Profiles to process:
#         {raw_text}
#         """
#         return prompt
    
#     def extract_profiles(self, raw_text: str) -> List[Dict[str, Any]]:
#         """
#         Extract structured profiles from raw text using OpenAI API.
        
#         Args:
#             raw_text: Raw text containing candidate profiles
            
#         Returns:
#             List of structured profile dictionaries
#         """
#         logger.info("Extracting structured profiles from raw text")
        
#         try:
#             # Create prompt
#             prompt = self.create_extraction_prompt(raw_text)
            
#             # Call OpenAI API
#             response = self.client.chat.completions.create(
#                 model=self.model,
#                 messages=[
#                     {"role": "system", "content": "You are a helpful assistant that extracts structured data from text. Always return valid JSON."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0.1,  # Low temperature for consistent output
#                 response_format={"type": "json_object"}
#             )
            
#             # Parse response
#             content = response.choices[0].message.content
#             result = json.loads(content)
            
#             # Extract profiles array
#             profiles = result.get("profiles", result)  # Handle different response formats
            
#             if not isinstance(profiles, list):
#                 profiles = [profiles]
            
#             logger.info(f"Successfully extracted {len(profiles)} profiles")
#             return profiles
            
#         except Exception as e:
#             logger.error(f"Error extracting profiles: {e}")
#             # Fallback to simple parsing
#             return self._fallback_extraction(raw_text)
    
#     def _fallback_extraction(self, raw_text: str) -> List[Dict[str, Any]]:
#         """
#         Fallback extraction method if API call fails.
#         Uses simple regex patterns to extract basic information.
        
#         Args:
#             raw_text: Raw text containing candidate profiles
            
#         Returns:
#             List of basic profile dictionaries
#         """
#         logger.warning("Using fallback extraction method")
        
#         # Split text into candidate sections
#         sections = re.split(r'\n\s*\n', raw_text.strip())
#         profiles = []
        
#         for i, section in enumerate(sections):
#             if not section.strip():
#                 continue
                
#             profile = {
#                 "id": str(i + 1),
#                 "name": "",
#                 "role": "",
#                 "skills": [],
#                 "skill_levels": {},
#                 "experience_years": 0,
#                 "tools": [],
#                 "collaboration_style": "",
#                 "availability_hours": 40,
#                 "timezone": "",
#                 "domains": []
#             }
            
#             # Extract name (first line)
#             lines = section.strip().split('\n')
#             if lines:
#                 profile["name"] = lines[0].strip()
            
#             # Extract skills (simplified)
#             for line in lines:
#                 line_lower = line.lower()
#                 if 'skill' in line_lower:
#                     # Simple skill extraction - in real implementation, use more sophisticated parsing
#                     pass
            
#             profiles.append(profile)
        
#         return profiles
    
#     def validate_profile(self, profile: Dict[str, Any]) -> bool:
#         """
#         Validate extracted profile against schema.
        
#         Args:
#             profile: Profile dictionary to validate
            
#         Returns:
#             True if valid, False otherwise
#         """
#         required_fields = ["id", "name", "role", "skills"]
        
#         for field in required_fields:
#             if field not in profile:
#                 logger.warning(f"Missing required field: {field}")
#                 return False
        
#         # Validate types
#         if not isinstance(profile.get("skills", []), list):
#             logger.warning("Skills should be a list")
#             return False
        
#         if not isinstance(profile.get("experience_years", 0), (int, float)):
#             logger.warning("experience_years should be a number")
#             return False
        
#         return True

# # Interface function
# def extract_profiles_from_raw(raw_text: str) -> List[CandidateProfile]:
#     """
#     Interface function for M5 module.
    
#     Args:
#         raw_text: Raw text containing candidate profiles
        
#     Returns:
#         List of CandidateProfile objects
#     """
#     extractor = JSONExtractor()
    
#     # Extract structured data
#     profile_dicts = extractor.extract_profiles(raw_text)
    
#     # Convert to CandidateProfile objects
#     profiles = []
#     for profile_dict in profile_dicts:
#         # Validate profile
#         if not extractor.validate_profile(profile_dict):
#             logger.warning(f"Skipping invalid profile: {profile_dict.get('name', 'Unknown')}")
#             continue
        
#         try:
#             profile = CandidateProfile(
#                 id=profile_dict.get("id", ""),
#                 name=profile_dict.get("name", ""),
#                 skills=profile_dict.get("skills", []),
#                 skill_levels=profile_dict.get("skill_levels", {}),
#                 role=profile_dict.get("role", ""),
#                 experience_years=profile_dict.get("experience_years", 0),
#                 collaboration_style=profile_dict.get("collaboration_style", ""),
#                 availability_hours=profile_dict.get("availability_hours", 40),
#                 tools=profile_dict.get("tools", []),
#                 domains=profile_dict.get("domains", [])
#             )
#             profiles.append(profile)
#         except Exception as e:
#             logger.error(f"Error converting profile: {e}")
    
#     return profiles

# if __name__ == "__main__":
#     """Test the JSON extractor with sample data"""
#     # Load sample data
#     sample_file = Path(__file__).parent.parent.parent.parent / "data" / "sample" / "sample_profiles_raw.txt"
#     with open(sample_file, 'r') as f:
#         raw_text = f.read()
    
#     # Extract profiles
#     profiles = extract_profiles_from_raw(raw_text)
    
#     print(f"Extracted {len(profiles)} profiles:")
#     for i, profile in enumerate(profiles[:3]):  # Show first 3
#         print(f"\nProfile {i+1}:")
#         print(f"  Name: {profile.name}")
#         print(f"  Role: {profile.role}")
#         print(f"  Skills: {', '.join(profile.skills[:5])}")
#         print(f"  Experience: {profile.experience_years} years")


# import os, json
# from pathlib import Path
# import pandas as pd
# from openai import OpenAI

# OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# SYSTEM = """You are an information extraction assistant.
# Extract ONLY what is supported by the input text. If unclear or missing, use "Unknown".
# Return VALID JSON ONLY (no markdown, no extra text).
# Do not invent facts, skills, tools, or behaviors that are not stated or clearly implied by the text.
# """

# # Put your full USER prompt string here (same one from notebook)
# USER = """Extract ONLY what is supported by the candidate profile.
# If information is unclear, ambiguous, or missing, use "Unknown".
# Do NOT invent facts, skills, tools, roles, or behaviors.
# Return VALID JSON ONLY (no markdown, no extra text).


# ------------------------------------------------------------
# OUTPUT FORMAT (EXACT JSON SCHEMA)
# ------------------------------------------------------------


# {
#   "id": "...",
#   "constraints": {
#     "weekly_availability_hours": "..."
#   },
#   "metadata": {
#     "dev_type": "...",
#     "work_experience_years": "...",
#     "years_code": "...",
#     "employment": "...",
#     "org_size": "...",
#     "industry": "..."
#   },
#   "technical": {
#     "skills": [],
#     "tools": []
    
#   },
#   "personality": {
#     "Belbin_team_role": "..."
#   },
#   "collaboration": {
#     "communication_style": "...",
#     "conflict_style": "...",
#     "leadership_preference": "...",
#     "deadline_discipline": "..."
#   },
#   "learning_behavior": {
#     "learning_orientation": "...",
#     "knowledge_sharing": "..."
#   },
#   "evidence": {
#   "personality": {
#     "team_role": ""
#   },
#   "collaboration": {
#     "communication_style": "",
#     "conflict_style": "",
#     "leadership_preference": "",
#     "deadline_discipline": ""
#   },
#   "learning_behavior": {
#     "learning_orientation": "",
#     "knowledge_sharing": ""
#   }
# }



# ------------------------------------------------------------
# HARD RULES
# ------------------------------------------------------------


# - Return ONLY valid JSON.
# - Do NOT omit any keys.
# - If a value is unknown or unsupported, use:
#   - "Unknown" for string fields
#   - [] for list fields
#   - "" for evidence fields


# ------------------------------------------------------------
# COPY-EXACTLY RULES (NO INFERENCE)
# ------------------------------------------------------------


# These rules apply to identifiers, metadata, constraints, and ALL technical fields.


# - id must be copied exactly from Candidate ID if present, else "Unknown".
# - constraints.weekly_availability_hours must be copied exactly from WeeklyAvailabilityHours if present, else "Unknown".
# - metadata.dev_type must be copied exactly from DevType if present, else "Unknown".
# - metadata.work_experience_years must be copied exactly from WorkExp if present, else "Unknown".
# - metadata.years_code must be copied exactly from YearsCode if present, else "Unknown".
# - metadata.employment must be copied exactly from Employment if present, else "Unknown".
# - metadata.org_size must be copied exactly from OrgSize if present, else "Unknown".
# - metadata.industry must be copied exactly from Industry if present, else "Unknown".


# IMPORTANT:
# If metadata.dev_type starts with "Other",
# or equals "Other (please specify):",
# set metadata.dev_type to "Unknown".


# ------------------------------------------------------------
# TECHNICAL CLASSIFICATION RULES (STRICT, VERBATIM)
# ------------------------------------------------------------


# - technical.skills MUST include ONLY programming languages, frameworks, libraries, databases, and cloud platforms explicitly mentioned.
# - technical.tools MUST include ONLY developer tools (IDEs, editors, CLIs, package managers).
# - Do NOT include survey option labels or workflow phrases
#   (e.g., "DevOps function", "Continuous delivery").
# - Every extracted technical item MUST appear verbatim in the input text.
# - Do NOT infer, normalize, or generalize technical items.


# ------------------------------------------------------------
# ALLOWED VALUES (CATEGORICAL FIELDS)
# ------------------------------------------------------------


# - team_role:
#   Teamworker, Shaper, Coordinator, Implementer, Monitor-Evaluator,
#   Plant, Resource-Investigator, Completer-Finisher.


# - communication_style: Async, Sync, Mixed, Unknown
# - conflict_style: Avoid, Direct, Mediation, Unknown
# - leadership_preference: Lead, Follow, Shared, Unknown
# - deadline_discipline: Strict, Flexible, Depends, Unknown
# - learning_orientation: High, Medium, Low, Unknown
# - knowledge_sharing: High, Medium, Low, Unknown


# ------------------------------------------------------------
# SEMANTIC MAPPING RULES (FOR GENERALIZATION)
# ------------------------------------------------------------


# These rules apply ONLY to behavioral categorical fields:
# personality, collaboration, and learning_behavior.


# You MAY assign an allowed value even if the exact label word
# (e.g., "Shaper", "Async") does NOT appear,
# AS LONG AS the text clearly and unambiguously describes
# the corresponding behavior.


# If signals are mixed, weak, or ambiguous, return "Unknown".


# ------------------------------------------------------------
# BELBIN TEAM ROLE MAPPING (PERSONALITY)
# ------------------------------------------------------------


# - Shaper:
#   pushes progress, challenges others, results-driven, urgency


# - Teamworker:
#   supportive, harmony-focused, resolves tension, cooperative


# - Coordinator:
#   organizes people or tasks, aligns goals, delegates responsibility


# - Implementer:
#   practical execution, structured planning, turns ideas into action


# - Monitor-Evaluator:
#   analytical, cautious, evaluates pros and cons


# - Plant:
#   creative, idea generation, novel or unconventional approaches


# - Resource-Investigator:
#   explores opportunities, networking, outward-looking


# - Completer-Finisher:
#   detail-oriented, polishing work, quality control


# ------------------------------------------------------------
# COLLABORATION STYLE MAPPING
# ------------------------------------------------------------


# communication_style:
# - Async: prefers written updates, messaging, minimal meetings
# - Sync: prefers live discussion, calls, meetings
# - Mixed: explicitly uses both depending on context


# conflict_style:
# - Avoid: avoids confrontation, de-escalates tension
# - Direct: addresses issues openly and directly
# - Mediation: bridges viewpoints, seeks compromise


# leadership_preference:

# - Lead:
#   Assign if the text clearly shows directional influence
#   or responsibility for driving work forward.

#   Semantic indicators include:
#   - initiating tasks or actions
#   - taking responsibility or ownership
#   - organizing, coordinating, or motivating others
#   - influencing how work progresses

# - Follow:
#   Assign if the text emphasizes supporting others
#   or executing work under external direction.

#   Semantic indicators include:
#   - comfort supporting a leader
#   - focus on assigned or individual tasks
#   - executing decisions made by others
#   - explicitly not leading

# - Shared:
#   Assign if the text clearly indicates collective
#   decision-making or shared responsibility.

#   Semantic indicators include:
#   - shared ownership or responsibility
#   - group-based or joint decisions
#   - absence of a single leader
#   - rotating or distributed leadership

# - Unknown:
#   Use if:
#   - leadership behavior is weak, implicit, or ambiguous
#   - indicators for multiple categories appear
#   - leadership is not a meaningful focus of the text



# deadline_discipline:
# - Strict: emphasizes meeting deadlines, plans ahead
# - Flexible: adapts or negotiates timelines
# - Depends: explicitly conditional on context or workload


# ------------------------------------------------------------
# LEARNING BEHAVIOR (SEMANTIC RUBRIC)
# ------------------------------------------------------------


# learning_orientation:
# - High: AI used for learning, understanding, planning, reasoning
# - Medium: AI used mainly for execution support or productivity
# - Low: minimal or rare AI usage
# - Unknown: no AI usage information present


# knowledge_sharing:

# - High:
#   Actively helps others learn or understand
#   (explicit mentoring, teaching, explaining concepts,
#    guiding teammates, knowledge transfer).

# - Medium:
#   Explicitly mentions sharing ideas, giving feedback,
#   contributing insights, or collaborating on solutions
#   beyond own tasks.

# - Low:
#   Focuses mainly on own tasks or execution,
#   with little or no mention of helping others
#   or contributing ideas.

# - Unknown:
#   No explicit mention of sharing knowledge,
#   mentoring, explaining, or contributing insights.




# CONSISTENCY CONSTRAINT (MANDATORY):
# The label must be directly implied by the evidence quote.
# If evidence implies a different label, change the label to match the evidence.
# Do not output "Shared" unless the evidence quote explicitly indicates shared or collective decision-making.


# IMPORTANT CONSTRAINT:
# - Do NOT use inclusiveness, respect, feeling heard,
#   collaboration, or communication values
#   as evidence of knowledge_sharing.
# - knowledge_sharing requires explicit contribution of knowledge,
#   ideas, feedback, mentoring, or explanation.




# ------------------------------------------------------------
# EVIDENCE RULES
# ------------------------------------------------------------

# General:
# - Evidence must be grounded in the input text.
# - Evidence must be a SHORT verbatim excerpt (not a full sentence).
# - Evidence must NOT include a trailing period.
# - If a field value is "Unknown", its evidence MUST be "".

# Per-field evidence requirements:
# - evidence.personality.team_role: 3–8 words from PersonalityText (or "" if Unknown).
# - evidence.collaboration.*: 3–8 words from PersonalityText (or "" if Unknown).
# - evidence.learning_behavior.learning_orientation: 3–8 words copied EXACTLY from ONE of:
#   AIToolCurrentlyUsing, AIBen, AIComplex, AIChallenges, AIEthics.
# - evidence.learning_behavior.knowledge_sharing: 3–8 words from PersonalityText not ProfessionalTech.

# Consistency rule:
# - Evidence must directly support the chosen label.
# - If you cannot find evidence supporting the chosen label, set the label to "Unknown" and evidence to "".
# - Never provide evidence that contradicts the label.


# ------------------------------------------------------------

# Before returning the final JSON, verify:
# - All required keys are present (including nested evidence keys).
# - All categorical values belong to the allowed sets.
# - Each evidence string is 3–8 words and appears verbatim in the correct source text.
# - If a field is "Unknown", its evidence is "".
# - Evidence supports (does not contradict) the selected label.
# If any check fails, correct it before returning.


# Now extract from the following candidate text:


# """



# def as_str(v) -> str:
#     if v is None:
#         return "Unknown"
#     try:
#         if pd.isna(v):
#             return "Unknown"
#     except Exception:
#         pass
#     s = str(v).strip()
#     return s if s else "Unknown"


# def load_dataset(csv_path: str) -> pd.DataFrame:
#     df = pd.read_csv(csv_path)

#     rename_map = {}
#     if "CandidateNumber" in df.columns and "Candidate ID" not in df.columns:
#         rename_map["CandidateNumber"] = "Candidate ID"
#     if "AIToolCurrently Using" in df.columns and "AIToolCurrentlyUsing" not in df.columns:
#         rename_map["AIToolCurrently Using"] = "AIToolCurrentlyUsing"
#     if "OpSysPersonal use" in df.columns and "OpSysPersonalUse" not in df.columns:
#         rename_map["OpSysPersonal use"] = "OpSysPersonalUse"

#     if rename_map:
#         df = df.rename(columns=rename_map)

#     return df


# def build_profile_text(r: dict) -> str:
#     fields = [
#         ("Candidate ID", as_str(r.get("Candidate ID"))),
#         ("WeeklyAvailabilityHours", as_str(r.get("WeeklyAvailabilityHours"))),

#         ("Employment", as_str(r.get("Employment"))),
#         ("YearsCode", as_str(r.get("YearsCode"))),
#         ("DevType", as_str(r.get("DevType"))),
#         ("OrgSize", as_str(r.get("OrgSize"))),
#         ("Industry", as_str(r.get("Industry"))),
#         ("WorkExp", as_str(r.get("WorkExp"))),
#         ("ICorPM", as_str(r.get("ICorPM"))),

#         ("LanguageHaveWorkedWith", as_str(r.get("LanguageHaveWorkedWith"))),
#         ("LanguageAdmired", as_str(r.get("LanguageAdmired"))),
#         ("DatabaseHaveWorkedWith", as_str(r.get("DatabaseHaveWorkedWith"))),
#         ("PlatformHaveWorkedWith", as_str(r.get("PlatformHaveWorkedWith"))),
#         ("WebframeHaveWorkedWith", as_str(r.get("WebframeHaveWorkedWith"))),
#         ("MiscTechHaveWorkedWith", as_str(r.get("MiscTechHaveWorkedWith"))),
#         ("ToolsTechHaveWorkedWith", as_str(r.get("ToolsTechHaveWorkedWith"))),
#         ("NEWCollabToolsHaveWorkedWith", as_str(r.get("NEWCollabToolsHaveWorkedWith"))),
#         ("OpSysPersonalUse", as_str(r.get("OpSysPersonalUse"))),

#         ("AISearchDevHaveWorkedWith", as_str(r.get("AISearchDevHaveWorkedWith"))),
#         ("AIToolCurrentlyUsing", as_str(r.get("AIToolCurrentlyUsing"))),
#         ("AIBen", as_str(r.get("AIBen"))),
#         ("AIComplex", as_str(r.get("AIComplex"))),
#         ("AIEthics", as_str(r.get("AIEthics"))),
#         ("AIChallenges", as_str(r.get("AIChallenges"))),

#         ("Frustration", as_str(r.get("Frustration"))),
#         ("PersonalityText", as_str(r.get("PersonalityText"))),

#         ("ProfessionalTech", as_str(r.get("ProfessionalTech"))),
#         ("ProfessionalCloud", as_str(r.get("ProfessionalCloud"))),
#     ]
#     return "\n".join([f"{k}: {v}" for k, v in fields])


# def safe_json_loads(raw: str) -> dict:
#     raw = (raw or "").strip()
#     start = raw.find("{")
#     end = raw.rfind("}")
#     if start == -1 or end == -1 or end <= start:
#         raise ValueError("No JSON found in model output")
#     return json.loads(raw[start:end+1])


# def extract_one(client: OpenAI, row: dict, model: str) -> dict:
#     text = build_profile_text(row)

#     resp = client.chat.completions.create(
#         model=model,
#         temperature=0,
#         messages=[
#             {"role": "system", "content": SYSTEM},
#             {"role": "user", "content": USER + "\n\n" + text},
#         ],
#     )

#     profile = safe_json_loads(resp.choices[0].message.content)
#     profile["id"] = as_str(row.get("Candidate ID"))  # force copy exact
#     return profile


# def strip_evidence(profile: dict) -> dict:
#     p = dict(profile)
#     p.pop("evidence", None)
#     return p


# def run_extraction(
#     csv_path: str = "data/skillsync_dataset_v1_draft.csv",
#     out_clean: str = "data/candidate_profiles.json",
#     out_with_evidence: str | None = "data/candidate_profiles_with_evidence.json",
#     model: str = "openai/gpt-4o-mini",
#     n: int = 200,
# ):
#     api_key = os.getenv("OPENROUTER_API_KEY")
#     if not api_key:
#         raise ValueError("Missing OPENROUTER_API_KEY in environment")

#     client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)
#     df = load_dataset(csv_path)

#     profiles_with_ev = []
#     profiles_clean = []

#     for i in range(min(n, len(df))):
#         row = df.iloc[i].to_dict()
#         try:
#             prof = extract_one(client, row, model)
#         except Exception as e:
#             prof = {"id": as_str(row.get("Candidate ID")), "error": str(e)}

#         profiles_with_ev.append(prof)
#         profiles_clean.append(strip_evidence(prof))

#     Path(out_clean).parent.mkdir(parents=True, exist_ok=True)

#     if out_with_evidence:
#         with open(out_with_evidence, "w", encoding="utf-8") as f:
#             json.dump(profiles_with_ev, f, indent=2, ensure_ascii=False)

#     with open(out_clean, "w", encoding="utf-8") as f:
#         json.dump(profiles_clean, f, indent=2, ensure_ascii=False)

#     print(f"Saved: {out_clean}")
#     if out_with_evidence:
#         print(f"Saved: {out_with_evidence}")


# def main():
#     run_extraction()


# if __name__ == "__main__":
#     main()


from __future__ import annotations

import os
import json
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from openai import OpenAI


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

SYSTEM_PROMPT = """You are an information extraction assistant.
Extract ONLY what is supported by the input text. If unclear or missing, use "Unknown".
Return VALID JSON ONLY (no markdown, no extra text).
Do not invent facts, skills, tools, or behaviors that are not stated or clearly implied by the text.
"""

USER_PROMPT = """Extract ONLY what is supported by the candidate profile.
If information is unclear, ambiguous, or missing, use "Unknown".
Do NOT invent facts, skills, tools, roles, or behaviors.
Return VALID JSON ONLY (no markdown, no extra text).


------------------------------------------------------------
OUTPUT FORMAT (EXACT JSON SCHEMA)
------------------------------------------------------------


{
  "id": "...",
  "constraints": {
    "weekly_availability_hours": "..."
  },
  "metadata": {
    "dev_type": "...",
    "work_experience_years": "...",
    "years_code": "...",
    "employment": "...",
    "org_size": "...",
    "industry": "..."
  },
  "technical": {
    "skills": [],
    "tools": []
    
  },
  "personality": {
    "Belbin_team_role": "..."
  },
  "collaboration": {
    "communication_style": "...",
    "conflict_style": "...",
    "leadership_preference": "...",
    "deadline_discipline": "..."
  },
  "learning_behavior": {
    "learning_orientation": "...",
    "knowledge_sharing": "..."
  },
  "evidence": {
  "personality": {
    "team_role": ""
  },
  "collaboration": {
    "communication_style": "",
    "conflict_style": "",
    "leadership_preference": "",
    "deadline_discipline": ""
  },
  "learning_behavior": {
    "learning_orientation": "",
    "knowledge_sharing": ""
  }
}



------------------------------------------------------------
HARD RULES
------------------------------------------------------------


- Return ONLY valid JSON.
- Do NOT omit any keys.
- If a value is unknown or unsupported, use:
  - "Unknown" for string fields
  - [] for list fields
  - "" for evidence fields


------------------------------------------------------------
COPY-EXACTLY RULES (NO INFERENCE)
------------------------------------------------------------


These rules apply to identifiers, metadata, constraints, and ALL technical fields.


- id must be copied exactly from Candidate ID if present, else "Unknown".
- constraints.weekly_availability_hours must be copied exactly from WeeklyAvailabilityHours if present, else "Unknown".
- metadata.dev_type must be copied exactly from DevType if present, else "Unknown".
- metadata.work_experience_years must be copied exactly from WorkExp if present, else "Unknown".
- metadata.years_code must be copied exactly from YearsCode if present, else "Unknown".
- metadata.employment must be copied exactly from Employment if present, else "Unknown".
- metadata.org_size must be copied exactly from OrgSize if present, else "Unknown".
- metadata.industry must be copied exactly from Industry if present, else "Unknown".


IMPORTANT:
If metadata.dev_type starts with "Other",
or equals "Other (please specify):",
set metadata.dev_type to "Unknown".


------------------------------------------------------------
TECHNICAL CLASSIFICATION RULES (STRICT, VERBATIM)
------------------------------------------------------------


- technical.skills MUST include ONLY programming languages, frameworks, libraries, databases, and cloud platforms explicitly mentioned.
- technical.tools MUST include ONLY developer tools (IDEs, editors, CLIs, package managers).
- Do NOT include survey option labels or workflow phrases
  (e.g., "DevOps function", "Continuous delivery").
- Every extracted technical item MUST appear verbatim in the input text.
- Do NOT infer, normalize, or generalize technical items.


------------------------------------------------------------
ALLOWED VALUES (CATEGORICAL FIELDS)
------------------------------------------------------------


- team_role:
  Teamworker, Shaper, Coordinator, Implementer, Monitor-Evaluator,
  Plant, Resource-Investigator, Completer-Finisher.


- communication_style: Async, Sync, Mixed, Unknown
- conflict_style: Avoid, Direct, Mediation, Unknown
- leadership_preference: Lead, Follow, Shared, Unknown
- deadline_discipline: Strict, Flexible, Depends, Unknown
- learning_orientation: High, Medium, Low, Unknown
- knowledge_sharing: High, Medium, Low, Unknown


------------------------------------------------------------
SEMANTIC MAPPING RULES (FOR GENERALIZATION)
------------------------------------------------------------


These rules apply ONLY to behavioral categorical fields:
personality, collaboration, and learning_behavior.


You MAY assign an allowed value even if the exact label word
(e.g., "Shaper", "Async") does NOT appear,
AS LONG AS the text clearly and unambiguously describes
the corresponding behavior.


If signals are mixed, weak, or ambiguous, return "Unknown".


------------------------------------------------------------
BELBIN TEAM ROLE MAPPING (PERSONALITY)
------------------------------------------------------------


- Shaper:
  pushes progress, challenges others, results-driven, urgency


- Teamworker:
  supportive, harmony-focused, resolves tension, cooperative


- Coordinator:
  organizes people or tasks, aligns goals, delegates responsibility


- Implementer:
  practical execution, structured planning, turns ideas into action


- Monitor-Evaluator:
  analytical, cautious, evaluates pros and cons


- Plant:
  creative, idea generation, novel or unconventional approaches


- Resource-Investigator:
  explores opportunities, networking, outward-looking


- Completer-Finisher:
  detail-oriented, polishing work, quality control


------------------------------------------------------------
COLLABORATION STYLE MAPPING
------------------------------------------------------------


communication_style:
- Async: prefers written updates, messaging, minimal meetings
- Sync: prefers live discussion, calls, meetings
- Mixed: explicitly uses both depending on context


conflict_style:
- Avoid: avoids confrontation, de-escalates tension
- Direct: addresses issues openly and directly
- Mediation: bridges viewpoints, seeks compromise


leadership_preference:

- Lead:
  Assign if the text clearly shows directional influence
  or responsibility for driving work forward.

  Semantic indicators include:
  - initiating tasks or actions
  - taking responsibility or ownership
  - organizing, coordinating, or motivating others
  - influencing how work progresses

- Follow:
  Assign if the text emphasizes supporting others
  or executing work under external direction.

  Semantic indicators include:
  - comfort supporting a leader
  - focus on assigned or individual tasks
  - executing decisions made by others
  - explicitly not leading

- Shared:
  Assign if the text clearly indicates collective
  decision-making or shared responsibility.

  Semantic indicators include:
  - shared ownership or responsibility
  - group-based or joint decisions
  - absence of a single leader
  - rotating or distributed leadership

- Unknown:
  Use if:
  - leadership behavior is weak, implicit, or ambiguous
  - indicators for multiple categories appear
  - leadership is not a meaningful focus of the text



deadline_discipline:
- Strict: emphasizes meeting deadlines, plans ahead
- Flexible: adapts or negotiates timelines
- Depends: explicitly conditional on context or workload


------------------------------------------------------------
LEARNING BEHAVIOR (SEMANTIC RUBRIC)
------------------------------------------------------------


learning_orientation:
- High: AI used for learning, understanding, planning, reasoning
- Medium: AI used mainly for execution support or productivity
- Low: minimal or rare AI usage
- Unknown: no AI usage information present


knowledge_sharing:

- High:
  Actively helps others learn or understand
  (explicit mentoring, teaching, explaining concepts,
   guiding teammates, knowledge transfer).

- Medium:
  Explicitly mentions sharing ideas, giving feedback,
  contributing insights, or collaborating on solutions
  beyond own tasks.

- Low:
  Focuses mainly on own tasks or execution,
  with little or no mention of helping others
  or contributing ideas.

- Unknown:
  No explicit mention of sharing knowledge,
  mentoring, explaining, or contributing insights.




CONSISTENCY CONSTRAINT (MANDATORY):
The label must be directly implied by the evidence quote.
If evidence implies a different label, change the label to match the evidence.
Do not output "Shared" unless the evidence quote explicitly indicates shared or collective decision-making.


IMPORTANT CONSTRAINT:
- Do NOT use inclusiveness, respect, feeling heard,
  collaboration, or communication values
  as evidence of knowledge_sharing.
- knowledge_sharing requires explicit contribution of knowledge,
  ideas, feedback, mentoring, or explanation.




------------------------------------------------------------
EVIDENCE RULES
------------------------------------------------------------

General:
- Evidence must be grounded in the input text.
- Evidence must be a SHORT verbatim excerpt (not a full sentence).
- Evidence must NOT include a trailing period.
- If a field value is "Unknown", its evidence MUST be "".

Per-field evidence requirements:
- evidence.personality.team_role: 3–8 words from PersonalityText (or "" if Unknown).
- evidence.collaboration.*: 3–8 words from PersonalityText (or "" if Unknown).
- evidence.learning_behavior.learning_orientation: 3–8 words copied EXACTLY from ONE of:
  AIToolCurrentlyUsing, AIBen, AIComplex, AIChallenges, AIEthics.
- evidence.learning_behavior.knowledge_sharing: 3–8 words from PersonalityText not ProfessionalTech.

Consistency rule:
- Evidence must directly support the chosen label.
- If you cannot find evidence supporting the chosen label, set the label to "Unknown" and evidence to "".
- Never provide evidence that contradicts the label.


------------------------------------------------------------

Before returning the final JSON, verify:
- All required keys are present (including nested evidence keys).
- All categorical values belong to the allowed sets.
- Each evidence string is 3–8 words and appears verbatim in the correct source text.
- If a field is "Unknown", its evidence is "".
- Evidence supports (does not contradict) the selected label.
If any check fails, correct it before returning.


Now extract from the following candidate text:


"""


@dataclass
class ExtractorConfig:
    model: str = "openai/gpt-4o-mini"
    temperature: float = 0.0
    limit: int = 3
    retries: int = 1
    request_timeout_s: int = 60  
    sleep_between_calls_s: float = 0.2  
    debug: bool = True  



class CandidateProfileExtractor:
    """
    Pipeline-friendly extractor (OOP):
    - reads a row -> builds profile text -> LLM -> JSON dict
    - can process a DataFrame
    - saves outputs to /data
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = OPENROUTER_BASE_URL,
        config: Optional[ExtractorConfig] = None,
    ):
        self.config = config or ExtractorConfig()

     
        if not api_key:
            raise ValueError("Missing OPENROUTER_API_KEY in environment")

        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=self.config.request_timeout_s,
        )

        if self.config.debug:
            print(f"[DEBUG] OpenRouter base_url: {base_url}", flush=True)
            print(f"[DEBUG] Model: {self.config.model}", flush=True)
            print(f"[DEBUG] Timeout(s): {self.config.request_timeout_s}", flush=True)

   
    @staticmethod
    def as_str(v: Any) -> str:
        if v is None:
            return "Unknown"
        try:
            if pd.isna(v):
                return "Unknown"
        except Exception:
            pass
        s = str(v).strip()
        return s if s else "Unknown"

    @staticmethod
    def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        DEBUG: Ensures the code works even if the CSV columns have slightly different names.
        """
        rename_map = {}
        if "CandidateNumber" in df.columns and "Candidate ID" not in df.columns:
            rename_map["CandidateNumber"] = "Candidate ID"
        if "AIToolCurrently Using" in df.columns and "AIToolCurrentlyUsing" not in df.columns:
            rename_map["AIToolCurrently Using"] = "AIToolCurrentlyUsing"
        if "OpSysPersonal use" in df.columns and "OpSysPersonalUse" not in df.columns:
            rename_map["OpSysPersonal use"] = "OpSysPersonalUse"
        return df.rename(columns=rename_map) if rename_map else df

    @staticmethod
    def safe_json_loads(raw: str) -> Dict[str, Any]:
        """
        DEBUG: Extract the first {...} JSON object from the model output
        even if the model adds extra text.
        """
        raw = (raw or "").strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in model output")
        return json.loads(raw[start : end + 1])

    def build_profile_text(self, r: Dict[str, Any]) -> str:
        """
        DEBUG: This constructs exactly what the LLM sees.
        If something is missing in output, check it appears here.
        """
        fields = [
            ("Candidate ID", self.as_str(r.get("Candidate ID"))),
            ("WeeklyAvailabilityHours", self.as_str(r.get("WeeklyAvailabilityHours"))),

            ("Employment", self.as_str(r.get("Employment"))),
            ("YearsCode", self.as_str(r.get("YearsCode"))),
            ("DevType", self.as_str(r.get("DevType"))),
            ("OrgSize", self.as_str(r.get("OrgSize"))),
            ("Industry", self.as_str(r.get("Industry"))),
            ("WorkExp", self.as_str(r.get("WorkExp"))),
            ("ICorPM", self.as_str(r.get("ICorPM"))),

            ("LanguageHaveWorkedWith", self.as_str(r.get("LanguageHaveWorkedWith"))),
            ("LanguageAdmired", self.as_str(r.get("LanguageAdmired"))),
            ("DatabaseHaveWorkedWith", self.as_str(r.get("DatabaseHaveWorkedWith"))),
            ("PlatformHaveWorkedWith", self.as_str(r.get("PlatformHaveWorkedWith"))),
            ("WebframeHaveWorkedWith", self.as_str(r.get("WebframeHaveWorkedWith"))),
            ("MiscTechHaveWorkedWith", self.as_str(r.get("MiscTechHaveWorkedWith"))),
            ("ToolsTechHaveWorkedWith", self.as_str(r.get("ToolsTechHaveWorkedWith"))),
            ("NEWCollabToolsHaveWorkedWith", self.as_str(r.get("NEWCollabToolsHaveWorkedWith"))),
            ("OpSysPersonalUse", self.as_str(r.get("OpSysPersonalUse"))),

            ("AISearchDevHaveWorkedWith", self.as_str(r.get("AISearchDevHaveWorkedWith"))),
            ("AIToolCurrentlyUsing", self.as_str(r.get("AIToolCurrentlyUsing"))),
            ("AIBen", self.as_str(r.get("AIBen"))),
            ("AIComplex", self.as_str(r.get("AIComplex"))),
            ("AIEthics", self.as_str(r.get("AIEthics"))),
            ("AIChallenges", self.as_str(r.get("AIChallenges"))),

            ("Frustration", self.as_str(r.get("Frustration"))),
            ("PersonalityText", self.as_str(r.get("PersonalityText"))),

            ("ProfessionalTech", self.as_str(r.get("ProfessionalTech"))),
            ("ProfessionalCloud", self.as_str(r.get("ProfessionalCloud"))),
        ]
        return "\n".join([f"{k}: {v}" for k, v in fields])

    #  LLM call 
    def extract_one(self, row: Dict[str, Any], i: int = -1) -> Dict[str, Any]:
        """
        DEBUG: Extract a single row. Prints key checkpoints and short preview.
        """
        text = self.build_profile_text(row)

        if self.config.debug:
            cid = self.as_str(row.get("Candidate ID"))
            print(f"[DEBUG] Calling LLM for row={i} CID={cid}", flush=True)
            
            preview = text.replace("\n", " | ")
            print(f"[DEBUG] Input preview: {preview[:200]}...", flush=True)

        resp = self.client.chat.completions.create(
            model=self.config.model,
            temperature=self.config.temperature,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT + "\n\n" + text},
            ],
        )

        raw = resp.choices[0].message.content

        if self.config.debug:
            print(f"[DEBUG] Raw output preview: {(raw or '')[:200]}...", flush=True)

        profile = self.safe_json_loads(raw)

        
        profile["id"] = self.as_str(row.get("Candidate ID"))

      
        if self.config.sleep_between_calls_s > 0:
            time.sleep(self.config.sleep_between_calls_s)

        return profile


    def extract_all(self, df: pd.DataFrame, n: Optional[int] = None) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        DEBUG: Batch extraction with progress + retries + per-row error visibility.
        """
        df = self.rename_columns(df)
        limit = min(n or self.config.limit, len(df))

        if self.config.debug:
            print(f"[DEBUG] DataFrame rows={len(df)} limit={limit}", flush=True)
            print(f"[DEBUG] Columns: {list(df.columns)[:20]}", flush=True)

        profiles: List[Dict[str, Any]] = []
        inputs: Dict[str, str] = {}

        for i in range(limit):
            row = df.iloc[i].to_dict()
            cid = self.as_str(row.get("Candidate ID"))

           
            print(f"➡️ Extracting row {i+1}/{limit} (CID={cid})", flush=True)

            text = self.build_profile_text(row)
            inputs[cid] = text

            last_err: Optional[str] = None
            for attempt in range(self.config.retries + 1):
                try:
                    if self.config.debug:
                        print(f"[DEBUG] Attempt {attempt+1}/{self.config.retries+1} for CID={cid}", flush=True)

                    prof = self.extract_one(row, i=i)
                    profiles.append(prof)
                    last_err = None
                    break

                except Exception as e:
                    last_err = str(e)
                    print(f"[ERROR] row={i} CID={cid} attempt={attempt+1} error={last_err}", flush=True)

            if last_err is not None:
                
                profiles.append({"id": cid, "error": last_err})

        return profiles, inputs

  
    @staticmethod
    def save_json(obj: Any, out_path: str) -> None:
        """
        DEBUG: Always ensure parent folder exists and save pretty JSON.
        """
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)

    @staticmethod
    def strip_evidence(profile: Dict[str, Any]) -> Dict[str, Any]:
        p = dict(profile)
        p.pop("evidence", None)
        return p



def run_extraction(
    csv_path: str = "data/skillsync_dataset_v1_draft_with_candidate_id.csv",
    out_clean: str = "data/candidate_profiles.json",
    out_with_evidence: Optional[str] = "data/candidate_profiles_with_evidence.json",
    out_inputs: Optional[str] = "data/candidate_inputs.json",
    model: str = "openai/gpt-4o-mini",
    n: int = 3,
) -> None:
    """
    Public entry point for the pipeline.
    Reads CSV -> extracts profiles -> saves JSON into /data
    """

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    print("🔹 Loading dataset:", csv_path, flush=True)
    df = pd.read_csv(csv_path)

    cfg = ExtractorConfig(model=model, limit=n, debug=True)
    extractor = CandidateProfileExtractor(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        config=cfg,
    )

    print("🔹 Running profile extraction...", flush=True)
    profiles, inputs = extractor.extract_all(df, n=n)

    print("🔹 Saving outputs...", flush=True)
    if out_with_evidence:
        extractor.save_json(profiles, out_with_evidence)
    extractor.save_json([extractor.strip_evidence(p) for p in profiles], out_clean)
    if out_inputs:
        extractor.save_json(inputs, out_inputs)

    print(f" Saved: {out_clean}", flush=True)
    if out_with_evidence:
        print(f" Saved: {out_with_evidence}", flush=True)
    if out_inputs:
        print(f" Saved: {out_inputs}", flush=True)




