#!/usr/bin/env python3
"""
EKS Advisor Web Interface
FastAPI-based web dashboard for EKS cluster analysis
"""

import uvicorn
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse

# MVC Components
from controllers.cluster_controller import ClusterController
from controllers.analysis_controller import AnalysisController
from controllers.history_controller import HistoryController
from views.web_view import WebView

# Initialize FastAPI app
app = FastAPI(
    title="EKS Advisor Web Dashboard",
    description="AI-Powered Kubernetes Analysis Dashboard",
    version="1.0.0"
)

# Templates directory
templates = Jinja2Templates(directory="templates")

# Initialize MVC components
cluster_controller = ClusterController()
analysis_controller = AnalysisController()
history_controller = HistoryController()
web_view = WebView()

# Global cache for cluster data
cluster_cache = {
    'last_update': None,
    'cluster_info': None,
    'cluster_overview': None,
    'recent_events': None,
    'problem_events': None,
    'analysis_summary': None
}

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    
    try:
        # Get or refresh cluster data
        await refresh_cluster_data()
        
        # Prepare data for template
        context = {
            "request": request,
            "cluster_overview": web_view.render_cluster_overview(cluster_cache['cluster_overview']),
            "metrics_cards": web_view.render_metrics_cards(cluster_cache.get('analysis_summary', {})),
            "problem_events": web_view.render_problem_events(cluster_cache['problem_events']),
            "last_update": cluster_cache['last_update'].strftime("%Y-%m-%d %H:%M:%S") if cluster_cache['last_update'] else 'Never'
        }
        
        return templates.TemplateResponse("dashboard.html", context)
        
    except Exception as e:
        # Error page
        context = {
            "request": request,
            "error": str(e),
            "error_type": type(e).__name__
        }
        return templates.TemplateResponse("error.html", context)

@app.get("/events", response_class=HTMLResponse)
async def events_page(request: Request):
    """Events detail page"""
    
    try:
        await refresh_cluster_data()
        
        context = {
            "request": request,
            "cluster_name": cluster_cache['cluster_info'].display_name if cluster_cache['cluster_info'] else 'Unknown',
            "events": web_view.render_events_table(cluster_cache['recent_events']),
            "total_events": len(cluster_cache['recent_events']),
            "last_update": cluster_cache['last_update'].strftime("%Y-%m-%d %H:%M:%S") if cluster_cache['last_update'] else 'Never'
        }
        
        return templates.TemplateResponse("events.html", context)
        
    except Exception as e:
        context = {
            "request": request,
            "error": str(e),
            "error_type": type(e).__name__
        }
        return templates.TemplateResponse("error.html", context)

@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    """Analysis results page"""
    
    try:
        await refresh_cluster_data()
        
        analysis_summary = cluster_cache.get('analysis_summary', {})
        
        context = {
            "request": request,
            "cluster_name": cluster_cache['cluster_info'].display_name if cluster_cache['cluster_info'] else 'Unknown',
            "analysis": web_view.render_analysis_summary(analysis_summary),
            "security_details": analysis_summary.get('security', {}),
            "performance_details": analysis_summary.get('performance', {}),
            "last_update": cluster_cache['last_update'].strftime("%Y-%m-%d %H:%M:%S") if cluster_cache['last_update'] else 'Never'
        }
        
        return templates.TemplateResponse("analysis.html", context)
        
    except Exception as e:
        context = {
            "request": request,
            "error": str(e),
            "error_type": type(e).__name__
        }
        return templates.TemplateResponse("error.html", context)

@app.get("/history")
async def history_page(request: Request):
    """History page with charts for viewing scores over time"""
    
    try:
        cluster_info = cluster_cache.get('cluster_info')
        if not cluster_info:
            await refresh_cluster_data()
            cluster_info = cluster_cache.get('cluster_info')
        
        if not cluster_info:
            raise Exception("Unable to connect to cluster")
        
        # Get trend data for the last 30 days
        trend_data = history_controller.get_trend_data(
            cluster_name=cluster_info.display_name,
            days_back=30
        )
        
        # Get cluster timeline for the last 30 days
        timeline_data = history_controller.get_cluster_timeline(
            cluster_name=cluster_info.display_name,
            days_back=30,
            limit=100
        )
        
        # Get cluster comparison data
        comparison_data = history_controller.get_cluster_comparison(days_back=7)
        
        # Get database summary
        history_summary = history_controller.get_history_summary()
        
        context = {
            "request": request,
            "cluster_name": cluster_info.display_name,
            "trend_data": trend_data,
            "timeline_data": timeline_data,
            "comparison_data": comparison_data,
            "history_summary": history_summary,
            "last_update": cluster_cache['last_update'].strftime("%Y-%m-%d %H:%M:%S") if cluster_cache['last_update'] else 'Never'
        }
        
        return templates.TemplateResponse("history.html", context)
        
    except Exception as e:
        context = {
            "request": request,
            "error": str(e),
            "error_type": type(e).__name__
        }
        return templates.TemplateResponse("error.html", context)

@app.get("/api/history/{cluster_name}")
async def get_history_data(cluster_name: str, days_back: int = 7):
    """API endpoint to get historical data for charts"""
    
    try:
        trend_data = history_controller.get_trend_data(
            cluster_name=cluster_name,
            days_back=days_back
        )
        
        return JSONResponse({
            "status": "success",
            "data": trend_data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/refresh")
async def refresh_data():
    """API endpoint to refresh cluster data"""
    
    try:
        await refresh_cluster_data(force_refresh=True)
        return JSONResponse({
            "status": "success",
            "message": "Data refreshed successfully",
            "last_update": cluster_cache['last_update'].isoformat() if cluster_cache['last_update'] else None
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    """API endpoint for cluster status"""
    
    try:
        cluster_info = cluster_cache.get('cluster_info')
        if not cluster_info:
            await refresh_cluster_data()
            cluster_info = cluster_cache.get('cluster_info')
        
        return JSONResponse({
            "status": "connected" if cluster_info else "disconnected",
            "cluster_name": cluster_info.display_name if cluster_info else "Unknown",
            "last_update": cluster_cache['last_update'].isoformat() if cluster_cache['last_update'] else None,
            "node_count": cluster_info.node_count if cluster_info else 0,
            "namespace_count": cluster_info.namespace_count if cluster_info else 0
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e)
        })

async def refresh_cluster_data(force_refresh: bool = False):
    """Refresh cluster data cache"""
    
    # Check if cache is fresh (less than 5 minutes old)
    if not force_refresh and cluster_cache['last_update']:
        age_minutes = (datetime.utcnow() - cluster_cache['last_update']).total_seconds() / 60
        if age_minutes < 5:
            return
    
    try:
        # Connect to cluster
        connection_result = cluster_controller.connect_to_cluster()
        if not connection_result["success"]:
            raise Exception(f"Cluster connection failed: {connection_result['message']}")
        
        cluster_cache['cluster_info'] = connection_result["cluster_info"]
        
        # Get cluster overview
        cluster_cache['cluster_overview'] = cluster_controller.get_cluster_overview()
        
        # Get recent events
        cluster_cache['recent_events'] = cluster_controller.get_recent_events(hours_back=24, limit=100)
        
        # Get problem events
        cluster_cache['problem_events'] = cluster_controller.get_problem_events(hours_back=2)
        
        # Get analysis summary if we have events
        if cluster_cache['recent_events']:
            cluster_cache['analysis_summary'] = analysis_controller.get_analysis_summary(
                cluster_cache['cluster_info'].display_name,
                cluster_cache['recent_events']
            )
        
        cluster_cache['last_update'] = datetime.utcnow()
        
    except Exception as e:
        print(f"Error refreshing cluster data: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize app on startup"""
    print("🚀 EKS Advisor Web Dashboard starting...")
    print("📊 Attempting initial cluster connection...")
    
    try:
        await refresh_cluster_data()
        print("✅ Initial cluster data loaded successfully")
    except Exception as e:
        print(f"⚠️  Initial cluster connection failed: {e}")
        print("💡 Dashboard will show error page until cluster is available")

def main():
    """Main entry point for web server"""
    
    print("🎯 EKS Advisor Web Dashboard")
    print("=" * 50)
    print("Starting web server...")
    print("Dashboard will be available at: http://localhost:8000")
    print("API endpoints:")
    print("  - GET /api/status  - Cluster status")
    print("  - GET /api/refresh - Refresh data")
    print("=" * 50)
    
    uvicorn.run(
        "web_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()