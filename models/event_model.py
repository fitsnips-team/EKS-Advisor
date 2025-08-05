"""
Event Model - Represents Kubernetes events and operations
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from kubernetes import client
from enum import Enum


class EventType(Enum):
    """Kubernetes event types"""
    NORMAL = "Normal"
    WARNING = "Warning"


class EventSeverity(Enum):
    """Event severity levels"""
    LOW = "low"
    MEDIUM = "medium"  
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class KubernetesEvent:
    """Represents a Kubernetes event"""
    name: str
    namespace: Optional[str]
    event_type: EventType
    reason: str
    message: str
    count: int
    first_timestamp: datetime
    last_timestamp: datetime
    involved_object_kind: str
    involved_object_name: str
    involved_object_namespace: Optional[str]
    source_component: Optional[str] = None
    
    @property
    def severity(self) -> EventSeverity:
        """Determine event severity based on reason and type"""
        if self.event_type == EventType.WARNING:
            critical_reasons = ['Failed', 'Error', 'Evicted', 'OutOfMemory', 'DiskPressure']
            high_reasons = ['BackOff', 'Unhealthy', 'Killing', 'NetworkNotReady'] 
            
            if any(reason in self.reason for reason in critical_reasons):
                return EventSeverity.CRITICAL
            elif any(reason in self.reason for reason in high_reasons):
                return EventSeverity.HIGH
            else:
                return EventSeverity.MEDIUM
        else:
            return EventSeverity.LOW
    
    @property
    def age_minutes(self) -> int:
        """Get event age in minutes"""
        return int((datetime.utcnow() - self.last_timestamp.replace(tzinfo=None)).total_seconds() / 60)
    
    @property
    def is_recent(self) -> bool:
        """Check if event occurred in last hour"""
        return self.age_minutes <= 60
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'namespace': self.namespace,
            'type': self.event_type.value,
            'reason': self.reason,
            'message': self.message,
            'count': self.count,
            'first_timestamp': self.first_timestamp.isoformat(),
            'last_timestamp': self.last_timestamp.isoformat(),
            'involved_object': {
                'kind': self.involved_object_kind,
                'name': self.involved_object_name,
                'namespace': self.involved_object_namespace
            },
            'source_component': self.source_component,
            'severity': self.severity.value,
            'age_minutes': self.age_minutes
        }


class EventModel:
    """Model for Kubernetes event operations"""
    
    def __init__(self, cluster_model):
        self.cluster_model = cluster_model
        self.v1 = cluster_model.v1
        
        # User-friendly reason mappings for scary-sounding event reasons
        self.reason_translations = {
            'Unsupported': 'Configuration Not Recommended',
            'FailedMount': 'Volume Mount Issue',
            'BackOff': 'Container Restart Delay',
            'Killing': 'Container Termination',
            'Evicted': 'Pod Resource Eviction',
            'OutOfMemory': 'Memory Limit Exceeded',
            'FailedScheduling': 'Pod Scheduling Issue',
            'NetworkNotReady': 'Network Configuration Pending',
            'NodeNotReady': 'Node Status Check',
            'DeadlineExceeded': 'Timeout Occurred',
            'PodSecurityViolation': 'Security Policy Check',
            'FailedPodReasonUnschedulable': 'Scheduling Constraints',
            'InsufficientMemory': 'Memory Resources Low',
            'InsufficientCPU': 'CPU Resources Low'
        }
    
    def get_friendly_reason(self, reason: str) -> str:
        """Get user-friendly version of event reason"""
        return self.reason_translations.get(reason, reason)
    
    def get_events(self, 
                   namespace: Optional[str] = None,
                   hours_back: int = 24,
                   limit: int = 50,
                   event_types: Optional[List[EventType]] = None) -> List[KubernetesEvent]:
        """Get Kubernetes events with filtering"""
        
        if not self.cluster_model.is_connected():
            return []
        
        try:
            time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
            
            # Get events from API
            if namespace:
                events_response = self.v1.list_namespaced_event(namespace=namespace)
            else:
                events_response = self.v1.list_event_for_all_namespaces()
            
            events = []
            for event in events_response.items:
                # Parse timestamps
                last_timestamp = event.last_timestamp or event.event_time
                if last_timestamp is None:
                    continue
                    
                # Filter by time
                if last_timestamp.replace(tzinfo=None) < time_threshold:
                    continue
                
                # Create event object
                k8s_event = KubernetesEvent(
                    name=event.metadata.name,
                    namespace=event.metadata.namespace,
                    event_type=EventType(event.type),
                    reason=event.reason or 'Unknown',
                    message=event.message or '',
                    count=event.count or 1,
                    first_timestamp=event.first_timestamp or last_timestamp,
                    last_timestamp=last_timestamp,
                    involved_object_kind=event.involved_object.kind,
                    involved_object_name=event.involved_object.name,
                    involved_object_namespace=event.involved_object.namespace,
                    source_component=event.source.component if event.source else None
                )
                
                # Filter by event type if specified
                if event_types and k8s_event.event_type not in event_types:
                    continue
                
                events.append(k8s_event)
            
            # Sort by last timestamp (most recent first) and limit
            events.sort(key=lambda x: x.last_timestamp, reverse=True)
            return events[:limit]
            
        except Exception as e:
            raise RuntimeError(f"Error getting events: {e}")
    
    def get_warning_events(self, hours_back: int = 1, limit: int = 100) -> List[KubernetesEvent]:
        """Get warning events only"""
        return self.get_events(
            hours_back=hours_back,
            limit=limit,
            event_types=[EventType.WARNING]
        )
    
    def get_events_by_severity(self, severity: EventSeverity, hours_back: int = 24) -> List[KubernetesEvent]:
        """Get events filtered by severity"""
        all_events = self.get_events(hours_back=hours_back, limit=200)
        return [event for event in all_events if event.severity == severity]
    
    def get_events_by_namespace(self, namespace: str, hours_back: int = 24) -> List[KubernetesEvent]:
        """Get events for specific namespace"""
        return self.get_events(namespace=namespace, hours_back=hours_back)
    
    def get_event_summary(self, hours_back: int = 24) -> Dict:
        """Get summary statistics of events"""
        events = self.get_events(hours_back=hours_back, limit=500)
        
        summary = {
            'total_events': len(events),
            'warning_events': len([e for e in events if e.event_type == EventType.WARNING]),
            'normal_events': len([e for e in events if e.event_type == EventType.NORMAL]),
            'critical_events': len([e for e in events if e.severity == EventSeverity.CRITICAL]),
            'high_severity_events': len([e for e in events if e.severity == EventSeverity.HIGH]),
            'recent_events': len([e for e in events if e.is_recent]),
            'top_reasons': {},
            'affected_namespaces': set(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Count reasons
        reason_counts = {}
        for event in events:
            reason_counts[event.reason] = reason_counts.get(event.reason, 0) + 1
            if event.namespace:
                summary['affected_namespaces'].add(event.namespace)
        
        # Top 5 reasons
        summary['top_reasons'] = dict(
            sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        )
        summary['affected_namespaces'] = list(summary['affected_namespaces'])
        
        return summary