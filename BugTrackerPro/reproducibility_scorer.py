"""
Reproducibility scoring system for bug reports
Analyzes bug descriptions and assigns reproducibility scores
"""

import re
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class ReproducibilityMetrics:
    score: float
    confidence: str
    factors: List[str]
    missing_info: List[str]
    recommendations: List[str]

class ReproducibilityScorer:
    def __init__(self):
        self.step_indicators = [
            r'\d+\.\s+', r'step \d+', r'first', r'then', r'next', r'finally',
            r'click', r'navigate', r'enter', r'select', r'upload', r'submit'
        ]
        
        self.environment_indicators = [
            r'browser', r'chrome', r'firefox', r'safari', r'edge',
            r'windows', r'mac', r'linux', r'ios', r'android',
            r'version', r'operating system'
        ]
        
        self.specificity_indicators = [
            r'error message', r'console', r'network', r'status code',
            r'exact text', r'screenshot', r'specific', r'precisely'
        ]
    
    def score_bug_report(self, title: str, description: str, attachments: List = None) -> ReproducibilityMetrics:
        """Calculate reproducibility score for a bug report"""
        
        factors = []
        missing_info = []
        recommendations = []
        
        # Combine title and description for analysis
        full_text = f"{title} {description}".lower()
        
        # Factor 1: Clear steps (0-30 points)
        steps_score = self._score_reproduction_steps(full_text, factors, missing_info)
        
        # Factor 2: Environment details (0-20 points)
        env_score = self._score_environment_info(full_text, factors, missing_info)
        
        # Factor 3: Specificity and detail (0-20 points)
        detail_score = self._score_specificity(full_text, factors, missing_info)
        
        # Factor 4: Error information (0-15 points)
        error_score = self._score_error_info(full_text, factors, missing_info)
        
        # Factor 5: Attachments (0-10 points)
        attachment_score = self._score_attachments(attachments, factors, missing_info)
        
        # Factor 6: Description length and clarity (0-5 points)
        clarity_score = self._score_clarity(description, factors, missing_info)
        
        # Calculate total score
        total_score = steps_score + env_score + detail_score + error_score + attachment_score + clarity_score
        
        # Determine confidence level
        confidence = self._determine_confidence(total_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(missing_info, total_score)
        
        return ReproducibilityMetrics(
            score=min(100, total_score),
            confidence=confidence,
            factors=factors,
            missing_info=missing_info,
            recommendations=recommendations
        )
    
    def _score_reproduction_steps(self, text: str, factors: List, missing_info: List) -> float:
        """Score based on clarity of reproduction steps"""
        score = 0
        
        # Check for numbered steps or sequential indicators
        step_patterns = sum(1 for pattern in self.step_indicators if re.search(pattern, text))
        
        if step_patterns >= 3:
            score += 30
            factors.append("Clear step-by-step instructions provided")
        elif step_patterns >= 1:
            score += 15
            factors.append("Some reproduction steps mentioned")
        else:
            missing_info.append("Clear step-by-step reproduction instructions")
        
        # Bonus for action words
        action_words = ['click', 'type', 'navigate', 'select', 'upload', 'submit', 'press']
        action_count = sum(1 for word in action_words if word in text)
        score += min(10, action_count * 2)
        
        return score
    
    def _score_environment_info(self, text: str, factors: List, missing_info: List) -> float:
        """Score based on environment and system information"""
        score = 0
        
        env_patterns = sum(1 for pattern in self.environment_indicators if re.search(pattern, text))
        
        if env_patterns >= 2:
            score += 20
            factors.append("Environment details provided (browser, OS, etc.)")
        elif env_patterns >= 1:
            score += 10
            factors.append("Some environment information mentioned")
        else:
            missing_info.append("Browser and operating system information")
        
        return score
    
    def _score_specificity(self, text: str, factors: List, missing_info: List) -> float:
        """Score based on specificity and technical details"""
        score = 0
        
        specific_patterns = sum(1 for pattern in self.specificity_indicators if re.search(pattern, text))
        
        if specific_patterns >= 2:
            score += 20
            factors.append("Specific technical details provided")
        elif specific_patterns >= 1:
            score += 10
            factors.append("Some specific details mentioned")
        else:
            missing_info.append("Specific error messages or technical details")
        
        return score
    
    def _score_error_info(self, text: str, factors: List, missing_info: List) -> float:
        """Score based on error information"""
        score = 0
        
        error_indicators = ['error', 'exception', 'fails', 'crash', 'broken', 'bug', 'issue']
        error_count = sum(1 for indicator in error_indicators if indicator in text)
        
        if error_count >= 2:
            score += 15
            factors.append("Clear error descriptions provided")
        elif error_count >= 1:
            score += 8
            factors.append("Error mentioned")
        else:
            missing_info.append("Clear description of what goes wrong")
        
        return score
    
    def _score_attachments(self, attachments: List, factors: List, missing_info: List) -> float:
        """Score based on attachments provided"""
        score = 0
        
        if attachments and len(attachments) > 0:
            score += 10
            factors.append(f"Supporting files attached ({len(attachments)} files)")
        else:
            missing_info.append("Screenshots, logs, or other supporting files")
        
        return score
    
    def _score_clarity(self, description: str, factors: List, missing_info: List) -> float:
        """Score based on description length and clarity"""
        score = 0
        
        if len(description) >= 100:
            score += 5
            factors.append("Detailed description provided")
        else:
            missing_info.append("More detailed description")
        
        return score
    
    def _determine_confidence(self, score: float) -> str:
        """Determine confidence level based on score"""
        if score >= 80:
            return "Very High"
        elif score >= 60:
            return "High"
        elif score >= 40:
            return "Medium"
        elif score >= 20:
            return "Low"
        else:
            return "Very Low"
    
    def _generate_recommendations(self, missing_info: List, score: float) -> List[str]:
        """Generate recommendations for improving reproducibility"""
        recommendations = []
        
        if score < 50:
            recommendations.append("Consider adding more detailed step-by-step instructions")
        
        if "Environment details" in str(missing_info):
            recommendations.append("Include browser version, operating system, and device information")
        
        if "error messages" in str(missing_info):
            recommendations.append("Include exact error messages, console logs, or stack traces")
        
        if "supporting files" in str(missing_info):
            recommendations.append("Attach screenshots, logs, or video recordings if possible")
        
        if not recommendations:
            recommendations.append("Excellent reproducibility! This report provides clear instructions.")
        
        return recommendations