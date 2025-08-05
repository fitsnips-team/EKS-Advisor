"""
EKS Advisor - MVC Architecture Main Application
Clean separation of Model, View, and Controller layers
"""

import sys
import time
from typing import Optional
from datetime import datetime

# MVC Components
from models import ClusterModel, EventModel, AnalysisModel
from controllers import ClusterController, AnalysisController
from views import ConsoleView, DashboardView

# Configuration
from llm_config import get_configured_llm_manager


class EKSAdvisorMVC:
    """Main MVC application for EKS Advisor"""
    
    def __init__(self, kubeconfig_path: Optional[str] = None, view_type: str = "console"):
        # Controllers
        self.cluster_controller = ClusterController(kubeconfig_path)
        self.analysis_controller = AnalysisController()
        
        # Views
        self.console_view = ConsoleView()
        self.dashboard_view = DashboardView()
        
        # Select primary view
        self.view = self.console_view if view_type == "console" else self.dashboard_view
        
        # Application state
        self.cluster_info = None
        self.last_analysis = None
    
    def run_comprehensive_analysis(self):
        """Run comprehensive cluster analysis with MVC pattern"""
        
        # Display header
        self.console_view.show_header("EKS Advisor - MVC Architecture")
        
        # Step 1: Connect to cluster (Controller -> Model)
        connection_result = self.cluster_controller.connect_to_cluster()
        self.console_view.show_connection_status(
            connection_result["success"], 
            connection_result["message"]
        )
        
        if not connection_result["success"]:
            self.console_view.show_error("Cannot proceed without cluster connection")
            return
        
        # Store cluster info
        self.cluster_info = connection_result["cluster_info"]
        
        # Step 2: Display cluster context (View)
        self.console_view.show_cluster_context(self.cluster_info)
        
        # Step 3: Get cluster health (Controller -> Model -> View)
        health_data = self.cluster_controller.get_cluster_health()
        self.console_view.show_health_status(health_data)
        
        # Step 4: Get recent events (Controller -> Model)
        with self.console_view.show_progress("Fetching recent events...") as progress:
            task = progress.add_task("Processing events", total=100)
            
            recent_events = self.cluster_controller.get_recent_events(hours_back=24, limit=50)
            progress.update(task, advance=50)
            
            problem_events = self.cluster_controller.get_problem_events(hours_back=1)
            progress.update(task, advance=25)
            
            events_summary = self.cluster_controller.get_events_summary(hours_back=24)
            progress.update(task, advance=25)
        
        # Step 5: Display events (View)
        self.console_view.show_events_table(recent_events[:10], "Recent Events (Last 10)")
        self.console_view.show_events_summary(events_summary)
        self.console_view.show_problem_events(problem_events)
        
        # Step 6: Perform AI analysis (Controller -> Model)
        if recent_events:
            with self.console_view.show_progress("Performing AI analysis...") as progress:
                task = progress.add_task("AI Analysis", total=100)
                
                # Quick analysis
                quick_analysis = self.analysis_controller.quick_analysis(
                    recent_events, 
                    self.cluster_info.display_name
                )
                progress.update(task, advance=30)
                
                # Security assessment
                security_assessment = self.analysis_controller.get_security_assessment(recent_events)
                progress.update(task, advance=30)
                
                # Performance insights
                performance_insights = self.analysis_controller.get_performance_insights(recent_events)
                progress.update(task, advance=40)
            
            # Step 7: Display analysis results (View)
            self.console_view.show_quick_analysis(quick_analysis)
            self.console_view.show_security_assessment(security_assessment)
            self.console_view.show_performance_insights(performance_insights)
            
            # Store for later use
            self.last_analysis = {
                'overview': quick_analysis,
                'security': security_assessment,
                'performance': performance_insights,
                'events_analyzed': recent_events,
                'cluster_name': self.cluster_info.display_name,  
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Step 8: Display comprehensive summary (View)
            self.console_view.show_comprehensive_summary(
                self.cluster_info.display_name,
                self.last_analysis
            )
        else:
            self.console_view.show_warning("No recent events found for analysis")
    
    def run_dashboard_mode(self):
        """Run dashboard-style analysis"""
        
        self.console_view.show_header("EKS Advisor Dashboard - MVC Architecture")
        
        # Get comprehensive cluster overview
        cluster_overview = self.cluster_controller.get_cluster_overview()
        
        if 'error' in cluster_overview:
            self.console_view.show_error(cluster_overview['error'])
            return
        
        # Display dashboard
        self.dashboard_view.show_cluster_overview_dashboard(cluster_overview)
        
        # Get events for pattern analysis
        recent_events = self.cluster_controller.get_recent_events(hours_back=24, limit=100)
        
        if recent_events:
            # Show event patterns
            self.dashboard_view.show_event_pattern_analysis(recent_events)
            
            # Get analysis summary
            analysis_summary = self.analysis_controller.get_analysis_summary(
                cluster_overview['cluster']['name'],
                recent_events
            )
            
            # Show metrics dashboard
            self.dashboard_view.show_analysis_metrics_dashboard(analysis_summary)
            
            # Show trending analysis
            events_summary = self.cluster_controller.get_events_summary(hours_back=24)
            self.dashboard_view.show_trending_analysis(events_summary)
    
    def run_quick_health_check(self):
        """Run quick health check"""
        
        self.console_view.show_header("EKS Advisor - Quick Health Check")
        
        # Connect and get basic info
        connection_result = self.cluster_controller.connect_to_cluster()
        
        if not connection_result["success"]:
            self.console_view.show_error(connection_result["message"])
            return
        
        cluster_info = connection_result["cluster_info"]
        self.console_view.show_cluster_context(cluster_info)
        
        # Get health status
        health = self.cluster_controller.get_cluster_health()
        self.console_view.show_health_status(health)
        
        # Get problem events
        problem_events = self.cluster_controller.get_problem_events(hours_back=1)
        
        if problem_events:
            self.console_view.show_problem_events(problem_events[:5])
            
            # Quick AI analysis of top issue
            top_issue = problem_events[0]
            single_analysis = self.analysis_controller.analyze_single_event(top_issue)
            
            if 'ai_analysis' in single_analysis:
                self.console_view.show_success(
                    f"AI Analysis: {single_analysis['ai_analysis'][:200]}...",
                    "Top Priority Issue Analysis"
                )
        else:
            self.console_view.show_success("No critical issues detected - cluster appears healthy!")
        
        # Summary
        summary = {
            'cluster_name': cluster_info.display_name,
            'overview': {'events_analyzed': len(problem_events)},
            'processing_location': 'local',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.console_view.show_comprehensive_summary(cluster_info.display_name, summary)
    
    def run_security_focused_analysis(self):
        """Run security-focused analysis"""
        
        self.console_view.show_header("EKS Advisor - Security Analysis")
        
        # Connect
        connection_result = self.cluster_controller.connect_to_cluster()
        if not connection_result["success"]:
            self.console_view.show_error(connection_result["message"])
            return
        
        cluster_info = connection_result["cluster_info"]
        self.console_view.show_cluster_context(cluster_info)
        
        # Get events
        recent_events = self.cluster_controller.get_recent_events(hours_back=24, limit=200)
        
        if recent_events:
            # Security assessment
            security_assessment = self.analysis_controller.get_security_assessment(recent_events)
            self.console_view.show_security_assessment(security_assessment)
            
            # Security-focused event display
            security_events = [e for e in recent_events if any(
                keyword in f"{e.reason} {e.message}".lower() 
                for keyword in ['security', 'rbac', 'unauthorized', 'denied', 'forbidden']
            )]
            
            if security_events:
                self.console_view.show_events_table(security_events[:10], "Security-Related Events")
            else:
                self.console_view.show_success("No security-related events detected")
        else:
            self.console_view.show_warning("No events available for security analysis")
    
    def interactive_mode(self):
        """Run interactive mode with user choices"""
        
        while True:
            self.console_view.clear_screen()
            self.console_view.show_header("EKS Advisor - Interactive Mode")
            
            # Show menu
            self.console_view.console.print("\n[bold cyan]Select Analysis Mode:[/bold cyan]")
            self.console_view.console.print("1. 🎯 Comprehensive Analysis")
            self.console_view.console.print("2. 📊 Dashboard Mode")
            self.console_view.console.print("3. ⚡ Quick Health Check")
            self.console_view.console.print("4. 🛡️  Security Analysis")
            self.console_view.console.print("5. 🔄 Refresh Connection")
            self.console_view.console.print("6. ❌ Exit")
            
            choice = self.console_view.prompt_user("\nEnter your choice (1-6)")
            
            try:
                if choice == "1":
                    self.run_comprehensive_analysis()
                elif choice == "2":
                    self.run_dashboard_mode()
                elif choice == "3":
                    self.run_quick_health_check()
                elif choice == "4":
                    self.run_security_focused_analysis()
                elif choice == "5":
                    success = self.cluster_controller.refresh_connection()
                    if success:
                        self.console_view.show_success("Connection refreshed successfully")
                    else:
                        self.console_view.show_error("Failed to refresh connection")
                elif choice == "6":
                    self.console_view.show_success("Thank you for using EKS Advisor!")
                    break
                else:
                    self.console_view.show_warning("Invalid choice. Please select 1-6.")
                
                if choice in ["1", "2", "3", "4"]:
                    self.console_view.prompt_user("\nPress Enter to continue")
                    
            except KeyboardInterrupt:
                self.console_view.show_warning("Operation cancelled by user")
                break
            except Exception as e:
                self.console_view.show_error(f"An error occurred: {str(e)}")
                self.console_view.prompt_user("Press Enter to continue")
    
    def get_cluster_status(self) -> dict:
        """Get current cluster status (API for external use)"""
        if not self.cluster_controller.is_cluster_available():
            return {"status": "disconnected", "error": "No cluster connection"}
        
        try:
            cluster_info = self.cluster_controller.get_cluster_info()
            health = self.cluster_controller.get_cluster_health()
            
            return {
                "status": "connected",
                "cluster_name": cluster_info.display_name,
                "healthy": health.get("healthy", False),
                "nodes": cluster_info.node_count,
                "namespaces": cluster_info.namespace_count,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


def main():
    """Main entry point with command line arguments"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="EKS Advisor - MVC Architecture")
    parser.add_argument("--mode", choices=["comprehensive", "dashboard", "health", "security", "interactive"], 
                       default="comprehensive", help="Analysis mode")
    parser.add_argument("--kubeconfig", help="Path to kubeconfig file")
    parser.add_argument("--view", choices=["console", "dashboard"], default="console", help="View type")
    
    args = parser.parse_args()
    
    try:
        # Initialize MVC application
        app = EKSAdvisorMVC(kubeconfig_path=args.kubeconfig, view_type=args.view)
        
        # Run selected mode
        if args.mode == "comprehensive":
            app.run_comprehensive_analysis()
        elif args.mode == "dashboard":
            app.run_dashboard_mode()
        elif args.mode == "health":
            app.run_quick_health_check()
        elif args.mode == "security":
            app.run_security_focused_analysis()
        elif args.mode == "interactive":
            app.interactive_mode()
            
    except KeyboardInterrupt:
        print("\n👋 EKS Advisor stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()