"""
Event Translation Utilities
Provides user-friendly translations for scary-sounding Kubernetes event reasons
"""

from typing import Dict

# User-friendly reason mappings for scary-sounding event reasons
FRIENDLY_REASON_MAPPINGS: Dict[str, str] = {
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
    'InsufficientCPU': 'CPU Resources Low',
    'FailedCreatePodSandBox': 'Pod Startup Issue',
    'FailedKillPod': 'Pod Cleanup Issue',
    'ContainerCreating': 'Container Starting',
    'ImagePullBackOff': 'Image Download Retry',
    'ErrImagePull': 'Image Download Failed',
    'CrashLoopBackOff': 'Container Crash Loop',
    'Unhealthy': 'Health Check Failed',
    'ProbeWarning': 'Health Check Warning',
    'FailedToCreateEndpoint': 'Network Endpoint Issue',
    'TaintManagerEviction': 'Node Maintenance Eviction',
    'Preempting': 'Resource Priority Adjustment',
    'NodeAffinity': 'Node Placement Constraint',
    'PodTopologySpread': 'Pod Distribution Constraint'
}

def get_friendly_reason(reason: str) -> str:
    """
    Get user-friendly version of Kubernetes event reason
    
    Args:
        reason: Original Kubernetes event reason
        
    Returns:
        User-friendly version of the reason, or original if no mapping exists
    """
    return FRIENDLY_REASON_MAPPINGS.get(reason, reason)

def get_friendly_title(reason: str) -> str:
    """
    Get a friendly title for analysis sections
    
    Args:
        reason: Original Kubernetes event reason
        
    Returns:
        Friendly title for the analysis section
    """
    friendly_reason = get_friendly_reason(reason)
    
    # Add context for better understanding
    if reason == 'Unsupported':
        return f"{friendly_reason} - Review Configuration Settings"
    elif reason in ['BackOff', 'CrashLoopBackOff']:
        return f"{friendly_reason} - Application Stability Issue"
    elif reason in ['FailedScheduling', 'FailedPodReasonUnschedulable']:
        return f"{friendly_reason} - Resource Availability"
    elif reason in ['OutOfMemory', 'Evicted']:
        return f"{friendly_reason} - Resource Management"
    else:
        return friendly_reason

def get_analysis_context(reason: str) -> Dict[str, str]:
    """
    Get additional context for better AI analysis
    
    Args:
        reason: Original Kubernetes event reason
        
    Returns:
        Dictionary with category, urgency, and context information
    """
    context_map = {
        'Unsupported': {
            'category': 'configuration',
            'urgency': 'low',
            'context': 'This indicates a configuration that works but is not recommended for production use.'
        },
        'FailedMount': {
            'category': 'storage',
            'urgency': 'medium',
            'context': 'Storage volumes cannot be properly attached to containers.'
        },
        'BackOff': {
            'category': 'reliability',
            'urgency': 'medium',
            'context': 'Container is in a restart loop with exponential backoff delay.'
        },
        'OutOfMemory': {
            'category': 'performance',
            'urgency': 'high',
            'context': 'Container exceeded memory limits and was terminated.'
        },
        'FailedScheduling': {
            'category': 'resources',
            'urgency': 'medium',
            'context': 'Pod cannot be placed on any available nodes due to resource constraints.'
        }
    }
    
    return context_map.get(reason, {
        'category': 'general',
        'urgency': 'medium',
        'context': 'Standard Kubernetes operational event requiring review.'
    })