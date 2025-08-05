"""
History Controller - Manages analysis history and trending data
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from models.history_model import HistoryModel
from models.cluster_model import ClusterInfo


class HistoryController:
    """Controller for history tracking and analysis"""
    
    def __init__(self):
        self.history_model = HistoryModel()
    
    def save_current_analysis(self,
                            cluster_info: ClusterInfo,
                            analysis_summary: Dict,
                            cluster_overview: Dict) -> str:
        """Save current analysis results to history"""
        
        try:
            # Convert ClusterInfo to dict for storage
            cluster_dict = {
                'name': cluster_info.display_name,
                'context': cluster_info.context_name,
                'nodes': cluster_info.node_count,
                'namespaces': cluster_info.namespace_count
            }
            
            # Save to database
            history_id = self.history_model.save_analysis_result(
                cluster_name=cluster_info.display_name,
                cluster_info=cluster_dict,
                analysis_summary=analysis_summary,
                cluster_overview=cluster_overview
            )
            
            return history_id
            
        except Exception as e:
            print(f"Error saving analysis history: {e}")
            raise
    
    def get_cluster_timeline(self,
                           cluster_name: str,
                           days_back: int = 30,
                           limit: int = 50) -> List[Dict[str, Any]]:
        """Get historical timeline for a cluster"""
        
        try:
            history = self.history_model.get_cluster_history(
                cluster_name=cluster_name,
                days_back=days_back,
                limit=limit
            )
            
            # Add additional computed fields
            for record in history:
                record['days_ago'] = self._calculate_days_ago(record['timestamp'])
                record['overall_score'] = self._calculate_overall_score(
                    record['health_score'],
                    record['security_score'], 
                    record['performance_score']
                )
                record['status'] = self._determine_status(record)
            
            return history
            
        except Exception as e:
            print(f"Error getting cluster timeline: {e}")
            return []
    
    def get_trend_data(self,
                      cluster_name: str,
                      days_back: int = 7) -> Dict[str, Any]:
        """Get trend data for charts and visualization"""
        
        try:
            trends = self.history_model.get_score_trends(
                cluster_name=cluster_name,
                days_back=days_back
            )
            
            # Calculate trend indicators
            health_trend = self._calculate_trend(trends['health_scores'])
            security_trend = self._calculate_trend(trends['security_scores'])
            performance_trend = self._calculate_trend(trends['performance_scores'])
            
            # Add metadata
            trends.update({
                'cluster_name': cluster_name,
                'days_back': days_back,
                'data_points': len(trends['timestamps']),
                'trends': {
                    'health': health_trend,
                    'security': security_trend,
                    'performance': performance_trend
                },
                'latest_scores': {
                    'health': trends['health_scores'][-1] if trends['health_scores'] else 0,
                    'security': trends['security_scores'][-1] if trends['security_scores'] else 0,
                    'performance': trends['performance_scores'][-1] if trends['performance_scores'] else 0
                }
            })
            
            return trends
            
        except Exception as e:
            print(f"Error getting trend data: {e}")
            return {}
    
    def get_cluster_comparison(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Compare latest scores across all clusters"""
        
        try:
            comparison_data = self.history_model.get_cluster_comparison(days_back=days_back)
            
            # Add computed fields for comparison
            for cluster in comparison_data:
                cluster['overall_score'] = self._calculate_overall_score(
                    cluster['health_score'],
                    cluster['security_score'],
                    cluster['performance_score']
                )
                cluster['status'] = self._determine_status(cluster)
                cluster['last_seen'] = self._calculate_days_ago(cluster['timestamp'])
                
                # Risk assessment
                cluster['risk_level'] = self._assess_risk_level(cluster)
            
            # Sort by overall score (best first)
            comparison_data.sort(key=lambda x: x['overall_score'], reverse=True)
            
            return comparison_data
            
        except Exception as e:
            print(f"Error getting cluster comparison: {e}")
            return []
    
    def get_history_summary(self) -> Dict[str, Any]:
        """Get overall history database summary"""
        
        try:
            stats = self.history_model.get_database_stats()
            
            return {
                'database_stats': stats,
                'tracking_status': 'active' if stats['total_records'] > 0 else 'no_data',
                'data_range_days': self._calculate_data_range_days(
                    stats.get('oldest_record'),
                    stats.get('newest_record')
                ),
                'average_records_per_cluster': (
                    stats['total_records'] // max(stats['unique_clusters'], 1)
                    if stats['total_records'] > 0 else 0
                )
            }
            
        except Exception as e:
            print(f"Error getting history summary: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """Clean up old history records"""
        
        try:
            deleted_count = self.history_model.cleanup_old_records(days_to_keep)
            
            return {
                'deleted_records': deleted_count,
                'days_kept': days_to_keep,
                'cleanup_timestamp': datetime.utcnow().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'deleted_records': 0,
                'error': str(e),
                'status': 'failed'
            }
    
    def _calculate_days_ago(self, timestamp_str: str) -> int:
        """Calculate how many days ago a timestamp was"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            delta = datetime.utcnow() - timestamp.replace(tzinfo=None)
            return delta.days
        except:
            return 0
    
    def _calculate_overall_score(self,
                               health_score: Optional[int],
                               security_score: Optional[int],
                               performance_score: Optional[int]) -> int:
        """Calculate weighted overall score"""
        scores = [s for s in [health_score, security_score, performance_score] if s is not None]
        if not scores:
            return 0
            
        # Weighted average: health=40%, security=35%, performance=25%
        weights = [0.4, 0.35, 0.25][:len(scores)]
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        total_weight = sum(weights)
        
        return int(weighted_sum / total_weight) if total_weight > 0 else 0
    
    def _determine_status(self, record: Dict[str, Any]) -> str:
        """Determine status based on scores and issues"""
        overall_score = record.get('overall_score', 0)
        has_critical = record.get('has_critical_issues', False)
        requires_attention = record.get('requires_attention', False)
        
        if has_critical:
            return 'critical'
        elif requires_attention or overall_score < 60:
            return 'warning'
        elif overall_score >= 80:
            return 'excellent' 
        else:
            return 'good'
    
    def _calculate_trend(self, values: List[int]) -> str:
        """Calculate trend direction from a list of values"""
        if len(values) < 2:
            return 'stable'
        
        # Compare recent values with earlier values
        recent = values[-3:] if len(values) >= 3 else values[-2:]
        earlier = values[:-3] if len(values) >= 6 else values[:-2]
        
        if not earlier:
            return 'stable'
        
        recent_avg = sum(recent) / len(recent)
        earlier_avg = sum(earlier) / len(earlier)
        
        difference = recent_avg - earlier_avg
        
        if difference > 5:
            return 'improving'
        elif difference < -5:
            return 'declining' 
        else:
            return 'stable'
    
    def _assess_risk_level(self, cluster: Dict[str, Any]) -> str:
        """Assess risk level for a cluster"""
        overall_score = cluster.get('overall_score', 0)
        has_critical = cluster.get('has_critical_issues', False)
        critical_events = cluster.get('critical_events', 0)
        last_seen_days = cluster.get('last_seen', 0)
        
        if has_critical or critical_events > 5:
            return 'high'
        elif overall_score < 50 or last_seen_days > 1:
            return 'medium'
        elif overall_score < 70:
            return 'low'
        else:
            return 'minimal'
    
    def _calculate_data_range_days(self,
                                 oldest_record: Optional[str],
                                 newest_record: Optional[str]) -> int:
        """Calculate the range of data in days"""
        if not oldest_record or not newest_record:
            return 0
        
        try:
            oldest = datetime.fromisoformat(oldest_record.replace('Z', '+00:00'))
            newest = datetime.fromisoformat(newest_record.replace('Z', '+00:00'))
            delta = newest - oldest
            return delta.days
        except:
            return 0