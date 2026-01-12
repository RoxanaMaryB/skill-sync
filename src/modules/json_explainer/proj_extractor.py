
from __future__ import annotations


import json
from dataclasses import dataclass
from typing import Any, Dict, Optional
from openai import OpenAI


SYSTEM_PROMPT = """You are an information extraction assistant.


Hard constraints:
- Extract ONLY what is explicitly supported by the input text.
- Return VALID JSON ONLY (no markdown, no extra text).
- Do NOT invent, assume, infer, or expand beyond the text.
- If a term is clearly a technology and is explicitly mentioned, extract it.
- If uncertain or ambiguous, omit the item.


Very important:
- The USER'S project description is the ONLY source of truth for what to extract.
- Any lists in the prompt are for NAME NORMALIZATION ONLY, not for restricting extraction.
"""


USER_PROMPT = """Extract technical requirements from the project description.


Return EXACTLY this JSON schema (no extra keys):


{
  "technical_requirements": {
    "skills": [],
    "tools": []
  }
}


Rules:
- skills: programming languages, frameworks, libraries, databases, cloud platforms.
- tools: developer tools (IDEs, CLIs, package managers, build/test/deploy tools).
- Extract ONLY what is supported by the text (no guessing).
- Return lists with unique items (no duplicates).
- Return JSON only.


CRITICAL INTERPRETATION RULE:
- Extract technologies from the PROJECT DESCRIPTION, even if they are NOT listed anywhere in this prompt.
- Lists in this prompt exist ONLY to normalize spelling/casing/spacing/punctuation for consistency.
- Do NOT omit a clearly mentioned technology just because it is not listed below.


Category guidance using Stack Overflow 2024 sections (for classification only):
- "skills" may include items that belong to:
  1) Programming, scripting, and markup languages
  2) Web frameworks and web technologies
  3) Database environments
  4) Cloud platforms
  5) Other frameworks and libraries (miscellaneous)
- "tools" may include items that belong to:
  1) Developer tools for compiling, building and testing
  2) Collaborative work management and/or code documentation tools


Mapping / normalization rule:
- If the text mentions a technology using a variant/typo/alias, you MAY normalize it ONLY if the target is unambiguous.
- If normalization is ambiguous, keep the original wording from the project description (or omit if unclear).


TARGETED CANONICALIZATION PATCH (NORMALIZATION ONLY — NOT A WHITELIST):
These specific Stack Overflow 2024 labels often appear with spacing/punctuation/case variants.
If (and only if) the project description clearly refers to one of these items, output the EXACT label below.
Otherwise, ignore this list completely and extract normally.


Languages / markup / shell:
- Bash/Shell (all shells)
- HTML/CSS
- Objective-C
- Visual Basic (.Net)


Database environments:
- Cloud Firestore
- Cosmos DB
- Couch DB
- Databricks SQL
- Firebase Realtime Database
- IBM DB2
- Microsoft SQL Server
- Microsoft Access


Cloud platforms:
- Alibaba Cloud
- Amazon Web Services (AWS)
- Digital Ocean
- Google Cloud
- IBM Cloud Or Watson
- Oracle Cloud Infrastructure (OCI)


Web frameworks and web technologies:
- ASP.NET CORE
- Play Framework
- Ruby on Rails


Compilers / build / test / dev tooling:
- GNU GCC
- LLVM's Clang
- Google Test
- Maven (build tool)


Other frameworks and libraries:
- .NET (5+)
- .NET Framework (1.0 - 4.8)
- Apache Kafka
- Apache Spark
- Hugging Face Transformers
- React Native
- Scikit-Learn
- Spring Framework
- Torch/PyTorch


Game engines / platforms:
- Unity 3D
- Unreal Engine


IDEs / editors / developer environments:
- Visual Studio Solution
- Android Studio
- IntelliJ IDEA
- Jupyter Notebook/JupyterLab
- Qt Creator
- Rad Studio (Delphi, C++ Builder)


Collaborative work management and/or code documentation tools:
- GitHub Discussions
  NOTE: If excluded by the Exclusions rule, then OMIT it even if mentioned.


STRICTNESS RULE (to limit hallucinations):
- Do NOT output labels unless the project description explicitly supports them.
- Do NOT map unrelated terms to the labels above.
- If ambiguous, omit.


Output rule:
- Do NOT output "Other (please specify)".
- Do NOT output section headings.
- Output only the technology names.


Normalization rules (apply ONLY when clearly applicable):
1) Cloud platform normalization
- If the text mentions "AWS" or "Amazon Web Services", output: "Amazon Web Services (AWS)"
- If the text mentions "GCP" or "Google Cloud Platform", output: "Google Cloud"
- If the text mentions "OCI" or "Oracle Cloud", output: "Oracle Cloud Infrastructure (OCI)"
- If the text mentions "IBM Cloud" or "Watson", output: "IBM Cloud Or Watson"
- If the text mentions "DigitalOcean", output: "Digital Ocean"


2) .NET / Visual Basic normalization
- If the text mentions ".NET Core" or "ASP.NET Core", output: "ASP.NET CORE"
- If the text mentions "VB.NET" or "Visual Basic .NET", output: "Visual Basic (.Net)"
- If the text mentions ".NET 5" ".NET 6" ".NET 7" ".NET 8" or "modern .NET", output: ".NET (5+)"
- If the text mentions ".NET Framework", output: ".NET Framework (1.0 - 4.8)"


3) Shell normalization
- If the text mentions "Bash" or "Shell scripting", output: "Bash/Shell (all shells)"


4) PyTorch normalization
- If the text mentions "PyTorch" or "Torch", output: "Torch/PyTorch"


Exclusions (ASSUME EVERYONE HAS THESE):
- Do NOT include any Git/GitHub/version control items in tools or skills:
  "Git", "GitHub", "GitHub Actions", "GitLab", "Bitbucket", "SVN", "Mercurial".


If none found: empty lists.
"""


@dataclass
class ProjectExtractorConfig:
    model: str = "openai/gpt-4o-mini"
    temperature: float = 0.0




class ProjectSchemaExtractor:
    def __init__(self, api_key: str, base_url: str, config: Optional[ProjectExtractorConfig] = None):
        self.config = config or ProjectExtractorConfig()
        self.client = OpenAI(api_key=api_key, base_url=base_url)


    @staticmethod
    def safe_json_loads(raw: str) -> Dict[str, Any]:
        raw = (raw or "").strip()
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in model output")
        return json.loads(raw[start : end + 1])


    def extract_requirements(self, description: str) -> Dict[str, Any]:
        resp = self.client.chat.completions.create(
            model=self.config.model,
            temperature=self.config.temperature,
            top_p=1.0,
            presence_penalty=0.0,
            frequency_penalty=0.0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT + "\n\nProject description:\n" + (description or "")},
            ],
        )
        raw = resp.choices[0].message.content
        return self.safe_json_loads(raw)












