# SkillSync - EU Data Protection & Compliance Report

**Date**: January 21, 2026  
**Project**: SkillSync - AI-Powered Team Formation  
**Focus**: GDPR, data protection, and CV processing standards

---

## Executive Summary

SkillSync processes candidate CV data through an AI pipeline combining LLM extraction, embeddings, and team formation algorithms. This report evaluates compliance with EU data protection standards (GDPR, CCPA) and identifies necessary safeguards.

**Overall Status**: ⚠️ **REQUIRES IMMEDIATE ATTENTION** - Current implementation has significant compliance gaps that must be addressed before production deployment.

---

## 1. 🔒 GDPR Compliance Assessment

### 1.1 Legal Basis for Processing

| Aspect | Status | Finding |
|--------|--------|---------|
| **Legal Basis** | ❌ **NOT DEFINED** | No documented lawful basis (Article 6 GDPR) for processing CV data |
| **Consent** | ❌ **MISSING** | No explicit consent mechanism for candidates |
| **Privacy Notice** | ❌ **MISSING** | No privacy policy or data processing disclosure |
| **Purpose Limitation** | ⚠️ **UNCLEAR** | Purpose scope not clearly defined (team formation only?) |
| **Data Subject Rights** | ❌ **NOT IMPLEMENTED** | No mechanism for access/deletion/portability requests |

**Action Required**: Establish clear legal basis (Article 6) - typically:
- **Consent** (Article 6(1)(a)) - Requires explicit opt-in from candidates
- **Contract** (Article 6(1)(b)) - If processing is necessary to fulfill employment contract
- **Legal Obligation** (Article 6(1)(c)) - If required by law
- **Legitimate Interests** (Article 6(1)(f)) - If balancing test proves interest in fair team formation

---

### 1.2 Data Categories & Sensitivity

**Current Data Processed**:
```
✓ Technical skills (low risk)
✓ Tools/frameworks (low risk)
✓ Experience level (low risk)
⚠️ Role/position (medium risk - may indicate age/experience)
⚠️ Availability/constraints (medium risk - may indicate personal circumstances)
⚠️ Collaboration style (medium risk - behavioral data)
⚠️ Communication patterns (medium risk - behavioral data)
❌ Candidate name/ID (personal data - HIGH RISK)
❌ Experience years (can indicate age - SPECIAL CATEGORY)
```

**Risk**: Behavioral and psychological profiling data (Belbin roles, communication style, conflict style) may constitute **special categories of personal data** under Article 9 GDPR if used for employment decisions.

**Recommendation**: 
- Anonymize candidate names/IDs before processing
- Document why behavioral profiling is necessary
- Add explicit safeguards for psychological/personality data

---

### 1.3 Data Minimization & Purpose Limitation

| Principle | Current State | Gap | Fix |
|-----------|---------------|-----|-----|
| **Data Minimization** | Collects: name, skills, experience, personality, collaboration | Excessive collection of behavioral data | Limit to: skills, tools, availability only |
| **Purpose Limitation** | Purpose undefined | No clear scope of use | Document: "Team formation for project X only" |
| **Retention** | No deletion policy | Data persists indefinitely | Implement auto-deletion after project completion |
| **Secondary Use** | No restrictions documented | LLM receives raw CV data | Pseudonymize before LLM processing |

---

### 1.4 Data Processing & LLM Concerns

**⚠️ CRITICAL ISSUES**:

```python
# CURRENT ISSUE: Raw CV data sent to external LLM
extractor = json_extraction.extractor
response = extractor.extract_profiles_from_raw(raw_text)
# ❌ This sends personal data to OpenRouter/OpenAI (third-party processor)
```

**Problems**:
1. **Third-Party Processing**: OpenRouter/OpenAI becomes a Data Processor
2. **Data Transfer**: If servers are outside EU, violates GDPR Chapter 5
3. **No DPA**: No Data Processing Agreement in place
4. **Transparency**: Users may not consent to LLM processing

**Required Fixes**:

```python
# ✅ SOLUTION 1: Pseudonymization before processing
from shared.privacy import anonymize_profile

def extract_profiles_from_raw(raw_text: str) -> List[CandidateProfile]:
    """Extract with privacy-first approach"""
    # Anonymize: remove names, IDs, identifying information
    anonymized = anonymize_profile(raw_text)
    
    # Add mapping for post-processing
    mapping = create_anonymization_mapping(raw_text, anonymized)
    
    # Process anonymized version only
    extracted = openai_client.extract(anonymized)
    
    # Re-attach original IDs (stored securely)
    restored = restore_identifiers(extracted, mapping)
    
    return restored

# ✅ SOLUTION 2: Local processing alternative
def extract_profiles_local(raw_text: str) -> List[CandidateProfile]:
    """Extract using local open-source model (no external data transfer)"""
    from sentence_transformers import CrossEncoder
    from transformers import pipeline
    
    # Use open-source models (Ollama, LocalAI, etc.)
    # Keeps all data on-premises
    pass

# ✅ SOLUTION 3: Encryption in transit & at rest
from cryptography.fernet import Fernet

def process_with_encryption(raw_text: str, encryption_key: bytes):
    """Process with end-to-end encryption"""
    cipher = Fernet(encryption_key)
    encrypted = cipher.encrypt(raw_text.encode())
    # Send encrypted data to LLM API
    # Only decrypt results locally
    pass
```

---

### 1.5 Data Subject Rights (Articles 12-22 GDPR)

**Missing Implementations**:

```python
# Create: src/shared/data_subject_rights.py

class DataSubjectRights:
    """Implement GDPR rights for candidates"""
    
    def right_of_access(self, candidate_id: str) -> Dict[str, Any]:
        """Article 15: Right to access personal data"""
        # Return all data processed about this candidate
        pass
    
    def right_to_rectification(self, candidate_id: str, corrections: Dict) -> None:
        """Article 16: Right to correct inaccurate data"""
        pass
    
    def right_to_erasure(self, candidate_id: str) -> None:
        """Article 17: Right to be forgotten"""
        # Delete all traces: database, cache, embeddings, LLM history
        pass
    
    def right_to_restrict_processing(self, candidate_id: str) -> None:
        """Article 18: Right to restrict processing"""
        # Stop processing but keep data
        pass
    
    def right_to_data_portability(self, candidate_id: str) -> bytes:
        """Article 20: Right to export data in machine-readable format"""
        return json.dumps(self.get_candidate_data(candidate_id))
    
    def right_to_object(self, candidate_id: str) -> None:
        """Article 21: Right to object to processing"""
        pass
    
    def protection_from_automated_decision(self, candidate_id: str) -> None:
        """Article 22: Right not to be subject to solely automated decisions"""
        # Ensure human review of team recommendations
        pass
```

---

## 2. 📋 Data Processing Agreement (DPA)

**Current Status**: ❌ **NOT IN PLACE**

**Required DPA Clauses** (Article 28 GDPR):

```yaml
# Create: docs/DATA_PROCESSING_AGREEMENT.md

Data Processing Agreement (GDPR Article 28):

Parties:
  - Data Controller: [Your Organization]
  - Data Processor: OpenRouter / OpenAI
  
Purpose:
  - Extract structured data from candidate CVs for team formation

Processing Details:
  - Type of data: Skills, experience, collaboration styles, behavioral profiles
  - Categories of data subjects: Job candidates
  - Duration: [Project end date]
  - Data locations: EU/US [specify]

Processor Obligations:
  ✅ Process only on controller's instructions
  ✅ Implement adequate technical measures
  ✅ Sub-processor disclosures
  ✅ Assist with data subject rights
  ✅ Delete data after contract termination
  
Standard Contractual Clauses (SCCs):
  - If processor outside EU: Standard Contractual Clauses Module Three required
  - Transfer Impact Assessment needed
```

---

## 3. 🔐 Technical & Organizational Measures

### 3.1 Missing Security Controls

| Control | GDPR Requirement | Status | Priority |
|---------|------------------|--------|----------|
| **Encryption at Rest** | Article 32 | ❌ MISSING | HIGH |
| **Encryption in Transit** | Article 32 | ⚠️ PARTIAL | HIGH |
| **Access Control** | Article 32 | ❌ MISSING | HIGH |
| **Audit Logging** | Article 32 | ⚠️ PARTIAL | HIGH |
| **Data Backup** | Article 32 | ❌ MISSING | MEDIUM |
| **Incident Response** | Article 33 | ❌ MISSING | HIGH |
| **Privacy by Design** | Article 25 | ❌ MISSING | HIGH |
| **Data Impact Assessment** | Article 35 | ❌ MISSING | HIGH |

**Implementation Required**:

```python
# Create: src/shared/security.py

import os
from cryptography.fernet import Fernet
from pathlib import Path

class DataSecurity:
    """GDPR-compliant security measures"""
    
    def __init__(self):
        # Load encryption key from environment (never hardcode)
        self.encryption_key = os.getenv("DATA_ENCRYPTION_KEY")
        if not self.encryption_key:
            raise ValueError("DATA_ENCRYPTION_KEY not set - required for GDPR compliance")
        self.cipher = Fernet(self.encryption_key)
    
    def encrypt_at_rest(self, data: bytes, file_path: Path) -> None:
        """Article 32(1)(b) - Encryption at rest"""
        encrypted = self.cipher.encrypt(data)
        # Write with restricted permissions
        file_path.write_bytes(encrypted)
        os.chmod(file_path, 0o600)  # Read/write owner only
    
    def decrypt_at_rest(self, file_path: Path) -> bytes:
        """Decrypt data at rest"""
        encrypted = file_path.read_bytes()
        return self.cipher.decrypt(encrypted)
    
    def log_access(self, user: str, candidate_id: str, action: str) -> None:
        """Article 32(1)(c) - Audit logging"""
        # Log all access to candidate data
        with open("audit.log", "a") as f:
            f.write(f"{datetime.now()} | {user} | {candidate_id} | {action}\n")
    
    def anonymize_for_processing(self, candidate: Dict) -> Tuple[Dict, Dict]:
        """Pseudonymization before third-party processing"""
        import hashlib
        
        mapping = {}
        anonymized = {}
        
        # Replace identifying fields with hashes
        for key, value in candidate.items():
            if key in ["name", "id", "email"]:
                hash_val = hashlib.sha256(str(value).encode()).hexdigest()[:8]
                mapping[key] = {value: hash_val}
                anonymized[key] = hash_val
            else:
                anonymized[key] = value
        
        return anonymized, mapping
```

---

## 4. 🚨 Incident Response & Data Breaches

**Current Status**: ❌ **NO PLAN**

**GDPR Breach Notification Requirements** (Article 33-34):

```python
# Create: src/shared/incident_response.py

from datetime import datetime
from pathlib import Path
import json

class IncidentResponse:
    """GDPR Article 33 - Data Breach Notification"""
    
    def report_breach(
        self,
        affected_candidates: List[str],
        breach_type: str,
        discovery_date: datetime,
        data_categories: List[str],
        likely_risk: str = "low"
    ) -> None:
        """
        Notify supervisory authority within 72 hours of discovery
        Notify affected individuals without undue delay if high risk
        """
        
        breach_record = {
            "report_date": datetime.now().isoformat(),
            "discovery_date": discovery_date.isoformat(),
            "affected_count": len(affected_candidates),
            "data_categories": data_categories,
            "breach_type": breach_type,
            "likely_risk": likely_risk,
            "action_taken": [
                "✅ Contained the breach",
                "✅ Secured systems",
                "✅ Preserved evidence",
                "✅ Notified supervisory authority (within 72h)",
                "✅ Notified individuals (if high risk, without undue delay)"
            ]
        }
        
        # Save incident record
        Path("incident_reports").mkdir(exist_ok=True)
        incident_file = Path("incident_reports") / f"breach_{discovery_date.isoformat()}.json"
        json.dump(breach_record, incident_file.open("w"), indent=2)
        
        # TODO: Automatically notify:
        # 1. Supervisory authority (email to DPA)
        # 2. Affected individuals (if Article 34 applies)
        # 3. Internal stakeholders
```

---

## 5. 📊 Data Protection Impact Assessment (DPIA)

**Required Under**: Article 35 GDPR (High-risk processing)

**Assessment Status**: ❌ **NOT COMPLETED**

```markdown
# Data Protection Impact Assessment (DPIA)

## Scope
Processing of candidate CV data through LLM-based extraction and AI team formation

## High-Risk Factors
1. **Automated Decision-Making** (Article 22): Teams recommended algorithmically
2. **Behavioral Profiling**: Personality, communication, conflict analysis
3. **Special Categories**: Experience level may indicate age (Article 9)
4. **Large Scale**: Multiple candidates processed together
5. **Vulnerable Groups**: Job applicants may be vulnerable
6. **Data Sharing**: CV data shared with external LLMs

## Necessity & Proportionality
- **Necessity**: Team formation requires skills/experience data
- **Proportionality**: Behavioral profiling may be excessive
- **Alternatives**: Consider skills-only approach vs. behavioral analysis

## Risks Identified
- **Discrimination**: Behavioral profiling could disadvantage certain groups
- **Data Breach**: Candidate CVs exposed via LLM APIs
- **Profiling**: Creating psychological profiles without consent
- **Lack of Transparency**: Candidates may not understand team algorithm

## Mitigation Measures
- [ ] Anonymize data before LLM processing
- [ ] Implement human review of recommendations
- [ ] Limit data collection to necessary fields
- [ ] Provide transparency in team formation process
- [ ] Establish right to object to automated decisions
- [ ] Use local processing instead of cloud LLMs
- [ ] Implement audit logging and breach response plan

## Conclusion
**DPIA Status**: ❌ UNMITIGATED RISKS - Cannot proceed without implementing mitigations
```

---

## 6. 🏷️ Data Retention & Deletion Policy

**Current Status**: ❌ **NO RETENTION POLICY**

**GDPR Requirement**: Storage Limitation Principle (Article 5(1)(e))

```python
# Create: src/shared/retention_policy.py

from datetime import datetime, timedelta
from pathlib import Path
import json

class RetentionPolicy:
    """GDPR Article 5 - Storage Limitation"""
    
    RETENTION_PERIODS = {
        "cv_raw_text": timedelta(days=30),  # Delete after extraction
        "candidate_profiles": timedelta(days=90),  # Delete after project ends + 30 days
        "embeddings": timedelta(days=90),
        "team_recommendations": timedelta(days=365),  # Keep for review
        "audit_logs": timedelta(days=365),  # Regulatory requirement
    }
    
    def schedule_deletion(self, data_type: str, candidate_id: str) -> None:
        """Schedule data for automatic deletion"""
        retention_period = self.RETENTION_PERIODS.get(data_type, timedelta(days=90))
        deletion_date = datetime.now() + retention_period
        
        deletion_record = {
            "candidate_id": candidate_id,
            "data_type": data_type,
            "scheduled_deletion": deletion_date.isoformat()
        }
        
        Path("scheduled_deletions").mkdir(exist_ok=True)
        with open(Path("scheduled_deletions") / f"{candidate_id}_{data_type}.json", "w") as f:
            json.dump(deletion_record, f)
    
    def purge_expired_data(self) -> None:
        """Remove data that exceeded retention period"""
        now = datetime.now()
        
        for deletion_file in Path("scheduled_deletions").glob("*.json"):
            record = json.load(deletion_file.open())
            scheduled_date = datetime.fromisoformat(record["scheduled_deletion"])
            
            if scheduled_date <= now:
                # Perform actual deletion
                self._delete_candidate_data(record["candidate_id"])
                deletion_file.unlink()
    
    def _delete_candidate_data(self, candidate_id: str) -> None:
        """Completely remove candidate from all systems"""
        # Delete from database
        # Delete from embeddings cache
        # Delete from LLM processing logs
        # Overwrite with zeros before deletion (secure deletion)
        pass
```

---

## 7. ✅ Compliance Checklist & Action Plan

### Immediate Actions (Week 1)

- [ ] **Legal Basis**: Document which Article 6 basis applies (likely Consent)
- [ ] **Privacy Notice**: Create and display privacy policy to candidates
- [ ] **Consent Form**: Implement consent mechanism before processing
- [ ] **Data Minimization**: Remove unnecessary behavioral/psychological data
- [ ] **Anonymization**: Anonymize before sending to external LLMs
- [ ] **DPA**: Establish Data Processing Agreement with OpenRouter/OpenAI

### Short-Term (Week 2-4)

- [ ] **Data Subject Rights**: Implement access/deletion/portability endpoints
- [ ] **Encryption**: Enable encryption at rest and in transit
- [ ] **Audit Logging**: Add comprehensive access logging
- [ ] **Incident Response**: Create breach notification procedure
- [ ] **DPIA**: Complete Data Protection Impact Assessment

### Medium-Term (Month 2)

- [ ] **Retention Policy**: Implement automatic data deletion
- [ ] **Training**: Privacy training for development team
- [ ] **Local Processing**: Option for on-premises processing
- [ ] **Security Audit**: Third-party security assessment
- [ ] **Privacy by Design**: Rebuild architecture with privacy-first approach

### Long-Term (Month 3+)

- [ ] **Compliance Certification**: ISO 27001 / SOC 2 if needed
- [ ] **Regular Audits**: Quarterly DPIA reviews
- [ ] **Monitoring**: Continuous compliance monitoring
- [ ] **Updates**: Keep up with GDPR guidance updates

---

## 8. 🌍 International Compliance

### CCPA (California Consumer Privacy Act)

| Right | Status | Action |
|-------|--------|--------|
| Right to Know | ❌ MISSING | Implement data access endpoint |
| Right to Delete | ❌ MISSING | Implement erasure endpoint |
| Right to Opt-Out | ❌ MISSING | Consent mechanism needed |
| No Discrimination | ⚠️ UNCLEAR | Algorithm must not discriminate |
| Sensitive Data | ⚠️ UNCLEAR | Behavioral data requires additional consent |

---

## 9. 🎯 Recommended Architecture for Compliance

```
┌─────────────────────────────────────────────────────────┐
│         Privacy-First SkillSync Architecture            │
└─────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│  1. Consent & Transparency Layer                  │
│  - Privacy notice display                          │
│  - Explicit consent collection                     │
│  - Purpose limitation declaration                  │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  2. Data Minimization & Anonymization             │
│  - Remove identifying information (name, email)   │
│  - Keep only: skills, tools, availability        │
│  - Hash candidate IDs before processing           │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  3. Secure Processing                             │
│  - End-to-end encryption in transit               │
│  - Encryption at rest in database                 │
│  - Audit logging of all access                    │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  4. Data Subject Rights                           │
│  - Access: GET /api/candidate/{id}               │
│  - Deletion: DELETE /api/candidate/{id}          │
│  - Portability: GET /api/candidate/{id}/export   │
│  - Objection: POST /api/candidate/{id}/object    │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  5. Retention & Deletion                          │
│  - Automatic deletion after retention period      │
│  - Secure overwrite before deletion               │
│  - Audit trail of deletions                       │
└──────────────────────────────────────────────────┘
```

---

## 10. 📄 Implementation Priority

**🔴 CRITICAL** (Must implement before production):
1. Establish legal basis (consent/contract)
2. Privacy notice & consent mechanism
3. Data minimization (remove behavioral data)
4. Anonymization before LLM processing
5. Data Processing Agreement with providers
6. Encryption at rest
7. Incident response plan

**🟡 HIGH** (Implement within month):
1. Data subject rights endpoints
2. Audit logging
3. Retention policy implementation
4. DPIA completion

**🟢 MEDIUM** (Implement within 3 months):
1. ISO 27001 preparation
2. Local processing option
3. Regular compliance audits
4. Security assessment

---

## Summary & Recommendations

**Current Status**: ⚠️ **NOT COMPLIANT** - Multiple critical gaps

**Key Issues**:
1. No legal basis for data processing defined
2. No consent mechanism implemented
3. Sensitive behavioral data processed without safeguards
4. External LLM processing without proper DPA
5. No data subject rights implementation
6. Missing encryption and audit controls
7. No retention/deletion policy

**Path Forward**:
- Implement **critical items immediately** before production
- Establish **privacy-first architecture**
- Complete **DPIA** to understand and mitigate risks
- Prepare for **potential DPA/regulatory review**
- Consider **on-premises processing** as safer alternative

**Estimated Effort**: 2-3 weeks for critical items, 2-3 months for full compliance

---

**Report prepared**: January 21, 2026  
**Compliance Status**: ❌ Non-compliant - Remediation required  
**Next Review**: After implementation of critical measures
