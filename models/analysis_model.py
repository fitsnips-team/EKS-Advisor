"""
Analysis Model - Represents analysis results and AI processing
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class SecurityClassification(Enum):
    """Data sensitivity levels"""
    PUBLIC = "public"
    INTERNAL = "internal" 
    HIGHLY_SENSITIVE = "highly_sensitive"
    CRITICAL = "critical"


class AnalysisStatus(Enum):
    """Analysis processing status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Recommendation:
    """Represents a single recommendation"""
    title: str
    description: str
    priority: str  # high, medium, low
    category: str  # performance, security, reliability, etc.
    action_items: List[str] = field(default_factory=list)
    kubectl_commands: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'category': self.category,
            'action_items': self.action_items,
            'kubectl_commands': self.kubectl_commands
        }


@dataclass
class EventAnalysis:
    """Analysis of a specific event or event pattern"""
    event_reason: str
    event_count: int
    severity: str
    root_cause: str
    impact_assessment: str
    recommendations: List[Recommendation] = field(default_factory=list)
    confidence_score: float = 0.0  # 0-1
    
    def to_dict(self) -> Dict:
        return {
            'event_reason': self.event_reason,
            'event_count': self.event_count,
            'severity': self.severity,
            'root_cause': self.root_cause,
            'impact_assessment': self.impact_assessment,
            'recommendations': [r.to_dict() for r in self.recommendations],
            'confidence_score': self.confidence_score
        }


@dataclass
class ClusterHealthScore:
    """Overall cluster health assessment"""
    score: int  # 0-100
    status: str  # excellent, good, needs_attention, critical
    factors: Dict[str, int] = field(default_factory=dict)  # Factor scores
    trend: Optional[str] = None  # improving, stable, declining
    
    def to_dict(self) -> Dict:
        return {
            'score': self.score,
            'status': self.status,
            'factors': self.factors,
            'trend': self.trend
        }


@dataclass
class AnalysisResult:
    """Complete analysis result"""
    cluster_name: str
    analysis_timestamp: datetime
    status: AnalysisStatus
    health_score: ClusterHealthScore
    event_analyses: List[EventAnalysis] = field(default_factory=list)
    security_assessment: Dict = field(default_factory=dict)
    performance_insights: Dict = field(default_factory=dict)
    executive_summary: str = ""
    processing_time_seconds: float = 0.0
    ai_model_used: str = ""
    data_classification: SecurityClassification = SecurityClassification.INTERNAL
    
    def to_dict(self) -> Dict:
        return {
            'cluster_name': self.cluster_name,
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'status': self.status.value,
            'health_score': self.health_score.to_dict(),
            'event_analyses': [ea.to_dict() for ea in self.event_analyses],
            'security_assessment': self.security_assessment,
            'performance_insights': self.performance_insights,
            'executive_summary': self.executive_summary,
            'processing_time_seconds': self.processing_time_seconds,
            'ai_model_used': self.ai_model_used,
            'data_classification': self.data_classification.value
        }
    
    @property
    def total_recommendations(self) -> int:
        """Get total number of recommendations"""
        return sum(len(analysis.recommendations) for analysis in self.event_analyses)
    
    @property
    def high_priority_recommendations(self) -> List[Recommendation]:
        """Get all high priority recommendations"""
        high_priority = []
        for analysis in self.event_analyses:
            high_priority.extend([r for r in analysis.recommendations if r.priority == 'high'])
        return high_priority


class AnalysisModel:
    """Model for AI analysis operations"""
    
    def __init__(self, llm_manager):
        self.llm_manager = llm_manager
    
    def create_analysis_result(self, cluster_name: str) -> AnalysisResult:
        """Create a new analysis result"""
        return AnalysisResult(
            cluster_name=cluster_name,
            analysis_timestamp=datetime.utcnow(),
            status=AnalysisStatus.PENDING,
            health_score=ClusterHealthScore(score=0, status="unknown")
        )
    
    def classify_data_sensitivity(self, data: str) -> SecurityClassification:
        """Classify data sensitivity level"""
        # Delegate to LLM manager
        sensitivity = self.llm_manager.classify_data_sensitivity(data)
        
        # Map to our enum
        mapping = {
            'public': SecurityClassification.PUBLIC,
            'internal': SecurityClassification.INTERNAL,
            'highly_sensitive': SecurityClassification.HIGHLY_SENSITIVE,
            'critical': SecurityClassification.CRITICAL
        }
        
        return mapping.get(sensitivity.value, SecurityClassification.INTERNAL)
    
    def analyze_events_with_ai(self, events: List, cluster_name: str) -> AnalysisResult:
        """Perform AI analysis on events"""
        start_time = datetime.utcnow()
        
        result = self.create_analysis_result(cluster_name)
        result.status = AnalysisStatus.IN_PROGRESS
        
        try:
            # Group events by reason for analysis
            event_groups = {}
            for event in events:
                reason = event.get('reason', 'Unknown')
                if reason not in event_groups:
                    event_groups[reason] = []
                event_groups[reason].append(event)
            
            # Analyze each event group
            for reason, event_list in event_groups.items():
                event_count = sum(event.get('count', 1) for event in event_list)
                
                # Create analysis prompt
                analysis_prompt = f"""
                Analyze this Kubernetes event pattern:
                Event: {reason}
                Count: {event_count}
                Sample message: {event_list[0].get('message', '')}
                
                Provide:
                1. Root cause analysis
                2. Impact assessment  
                3. Specific remediation steps
                4. Prevention strategies
                """
                
                # Get AI analysis
                ai_response = self.llm_manager.process_with_appropriate_llm(
                    analysis_prompt,
                    f"Event analysis for {reason}"
                )
                
                # Parse AI response into structured analysis
                event_analysis = EventAnalysis(
                    event_reason=reason,
                    event_count=event_count,
                    severity=self._determine_severity(reason, event_count),
                    root_cause=self._extract_root_cause(ai_response),
                    impact_assessment=self._extract_impact(ai_response),
                    recommendations=self._extract_recommendations(ai_response, reason),
                    confidence_score=0.8  # Default confidence
                )
                
                result.event_analyses.append(event_analysis)
            
            # Calculate health score
            result.health_score = self._calculate_health_score(events, result.event_analyses)
            
            # Generate executive summary
            result.executive_summary = self._generate_executive_summary(result)
            
            result.status = AnalysisStatus.COMPLETED
            result.ai_model_used = "ollama/llama3.1:8b"
            
        except Exception as e:
            result.status = AnalysisStatus.FAILED
            result.executive_summary = f"Analysis failed: {str(e)}"
        
        # Calculate processing time
        end_time = datetime.utcnow()
        result.processing_time_seconds = (end_time - start_time).total_seconds()
        
        return result
    
    def _determine_severity(self, reason: str, count: int) -> str:
        """Determine event severity"""
        critical_patterns = ['Failed', 'Error', 'Evicted', 'OutOfMemory']
        high_patterns = ['BackOff', 'Unhealthy', 'Killing', 'NetworkNotReady']
        
        if any(pattern in reason for pattern in critical_patterns) or count > 1000:
            return 'critical'
        elif any(pattern in reason for pattern in high_patterns) or count > 100:
            return 'high'
        elif count > 10:
            return 'medium'
        else:
            return 'low'
    
    def _extract_root_cause(self, ai_response: str) -> str:
        """Extract root cause from AI response"""
        # Simple extraction - in production, use more sophisticated parsing
        lines = ai_response.split('\n')
        for line in lines:
            if 'root cause' in line.lower() or 'cause' in line.lower():
                return line.strip()
        return "Analysis pending"
    
    def _extract_impact(self, ai_response: str) -> str:
        """Extract impact assessment from AI response"""
        lines = ai_response.split('\n')
        for line in lines:
            if 'impact' in line.lower():
                return line.strip()
        return "Impact assessment pending"
    
    def _extract_recommendations(self, ai_response: str, event_reason: str) -> List[Recommendation]:
        """Extract recommendations from AI response"""
        # Simplified extraction - in production, use structured AI responses
        recommendations = []
        
        # Create a generic recommendation based on event type
        if 'Failed' in event_reason:
            recommendations.append(Recommendation(
                title=f"Resolve {event_reason} Issues",
                description="Address the underlying cause of failed operations",
                priority="high",
                category="reliability",
                action_items=["Investigate logs", "Check resource availability", "Verify configurations"]
            ))
        
        return recommendations
    
    def _calculate_health_score(self, events: List, analyses: List[EventAnalysis]) -> ClusterHealthScore:
        """Calculate overall cluster health score"""
        base_score = 100
        
        # Deduct points based on event severity and count
        warning_events = len([e for e in events if e.get('type') == 'Warning'])
        critical_analyses = len([a for a in analyses if a.severity == 'critical'])
        
        score = base_score - (warning_events * 2) - (critical_analyses * 10)
        score = max(0, min(100, score))  # Clamp to 0-100
        
        # Determine status
        if score >= 90:
            status = "excellent"
        elif score >= 70:
            status = "good"
        elif score >= 40:
            status = "needs_attention"
        else:
            status = "critical"
        
        return ClusterHealthScore(
            score=score,
            status=status,
            factors={
                'warning_events': warning_events,
                'critical_issues': critical_analyses,
                'total_events': len(events)
            }
        )
    
    def _generate_executive_summary(self, result: AnalysisResult) -> str:
        """Generate executive summary"""
        total_issues = len(result.event_analyses)
        critical_issues = len([a for a in result.event_analyses if a.severity == 'critical'])
        
        if result.status == AnalysisStatus.FAILED:
            return "Analysis could not be completed due to technical issues."
        
        if total_issues == 0:
            return f"Cluster {result.cluster_name} appears healthy with no significant issues detected."
        
        summary = f"Analysis of {result.cluster_name} identified {total_issues} issue patterns"
        if critical_issues > 0:
            summary += f" including {critical_issues} critical issues requiring immediate attention"
        
        summary += f". Overall health score: {result.health_score.score}/100 ({result.health_score.status})."
        
        return summary