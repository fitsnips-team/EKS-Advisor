"""
Dashboard View - Rich dashboard-style presentation layer
"""

from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.layout import Layout
from rich.align import Align

from models.event_model import KubernetesEvent
from models.analysis_model import AnalysisResult


class DashboardView:
    """Dashboard-style view for comprehensive data presentation"""
    
    def __init__(self):
        self.console = Console()
    
    def show_cluster_overview_dashboard(self, overview: Dict):
        """Display comprehensive cluster overview dashboard"""
        
        # Create main layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Split body into sections
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="cluster_info"),
            Layout(name="health_status")
        )
        
        layout["right"].split_column(
            Layout(name="event_summary"),
            Layout(name="problems")
        )
        
        # Header
        cluster_name = overview.get('cluster', {}).get('name', 'Unknown')
        layout["header"].update(Panel(
            Align.center(f"[bold blue]🎯 EKS Advisor Dashboard - {cluster_name}[/bold blue]"),
            style="bold blue"
        ))
        
        # Cluster Info Panel
        cluster = overview.get('cluster', {})
        cluster_info = f"""[cyan]📍 Cluster Information[/cyan]
Name: [bold]{cluster.get('name', 'Unknown')}[/bold]
Context: {cluster.get('context', 'Unknown')}
Namespace: {cluster.get('namespace', 'default')}
Nodes: [bold]{cluster.get('nodes', 0)}[/bold]
Namespaces: [bold]{cluster.get('namespaces', 0)}[/bold]"""
        
        layout["cluster_info"].update(Panel(cluster_info, title="🏗️  Infrastructure", border_style="cyan"))
        
        # Health Status Panel
        health = overview.get('health', {})
        health_status = health.get('healthy', False)
        health_color = "green" if health_status else "red"
        health_icon = "✅" if health_status else "❌"
        
        health_info = f"""[{health_color}]{health_icon} Status: {'Healthy' if health_status else 'Issues Detected'}[/{health_color}]
Healthy Nodes: [bold]{health.get('healthy_nodes', 0)}/{health.get('total_nodes', 0)}[/bold]
Recent Events: [bold]{health.get('recent_events', 0)}[/bold]
Warning Events: [yellow]{health.get('warning_events', 0)}[/yellow]"""
        
        layout["health_status"].update(Panel(health_info, title="🏥 Health Status", border_style=health_color))
        
        # Event Summary Panel
        events = overview.get('events', {})
        event_info = f"""Total Events: [bold]{events.get('total_events', 0)}[/bold]
Warning Events: [yellow]{events.get('warning_events', 0)}[/yellow]
Critical Events: [red]{events.get('critical_events', 0)}[/red]
Recent Activity: [green]{events.get('recent_events', 0)}[/green]"""
        
        if 'health_indicators' in events:
            indicators = events['health_indicators']
            stability_score = indicators.get('stability_score', 0)
            score_color = "green" if stability_score >= 80 else "yellow" if stability_score >= 60 else "red"
            event_info += f"\nStability Score: [{score_color}]{stability_score}/100[/{score_color}]"
        
        layout["event_summary"].update(Panel(event_info, title="📊 Event Summary", border_style="yellow"))
        
        # Problems Panel
        problems = overview.get('problems', {})
        problem_count = problems.get('count', 0)
        
        if problem_count == 0:
            problem_info = "[green]✅ No critical issues detected[/green]"
        else:
            problem_info = f"[red]🚨 {problem_count} issues requiring attention[/red]\n\n"
            
            top_issues = problems.get('top_issues', [])[:3]
            for issue in top_issues:
                severity_color = {
                    'critical': 'red',
                    'high': 'orange1',
                    'medium': 'yellow',
                    'low': 'green'
                }.get(issue.get('severity', 'medium'), 'white')
                
                problem_info += f"[{severity_color}]• {issue.get('reason', 'Unknown')}[/{severity_color}] ({issue.get('count', 0)})\n"
        
        layout["problems"].update(Panel(problem_info, title="🎯 Priority Issues", border_style="red" if problem_count > 0 else "green"))
        
        # Footer
        timestamp = overview.get('timestamp', 'Unknown')
        layout["footer"].update(Panel(
            Align.center(f"[dim]Last updated: {timestamp} | Processing: Local Ollama | Privacy: Maximum[/dim]"),
            style="dim"
        ))
        
        self.console.print(layout)
    
    def show_event_pattern_analysis(self, events: List[KubernetesEvent], title: str = "Event Pattern Analysis"):
        """Display event pattern analysis dashboard"""
        
        if not events:
            self.console.print(Panel("[yellow]No events available for pattern analysis[/yellow]", title=title))
            return
        
        # Group events by reason
        patterns = {}
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        namespace_impact = {}
        
        for event in events:
            # Pattern analysis
            reason = event.reason
            patterns[reason] = patterns.get(reason, 0) + 1
            
            # Severity analysis
            severity_counts[event.severity.value] += 1
            
            # Namespace impact
            if event.involved_object_namespace:
                ns = event.involved_object_namespace
                namespace_impact[ns] = namespace_impact.get(ns, 0) + 1
        
        # Create pattern table
        pattern_table = Table(title="Top Event Patterns")
        pattern_table.add_column("Event Reason", style="cyan")
        pattern_table.add_column("Count", style="green")
        pattern_table.add_column("Frequency", style="yellow")
        
        total_events = len(events)
        for reason, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
            frequency = f"{(count/total_events)*100:.1f}%"
            pattern_table.add_row(reason, str(count), frequency)
        
        # Create severity breakdown
        severity_text = ""
        for severity, count in severity_counts.items():
            if count > 0:
                color = {
                    'critical': 'red',
                    'high': 'orange1',
                    'medium': 'yellow', 
                    'low': 'green'
                }.get(severity, 'white')
                severity_text += f"[{color}]{severity.title()}: {count}[/{color}]\n"
        
        severity_panel = Panel(severity_text.strip(), title="Severity Breakdown", border_style="yellow")
        
        # Create namespace impact
        namespace_text = ""
        if namespace_impact:
            for ns, count in sorted(namespace_impact.items(), key=lambda x: x[1], reverse=True)[:5]:
                namespace_text += f"[cyan]• {ns}[/cyan]: {count} events\n"
        else:
            namespace_text = "[dim]No namespace data available[/dim]"
        
        namespace_panel = Panel(namespace_text.strip(), title="Namespace Impact", border_style="cyan")
        
        # Display layout
        self.console.print(Panel(f"[bold]{title}[/bold]", expand=False))
        self.console.print(pattern_table)
        self.console.print(Columns([severity_panel, namespace_panel]))
    
    def show_analysis_metrics_dashboard(self, analysis_summary: Dict):
        """Display analysis metrics in dashboard format"""
        
        overview = analysis_summary.get('overview', {})
        security = analysis_summary.get('security', {})
        performance = analysis_summary.get('performance', {})
        
        # Create metrics layout
        layout = Layout()
        layout.split_row(
            Layout(name="scores"),
            Layout(name="details")
        )
        
        layout["details"].split_column(
            Layout(name="security_details"),
            Layout(name="performance_details")
        )
        
        # Score Panel
        health_score = overview.get('health_score', 0)
        security_score = security.get('security_score', 0)
        performance_score = performance.get('performance_score', 0)
        
        def get_score_color(score):
            return "green" if score >= 80 else "yellow" if score >= 60 else "red"
        
        scores_text = f"""[bold]📊 System Scores[/bold]

[{get_score_color(health_score)}]🏥 Health: {health_score}/100[/{get_score_color(health_score)}]
[{get_score_color(security_score)}]🛡️  Security: {security_score}/100[/{get_score_color(security_score)}]
[{get_score_color(performance_score)}]⚡ Performance: {performance_score}/100[/{get_score_color(performance_score)}]

[bold]Overall Status:[/bold]
{self._get_overall_status(health_score, security_score, performance_score)}"""
        
        layout["scores"].update(Panel(scores_text, title="🎯 Key Metrics", border_style="blue"))
        
        # Security Details
        security_text = f"""Events: {security.get('security_events_count', 0)}
Sensitive Data: {security.get('sensitive_data_events_count', 0)}
Privacy: [green]{security.get('privacy_status', 'Local Processing')}[/green]

[bold]Data Classification:[/bold]"""
        
        if 'data_sensitivity_breakdown' in security:
            for level, count in security['data_sensitivity_breakdown'].items():
                if count > 0:
                    color = {
                        'public': 'green',
                        'internal': 'yellow',
                        'highly_sensitive': 'orange1',
                        'critical': 'red'
                    }.get(level, 'white')
                    security_text += f"\n[{color}]• {level.replace('_', ' ').title()}: {count}[/{color}]"
        
        layout["security_details"].update(Panel(security_text, title="🛡️  Security Analysis", border_style="red"))
        
        # Performance Details
        performance_text = f"""Performance Events: {performance.get('performance_events_count', 0)}
Resource Events: {performance.get('resource_events_count', 0)}

[bold]Top Issues:[/bold]"""
        
        if 'top_performance_issues' in performance:
            for issue in performance['top_performance_issues'][:3]:
                severity_color = {
                    'critical': 'red',
                    'high': 'orange1',
                    'medium': 'yellow',
                    'low': 'green'
                }.get(issue.get('severity', 'medium'), 'white')
                
                performance_text += f"\n[{severity_color}]• {issue['reason']}[/{severity_color}] ({issue['count']})"
        
        layout["performance_details"].update(Panel(performance_text, title="⚡ Performance Analysis", border_style="yellow"))
        
        self.console.print(layout)
    
    def show_remediation_dashboard(self, analysis_result: AnalysisResult):
        """Display remediation recommendations in dashboard format"""
        
        if not analysis_result.event_analyses:
            self.console.print(Panel("[green]✅ No issues requiring remediation[/green]", title="🔧 Remediation Dashboard"))
            return
        
        # Get high priority recommendations
        high_priority_recs = analysis_result.high_priority_recommendations
        
        # Create remediation table
        remediation_table = Table(title="🎯 Priority Remediation Actions")
        remediation_table.add_column("Priority", style="red")
        remediation_table.add_column("Category", style="cyan")
        remediation_table.add_column("Recommendation", style="white", max_width=50)
        remediation_table.add_column("Actions", style="green", max_width=30)
        
        # Add high priority recommendations first
        for rec in high_priority_recs[:5]:
            actions = "\n".join(rec.action_items[:2]) if rec.action_items else "See details"
            remediation_table.add_row(
                "[red]HIGH[/red]",
                rec.category.title(),
                rec.title,
                actions
            )
        
        # Add other recommendations
        other_recs = []
        for analysis in analysis_result.event_analyses:
            for rec in analysis.recommendations:
                if rec not in high_priority_recs and rec.priority != 'high':
                    other_recs.append(rec)
        
        for rec in other_recs[:3]:  # Add up to 3 more
            priority_color = "yellow" if rec.priority == "medium" else "green"
            actions = "\n".join(rec.action_items[:2]) if rec.action_items else "See details"
            remediation_table.add_row(
                f"[{priority_color}]{rec.priority.upper()}[/{priority_color}]",
                rec.category.title(),
                rec.title,
                actions
            )
        
        # Summary panel
        total_recs = analysis_result.total_recommendations
        summary_text = f"""[bold]📋 Remediation Summary[/bold]

Total Recommendations: [bold]{total_recs}[/bold]
High Priority: [red]{len(high_priority_recs)}[/red]
Issues Analyzed: [yellow]{len(analysis_result.event_analyses)}[/yellow]
Confidence: [green]{analysis_result.event_analyses[0].confidence_score:.1%}[/green] (avg)

[bold]Next Steps:[/bold]
1. Address high priority items first
2. Review kubectl commands in detail
3. Monitor cluster after changes
4. Re-run analysis to verify fixes"""
        
        summary_panel = Panel(summary_text, title="📊 Action Summary", border_style="blue")
        
        self.console.print(remediation_table)
        self.console.print(summary_panel)
    
    def show_trending_analysis(self, events_summary: Dict):
        """Display trending issues analysis"""
        
        trending_issues = events_summary.get('trending_issues', [])
        
        if not trending_issues:
            self.console.print(Panel("[green]✅ No trending issues detected[/green]", title="📈 Trending Analysis"))
            return
        
        # Create trending table
        trending_table = Table(title="📈 Trending Issues (Frequent Patterns)")
        trending_table.add_column("Issue", style="red")
        trending_table.add_column("Occurrences", style="yellow")
        trending_table.add_column("Total Count", style="orange1")
        trending_table.add_column("Latest", style="cyan")
        trending_table.add_column("Trend", style="white")
        
        for issue in trending_issues:
            # Determine trend indicator
            count = issue['total_count']
            if count > 100:
                trend = "[red]🔥 Critical[/red]"
            elif count > 50:
                trend = "[orange1]📈 Rising[/orange1]"
            else:
                trend = "[yellow]⚠️  Watch[/yellow]"
            
            trending_table.add_row(
                issue['reason'],
                str(issue['occurrences']),
                str(issue['total_count']),
                issue['latest_timestamp'].split('T')[1][:8],  # Time only
                trend
            )
        
        self.console.print(trending_table)
        
        # Add trend insights
        insights_text = f"""[bold]🔍 Trend Insights[/bold]

• {len(trending_issues)} issues showing frequent patterns
• Issues with >100 occurrences need immediate attention
• Rising trends may indicate systemic problems
• Monitor these patterns for cluster stability"""
        
        insights_panel = Panel(insights_text, title="💡 Insights", border_style="blue")
        self.console.print(insights_panel)
    
    def _get_overall_status(self, health_score: int, security_score: int, performance_score: int) -> str:
        """Determine overall system status"""
        avg_score = (health_score + security_score + performance_score) / 3
        
        if avg_score >= 85:
            return "[green]🟢 Excellent - System running optimally[/green]"
        elif avg_score >= 70:
            return "[yellow]🟡 Good - Minor issues to address[/yellow]"
        elif avg_score >= 50:
            return "[orange1]🟠 Needs Attention - Several issues detected[/orange1]"
        else:
            return "[red]🔴 Critical - Immediate action required[/red]"
    
    def show_cluster_comparison(self, clusters_data: List[Dict]):
        """Display comparison between multiple clusters"""
        
        if len(clusters_data) < 2:
            self.console.print("[yellow]Need at least 2 clusters for comparison[/yellow]")
            return
        
        # Create comparison table
        comparison_table = Table(title="🔍 Cluster Comparison")
        comparison_table.add_column("Metric", style="cyan")
        
        for cluster in clusters_data:
            cluster_name = cluster.get('name', 'Unknown')
            comparison_table.add_column(cluster_name, style="white")
        
        # Add comparison rows
        metrics = [
            ('Health Score', 'health_score'),
            ('Warning Events', 'warning_events'),
            ('Critical Events', 'critical_events'),
            ('Nodes', 'node_count'),
            ('Namespaces', 'namespace_count')
        ]
        
        for metric_name, metric_key in metrics:
            row = [metric_name]
            for cluster in clusters_data:
                value = cluster.get(metric_key, 0)
                
                # Color code values based on metric
                if 'score' in metric_key.lower():
                    color = "green" if value >= 80 else "yellow" if value >= 60 else "red"
                    row.append(f"[{color}]{value}[/{color}]")
                elif 'events' in metric_key.lower():
                    color = "red" if value > 10 else "yellow" if value > 5 else "green"
                    row.append(f"[{color}]{value}[/{color}]")
                else:
                    row.append(str(value))
            
            comparison_table.add_row(*row)
        
        self.console.print(comparison_table)