"""
Critic/Verifier for OriginFD AI Orchestrator.
Reviews and validates AI outputs for safety, quality, and compliance.
"""
import asyncio
import logging
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
from pydantic import BaseModel
from enum import Enum

try:
    from ..tools.registry import ToolResult
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from tools.registry import ToolResult

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationIssue(BaseModel):
    """Individual validation issue."""
    issue_id: str
    severity: ValidationSeverity
    category: str  # "safety", "quality", "compliance", "consistency", "accuracy"
    description: str
    location: Optional[str] = None  # Where in the output the issue was found
    suggested_fix: Optional[str] = None
    metadata: Dict[str, Any] = {}


class VerificationResult(BaseModel):
    """Result of output verification."""
    is_valid: bool
    overall_score: float  # 0.0 to 1.0
    issues: List[ValidationIssue]
    quality_metrics: Dict[str, float]
    safety_score: float
    compliance_score: float
    accuracy_score: float
    consistency_score: float
    verification_timestamp: datetime
    verification_duration_ms: int


class CriticVerifier:
    """
    Critic/Verifier system for validating AI outputs.
    
    Features:
    - Safety validation (harmful content, misinformation)
    - Quality assessment (coherence, relevance, completeness)
    - Compliance checking (data privacy, regulatory requirements)
    - Accuracy verification (factual correctness, calculations)
    - Consistency validation (logical consistency, contradictions)
    - Output sanitization and correction
    """
    
    def __init__(self):
        # Validation rules
        self.safety_rules = self._initialize_safety_rules()
        self.quality_rules = self._initialize_quality_rules()
        self.compliance_rules = self._initialize_compliance_rules()
        
        # Scoring weights
        self.scoring_weights = {
            "safety": 0.3,
            "quality": 0.25,
            "compliance": 0.2,
            "accuracy": 0.15,
            "consistency": 0.1
        }
        
        # Validation thresholds
        self.validation_thresholds = {
            "min_overall_score": 0.7,
            "max_critical_issues": 0,
            "max_error_issues": 2,
            "min_safety_score": 0.8,
            "min_compliance_score": 0.9
        }
        
        # Content filters
        self.pii_patterns = self._initialize_pii_patterns()
        self.harmful_content_patterns = self._initialize_harmful_patterns()
        
        logger.info("CriticVerifier initialized")
    
    async def verify_results(
        self,
        plan: Any,  # PlanningResult
        execution_results: List[ToolResult],
        context: Dict[str, Any]
    ) -> VerificationResult:
        """Verify and validate execution results."""
        start_time = datetime.utcnow()
        
        logger.info(f"Verifying results for plan {plan.plan_id}")
        
        try:
            all_issues = []
            quality_metrics = {}
            
            # Combine all outputs for analysis
            combined_output = self._combine_outputs(execution_results)
            
            # Safety validation
            safety_issues, safety_score = await self._validate_safety(
                combined_output, context
            )
            all_issues.extend(safety_issues)
            
            # Quality assessment
            quality_issues, quality_score = await self._assess_quality(
                combined_output, plan, context
            )
            all_issues.extend(quality_issues)
            quality_metrics["quality"] = quality_score
            
            # Compliance checking
            compliance_issues, compliance_score = await self._check_compliance(
                combined_output, context
            )
            all_issues.extend(compliance_issues)
            
            # Accuracy verification
            accuracy_issues, accuracy_score = await self._verify_accuracy(
                combined_output, execution_results, context
            )
            all_issues.extend(accuracy_issues)
            
            # Consistency validation
            consistency_issues, consistency_score = await self._validate_consistency(
                combined_output, execution_results
            )
            all_issues.extend(consistency_issues)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                safety_score, quality_score, compliance_score,
                accuracy_score, consistency_score
            )
            
            # Determine if results are valid
            is_valid = self._determine_validity(all_issues, overall_score)
            
            verification_duration = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
            result = VerificationResult(
                is_valid=is_valid,
                overall_score=overall_score,
                issues=all_issues,
                quality_metrics={
                    "safety": safety_score,
                    "quality": quality_score,
                    "compliance": compliance_score,
                    "accuracy": accuracy_score,
                    "consistency": consistency_score
                },
                safety_score=safety_score,
                compliance_score=compliance_score,
                accuracy_score=accuracy_score,
                consistency_score=consistency_score,
                verification_timestamp=start_time,
                verification_duration_ms=verification_duration
            )
            
            logger.info(
                f"Verification complete: valid={is_valid}, score={overall_score:.2f}, "
                f"issues={len(all_issues)}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            
            # Return failed verification
            return VerificationResult(
                is_valid=False,
                overall_score=0.0,
                issues=[ValidationIssue(
                    issue_id=str(uuid4()),
                    severity=ValidationSeverity.CRITICAL,
                    category="system",
                    description=f"Verification system error: {str(e)}"
                )],
                quality_metrics={},
                safety_score=0.0,
                compliance_score=0.0,
                accuracy_score=0.0,
                consistency_score=0.0,
                verification_timestamp=start_time,
                verification_duration_ms=int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                )
            )
    
    async def sanitize_output(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> Tuple[str, List[str]]:
        """Sanitize output by removing/masking sensitive content."""
        sanitized_content = content
        applied_sanitizations = []
        
        # Remove PII
        for pattern_name, pattern in self.pii_patterns.items():
            if re.search(pattern, sanitized_content):
                sanitized_content = re.sub(pattern, f"[REDACTED_{pattern_name.upper()}]", sanitized_content)
                applied_sanitizations.append(f"Redacted {pattern_name}")
        
        # Remove harmful content
        for pattern_name, pattern in self.harmful_content_patterns.items():
            if re.search(pattern, sanitized_content, re.IGNORECASE):
                sanitized_content = re.sub(pattern, "[CONTENT_FILTERED]", sanitized_content, flags=re.IGNORECASE)
                applied_sanitizations.append(f"Filtered {pattern_name}")
        
        return sanitized_content, applied_sanitizations
    
    # Private validation methods
    
    async def _validate_safety(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> Tuple[List[ValidationIssue], float]:
        """Validate content for safety issues."""
        issues = []
        safety_score = 1.0
        
        # Check for harmful content
        for rule_name, rule in self.safety_rules.items():
            if rule["type"] == "pattern":
                if re.search(rule["pattern"], content, re.IGNORECASE):
                    issues.append(ValidationIssue(
                        issue_id=str(uuid4()),
                        severity=ValidationSeverity(rule["severity"]),
                        category="safety",
                        description=rule["description"],
                        suggested_fix=rule.get("suggested_fix"),
                        metadata={"rule": rule_name}
                    ))
                    safety_score -= rule["penalty"]
        
        # Check for PII exposure
        for pattern_name, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                issues.append(ValidationIssue(
                    issue_id=str(uuid4()),
                    severity=ValidationSeverity.WARNING,
                    category="safety",
                    description=f"Potential PII exposure: {pattern_name}",
                    suggested_fix="Remove or mask personal information",
                    metadata={"pii_type": pattern_name, "matches_count": len(matches)}
                ))
                safety_score -= 0.1
        
        # Check content length (potential prompt injection)
        if len(content) > 50000:  # Very long responses might indicate issues
            issues.append(ValidationIssue(
                issue_id=str(uuid4()),
                severity=ValidationSeverity.WARNING,
                category="safety",
                description="Unusually long response detected",
                suggested_fix="Review for potential prompt injection",
                metadata={"content_length": len(content)}
            ))
            safety_score -= 0.05
        
        return issues, max(0.0, safety_score)
    
    async def _assess_quality(
        self,
        content: str,
        plan: Any,
        context: Dict[str, Any]
    ) -> Tuple[List[ValidationIssue], float]:
        """Assess content quality."""
        issues = []
        quality_score = 1.0
        
        # Check completeness
        if len(content.strip()) < 50:
            issues.append(ValidationIssue(
                issue_id=str(uuid4()),
                severity=ValidationSeverity.WARNING,
                category="quality",
                description="Response appears too short or incomplete",
                suggested_fix="Provide more detailed response",
                metadata={"content_length": len(content)}
            ))
            quality_score -= 0.2
        
        # Check for placeholder text
        placeholders = ["TODO", "TBD", "PLACEHOLDER", "[INSERT", "[REPLACE"]
        for placeholder in placeholders:
            if placeholder in content.upper():
                issues.append(ValidationIssue(
                    issue_id=str(uuid4()),
                    severity=ValidationSeverity.ERROR,
                    category="quality",
                    description=f"Placeholder text found: {placeholder}",
                    suggested_fix="Replace placeholder with actual content",
                    metadata={"placeholder": placeholder}
                ))
                quality_score -= 0.15
        
        # Check coherence (basic)
        sentences = content.split('.')
        if len(sentences) > 5:
            # Look for repeated sentences (sign of poor quality)
            sentence_counts = {}
            for sentence in sentences:
                clean_sentence = sentence.strip().lower()
                if len(clean_sentence) > 10:
                    sentence_counts[clean_sentence] = sentence_counts.get(clean_sentence, 0) + 1
            
            repeated_sentences = [s for s, count in sentence_counts.items() if count > 1]
            if repeated_sentences:
                issues.append(ValidationIssue(
                    issue_id=str(uuid4()),
                    severity=ValidationSeverity.WARNING,
                    category="quality",
                    description="Repeated sentences detected",
                    suggested_fix="Remove duplicate content",
                    metadata={"repeated_count": len(repeated_sentences)}
                ))
                quality_score -= 0.1
        
        # Check relevance to task
        task_description = plan.task_description.lower()
        content_lower = content.lower()
        
        # Extract key terms from task description
        key_terms = re.findall(r'\b\w{4,}\b', task_description)
        key_terms = [term for term in key_terms if term not in ['this', 'that', 'with', 'from', 'they', 'have']]
        
        if key_terms:
            relevant_terms = sum(1 for term in key_terms if term in content_lower)
            relevance_ratio = relevant_terms / len(key_terms)
            
            if relevance_ratio < 0.3:
                issues.append(ValidationIssue(
                    issue_id=str(uuid4()),
                    severity=ValidationSeverity.WARNING,
                    category="quality",
                    description="Response may not be relevant to the task",
                    suggested_fix="Ensure response addresses the specific task requirements",
                    metadata={"relevance_ratio": relevance_ratio}
                ))
                quality_score -= 0.2
        
        return issues, max(0.0, quality_score)
    
    async def _check_compliance(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> Tuple[List[ValidationIssue], float]:
        """Check compliance with regulations and policies."""
        issues = []
        compliance_score = 1.0
        
        # Check for compliance rules
        for rule_name, rule in self.compliance_rules.items():
            if rule["type"] == "required_disclaimer":
                if rule["pattern"] not in content:
                    issues.append(ValidationIssue(
                        issue_id=str(uuid4()),
                        severity=ValidationSeverity.WARNING,
                        category="compliance",
                        description=rule["description"],
                        suggested_fix=rule.get("suggested_fix"),
                        metadata={"rule": rule_name}
                    ))
                    compliance_score -= rule["penalty"]
            
            elif rule["type"] == "prohibited_content":
                if re.search(rule["pattern"], content, re.IGNORECASE):
                    issues.append(ValidationIssue(
                        issue_id=str(uuid4()),
                        severity=ValidationSeverity.ERROR,
                        category="compliance",
                        description=rule["description"],
                        suggested_fix=rule.get("suggested_fix"),
                        metadata={"rule": rule_name}
                    ))
                    compliance_score -= rule["penalty"]
        
        # Check data residency requirements
        if context.get("data_residency_required"):
            # TODO: Implement actual data residency validation
            pass
        
        return issues, max(0.0, compliance_score)
    
    async def _verify_accuracy(
        self,
        content: str,
        execution_results: List[ToolResult],
        context: Dict[str, Any]
    ) -> Tuple[List[ValidationIssue], float]:
        """Verify accuracy of the content."""
        issues = []
        accuracy_score = 1.0
        
        # Check for mathematical inconsistencies
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', content)
        if len(numbers) > 5:
            # Look for obviously wrong calculations
            # This is a simplified check - in practice, would be more sophisticated
            for i, result in enumerate(execution_results):
                if result.success and "calculation" in str(result.content).lower():
                    # Basic validation that numbers in content match tool outputs
                    # TODO: Implement more sophisticated accuracy checking
                    pass
        
        # Check for contradictory statements
        # TODO: Implement contradiction detection
        
        # Check for factual accuracy against known databases
        # TODO: Implement fact-checking integration
        
        return issues, accuracy_score
    
    async def _validate_consistency(
        self,
        content: str,
        execution_results: List[ToolResult]
    ) -> Tuple[List[ValidationIssue], float]:
        """Validate logical consistency."""
        issues = []
        consistency_score = 1.0
        
        # Check for logical contradictions
        # TODO: Implement more sophisticated consistency checking
        
        # Check consistency with tool results
        for result in execution_results:
            if result.success and result.content:
                # Basic check that content doesn't contradict tool results
                # TODO: Implement semantic consistency checking
                pass
        
        return issues, consistency_score
    
    def _combine_outputs(self, execution_results: List[ToolResult]) -> str:
        """Combine all execution results into a single text for analysis."""
        combined_parts = []
        
        for result in execution_results:
            if result.success and result.content:
                if isinstance(result.content, dict):
                    combined_parts.append(json.dumps(result.content, indent=2))
                else:
                    combined_parts.append(str(result.content))
        
        return "\n\n".join(combined_parts)
    
    def _calculate_overall_score(
        self,
        safety_score: float,
        quality_score: float,
        compliance_score: float,
        accuracy_score: float,
        consistency_score: float
    ) -> float:
        """Calculate weighted overall score."""
        return (
            safety_score * self.scoring_weights["safety"] +
            quality_score * self.scoring_weights["quality"] +
            compliance_score * self.scoring_weights["compliance"] +
            accuracy_score * self.scoring_weights["accuracy"] +
            consistency_score * self.scoring_weights["consistency"]
        )
    
    def _determine_validity(
        self,
        issues: List[ValidationIssue],
        overall_score: float
    ) -> bool:
        """Determine if results are valid based on issues and score."""
        # Count issues by severity
        critical_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.CRITICAL)
        error_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.ERROR)
        
        # Check against thresholds
        if critical_count > self.validation_thresholds["max_critical_issues"]:
            return False
        
        if error_count > self.validation_thresholds["max_error_issues"]:
            return False
        
        if overall_score < self.validation_thresholds["min_overall_score"]:
            return False
        
        return True
    
    def _initialize_safety_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize safety validation rules."""
        return {
            "harmful_instructions": {
                "type": "pattern",
                "pattern": r"(how to (harm|hurt|damage|destroy|kill|attack))",
                "severity": "critical",
                "description": "Content contains harmful instructions",
                "penalty": 0.5,
                "suggested_fix": "Remove harmful content"
            },
            "personal_attacks": {
                "type": "pattern", 
                "pattern": r"(you are (stupid|dumb|worthless|useless))",
                "severity": "error",
                "description": "Content contains personal attacks",
                "penalty": 0.3,
                "suggested_fix": "Use respectful language"
            },
            "misinformation_indicators": {
                "type": "pattern",
                "pattern": r"(definitely|absolutely|100% certain|guaranteed) (cure|fix|solve)",
                "severity": "warning",
                "description": "Content may contain overstated claims",
                "penalty": 0.1,
                "suggested_fix": "Use more measured language"
            }
        }
    
    def _initialize_quality_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize quality assessment rules."""
        return {
            "min_length": {
                "type": "length",
                "min_chars": 50,
                "severity": "warning",
                "description": "Response too short",
                "penalty": 0.2
            },
            "max_length": {
                "type": "length", 
                "max_chars": 10000,
                "severity": "warning",
                "description": "Response too long",
                "penalty": 0.1
            }
        }
    
    def _initialize_compliance_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize compliance checking rules."""
        return {
            "financial_disclaimer": {
                "type": "required_disclaimer",
                "pattern": "not financial advice",
                "severity": "warning",
                "description": "Missing financial advice disclaimer",
                "penalty": 0.2,
                "suggested_fix": "Add appropriate disclaimer"
            },
            "personal_data_usage": {
                "type": "prohibited_content",
                "pattern": r"(store|save|remember) your (password|ssn|credit card)",
                "severity": "error", 
                "description": "Content suggests storing personal data",
                "penalty": 0.4,
                "suggested_fix": "Remove references to storing personal data"
            }
        }
    
    def _initialize_pii_patterns(self) -> Dict[str, str]:
        """Initialize PII detection patterns."""
        return {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
        }
    
    def _initialize_harmful_patterns(self) -> Dict[str, str]:
        """Initialize harmful content patterns."""
        return {
            "violence": r"(kill|murder|attack|harm|hurt|destroy) (people|person|someone)",
            "illegal_activities": r"(how to (steal|rob|hack|break into))",
            "hate_speech": r"(all (jews|muslims|christians|blacks|whites) are)"
        }
