# 🌍 Multilingual Falco AI System - Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the **Falco AI Alert System v1.5.7** with **comprehensive multilingual support** in production environments.

### ✨ Key Features
- **24 Languages Supported** (covering 90% of global speakers)
- **Native AI Security Analysis** in multiple languages via multilingual AI models
- **Zero External API Costs** (fully local deployment)
- **Intelligent Fallback** mechanisms
- **Advanced Vector Search** via Weaviate
- **Real-time Security Monitoring** with Falco

---

## 🚀 Quick Start

### Prerequisites
- **Kubernetes cluster** (1.19+)
- **Docker** and **docker-compose** (for local testing)
- **kubectl** configured for your cluster
- **Helm 3.x** (optional but recommended)
- **4GB RAM minimum** (8GB+ recommended for multilingual AI models)
- **20GB storage** (for models and vector database)

### Supported Languages
🇺🇸 English • 🇨🇳 中文 • 🇮🇳 हिन्दी • 🇪🇸 Español • 🇸🇦 العربية • 🇫🇷 Français • 🇧🇩 বাংলা • 🇵🇹 Português • 🇷🇺 Русский • 🇵🇰 اردو • 🇮🇩 Bahasa Indonesia • 🇩🇪 Deutsch • 🇯🇵 日本語 • 🇰🇪 Kiswahili • 🇵🇭 Filipino • 🇮🇳 தமிழ் • 🇻🇳 Tiếng Việt • 🇹🇷 Türkçe • 🇮🇹 Italiano • 🇰🇷 한국어 • 🇳🇬 Hausa • 🇮🇷 فارسی • 🇹🇭 ภาษาไทย • 🇲🇲 မြန်မာဘာသာ

---

## 📋 Deployment Methods

### Method 1: Docker Compose (Local/Development)

```bash
# 1. Clone the repository
git clone https://github.com/maddigsys/falco-rag-ai-gateway.git
cd falco-rag-ai-gateway
git checkout feature/weaviate-ai-enhancement

# 2. Configure environment
cp env.example .env
# Edit .env with your settings

# 3. Deploy the stack
docker-compose up -d

# 4. Access the dashboard
open http://localhost:8080/dashboard

# 5. Configure multilingual settings
open http://localhost:8080/config/multilingual
```

### Method 2: Kubernetes Production Deployment

```bash
# 1. Apply namespace and base resources
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/

# 2. Apply production overlay
kubectl apply -k k8s/overlays/production/

# 3. Verify deployment
kubectl get pods -n falco-ai-system

# 4. Access via ingress or port-forward
kubectl port-forward -n falco-ai-system svc/falco-ai-alerts 8080:8080
```

### Method 3: Cloud Deployment (AWS EKS/GKE/AKS)

```bash
# 1. Deploy with cloud-specific overlay
kubectl apply -k k8s/overlays/eks/  # For AWS EKS
# or
kubectl apply -k k8s/overlays/gke/  # For Google GKE
# or
kubectl apply -k k8s/overlays/aks/  # For Azure AKS

# 2. Configure cloud storage for persistence
# Edit PVC in overlay to use cloud storage classes

# 3. Set up external access (LoadBalancer/Ingress)
# Configure according to your cloud provider
```

---

## ⚙️ Configuration

### 1. Multilingual Configuration

Access the configuration at: `http://your-domain/config/multilingual`

#### General Settings
```yaml
default_language: "en"              # Default system language
auto_detect_language: true          # Auto-detect from browser
enable_ui_translation: "ai"         # Use AI models for translations
fallback_behavior: "english"        # Fallback to English if needed
persist_language: true              # Remember user language choice
```

#### Multilingual AI Model Configuration
```yaml
ai_model: "qwen2:7b"                # Model: qwen2:7b (fast) or llama3:latest (accurate)
ai_timeout: 60                      # Request timeout in seconds
ai_temperature: 0.7                 # Creativity level (0.1-1.0)
ai_max_tokens: 1000                 # Maximum response length
ollama_endpoint: "http://ollama:11434"  # Ollama API endpoint
enable_multilingual_ai: true        # Enable/disable multilingual AI models
```

#### Language Selection
- Select from **24 supported languages**
- Enable/disable specific languages for your organization
- Configure priority languages for your user base

### 2. Model Management

#### Download Multilingual AI Models
```bash
# Via the UI (recommended)
# Go to: http://your-domain/config/multilingual
# Click "Model Management" tab
# Click "Download qwen2:7b" button

# Via API
curl -X POST http://your-domain/api/translation/pull-model \
  -H "Content-Type: application/json" \
  -d '{"model_name": "qwen2:7b"}'

# Via kubectl (direct to Ollama)
kubectl exec -n falco-ai-system deployment/ollama -- \
  ollama pull qwen2:7b
```

#### Model Storage Requirements
- **qwen2:7b**: ~4.4GB storage (recommended for most deployments)
- **llama3:latest**: ~4.7GB storage (for maximum accuracy)

### 3. Environment Variables

```bash
# Core Configuration
PROVIDER_NAME=ollama                     # AI provider: ollama/openai/gemini
WEB_UI_ENABLED=true                     # Enable web dashboard
LOG_LEVEL=INFO                          # Logging level

# Multilingual Settings
AI_MODEL=qwen2:7b                       # Default multilingual AI model
AI_MULTILINGUAL_ENABLED=true            # Enable multilingual support
DEFAULT_LANGUAGE=en                     # System default language

# Weaviate Configuration
WEAVIATE_ENABLED=true                   # Enable vector search
WEAVIATE_HOST=weaviate                  # Weaviate hostname
WEAVIATE_PORT=8080                      # Weaviate port

# Security Settings
MIN_PRIORITY=warning                    # Minimum alert priority
IGNORE_OLDER=1                          # Ignore alerts older than X minutes

# Optional: Cloud AI (if not using local multilingual AI models)
PORTKEY_API_KEY=your_portkey_key       # For OpenAI/Gemini fallback
OPENAI_VIRTUAL_KEY=your_openai_key     # OpenAI via Portkey
GEMINI_VIRTUAL_KEY=your_gemini_key     # Gemini via Portkey

# Slack Integration (optional)
SLACK_BOT_TOKEN=xoxb-your-token        # Slack bot token
SLACK_CHANNEL_NAME=#security-alerts    # Default channel
```

---

## 🔧 Performance Tuning

### Resource Requirements

#### Minimum (Development)
```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "1000m"
```

#### Recommended (Production)
```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "1000m"
  limits:
    memory: "8Gi"
    cpu: "2000m"
```

#### High-Performance (Enterprise)
```yaml
resources:
  requests:
    memory: "8Gi"
    cpu: "2000m"
  limits:
    memory: "16Gi"
    cpu: "4000m"
```

### Scaling Configuration

#### Horizontal Pod Autoscaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: falco-ai-alerts-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: falco-ai-alerts
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Multilingual AI Model Optimization

#### Model Selection Guidelines
- **qwen2:7b**: Best for most use cases (faster, lower memory)
- **llama3:latest**: Use when maximum accuracy is required

#### Performance Settings
```yaml
# Fast Response (lower accuracy)
temperature: 0.3
max_tokens: 500
timeout: 30

# Balanced (recommended)
temperature: 0.7
max_tokens: 1000
timeout: 60

# High Accuracy (slower)
temperature: 0.9
max_tokens: 2000
timeout: 120
```

---

## 🛡️ Security Configuration

### 1. Network Security

#### Network Policies
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: falco-ai-network-policy
spec:
  podSelector:
    matchLabels:
      app: falco-ai-alerts
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: falco-ai-system
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: falco-ai-system
    ports:
    - protocol: TCP
      port: 8080    # Weaviate
    - protocol: TCP
      port: 11434   # Ollama
```

### 2. RBAC Configuration

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: falco-ai-reader
rules:
- apiGroups: [""]
  resources: ["pods", "nodes", "events"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: falco-ai-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: falco-ai-reader
subjects:
- kind: ServiceAccount
  name: falco-ai-service-account
  namespace: falco-ai-system
```

### 3. Secret Management

```bash
# Create secrets for sensitive data
kubectl create secret generic falco-ai-secrets \
  --from-literal=portkey-api-key="your-key" \
  --from-literal=slack-bot-token="your-token" \
  -n falco-ai-system

# Reference in deployment
envFrom:
- secretRef:
    name: falco-ai-secrets
```

---

## 📊 Monitoring & Observability

### 1. Health Checks

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 60
  periodSeconds: 30
  timeoutSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
```

### 2. Metrics & Alerting

#### Prometheus Configuration
```yaml
- job_name: 'falco-ai-alerts'
  static_configs:
  - targets: ['falco-ai-alerts:8080']
  metrics_path: '/metrics'
  scrape_interval: 30s
```

#### Key Metrics to Monitor
- **AI Response Time**: `ai_analysis_duration_seconds`
- **Alert Processing Rate**: `alerts_processed_total`
- **Translation Success Rate**: `translation_success_rate`
- **Weaviate Operations**: `weaviate_operations_total`
- **Memory Usage**: `container_memory_usage_bytes`
- **Model Performance**: `multilingual_ai_requests_total`

### 3. Logging Configuration

```yaml
logging:
  level: INFO
  structured: true
  fields:
    service: falco-ai-alerts
    version: v1.5.7
    language: ${CURRENT_LANGUAGE}
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Multilingual AI Model Not Available
```bash
# Check if model is downloaded
kubectl exec -n falco-ai-system deployment/ollama -- ollama list

# Download model manually
kubectl exec -n falco-ai-system deployment/ollama -- ollama pull qwen2:7b

# Check model status via API
curl http://your-domain/api/translation/status
```

#### 2. Weaviate Connection Issues
```bash
# Check Weaviate health
kubectl get pods -n falco-ai-system -l app=weaviate

# Check service connectivity
kubectl exec -n falco-ai-system deployment/falco-ai-alerts -- \
  curl -f http://weaviate:8080/v1/.well-known/ready

# Restart Weaviate if needed
kubectl rollout restart deployment/weaviate -n falco-ai-system
```

#### 3. Language Switching Not Working
```bash
# Test language API
curl -X POST http://your-domain/api/lang/es \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Check multilingual configuration
curl http://your-domain/api/multilingual/config

# Verify multilingual AI status
curl http://your-domain/api/translation/status
```

#### 4. Performance Issues
```bash
# Check resource usage
kubectl top pods -n falco-ai-system

# Check logs for errors
kubectl logs -n falco-ai-system deployment/falco-ai-alerts --tail=100

# Scale up if needed
kubectl scale deployment/falco-ai-alerts --replicas=3 -n falco-ai-system
```

### Debug Commands

```bash
# Get all system status
curl http://your-domain/api/features/status

# Test AI analysis
curl -X POST http://your-domain/api/ai/test \
  -H "Content-Type: application/json" \
  -d '{"test_type": "connection"}'

# Test multilingual analysis
curl -X POST http://your-domain/api/ai/analyze-multilingual \
  -H "Content-Type: application/json" \
  -d '{
    "alert_payload": {
      "rule": "Terminal shell",
      "priority": "warning", 
      "output": "Shell detected in container"
    },
    "language": "es"
  }'

# Check Weaviate health
curl http://your-domain/api/weaviate/health
```

---

## 🔄 Backup & Recovery

### Database Backup
```bash
# Backup SQLite database
kubectl cp falco-ai-system/falco-ai-alerts-xxx:/app/data/alerts.db ./backup-$(date +%Y%m%d).db

# Backup Weaviate data
kubectl cp falco-ai-system/weaviate-xxx:/var/lib/weaviate ./weaviate-backup-$(date +%Y%m%d)/
```

### Model Backup
```bash
# Backup Ollama models
kubectl cp falco-ai-system/ollama-xxx:/root/.ollama ./ollama-backup-$(date +%Y%m%d)/
```

### Restore Procedure
```bash
# Restore database
kubectl cp ./backup-20240101.db falco-ai-system/falco-ai-alerts-xxx:/app/data/alerts.db

# Restart pods to apply changes
kubectl rollout restart deployment/falco-ai-alerts -n falco-ai-system
```

---

## 📈 Production Checklist

### Pre-Deployment
- [ ] Review and configure all environment variables
- [ ] Set up persistent storage for databases and models
- [ ] Configure network policies and RBAC
- [ ] Set up monitoring and alerting
- [ ] Test backup and recovery procedures
- [ ] Configure SSL/TLS certificates
- [ ] Set up log aggregation

### Post-Deployment
- [ ] Verify all services are healthy
- [ ] Test multilingual functionality
- [ ] Download required multilingual AI models
- [ ] Configure language preferences
- [ ] Test alert processing pipeline
- [ ] Verify Weaviate vector search
- [ ] Test Slack integration (if enabled)
- [ ] Set up monitoring dashboards

### Security Hardening
- [ ] Enable network policies
- [ ] Configure RBAC with least privilege
- [ ] Set up secret management
- [ ] Enable audit logging
- [ ] Configure firewall rules
- [ ] Review default credentials
- [ ] Enable HTTPS/TLS
- [ ] Set up vulnerability scanning

---

## 🆘 Support & Resources

### Documentation
- **Main Repository**: https://github.com/maddigsys/falco-rag-ai-gateway
- **Qwen2 Model**: https://huggingface.co/Qwen/Qwen2-7B-Instruct
- **Weaviate Documentation**: https://weaviate.io/developers/weaviate
- **Falco Documentation**: https://falco.org/docs/

### Community Support
- **Discord**: Join our multilingual security community
- **GitHub Issues**: Report bugs and feature requests
- **Stack Overflow**: Tag questions with `falco-ai-multilingual`

### Commercial Support
- **Enterprise Support**: Available for production deployments
- **Custom Language Models**: Tailored multilingual AI model training
- **Professional Services**: Implementation and optimization

---

## 📝 Changelog

### v1.5.7 - Multilingual Release
- ✅ Added comprehensive 24-language support via multilingual AI models
- ✅ Implemented native language AI security analysis
- ✅ Added multilingual configuration interface
- ✅ Enhanced Weaviate integration with proper vectorization
- ✅ Improved fallback mechanisms for high availability
- ✅ Added extensive monitoring and health checks
- ✅ Zero external API costs for multilingual features

---

## 🎯 Next Steps

1. **Access your deployment**: `http://your-domain/dashboard`
2. **Configure languages**: `http://your-domain/config/multilingual`
3. **Download multilingual models**: Use the Model Management tab
4. **Test with sample alerts**: Use the test scripts in `test scripts/`
5. **Monitor system health**: Set up Prometheus/Grafana dashboards
6. **Customize for your environment**: Adjust settings via configuration APIs

---

*This production deployment guide ensures your multilingual Falco AI Alert System is secure, scalable, and ready for global enterprise deployment. For questions or support, please refer to the community resources above.* 