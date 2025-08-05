"""
Analysis Controller - Orchestrates AI analysis and security operations
"""

from typing import Dict, List, Optional
from datetime import datetime
import time

from models.analysis_model import AnalysisModel, AnalysisResult, SecurityClassification
from models.event_model import KubernetesEvent
from llm_config import get_configured_llm_manager
from utils.event_translations import get_friendly_reason, get_friendly_title


class AnalysisController:
    """Controller for AI analysis operations"""
    
    def __init__(self):
        self.llm_manager = get_configured_llm_manager()
        self.analysis_model = AnalysisModel(self.llm_manager)
        self._analysis_cache = {}
    
    def analyze_cluster_events(self, 
                             cluster_name: str,
                             events: List[KubernetesEvent],
                             force_refresh: bool = False) -> AnalysisResult:
        """Perform comprehensive analysis of cluster events"""
        
        # Check cache first (unless force refresh)
        cache_key = f"{cluster_name}_{len(events)}_{hash(str([e.name for e in events[:5]]))}"
        if not force_refresh and cache_key in self._analysis_cache:
            cached_result, timestamp = self._analysis_cache[cache_key]
            # Use cache if less than 10 minutes old
            if (datetime.utcnow() - timestamp).seconds < 600:
                return cached_result
        
        start_time = time.time()
        
        # Convert events to dict format for analysis
        event_dicts = [event.to_dict() for event in events]
        
        # Perform analysis
        result = self.analysis_model.analyze_events_with_ai(event_dicts, cluster_name)
        
        # Cache the result
        self._analysis_cache[cache_key] = (result, datetime.utcnow())
        
        return result
    
    def quick_analysis(self, events: List[KubernetesEvent], cluster_name: str) -> Dict:
        """Perform quick analysis for immediate insights"""
        if not events:
            return {
                'summary': f'No events found for analysis in cluster {cluster_name}',
                'recommendations': [],
                'priority_issues': [],
                'health_score': 100
            }
        
        # Group events by severity and reason
        critical_events = [e for e in events if e.severity.value == 'critical']
        high_events = [e for e in events if e.severity.value == 'high']
        
        # Identify top issues
        reason_counts = {}
        for event in events:
            reason_counts[event.reason] = reason_counts.get(event.reason, 0) + event.count
        
        top_issues = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Calculate simple health score
        health_score = max(0, 100 - len(critical_events) * 15 - len(high_events) * 5)
        
        # Generate quick recommendations
        recommendations = []
        if critical_events:
            recommendations.append("Immediate attention required for critical issues")
        if len(events) > 50:
            recommendations.append("High event volume - investigate underlying causes")
        if health_score < 70:
            recommendations.append("Cluster health needs attention")
        
        return {
            'cluster_name': cluster_name,
            'summary': f'Analyzed {len(events)} events, found {len(critical_events)} critical and {len(high_events)} high severity issues',
            'recommendations': recommendations,
            'priority_issues': [{'reason': reason, 'count': count} for reason, count in top_issues],
            'health_score': health_score,
            'critical_count': len(critical_events),
            'high_count': len(high_events),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def analyze_single_event(self, event: KubernetesEvent) -> Dict:
        """Analyze a single event in detail"""
        
        # Classify data sensitivity
        data_classification = self.analysis_model.classify_data_sensitivity(event.message)
        
        # Get user-friendly reason and title
        friendly_reason = get_friendly_reason(event.reason)
        friendly_title = get_friendly_title(event.reason)
        
        # Create analysis prompt with friendly terminology
        prompt = f"""
        Analyze this Kubernetes issue: {friendly_title}
        
        Issue Type: {friendly_reason}
        Technical Event Code: {event.reason}
        Details: {event.message}
        Occurrence Count: {event.count}
        Severity Level: {event.severity.value}
        Affected Resource: {event.involved_object_kind}/{event.involved_object_name}
        
        Please provide:
        1. Root cause analysis (what's causing this issue)
        2. Immediate impact (how this affects the system)
        3. Recommended actions (specific steps to resolve)
        4. Prevention steps (how to prevent future occurrences)
        
        Keep explanations clear and actionable for operations teams.
        Focus on practical solutions rather than technical jargon.
        """
        
        # Get AI analysis
        try:
            ai_response = self.llm_manager.process_with_appropriate_llm(
                "Analyze this Kubernetes event and provide actionable insights:",
                prompt
            )
            
            return {
                'event_name': event.name,
                'reason': event.reason,
                'severity': event.severity.value,
                'count': event.count,
                'data_classification': data_classification.value,
                'ai_analysis': ai_response,
                'recommendations': self._extract_action_items(ai_response),
                'confidence': 0.8,
                'processing_model': 'ollama/llama3.1:8b',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'event_name': event.name,
                'reason': event.reason,
                'error': f"Analysis failed: {str(e)}",
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_security_assessment(self, events: List[KubernetesEvent]) -> Dict:
        """Perform security-focused analysis of events"""
        
        security_events = []
        sensitive_data_events = []
        
        # Security-related keywords
        security_keywords = [
            'security', 'rbac', 'unauthorized', 'denied', 'forbidden',
            'secret', 'token', 'certificate', 'tls', 'ssl'
        ]
        
        for event in events:
            # Check for security-related content
            event_text = f"{event.reason} {event.message}".lower()
            if any(keyword in event_text for keyword in security_keywords):
                security_events.append(event)
            
            # Check data sensitivity
            classification = self.analysis_model.classify_data_sensitivity(event.message)
            if classification in [SecurityClassification.HIGHLY_SENSITIVE, SecurityClassification.CRITICAL]:
                sensitive_data_events.append({
                    'event': event,
                    'classification': classification.value
                })
        
        return {
            'security_events_count': len(security_events),
            'sensitive_data_events_count': len(sensitive_data_events),
            'security_events': [
                {
                    'reason': event.reason,
                    'message': event.message[:100] + "..." if len(event.message) > 100 else event.message,
                    'severity': event.severity.value,
                    'count': event.count
                }
                for event in security_events[:5]  # Top 5
            ],
            'data_sensitivity_breakdown': self._get_sensitivity_breakdown(events),
            'privacy_status': 'All analysis performed locally with Ollama',
            'security_score': max(0, 100 - len(security_events) * 5 - len(sensitive_data_events) * 10),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_performance_insights(self, events: List[KubernetesEvent]) -> Dict:
        """Analyze events for performance implications"""
        
        performance_events = []
        resource_events = []
        
        # Performance-related patterns
        performance_keywords = [
            'resource', 'memory', 'cpu', 'disk', 'network', 'throttling',
            'limit', 'quota', 'scheduling', 'evicted', 'oom'
        ]
        
        for event in events:
            event_text = f"{event.reason} {event.message}".lower()
            if any(keyword in event_text for keyword in performance_keywords):
                performance_events.append(event)
                
            # Specifically track resource-related events
            if any(word in event_text for word in ['memory', 'cpu', 'resource']):
                resource_events.append(event)
        
        # Calculate performance score
        performance_score = max(0, 100 - len(performance_events) * 3)
        
        return {
            'performance_events_count': len(performance_events),
            'resource_events_count': len(resource_events),
            'performance_score': performance_score,
            'top_performance_issues': [
                {
                    'reason': event.reason,
                    'count': event.count,
                    'severity': event.severity.value,
                    'message_preview': event.message[:80] + "..." if len(event.message) > 80 else event.message
                }
                for event in sorted(performance_events, key=lambda x: x.count, reverse=True)[:3]
            ],
            'recommendations': self._get_performance_recommendations(performance_events),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_analysis_summary(self, cluster_name: str, events: List[KubernetesEvent]) -> Dict:
        """Get comprehensive analysis summary"""
        
        quick_analysis = self.quick_analysis(events, cluster_name)
        security_assessment = self.get_security_assessment(events)
        performance_insights = self.get_performance_insights(events)
        
        return {
            'cluster_name': cluster_name,
            'overview': quick_analysis,
            'security': security_assessment,
            'performance': performance_insights,
            'llm_provider': 'ollama',
            'processing_location': 'local',
            'privacy_level': 'maximum',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _extract_action_items(self, ai_response: str) -> List[str]:
        """Extract actionable items from AI response"""
        actions = []
        lines = ai_response.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for numbered lists, bullet points, or action verbs
            if (line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '•')) or
                any(verb in line.lower() for verb in ['check', 'verify', 'update', 'fix', 'restart', 'review'])):
                actions.append(line)
        
        return actions[:5]  # Limit to top 5 actions
    
    def _get_sensitivity_breakdown(self, events: List[KubernetesEvent]) -> Dict[str, int]:
        """Get breakdown of data sensitivity classifications"""
        breakdown = {
            'public': 0,
            'internal': 0,
            'highly_sensitive': 0,
            'critical': 0
        }
        
        for event in events:
            classification = self.analysis_model.classify_data_sensitivity(event.message)
            breakdown[classification.value] += 1
        
        return breakdown
    
    def _get_performance_recommendations(self, performance_events: List[KubernetesEvent]) -> List[str]:
        """Generate performance-specific recommendations"""
        recommendations = []
        
        # Analyze event patterns
        resource_issues = len([e for e in performance_events if 'resource' in e.message.lower()])
        memory_issues = len([e for e in performance_events if 'memory' in e.message.lower()])
        scheduling_issues = len([e for e in performance_events if 'schedul' in e.message.lower()])
        
        if resource_issues > 5:
            recommendations.append("Review resource requests and limits for containers")
        
        if memory_issues > 3:
            recommendations.append("Investigate memory usage patterns and potential leaks")
            
        if scheduling_issues > 2:
            recommendations.append("Analyze node capacity and scheduling constraints")
        
        if len(performance_events) > 20:
            recommendations.append("Consider implementing horizontal pod autoscaling")
        
        return recommendations or ["No specific performance recommendations at this time"]
    
    def clear_cache(self):
        """Clear analysis cache"""
        self._analysis_cache.clear()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'cached_analyses': len(self._analysis_cache),
            'cache_size_mb': sum(len(str(result)) for result, _ in self._analysis_cache.values()) / (1024 * 1024)
        }