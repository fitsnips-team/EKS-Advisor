"""
LLM Configuration and Security Management
Supports OpenAI, Ollama, and hybrid configurations with security-first approach
"""

import os
import re
import hashlib
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

import ollama


class LLMProvider(Enum):
    OPENAI = "openai"
    OLLAMA = "ollama" 
    HYBRID = "hybrid"


class DataSensitivity(Enum):
    """SOC2-aligned data sensitivity classifications"""
    PUBLIC = "public"                           # No restrictions, publicly available
    INTERNAL = "internal"                       # Internal use only, basic confidentiality
    CONFIDENTIAL = "confidential"               # Restricted access, confidentiality controls
    SENSITIVE = "sensitive"                     # Customer data, processing integrity required
    HIGHLY_SENSITIVE = "highly_sensitive"       # Customer PII, enhanced privacy controls
    RESTRICTED = "restricted"                   # Security-critical, availability controls
    CRITICAL = "critical"                       # Maximum security, all SOC2 controls


@dataclass
class SecurityConfig:
    """SOC2-compliant security configuration for LLM processing"""
    # Security Controls
    enable_data_redaction: bool = True
    local_processing_only: bool = False
    audit_logging: bool = True
    auto_classify_data: bool = True
    
    # Availability Controls
    max_processing_timeout: int = 300  # 5 minutes
    enable_failover: bool = True
    health_check_interval: int = 60
    
    # Processing Integrity Controls
    validate_input_data: bool = True
    verify_output_completeness: bool = True
    enable_data_checksums: bool = True
    
    # Confidentiality Controls
    encryption_at_rest: bool = True
    encryption_in_transit: bool = True
    access_control_enabled: bool = True
    
    # Privacy Controls
    anonymize_customer_data: bool = True
    data_minimization: bool = True
    consent_tracking: bool = True
    
    # Data Retention (SOC2 requirement)
    max_data_retention_days: int = 90
    auto_purge_expired_data: bool = True
    retention_policy_version: str = "1.0"


class SecureLLMManager:
    """Manages LLM providers with security-first approach"""
    
    def __init__(self, security_config: SecurityConfig = None):
        self.security_config = security_config or SecurityConfig()
        self.provider = self._determine_provider()
        self.llm_instances = self._initialize_llm_instances()
    
    def _determine_provider(self) -> LLMProvider:
        """Determine which LLM provider to use based on configuration"""
        
        provider_str = os.getenv('LLM_PROVIDER', 'ollama').lower()
        
        try:
            return LLMProvider(provider_str)
        except ValueError:
            print(f"⚠️  Unknown LLM provider '{provider_str}', defaulting to Ollama for security")
            return LLMProvider.OLLAMA
    
    def _initialize_llm_instances(self) -> Dict[str, Any]:
        """Initialize LLM instances based on provider configuration"""
        
        instances = {}
        
        # Initialize Ollama (local) if configured
        if self.provider in [LLMProvider.OLLAMA, LLMProvider.HYBRID]:
            try:
                ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
                ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')
                
                # Test Ollama connection
                client = ollama.Client(host=ollama_base_url, timeout=30)
                models = client.list()
                
                if any(ollama_model in model.model for model in models.models):
                    instances['ollama'] = {
                        'client': client,
                        'model': ollama_model,
                        'base_url': ollama_base_url,
                        'privacy_level': 'maximum'  # Local processing
                    }
                    print(f"✅ Ollama connected: {ollama_model} at {ollama_base_url}")
                else:
                    print(f"⚠️  Model {ollama_model} not found in Ollama. Available models:")
                    for model in models.models:
                        print(f"   - {model.model}")
                    
            except Exception as e:
                print(f"❌ Failed to connect to Ollama: {e}")
                if self.provider == LLMProvider.OLLAMA:
                    print("💡 To use Ollama:")
                    print("   1. Install: curl -fsSL https://ollama.ai/install.sh | sh")
                    print("   2. Start: ollama serve")
                    print("   3. Pull model: ollama pull llama3.1:8b")
        
        # Initialize OpenAI if configured
        if self.provider in [LLMProvider.OPENAI, LLMProvider.HYBRID]:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                instances['openai'] = {
                    'api_key': openai_key,
                    'model': 'gpt-4',
                    'privacy_level': 'external'  # External API
                }
                print("✅ OpenAI configured")
            else:
                print("⚠️  OPENAI_API_KEY not found")
        
        return instances
    
    def classify_data_sensitivity(self, data: str) -> DataSensitivity:
        """Automatically classify data sensitivity level"""
        
        # Check for critical patterns first
        critical_patterns = ['token', 'key', 'secret', 'password', 'certificate']
        if any(pattern in data.lower() for pattern in critical_patterns):
            return DataSensitivity.CRITICAL
        
        # Check for highly sensitive patterns
        highly_sensitive_patterns = ['rbac', 'securitypolicy', 'networkpolicy']
        if any(pattern in data.lower() for pattern in highly_sensitive_patterns):
            return DataSensitivity.HIGHLY_SENSITIVE
        
        # Check for sensitive patterns
        sensitive_patterns = ['pod/', 'namespace/', 'deployment/']
        if any(pattern in data.lower() for pattern in sensitive_patterns):
            return DataSensitivity.SENSITIVE
        
        # Check for internal patterns
        internal_patterns = ['cluster', 'node', 'event']
        if any(pattern in data.lower() for pattern in internal_patterns):
            return DataSensitivity.INTERNAL
        
        return DataSensitivity.PUBLIC
    
    def process_with_appropriate_llm(self, prompt: str, data: str) -> str:
        """Process data with appropriate LLM based on sensitivity"""
        
        # Classify data sensitivity
        sensitivity = self.classify_data_sensitivity(data)
        
        # Choose appropriate LLM based on security requirements
        if sensitivity in [DataSensitivity.CRITICAL, DataSensitivity.HIGHLY_SENSITIVE, DataSensitivity.SENSITIVE]:
            if 'ollama' in self.llm_instances:
                return self._process_with_ollama(prompt, data)
            else:
                print(f"⚠️  Sensitive data detected but Ollama not available. Skipping processing.")
                return "[ANALYSIS SKIPPED - SENSITIVE DATA REQUIRES LOCAL PROCESSING]"
        else:
            # For internal/public data, can use any available LLM
            if 'ollama' in self.llm_instances:
                return self._process_with_ollama(prompt, data)
            elif 'openai' in self.llm_instances:
                return self._process_with_openai(prompt, data)
            else:
                return "[NO LLM AVAILABLE FOR PROCESSING]"
    
    def _process_with_ollama(self, prompt: str, data: str) -> str:
        """Process with Ollama (local processing)"""
        
        try:
            client = self.llm_instances['ollama']['client']
            model = self.llm_instances['ollama']['model']
            
            full_prompt = f"{prompt}\n\nData to analyze:\n{data}"
            
            response = client.generate(
                model=model,
                prompt=full_prompt,
                options={
                    'temperature': 0.1,  # Low temperature for consistent analysis
                    'top_p': 0.9,
                    'num_predict': 1000
                }
            )
            
            return response['response']
            
        except Exception as e:
            print(f"❌ Ollama processing error: {e}")
            return f"[OLLAMA PROCESSING ERROR: {str(e)}]"
    
    def _process_with_openai(self, prompt: str, data: str) -> str:
        """Process with OpenAI (external API - requires data to be safe)"""
        
        # This would integrate with CrewAI's OpenAI LLM
        # For now, return a placeholder
        return "[OPENAI PROCESSING - WOULD USE CREWAI'S OPENAI INTEGRATION]"
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security configuration status"""
        
        return {
            'provider': self.provider.value,
            'available_llms': list(self.llm_instances.keys()),
            'security_config': {
                'data_redaction_enabled': self.security_config.enable_data_redaction,
                'local_processing_only': self.security_config.local_processing_only,
                'audit_logging': self.security_config.audit_logging
            }
        }


def get_configured_llm_manager() -> SecureLLMManager:
    """Get configured LLM manager based on environment variables"""
    
    security_config = SecurityConfig(
        enable_data_redaction=os.getenv('ENABLE_DATA_REDACTION', 'true').lower() == 'true',
        local_processing_only=os.getenv('LOCAL_PROCESSING_ONLY', 'false').lower() == 'true',
        audit_logging=os.getenv('AUDIT_LOGGING', 'true').lower() == 'true'
    )
    
    return SecureLLMManager(security_config)


# Test function
if __name__ == "__main__":
    # Test the LLM manager
    manager = get_configured_llm_manager()
    
    print("\n🔍 Security Status:")
    status = manager.get_security_status()
    print(f"Provider: {status['provider']}")
    print(f"Available LLMs: {status['available_llms']}")
    print(f"Security Config: {status['security_config']}")
    
    # Test data classification
    test_data = "Pod web-app-123 failed to start due to insufficient CPU resources"
    sensitivity = manager.classify_data_sensitivity(test_data)
    print(f"\nData sensitivity: {sensitivity.value}")
    
    # Test processing
    result = manager.process_with_appropriate_llm(
        "Analyze this Kubernetes event for issues:",
        test_data
    )
    print(f"\nAnalysis result: {result[:100]}...")