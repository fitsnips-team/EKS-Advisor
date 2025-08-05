"""
Console View - Terminal-based presentation layer
"""

from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from models.cluster_model import ClusterInfo
from models.event_model import KubernetesEvent
from models.analysis_model import AnalysisResult
from utils.event_translations import get_friendly_reason


class ConsoleView:
    """Console-based view for EKS Advisor"""
    
    def __init__(self):
        self.console = Console()
    
    def show_header(self, title: str = "EKS Advisor - AI-Powered Kubernetes Analysis"):
        """Display application header"""
        self.console.print(Panel(f"[bold blue]{title}[/bold blue]", expand=False))
    
    def show_cluster_context(self, cluster_info: ClusterInfo):
        """Display cluster context information"""
        self.console.print(f"\n[cyan]📍 Cluster Context:[/cyan]")
        self.console.print(f"   Cluster: [bold]{cluster_info.display_name}[/bold]")
        self.console.print(f"   Context: [bold]{cluster_info.context_name}[/bold]")
        self.console.print(f"   Namespace: [bold]{cluster_info.current_namespace}[/bold]")
        self.console.print(f"   Nodes: [bold]{cluster_info.node_count}[/bold]")
    
    def show_connection_status(self, success: bool, message: str):
        """Display connection status"""
        if success:
            self.console.print(f"✅ {message}")
        else:
            self.console.print(f"❌ {message}")
    
    def show_health_status(self, health_data: Dict):
        """Display cluster health status"""
        if health_data.get("healthy"):
            status_color = "green"
            status_icon = "✅"
        else:
            status_color = "red" 
            status_icon = "❌"
        
        self.console.print(f"\n[bold]🏥 Cluster Health Status[/bold]")
        self.console.print(f"{status_icon} Status: [{status_color}]{health_data.get('reason', 'Healthy')}[/{status_color}]")
        
        if "healthy_nodes" in health_data:
            self.console.print(f"🖥️  Nodes: {health_data['healthy_nodes']}/{health_data['total_nodes']} healthy")
        
        if "recent_events" in health_data:
            self.console.print(f"📊 Recent Events: {health_data['recent_events']} total, {health_data.get('warning_events', 0)} warnings")
    
    def show_events_table(self, events: List[KubernetesEvent], title: str = "Recent Events"):
        """Display events in a formatted table"""
        if not events:
            self.console.print(f"[yellow]No events found[/yellow]")
            return
        
        table = Table(title=title)
        table.add_column("Time", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Issue", style="red")
        table.add_column("Object", style="green")
        table.add_column("Message", style="white", max_width=60)
        
        for event in events:
            # Format timestamp
            time_str = event.last_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            # Get user-friendly reason
            friendly_reason = get_friendly_reason(event.reason)
            
            # Truncate message if too long
            message = event.message
            if len(message) > 60:
                message = message[:57] + "..."
            
            # Color code by severity
            type_color = "yellow" if event.event_type.value == "Warning" else "green"
            
            table.add_row(
                time_str,
                f"[{type_color}]{event.event_type.value}[/{type_color}]",
                friendly_reason,
                f"{event.involved_object_kind}/{event.involved_object_name}",
                message
            )
        
        self.console.print(table)
    
    def show_events_summary(self, summary: Dict):
        """Display event summary statistics"""
        self.console.print(f"\n[bold]📊 Events Summary (Last 24h)[/bold]")
        
        # Create summary table
        summary_table = Table(show_header=False)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="yellow")
        
        summary_table.add_row("Total Events", str(summary.get('total_events', 0)))
        summary_table.add_row("Warning Events", str(summary.get('warning_events', 0)))
        summary_table.add_row("Normal Events", str(summary.get('normal_events', 0)))
        summary_table.add_row("Critical Events", str(summary.get('critical_events', 0)))
        summary_table.add_row("Recent Events", str(summary.get('recent_events', 0)))
        
        self.console.print(summary_table)
        
        # Show top reasons if available
        if 'top_reasons' in summary and summary['top_reasons']:
            self.console.print(f"\n[bold]🔍 Top Event Reasons:[/bold]")
            for reason, count in list(summary['top_reasons'].items())[:5]:
                self.console.print(f"  • {reason}: {count}")
    
    def show_problem_events(self, problem_events: List[KubernetesEvent]):
        """Display problem events with priority"""
        if not problem_events:
            self.console.print("[green]✅ No problem events found - cluster appears healthy![/green]")
            return
        
        self.console.print(f"\n[bold red]🚨 Issues Detected ({len(problem_events)})[/bold red]")
        
        for i, event in enumerate(problem_events[:5], 1):  # Show top 5
            severity_color = {
                'critical': 'red',
                'high': 'orange1',
                'medium': 'yellow',
                'low': 'green'
            }.get(event.severity.value, 'white')
            
            friendly_reason = get_friendly_reason(event.reason)
            
            self.console.print(f"\n{i}. [{severity_color}]{friendly_reason}[/{severity_color}] (Count: {event.count})")
            self.console.print(f"   Resource: {event.involved_object_kind}/{event.involved_object_name}")
            if event.involved_object_namespace:
                self.console.print(f"   Namespace: {event.involved_object_namespace}")
            self.console.print(f"   Severity: [{severity_color}]{event.severity.value.upper()}[/{severity_color}]")
            
            # Truncate message
            message = event.message
            if len(message) > 150:
                message = message[:147] + "..."
            self.console.print(f"   Message: {message}")
    
    def show_analysis_result(self, result: AnalysisResult):
        """Display comprehensive analysis results"""
        self.console.print(f"\n[bold green]🤖 AI Analysis Results[/bold green]")
        
        # Executive Summary
        self.console.print(Panel(
            result.executive_summary,
            title="Executive Summary",
            title_align="left"
        ))
        
        # Health Score
        score = result.health_score.score
        score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
        
        self.console.print(f"\n[bold]🏥 Cluster Health Score: [{score_color}]{score}/100[/{score_color}] ({result.health_score.status.upper()})[/bold]")
        
        # Event Analyses
        if result.event_analyses:
            self.console.print(f"\n[bold]📋 Detailed Event Analysis:[/bold]")
            
            for i, analysis in enumerate(result.event_analyses, 1):
                severity_color = {
                    'critical': 'red',
                    'high': 'orange1', 
                    'medium': 'yellow',
                    'low': 'green'
                }.get(analysis.severity, 'white')
                
                self.console.print(f"\n{i}. [{severity_color}]{analysis.event_reason}[/{severity_color}] (Count: {analysis.event_count})")
                self.console.print(f"   Root Cause: {analysis.root_cause}")
                self.console.print(f"   Impact: {analysis.impact_assessment}")
                
                if analysis.recommendations:
                    self.console.print(f"   Recommendations:")
                    for rec in analysis.recommendations[:3]:  # Top 3
                        self.console.print(f"     • {rec.title}")
        
        # Processing Info
        self.console.print(f"\n[dim]Processing time: {result.processing_time_seconds:.1f}s | Model: {result.ai_model_used} | Classification: {result.data_classification.value}[/dim]")
    
    def show_quick_analysis(self, analysis: Dict):
        """Display quick analysis results"""
        cluster_name = analysis.get('cluster_name', 'Unknown')
        
        self.console.print(f"\n[bold green]⚡ Quick Analysis - {cluster_name}[/bold green]")
        self.console.print(f"📊 {analysis.get('summary', 'No summary available')}")
        
        # Health Score
        health_score = analysis.get('health_score', 0)
        score_color = "green" if health_score >= 80 else "yellow" if health_score >= 60 else "red"
        self.console.print(f"🏥 Health Score: [{score_color}]{health_score}/100[/{score_color}]")
        
        # Priority Issues
        if 'priority_issues' in analysis and analysis['priority_issues']:
            self.console.print(f"\n🎯 Top Issues:")
            for issue in analysis['priority_issues'][:3]:
                self.console.print(f"  • {issue['reason']}: {issue['count']} occurrences")
        
        # Recommendations
        if 'recommendations' in analysis and analysis['recommendations']:
            self.console.print(f"\n💡 Recommendations:")
            for rec in analysis['recommendations'][:3]:
                self.console.print(f"  • {rec}")
    
    def show_security_assessment(self, security: Dict):
        """Display security assessment"""
        self.console.print(f"\n[bold red]🛡️  Security Assessment[/bold red]")
        
        score = security.get('security_score', 0)
        score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
        
        self.console.print(f"Security Score: [{score_color}]{score}/100[/{score_color}]")
        self.console.print(f"Security Events: {security.get('security_events_count', 0)}")
        self.console.print(f"Sensitive Data Events: {security.get('sensitive_data_events_count', 0)}")
        self.console.print(f"Privacy Status: [green]{security.get('privacy_status', 'Unknown')}[/green]")
        
        # Data sensitivity breakdown
        if 'data_sensitivity_breakdown' in security:
            breakdown = security['data_sensitivity_breakdown']
            self.console.print(f"\n📊 Data Classification:")
            for level, count in breakdown.items():
                if count > 0:
                    level_color = {
                        'public': 'green',
                        'internal': 'yellow',
                        'highly_sensitive': 'orange1',
                        'critical': 'red'
                    }.get(level, 'white')
                    self.console.print(f"  • [{level_color}]{level.replace('_', ' ').title()}[/{level_color}]: {count}")
    
    def show_performance_insights(self, performance: Dict):
        """Display performance insights"""
        self.console.print(f"\n[bold yellow]⚡ Performance Insights[/bold yellow]")
        
        score = performance.get('performance_score', 0)
        score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
        
        self.console.print(f"Performance Score: [{score_color}]{score}/100[/{score_color}]")
        self.console.print(f"Performance Events: {performance.get('performance_events_count', 0)}")
        self.console.print(f"Resource Events: {performance.get('resource_events_count', 0)}")
        
        # Top performance issues
        if 'top_performance_issues' in performance and performance['top_performance_issues']:
            self.console.print(f"\n🎯 Top Performance Issues:")
            for issue in performance['top_performance_issues']:
                severity_color = {
                    'critical': 'red',
                    'high': 'orange1',
                    'medium': 'yellow',
                    'low': 'green'
                }.get(issue.get('severity', 'medium'), 'white')
                
                self.console.print(f"  • [{severity_color}]{issue['reason']}[/{severity_color}] (Count: {issue['count']})")
                self.console.print(f"    {issue['message_preview']}")
        
        # Recommendations
        if 'recommendations' in performance and performance['recommendations']:
            self.console.print(f"\n💡 Performance Recommendations:")
            for rec in performance['recommendations']:
                self.console.print(f"  • {rec}")
    
    def show_comprehensive_summary(self, cluster_name: str, summary: Dict):
        """Display comprehensive analysis summary"""
        display_name = cluster_name.split('/')[-1] if cluster_name.startswith('arn:aws:eks:') else cluster_name
        
        self.console.print(Panel(f"[bold]🎉 Analysis Summary - {display_name}[/bold]", style="bold green"))
        
        overview = summary.get('overview', {})
        security = summary.get('security', {})
        performance = summary.get('performance', {})
        
        # Create summary columns
        summary_items = [
            f"✅ Cluster: {display_name}",
            f"🤖 Events Analyzed: {len(summary.get('events_analyzed', []))}",
            f"🔐 Processing: {summary.get('processing_location', 'local').title()}",
            f"📊 Health Score: {overview.get('health_score', 0)}/100",
            f"🛡️  Security Score: {security.get('security_score', 0)}/100",
            f"⚡ Performance Score: {performance.get('performance_score', 0)}/100"
        ]
        
        for item in summary_items:
            self.console.print(item)
        
        self.console.print(f"\n[dim]Analysis completed with maximum privacy protection[/dim]")
    
    def show_error(self, error_message: str, title: str = "Error"):
        """Display error message"""
        self.console.print(Panel(
            f"[red]{error_message}[/red]",
            title=f"❌ {title}",
            title_align="left"
        ))
    
    def show_warning(self, warning_message: str, title: str = "Warning"):
        """Display warning message"""
        self.console.print(Panel(
            f"[yellow]{warning_message}[/yellow]",
            title=f"⚠️  {title}",
            title_align="left"
        ))
    
    def show_success(self, success_message: str, title: str = "Success"):
        """Display success message"""
        self.console.print(Panel(
            f"[green]{success_message}[/green]",
            title=f"✅ {title}",
            title_align="left"
        ))
    
    def show_progress(self, description: str = "Processing..."):
        """Show progress spinner"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        )
    
    def prompt_user(self, message: str, choices: Optional[List[str]] = None) -> str:
        """Prompt user for input"""
        if choices:
            choice_str = "/".join(choices)
            return self.console.input(f"{message} ({choice_str}): ")
        else:
            return self.console.input(f"{message}: ")
    
    def clear_screen(self):
        """Clear the console screen"""
        self.console.clear()
    
    def print_separator(self, character: str = "=", length: int = 80):
        """Print a separator line"""
        self.console.print(character * length)