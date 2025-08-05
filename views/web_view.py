"""
Web View - FastAPI-based web interface for EKS Advisor
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from models.cluster_model import ClusterInfo
from models.event_model import KubernetesEvent
from models.analysis_model import AnalysisResult
from utils.event_translations import get_friendly_reason


class WebView:
    """Web-based view for EKS Advisor using HTML templates"""
    
    def __init__(self):
        pass
    
    def render_cluster_overview(self, overview: Dict) -> Dict[str, Any]:
        """Convert cluster overview to web-friendly format"""
        
        cluster = overview.get('cluster', {})
        health = overview.get('health', {})
        events = overview.get('events', {})
        problems = overview.get('problems', {})
        
        return {
            'cluster_name': cluster.get('name', 'Unknown'),
            'cluster_context': cluster.get('context', 'Unknown'),
            'node_count': cluster.get('nodes', 0),
            'namespace_count': cluster.get('namespaces', 0),
            'health_status': 'Healthy' if health.get('healthy', False) else 'Issues Detected',
            'health_color': 'success' if health.get('healthy', False) else 'warning',
            'total_events': events.get('total_events', 0),
            'warning_events': events.get('warning_events', 0),
            'critical_events': events.get('critical_events', 0),
            'problem_count': problems.get('count', 0),
            'top_issues': problems.get('top_issues', [])[:5],
            'timestamp': overview.get('timestamp', datetime.utcnow().isoformat())
        }
    
    def render_events_table(self, events: List[KubernetesEvent]) -> List[Dict[str, Any]]:
        """Convert events to web table format"""
        
        web_events = []
        for event in events:
            friendly_reason = get_friendly_reason(event.reason)
            
            # Determine severity color for web
            severity_colors = {
                'critical': 'danger',
                'high': 'warning', 
                'medium': 'info',
                'low': 'success'
            }
            
            web_events.append({
                'timestamp': event.last_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                'friendly_reason': friendly_reason,
                'original_reason': event.reason,
                'event_type': event.event_type.value,
                'severity': event.severity.value,
                'severity_color': severity_colors.get(event.severity.value, 'secondary'),
                'count': event.count,
                'object_kind': event.involved_object_kind,
                'object_name': event.involved_object_name,
                'namespace': event.involved_object_namespace or 'N/A',
                'message': event.message[:100] + '...' if len(event.message) > 100 else event.message,
                'full_message': event.message
            })
        
        return web_events
    
    def render_analysis_summary(self, analysis_summary: Dict) -> Dict[str, Any]:
        """Convert analysis summary to web format"""
        
        overview = analysis_summary.get('overview', {})
        security = analysis_summary.get('security', {})
        performance = analysis_summary.get('performance', {})
        
        # Score colors for web
        def get_score_color(score):
            if score >= 80:
                return 'success'
            elif score >= 60:
                return 'warning'
            else:
                return 'danger'
        
        health_score = overview.get('health_score', 0)
        security_score = security.get('security_score', 0)
        performance_score = performance.get('performance_score', 0)
        
        return {
            'cluster_name': analysis_summary.get('cluster_name', 'Unknown'),
            'health_score': health_score,
            'health_score_color': get_score_color(health_score),
            'security_score': security_score,
            'security_score_color': get_score_color(security_score),
            'performance_score': performance_score,
            'performance_score_color': get_score_color(performance_score),
            'events_analyzed': len(analysis_summary.get('events_analyzed', [])),
            'security_events': security.get('security_events_count', 0),
            'performance_events': performance.get('performance_events_count', 0),
            'privacy_status': 'All processing done locally with Ollama',
            'timestamp': analysis_summary.get('timestamp', datetime.utcnow().isoformat())
        }
    
    def render_problem_events(self, problem_events: List[KubernetesEvent]) -> List[Dict[str, Any]]:
        """Convert problem events to web cards format"""
        
        web_problems = []
        for i, event in enumerate(problem_events[:10], 1):  # Top 10
            friendly_reason = get_friendly_reason(event.reason)
            
            severity_colors = {
                'critical': 'danger',
                'high': 'warning',
                'medium': 'info',
                'low': 'success'
            }
            
            severity_icons = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }
            
            web_problems.append({
                'rank': i,
                'friendly_reason': friendly_reason,
                'original_reason': event.reason,
                'severity': event.severity.value,
                'severity_color': severity_colors.get(event.severity.value, 'secondary'),
                'severity_icon': severity_icons.get(event.severity.value, '⚪'),
                'count': event.count,
                'object_kind': event.involved_object_kind,
                'object_name': event.involved_object_name,
                'namespace': event.involved_object_namespace or 'N/A',
                'message': event.message[:200] + '...' if len(event.message) > 200 else event.message,
                'age_minutes': event.age_minutes,
                'timestamp': event.last_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return web_problems
    
    def render_metrics_cards(self, metrics: Dict) -> List[Dict[str, Any]]:
        """Convert metrics to web cards format"""
        
        cards = []
        
        # Health card
        if 'health_score' in metrics:
            score = metrics['health_score']
            color = 'success' if score >= 80 else 'warning' if score >= 60 else 'danger'
            cards.append({
                'title': 'Cluster Health',
                'value': f"{score}/100",
                'color': color,
                'icon': '🏥',
                'description': 'Overall cluster health assessment'
            })
        
        # Security card
        if 'security_score' in metrics:
            score = metrics['security_score']
            color = 'success' if score >= 80 else 'warning' if score >= 60 else 'danger'
            cards.append({
                'title': 'Security Score',
                'value': f"{score}/100",
                'color': color,
                'icon': '🛡️',
                'description': 'Security assessment and compliance'
            })
        
        # Performance card
        if 'performance_score' in metrics:
            score = metrics['performance_score']
            color = 'success' if score >= 80 else 'warning' if score >= 60 else 'danger'
            cards.append({
                'title': 'Performance',
                'value': f"{score}/100",
                'color': color,
                'icon': '⚡',
                'description': 'Resource utilization and efficiency'
            })
        
        # Event counts
        if 'total_events' in metrics:
            cards.append({
                'title': 'Total Events',
                'value': str(metrics['total_events']),
                'color': 'info',
                'icon': '📊',
                'description': 'Events analyzed in current session'
            })
        
        return cards
    
    def get_status_badge(self, status: str) -> Dict[str, str]:
        """Get Bootstrap badge class for status"""
        
        status_map = {
            'healthy': {'class': 'success', 'text': '✅ Healthy'},
            'warning': {'class': 'warning', 'text': '⚠️ Issues Detected'},
            'critical': {'class': 'danger', 'text': '🚨 Critical Issues'},
            'unknown': {'class': 'secondary', 'text': '❓ Unknown'}
        }
        
        return status_map.get(status.lower(), status_map['unknown'])