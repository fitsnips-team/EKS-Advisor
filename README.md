# EKS Advisor - AI-Powered Kubernetes Analysis

A production-ready system for intelligent EKS cluster monitoring and optimization using **MVC architecture** and local AI processing with security-first design.

## 🚀 Overview

EKS Advisor provides real-time analysis of your Kubernetes cluster events using local AI models for maximum privacy and security. Built with clean **Model-View-Controller (MVC) architecture** for maintainability and extensibility.

**Key Features:**
- **🏗️ MVC Architecture**: Clean separation of concerns with Models, Views, and Controllers
- **🔐 Privacy-First**: All AI processing done locally with Ollama (zero external API calls)
- **🤖 Intelligent Analysis**: User-friendly event translations and root cause analysis
- **📊 Multiple Analysis Modes**: Comprehensive, dashboard, health check, security, and interactive modes
- **🛡️ Security-Focused**: Automatic data classification and sensitivity handling
- **⚡ Fast Setup**: One-command installation with UV package manager

## 🏗️ MVC Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        EKS Advisor MVC                         │
├─────────────────────────────────────────────────────────────────┤
│                     main_mvc.py (Entry Point)                  │
├─────────────────────────────────────────────────────────────────┤
│  Controllers         │    Models           │    Views          │
│ • ClusterController  │  • ClusterModel     │  • ConsoleView    │
│ • AnalysisController │  • EventModel       │  • DashboardView  │
│                      │  • AnalysisModel    │                   │
├─────────────────────────────────────────────────────────────────┤
│            Infrastructure Layer (Kubernetes API, Ollama)       │
└─────────────────────────────────────────────────────────────────┘
```

## 🛠️ Quick Start

### Prerequisites
- Python 3.8+
- Kubernetes cluster access (optional - uses sample data if unavailable)
- Ollama installed (automatically handled by setup script)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd CrewAI_Demo

# Install UV package manager (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Set up environment
cp .env.example .env
```

### Environment Configuration

Create a `.env` file with:

```bash
# LLM Configuration - Using Ollama for local processing
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1:8b

# LLM Provider Selection: "ollama", "openai", or "hybrid"
LLM_PROVIDER=ollama

# Security Settings
ENABLE_DATA_REDACTION=true
LOCAL_PROCESSING_ONLY=true
AUDIT_LOGGING=true
```

## 🎯 Usage Commands - MVC Architecture

### Analysis Modes

#### Comprehensive Analysis (Recommended)
```bash
# Full cluster analysis with AI insights
uv run python main_mvc.py --mode comprehensive
```

#### Dashboard Mode
```bash
# Rich visual dashboard with multiple panels
uv run python main_mvc.py --mode dashboard
```

#### Quick Health Check
```bash
# Fast health assessment
uv run python main_mvc.py --mode health
```

#### Security-Focused Analysis
```bash
# Security-specific analysis and recommendations
uv run python main_mvc.py --mode security
```

#### Interactive Mode
```bash
# Interactive menu-driven interface
uv run python main_mvc.py --mode interactive
```

#### Web Dashboard (New!)
```bash
# Install web dependencies
uv sync --extra web

# Start web dashboard (recommended)
uv run python start_web.py

# Or start directly
uv run python web_app.py

# Then open: http://localhost:8000
```

### Component Testing
```bash
# Test LLM configuration and security features
uv run python llm_config.py

# Set up Ollama if needed
uv run python setup_ollama.py
```

## 📊 Sample Output

### Comprehensive Analysis
```
🎯 EKS Advisor - MVC Architecture
============================================================
📍 Cluster Context:
   Cluster: beta-stg01-usw2
   Context: arn:aws:eks:us-west-2:123456789:cluster/beta-stg01-usw2
   Namespace: default
   Nodes: 3

🏥 Cluster Health Status
✅ Status: Healthy (3/3 nodes healthy)
📊 Recent Events: 47 total, 23 warnings

🚨 Issues Detected (5)

1. Configuration Not Recommended (Count: 105)
   Resource: Event/strimzi-cluster-operator.17e8f4b3c2f8a1b2
   Namespace: kafka
   Severity: MEDIUM

2. Container Restart Delay (Count: 12)  
   Resource: Pod/web-app-deployment-xyz
   Namespace: production
   Severity: HIGH

⚡ Quick Analysis - beta-stg01-usw2
📊 Analyzed 47 events, found 0 critical and 5 high severity issues
🏥 Health Score: 73/100

✅ Analysis Summary - beta-stg01-usw2
🤖 Events Analyzed: 47
🔐 Processing: Local
🛡️  Security Score: 85/100
⚡ Performance Score: 78/100

Analysis completed with maximum privacy protection
```

### Dashboard Mode
```
🎯 EKS Advisor Dashboard - beta-stg01-usw2

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                           📍 Infrastructure                                   ┃
┃ Name: beta-stg01-usw2          Health Status: ✅ Healthy                     ┃  
┃ Context: arn:aws:eks...        Nodes: 3/3 healthy                           ┃
┃ Nodes: 3 | Namespaces: 12      Recent Events: 47                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                              🎯 Key Metrics                                  ┃
┃ 🏥 Health: 73/100          🛡️  Security: 85/100          ⚡ Performance: 78/100┃
┃                                                                               ┃
┃ Overall Status: 🟡 Good - Minor issues to address                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Web Dashboard
```
🚀 EKS Advisor Web Dashboard starting...
📊 Attempting initial cluster connection...
✅ Initial cluster data loaded successfully

Dashboard available at: http://localhost:8000

Features:
• 📊 Real-time cluster overview with health metrics
• 📋 Searchable events table with user-friendly translations  
• 🧠 AI analysis results with security & performance scores
• 🔄 Auto-refresh every 5 minutes + manual refresh button
• 📱 Responsive Bootstrap design for mobile/desktop
• 🛡️ Privacy-first: All processing done locally
```

## 🔐 Security Features

### Data Classification
- **PUBLIC**: General cluster information
- **INTERNAL**: Resource names and configurations  
- **HIGHLY_SENSITIVE**: RBAC and security policies
- **CRITICAL**: Secrets, tokens, and authentication data

### Privacy Protection
- **Local Processing**: All AI analysis done with local Ollama models
- **Zero External Calls**: No data sent to cloud services
- **Automatic Redaction**: Sensitive data automatically protected
- **Audit Logging**: Complete audit trail of all operations

## 🔧 MVC System Components

### Models Layer
- **ClusterModel** (`models/cluster_model.py`): Kubernetes cluster connection and data management
- **EventModel** (`models/event_model.py`): Event data modeling with user-friendly translations
- **AnalysisModel** (`models/analysis_model.py`): AI analysis integration and result processing

### Controllers Layer  
- **ClusterController** (`controllers/cluster_controller.py`): Orchestrates cluster operations
- **AnalysisController** (`controllers/analysis_controller.py`): Manages AI analysis workflows

### Views Layer
- **ConsoleView** (`views/console_view.py`): Terminal-based user interface with Rich formatting
- **DashboardView** (`views/dashboard_view.py`): Rich dashboard with multi-panel layouts

### Supporting Components
- **LLM Configuration** (`llm_config.py`): Ollama integration and data privacy management
- **Event Translations** (`utils/event_translations.py`): User-friendly event reason mappings
- **Setup Helper** (`setup_ollama.py`): Automated Ollama installation and configuration

## 🛡️ Production Considerations

### Security
- All sensitive data processed locally
- No external API dependencies for sensitive operations
- Comprehensive audit logging
- Configurable data redaction

### Performance
- Efficient event streaming with Kubernetes client-go patterns
- Local LLM caching for repeated analysis
- Minimal resource footprint

### Scalability
- Designed for enterprise EKS clusters
- Handles high-volume event streams
- Configurable analysis depth and scope

## 🐛 Troubleshooting

### Common Issues

**Ollama Connection Issues:**
```bash
# Check Ollama status
ollama list

# Start Ollama service
ollama serve

# Test model availability
ollama run llama3.1:8b "test prompt"
```

**Kubernetes Connection Issues:**
```bash
# Verify cluster access
kubectl get nodes

# Check kubeconfig
echo $KUBECONFIG

# Test event access
kubectl get events --sort-by=.metadata.creationTimestamp
```

**UV Environment Issues:**
```bash
# Reset UV environment
uv sync --reload

# Check Python path
uv run python --version
```

## 🚧 Known Limitations

- **CrewAI Integration**: Legacy multi-agent workflow removed in MVC refactor (low priority)
- **Model Performance**: Local LLM analysis takes 2-10 seconds per query
- **Memory Usage**: Ollama models require 4-8GB RAM depending on model size
- **User-Friendly Events**: Some rare Kubernetes events may not have friendly translations yet

## 🔮 Roadmap

### Phase 1 - Core Stability ✅
- [x] Event streaming and analysis
- [x] Local AI processing with Ollama
- [x] Security-first data handling
- [x] Basic cluster health assessment

### Phase 2 - Enhanced Features
- [ ] Fix CrewAI multi-agent integration
- [ ] Web dashboard interface
- [ ] Prometheus metrics integration
- [ ] Historical trend analysis

### Phase 3 - Enterprise Features
- [ ] Multi-cluster support
- [ ] Custom alerting rules
- [ ] Integration with monitoring systems
- [ ] Advanced ML-based anomaly detection

## 📖 Documentation

- [Technical Specification](EKS-Advisor-Technical-Specification.md) - Detailed architecture and security design
- [API Documentation](docs/api.md) - Component APIs and interfaces
- [Security Guide](docs/security.md) - Security features and best practices

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review existing GitHub issues
3. Create a new issue with detailed information

---

**Built with ❤️ for Kubernetes operators who value privacy and security**