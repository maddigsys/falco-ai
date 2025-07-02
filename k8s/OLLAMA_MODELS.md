# Ollama Model Selection and Resource Requirements

This guide helps you choose the right Ollama model for your environment and understand the resource requirements.

## Model Recommendations by Use Case

### Development/Testing ✅ **DEFAULT**
**Recommended Model**: `llama3.1:7b`
- **Memory Required**: 6-8GB RAM
- **Storage**: ~4GB
- **Response Quality**: Good for testing and development
- **Speed**: Fast inference (2-5 seconds)
- **Use Case**: Default for all environments

### Production (Balanced) ✅ **RECOMMENDED**
**Default Model**: `llama3.1:7b`
- **Memory Required**: 6-8GB RAM
- **Storage**: ~4GB
- **Response Quality**: Good general security analysis
- **Speed**: Fast inference (2-5 seconds)
- **Reliability**: Excellent uptime and responsiveness

### Production (Cybersecurity-Specialized) 🛡️ **UPGRADE OPTION**
**Cybersecurity Model**: `jimscard/whiterabbit-neo:latest` (13B)
- **Memory Required**: 14-16GB RAM
- **Storage**: ~9GB
- **Response Quality**: Excellent cybersecurity analysis
- **Speed**: Slower inference (15-30 seconds)
- **Specialization**: Specifically tuned for cybersecurity contexts
- **Trade-off**: Better analysis quality but slower response times

### High-Performance Production
**Expert Model**: `llama3.1:70b` (if resources allow)
- **Memory Required**: 40-50GB RAM
- **Storage**: ~40GB
- **Response Quality**: Excellent
- **Speed**: Very slow inference (60+ seconds)
- **Use Case**: Batch analysis or dedicated high-end hardware

## Resource Requirements by Model Size

| Model Size | RAM Required | Storage | CPU | Use Case | Notes |
|------------|-------------|---------|-----|----------|-------|
| 7B | 6-8GB | 4-6GB | 2 cores | Development, Testing | Fast inference (~2-5s) |
| 13B | **14-16GB** | 8-10GB | 4 cores | Production | **TESTED**: Model buffer 8.8GB + context 6GB = 16GB total, slower inference (~15-30s) |
| 30B | 20-24GB | 16-20GB | 6 cores | High-end Production | Very slow inference (60s+) |
| 70B | 40-50GB | 35-40GB | 8 cores | Enterprise | Extremely slow without GPU |

## Kubernetes Resource Configurations

### Small Models (7B) - Development
```yaml
resources:
  requests:
    memory: "6Gi"
    cpu: "1000m"
  limits:
    memory: "8Gi"
    cpu: "2000m"
```

### Medium Models (13B) - Production Default
```yaml
resources:
  requests:
    memory: "14Gi"  # TESTED: Required for jimscard/whiterabbit-neo
    cpu: "2000m"
  limits:
    memory: "16Gi"  # TESTED: Prevents OOM kills during inference
    cpu: "4000m"
```

### Large Models (30B+) - High-End Production
```yaml
resources:
  requests:
    memory: "20Gi"
    cpu: "4000m"
  limits:
    memory: "24Gi"
    cpu: "8000m"
```

## Environment-Specific Configurations

### Development Environment
Our development overlay automatically configures:
- **Model**: `llama3.1:7b`
- **Memory**: 6-8GB
- **Storage**: 15GB PVC
- **Replicas**: 1

### Production Environment
Our production overlay uses:
- **Model**: `jimscard/whiterabbit-neo:latest` (13B)
- **Memory**: 10-12GB
- **Storage**: 30GB PVC
- **Replicas**: 1

## Upgrading to Cybersecurity Model

### Via Dashboard (Recommended)
1. **Deploy with default 7B model** first for fast, reliable setup
2. **Access AI Configuration**: Go to `http://localhost:8080/config/ai`
3. **Change Model**: Update "Ollama Model Name" to `jimscard/whiterabbit-neo:latest`
4. **Increase Resources**: Update Kubernetes deployment resources:
   ```bash
   kubectl patch deployment prod-ollama -n falco-ai-alerts --patch '
   spec:
     template:
       spec:
         containers:
         - name: ollama
           resources:
             requests:
               memory: "14Gi"
             limits:
               memory: "16Gi"
   '
   ```
5. **Restart Ollama**: `kubectl rollout restart deployment/prod-ollama -n falco-ai-alerts`
6. **Wait for Model Download**: Monitor with `kubectl logs -f deployment/prod-ollama -n falco-ai-alerts`

### Benefits of Cybersecurity Model
- **Specialized Training**: Trained on cybersecurity datasets and terminology
- **Better Context Understanding**: Superior analysis of security incidents
- **Enhanced Threat Detection**: More accurate risk assessment
- **Detailed Remediation**: More comprehensive response recommendations

### When to Upgrade
- **After initial deployment works** with 7B model
- **When you have sufficient resources** (16GB+ RAM available)
- **For production security analysis** where quality > speed
- **When timeout issues are resolved** in your environment

## Changing Models

### Via Kubernetes Configuration
1. Update the model in your overlay's `kustomization.yaml`:
```yaml
- target:
    kind: Job
    name: ollama-model-init
  patch: |-
    - op: replace
      path: /spec/template/spec/containers/0/env/1/value
      value: "llama3.1:7b"  # Change this to your desired model
```

2. Update resources accordingly:
```yaml
- target:
    kind: Deployment
    name: ollama
  patch: |-
    - op: replace
      path: /spec/template/spec/containers/0/resources/limits/memory
      value: "8Gi"  # Adjust based on model size
```

### Via Dashboard Configuration
1. Go to the Falco AI Dashboard
2. Navigate to **AI Configuration**
3. Change the **Ollama Model Name** setting
4. Restart the Ollama deployment: `kubectl rollout restart deployment/ollama -n <namespace>`

## Troubleshooting

### "llama runner process has terminated: signal: killed"
**Cause**: Insufficient memory for the model
**Solution**: 
1. Check model requirements in the table above
2. Increase memory limits in your Kubernetes deployment
3. Consider using a smaller model

**Real-world Example**: 
- `jimscard/whiterabbit-neo:latest` (13B) requires 16GB total memory
- Model buffer alone: 8.8GB
- Context creation + overhead: ~6GB additional
- Original 12GB limit caused OOM kills, 16GB resolved the issue

### Model Download Failures
**Cause**: Insufficient storage or network issues
**Solution**:
1. Increase PVC size
2. Check internet connectivity
3. Verify model name exists in Ollama registry

### Slow Inference
**Cause**: Insufficient CPU or competing workloads
**Solution**:
1. Increase CPU limits
2. Use node selectors to place on dedicated nodes
3. Consider GPU acceleration (requires GPU-enabled nodes)

## Security Considerations

### Model Selection for Security Analysis
- **jimscard/whiterabbit-neo**: Specifically trained for cybersecurity contexts
- **llama3.1**: General-purpose but good reasoning capabilities
- **mistral:7b**: Fast and efficient for basic security analysis

### Custom Models
You can use any compatible Ollama model by:
1. Updating the model name in configuration
2. Adjusting resource limits accordingly
3. Testing with sample security alerts

## Performance Optimization

### CPU Optimization
- Set CPU requests to 50% of limits for better scheduling
- Use CPU limits 2-4x the requests for burst capability

### Memory Optimization
- Set memory requests to 80-90% of limits
- Monitor actual usage with `kubectl top pods`
- Adjust based on real-world usage patterns

### Storage Optimization
- Use SSD storage classes for better performance
- Size storage to 2-3x the model size for overhead
- Consider ReadWriteMany for multi-replica scenarios (if supported)

## Migration Guide

### From Small to Large Models
1. Update resource limits first
2. Scale down Ollama deployment
3. Update model configuration
4. Scale up deployment
5. Wait for model download completion

### Resource Validation
Use this command to check if your cluster has sufficient resources:
```bash
kubectl describe nodes | grep -A5 "Allocated resources"
```

## Performance Considerations

### Inference Speed vs Model Size Trade-off
- **7B models**: 2-5 second responses, good for high-volume alerts
- **13B models**: 15-30 second responses, better quality analysis
- **30B+ models**: 60+ second responses, excellent but impractical for real-time

### Production Recommendations
1. **For high-volume environments**: Use 7B models (llama3.1:7b, mistral:7b)
2. **For quality analysis**: Use 13B models but increase AI request timeouts
3. **For batch processing**: Larger models acceptable with async processing

### Timeout Configuration
Update AI timeouts in your application configuration:
```yaml
# In ConfigMap or environment
OLLAMA_TIMEOUT: "60"  # Increase for larger models
AI_REQUEST_TIMEOUT: "45"  # Application-level timeout
```

## Best Practices

1. **Start Small**: Begin with 7B models for testing
2. **Monitor Usage**: Use monitoring tools to track actual resource consumption
3. **Plan Capacity**: Ensure cluster has 20% headroom above model requirements
4. **Test Inference**: Verify model performance with real security alerts
5. **Backup Configurations**: Save working configurations before changes
6. **Performance Testing**: Test response times with your actual alert volume
7. **Consider Hybrid**: Use fast models for real-time, larger models for detailed analysis 