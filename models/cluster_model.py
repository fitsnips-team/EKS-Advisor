"""
Cluster Model - Represents Kubernetes cluster data and operations
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from kubernetes import client, config


@dataclass
class NodeInfo:
    """Represents a Kubernetes node"""
    name: str
    status: str
    version: str
    os: str
    instance_type: Optional[str] = None


@dataclass 
class ClusterInfo:
    """Represents cluster information"""
    cluster_name: str
    context_name: str
    current_namespace: str
    node_count: int
    namespace_count: int
    nodes: List[NodeInfo]
    
    @property
    def display_name(self) -> str:
        """Get clean cluster name without ARN"""
        if self.cluster_name.startswith('arn:aws:eks:'):
            return self.cluster_name.split('/')[-1]
        return self.cluster_name


class ClusterModel:
    """Model for Kubernetes cluster operations"""
    
    def __init__(self, kubeconfig_path: Optional[str] = None):
        self.connected = False
        self.v1 = None
        self._connect(kubeconfig_path)
    
    def _connect(self, kubeconfig_path: Optional[str] = None) -> None:
        """Connect to Kubernetes cluster"""
        try:
            if kubeconfig_path:
                config.load_kube_config(config_file=kubeconfig_path)
            else:
                try:
                    config.load_incluster_config()
                except Exception:
                    config.load_kube_config()
            
            self.v1 = client.CoreV1Api()
            self.connected = True
            
        except Exception as e:
            self.connected = False
            raise ConnectionError(f"Failed to connect to Kubernetes: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to cluster"""
        return self.connected
    
    def get_cluster_info(self) -> ClusterInfo:
        """Get comprehensive cluster information"""
        if not self.connected:
            raise RuntimeError("Not connected to cluster")
        
        try:
            # Get context information
            try:
                contexts, current_context = config.list_kube_config_contexts()
                cluster_name = current_context.get('context', {}).get('cluster', 'unknown')
                context_name = current_context.get('name', 'unknown')
                namespace = current_context.get('context', {}).get('namespace', 'default')
            except Exception:
                cluster_name = 'unknown'
                context_name = 'unknown'
                namespace = 'default'
            
            # Get nodes
            nodes_response = self.v1.list_node()
            nodes = [
                NodeInfo(
                    name=node.metadata.name,
                    status='Ready' if any(
                        condition.type == 'Ready' and condition.status == 'True'
                        for condition in node.status.conditions
                    ) else 'NotReady',
                    version=node.status.node_info.kubelet_version,
                    os=node.status.node_info.os_image,
                    instance_type=node.metadata.labels.get('node.kubernetes.io/instance-type')
                )
                for node in nodes_response.items
            ]
            
            # Get namespaces  
            namespaces_response = self.v1.list_namespace()
            
            return ClusterInfo(
                cluster_name=cluster_name,
                context_name=context_name,
                current_namespace=namespace,
                node_count=len(nodes),
                namespace_count=len(namespaces_response.items),
                nodes=nodes
            )
            
        except Exception as e:
            raise RuntimeError(f"Error getting cluster info: {e}")
    
    def health_check(self) -> Dict[str, any]:
        """Perform cluster health check"""
        if not self.connected:
            return {"healthy": False, "reason": "Not connected"}
        
        try:
            # Basic API server check
            self.v1.get_api_resources()
            cluster_info = self.get_cluster_info()
            
            # Check node health
            healthy_nodes = sum(1 for node in cluster_info.nodes if node.status == 'Ready')
            
            return {
                "healthy": True,
                "cluster_name": cluster_info.display_name,
                "total_nodes": cluster_info.node_count,
                "healthy_nodes": healthy_nodes,
                "unhealthy_nodes": cluster_info.node_count - healthy_nodes,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {"healthy": False, "reason": str(e)}