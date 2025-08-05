"""
Cluster Controller - Orchestrates cluster-related business logic
"""

from typing import Dict, List, Optional
from models.cluster_model import ClusterModel, ClusterInfo
from models.event_model import EventModel, KubernetesEvent, EventType, EventSeverity
from datetime import datetime


class ClusterController:
    """Controller for cluster operations and event management"""
    
    def __init__(self, kubeconfig_path: Optional[str] = None):
        self.cluster_model = ClusterModel(kubeconfig_path)
        self.event_model = EventModel(self.cluster_model)
        self._cluster_info_cache = None
        self._cache_timestamp = None
    
    def connect_to_cluster(self) -> Dict[str, any]:
        """Attempt to connect to cluster and return status"""
        try:
            if self.cluster_model.is_connected():
                cluster_info = self.get_cluster_info()
                return {
                    "success": True,
                    "message": f"Connected to cluster: {cluster_info.display_name}",
                    "cluster_info": cluster_info
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to connect to cluster",
                    "cluster_info": None
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}",
                "cluster_info": None
            }
    
    def get_cluster_info(self, use_cache: bool = True) -> ClusterInfo:
        """Get cluster information with optional caching"""
        if use_cache and self._cluster_info_cache and self._cache_timestamp:
            # Cache for 5 minutes
            if (datetime.utcnow() - self._cache_timestamp).seconds < 300:
                return self._cluster_info_cache
        
        cluster_info = self.cluster_model.get_cluster_info()
        self._cluster_info_cache = cluster_info
        self._cache_timestamp = datetime.utcnow()
        
        return cluster_info
    
    def get_cluster_health(self) -> Dict[str, any]:
        """Get comprehensive cluster health status"""
        health_check = self.cluster_model.health_check()
        
        if not health_check["healthy"]:
            return health_check
        
        # Get additional health metrics
        try:
            cluster_info = self.get_cluster_info()
            recent_events = self.event_model.get_events(hours_back=1, limit=100)
            warning_events = [e for e in recent_events if e.event_type == EventType.WARNING]
            critical_events = [e for e in recent_events if e.severity == EventSeverity.CRITICAL]
            
            health_check.update({
                "recent_events": len(recent_events),
                "warning_events": len(warning_events),
                "critical_events": len(critical_events),
                "namespace_count": cluster_info.namespace_count,
                "last_updated": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            health_check["warnings"] = [f"Could not fetch additional metrics: {str(e)}"]
        
        return health_check
    
    def get_recent_events(self, hours_back: int = 24, limit: int = 50) -> List[KubernetesEvent]:
        """Get recent events from the cluster"""
        return self.event_model.get_events(hours_back=hours_back, limit=limit)
    
    def get_problem_events(self, hours_back: int = 1) -> List[KubernetesEvent]:
        """Get events that indicate problems"""
        warning_events = self.event_model.get_warning_events(hours_back=hours_back)
        
        # Filter for actual problems
        problem_indicators = [
            'Failed', 'Error', 'Unhealthy', 'Killing', 'Evicted',
            'BackOff', 'Pulling', 'NetworkNotReady', 'Unsupported'
        ]
        
        problem_events = []
        for event in warning_events:
            if any(indicator in event.reason for indicator in problem_indicators):
                problem_events.append(event)
        
        # Sort by severity and count
        problem_events.sort(key=lambda x: (x.severity.value, x.count), reverse=True)
        
        return problem_events
    
    def get_events_by_namespace(self, namespace: str, hours_back: int = 24) -> List[KubernetesEvent]:
        """Get events for a specific namespace"""
        return self.event_model.get_events_by_namespace(namespace, hours_back)
    
    def get_events_summary(self, hours_back: int = 24) -> Dict:
        """Get comprehensive event summary with insights"""
        base_summary = self.event_model.get_event_summary(hours_back)
        
        # Add controller-level insights
        events = self.event_model.get_events(hours_back=hours_back, limit=500)
        
        # Categorize events by severity
        severity_counts = {
            'critical': 0,
            'high': 0, 
            'medium': 0,
            'low': 0
        }
        
        for event in events:
            severity_counts[event.severity.value] += 1
        
        # Identify trending issues (same reason appearing frequently)
        trending_issues = []
        reason_events = {}
        for event in events:
            if event.reason not in reason_events:
                reason_events[event.reason] = []
            reason_events[event.reason].append(event)
        
        for reason, event_list in reason_events.items():
            if len(event_list) >= 5:  # Trending threshold
                total_count = sum(e.count for e in event_list)
                trending_issues.append({
                    'reason': reason,
                    'occurrences': len(event_list),
                    'total_count': total_count,
                    'latest_timestamp': max(e.last_timestamp for e in event_list).isoformat()
                })
        
        # Sort trending issues by total count
        trending_issues.sort(key=lambda x: x['total_count'], reverse=True)
        
        base_summary.update({
            'severity_breakdown': severity_counts,
            'trending_issues': trending_issues[:5],  # Top 5
            'health_indicators': {
                'error_rate': severity_counts['critical'] + severity_counts['high'],
                'stability_score': max(0, 100 - (severity_counts['critical'] * 10 + severity_counts['high'] * 5)),
                'recent_activity': len([e for e in events if e.is_recent])
            }
        })
        
        return base_summary
    
    def get_cluster_overview(self) -> Dict:
        """Get complete cluster overview for dashboards"""
        try:
            cluster_info = self.get_cluster_info()
            health = self.get_cluster_health()
            events_summary = self.get_events_summary(hours_back=1)  # Last hour
            problem_events = self.get_problem_events(hours_back=1)
            
            return {
                'cluster': {
                    'name': cluster_info.display_name,
                    'full_name': cluster_info.cluster_name,
                    'context': cluster_info.context_name,
                    'namespace': cluster_info.current_namespace,
                    'nodes': cluster_info.node_count,
                    'namespaces': cluster_info.namespace_count
                },
                'health': health,
                'events': events_summary,
                'problems': {
                    'count': len(problem_events),
                    'top_issues': [
                        {
                            'reason': event.reason,
                            'count': event.count,
                            'severity': event.severity.value,
                            'message': event.message[:100] + "..." if len(event.message) > 100 else event.message
                        }
                        for event in problem_events[:5]
                    ]
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def is_cluster_available(self) -> bool:
        """Check if cluster is available for operations"""
        return self.cluster_model.is_connected()
    
    def refresh_connection(self) -> bool:
        """Refresh cluster connection"""
        try:
            # Clear cache
            self._cluster_info_cache = None
            self._cache_timestamp = None
            
            # Test connection
            if self.cluster_model.is_connected():
                self.cluster_model.get_cluster_info()  # Test API call
                return True
            return False
        except Exception:
            return False