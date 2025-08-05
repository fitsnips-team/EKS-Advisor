"""
History Model - Database models for tracking analysis history over time
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Index
from sqlalchemy.orm import Session

from config.database import Base, get_database_session


class AnalysisHistory(Base):
    """Store analysis results history for trending and comparison"""
    
    __tablename__ = "analysis_history"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic cluster information
    cluster_name = Column(String, nullable=False, index=True)
    cluster_context = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Core metrics
    health_score = Column(Integer, nullable=True)
    security_score = Column(Integer, nullable=True) 
    performance_score = Column(Integer, nullable=True)
    
    # Event statistics
    total_events = Column(Integer, default=0)
    warning_events = Column(Integer, default=0)
    critical_events = Column(Integer, default=0)
    problem_events_count = Column(Integer, default=0)
    
    # Cluster state
    node_count = Column(Integer, nullable=True)
    namespace_count = Column(Integer, nullable=True)
    healthy_nodes = Column(Integer, nullable=True)
    
    # Analysis metadata
    analysis_duration_seconds = Column(Integer, nullable=True)
    events_analyzed = Column(Integer, default=0)
    ai_model_used = Column(String, default="ollama/llama3.1:8b")
    
    # Detailed analysis (JSON storage)
    analysis_summary = Column(JSON, nullable=True)  # Full analysis results
    top_issues = Column(JSON, nullable=True)        # Top priority issues
    recommendations = Column(JSON, nullable=True)   # AI recommendations
    
    # Flags
    has_critical_issues = Column(Boolean, default=False)
    requires_attention = Column(Boolean, default=False)
    
    # Version for schema evolution
    schema_version = Column(String, default="1.0")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_cluster_timestamp', 'cluster_name', 'timestamp'),
        Index('idx_cluster_health', 'cluster_name', 'health_score'),
        Index('idx_timestamp_scores', 'timestamp', 'health_score', 'security_score', 'performance_score'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'cluster_name': self.cluster_name,
            'cluster_context': self.cluster_context,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'health_score': self.health_score,
            'security_score': self.security_score,
            'performance_score': self.performance_score,
            'total_events': self.total_events,
            'warning_events': self.warning_events,
            'critical_events': self.critical_events,
            'problem_events_count': self.problem_events_count,
            'node_count': self.node_count,
            'namespace_count': self.namespace_count,
            'healthy_nodes': self.healthy_nodes,
            'analysis_duration_seconds': self.analysis_duration_seconds,
            'events_analyzed': self.events_analyzed,
            'ai_model_used': self.ai_model_used,
            'has_critical_issues': self.has_critical_issues,
            'requires_attention': self.requires_attention,
            'schema_version': self.schema_version
        }


class ClusterSnapshot(Base):
    """Store periodic cluster snapshots for infrastructure tracking"""
    
    __tablename__ = "cluster_snapshots"
    
    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Cluster identification
    cluster_name = Column(String, nullable=False, index=True)
    cluster_context = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Infrastructure state
    kubernetes_version = Column(String, nullable=True)
    node_count = Column(Integer, default=0)
    namespace_count = Column(Integer, default=0)
    
    # Node details (JSON)
    nodes_info = Column(JSON, nullable=True)
    namespaces_list = Column(JSON, nullable=True)
    
    # Resource utilization summary
    total_cpu_capacity = Column(String, nullable=True)  # e.g., "12000m"
    total_memory_capacity = Column(String, nullable=True)  # e.g., "48Gi"
    
    # Health indicators
    ready_nodes = Column(Integer, default=0)
    not_ready_nodes = Column(Integer, default=0)
    
    # Snapshot metadata
    snapshot_type = Column(String, default="scheduled")  # scheduled, manual, trigger
    
    __table_args__ = (
        Index('idx_cluster_snapshot_time', 'cluster_name', 'timestamp'),
    )


class HistoryModel:
    """Model for managing analysis history operations"""
    
    def save_analysis_result(self, 
                           cluster_name: str,
                           cluster_info: Dict,
                           analysis_summary: Dict,
                           cluster_overview: Dict) -> str:
        """Save analysis results to history"""
        
        with get_database_session() as db:
            # Extract scores from analysis summary
            overview = analysis_summary.get('overview', {})
            security = analysis_summary.get('security', {})
            performance = analysis_summary.get('performance', {})
            
            # Create history record
            history_record = AnalysisHistory(
                cluster_name=cluster_name,
                cluster_context=cluster_info.get('context', ''),
                timestamp=datetime.utcnow(),
                
                # Scores
                health_score=overview.get('health_score', 0),
                security_score=security.get('security_score', 0),
                performance_score=performance.get('performance_score', 0),
                
                # Event counts
                total_events=cluster_overview.get('events', {}).get('total_events', 0),
                warning_events=cluster_overview.get('events', {}).get('warning_events', 0),
                critical_events=cluster_overview.get('events', {}).get('critical_events', 0),
                problem_events_count=cluster_overview.get('problems', {}).get('count', 0),
                
                # Cluster state
                node_count=cluster_overview.get('cluster', {}).get('nodes', 0),
                namespace_count=cluster_overview.get('cluster', {}).get('namespaces', 0),
                events_analyzed=len(analysis_summary.get('events_analyzed', [])),
                
                # Detailed analysis
                analysis_summary=analysis_summary,
                top_issues=cluster_overview.get('problems', {}).get('top_issues', [])[:5],
                
                # Flags
                has_critical_issues=cluster_overview.get('events', {}).get('critical_events', 0) > 0,
                requires_attention=cluster_overview.get('problems', {}).get('count', 0) > 0
            )
            
            db.add(history_record)
            db.commit()
            db.refresh(history_record)
            
            return history_record.id
    
    def get_cluster_history(self,
                          cluster_name: str,
                          limit: int = 50,
                          days_back: int = 30) -> List[Dict[str, Any]]:
        """Get analysis history for a cluster"""
        
        with get_database_session() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            history = db.query(AnalysisHistory)\
                        .filter(AnalysisHistory.cluster_name == cluster_name)\
                        .filter(AnalysisHistory.timestamp >= cutoff_date)\
                        .order_by(AnalysisHistory.timestamp.desc())\
                        .limit(limit)\
                        .all()
            
            return [record.to_dict() for record in history]
    
    def get_score_trends(self,
                        cluster_name: str,
                        days_back: int = 7) -> Dict[str, List]:
        """Get score trends for charts"""
        
        with get_database_session() as db:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            history = db.query(AnalysisHistory)\
                        .filter(AnalysisHistory.cluster_name == cluster_name)\
                        .filter(AnalysisHistory.timestamp >= cutoff_date)\
                        .order_by(AnalysisHistory.timestamp.asc())\
                        .all()
            
            trends = {
                'timestamps': [],
                'health_scores': [],
                'security_scores': [],
                'performance_scores': [],
                'event_counts': []
            }
            
            for record in history:
                trends['timestamps'].append(record.timestamp.isoformat())
                trends['health_scores'].append(record.health_score or 0)
                trends['security_scores'].append(record.security_score or 0)
                trends['performance_scores'].append(record.performance_score or 0)
                trends['event_counts'].append(record.total_events or 0)
            
            return trends
    
    def get_cluster_comparison(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Compare multiple clusters"""
        
        with get_database_session() as db:
            from datetime import timedelta
            from sqlalchemy import func
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Get latest scores for each cluster
            subquery = db.query(
                AnalysisHistory.cluster_name,
                func.max(AnalysisHistory.timestamp).label('latest_timestamp')
            ).filter(
                AnalysisHistory.timestamp >= cutoff_date
            ).group_by(AnalysisHistory.cluster_name).subquery()
            
            latest_records = db.query(AnalysisHistory)\
                              .join(subquery, 
                                   (AnalysisHistory.cluster_name == subquery.c.cluster_name) &
                                   (AnalysisHistory.timestamp == subquery.c.latest_timestamp))\
                              .all()
            
            return [record.to_dict() for record in latest_records]
    
    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """Clean up old history records"""
        
        with get_database_session() as db:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            deleted_count = db.query(AnalysisHistory)\
                             .filter(AnalysisHistory.timestamp < cutoff_date)\
                             .delete()
            
            db.commit()
            return deleted_count
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        
        with get_database_session() as db:
            from sqlalchemy import func
            
            stats = db.query(
                func.count(AnalysisHistory.id).label('total_records'),
                func.count(func.distinct(AnalysisHistory.cluster_name)).label('unique_clusters'),
                func.min(AnalysisHistory.timestamp).label('oldest_record'),
                func.max(AnalysisHistory.timestamp).label('newest_record')
            ).first()
            
            return {
                'total_records': stats.total_records or 0,
                'unique_clusters': stats.unique_clusters or 0,
                'oldest_record': stats.oldest_record.isoformat() if stats.oldest_record else None,
                'newest_record': stats.newest_record.isoformat() if stats.newest_record else None
            }