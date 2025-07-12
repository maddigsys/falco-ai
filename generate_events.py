#!/usr/bin/env python3
"""
Security Event Generator for Falco AI Gateway Testing
Generates realistic security events to test the event details functionality.
"""

import json
import time
import random
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List

class SecurityEventGenerator:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.container_names = [
            "web-server", "database", "api-gateway", "cache-redis", 
            "worker-queue", "monitoring", "logging", "auth-service"
        ]
        self.images = [
            "nginx:latest", "postgres:13", "redis:alpine", "node:16",
            "python:3.9", "mysql:8.0", "ubuntu:20.04", "alpine:latest"
        ]
        
    def generate_event(self) -> Dict:
        """Generate a random security event"""
        event_type = random.choice([
            "terminal_shell", "file_write", "network_connection", 
            "privilege_escalation", "suspicious_process", "container_escape"
        ])
        
        return getattr(self, f"generate_{event_type}_event")()
    
    def generate_terminal_shell_event(self) -> Dict:
        """Generate terminal shell in container event"""
        container_name = random.choice(self.container_names)
        image = random.choice(self.images)
        user = random.choice(["root", "www-data", "nobody", "app"])
        
        return {
            "rule": "Terminal shell in container",
            "priority": "warning",
            "output": f"A shell was used as the entrypoint/exec point into a container with an attached terminal (user={user} user_loginuid=-1 k8s_ns=default k8s_pod={container_name})",
            "time": datetime.now().isoformat(),
            "output_fields": {
                "container.id": f"{''.join(random.choices('0123456789abcdef', k=12))}",
                "container.name": container_name,
                "container.image.repository": image.split(':')[0],
                "container.image.tag": image.split(':')[1] if ':' in image else "latest",
                "proc.cmdline": "/bin/bash",
                "proc.name": "bash",
                "proc.pname": "docker-runc",
                "proc.tty": "34816",
                "user.name": user,
                "user.loginuid": "-1",
                "k8s.ns.name": "default",
                "k8s.pod.name": container_name
            }
        }
    
    def generate_file_write_event(self) -> Dict:
        """Generate file write in sensitive directory event"""
        container_name = random.choice(self.container_names)
        image = random.choice(self.images)
        sensitive_dirs = ["/etc", "/root", "/usr/bin", "/sbin", "/boot"]
        sensitive_dir = random.choice(sensitive_dirs)
        filename = random.choice(["config", "passwd", "shadow", "hosts", "crontab"])
        
        return {
            "rule": "Write below binary dir",
            "priority": "error",
            "output": f"File below a binary directory opened for writing (user=root user_loginuid=-1 command=touch {sensitive_dir}/{filename} file={sensitive_dir}/{filename} parent=sh pcmdline=sh -c touch {sensitive_dir}/{filename} gparent=<NA> container_id={container_name})",
            "time": datetime.now().isoformat(),
            "output_fields": {
                "container.id": f"{''.join(random.choices('0123456789abcdef', k=12))}",
                "container.name": container_name,
                "container.image.repository": image.split(':')[0],
                "fd.name": f"{sensitive_dir}/{filename}",
                "proc.cmdline": f"touch {sensitive_dir}/{filename}",
                "proc.name": "touch",
                "proc.pname": "sh",
                "user.name": "root",
                "user.loginuid": "-1"
            }
        }
    
    def generate_network_connection_event(self) -> Dict:
        """Generate suspicious network connection event"""
        container_name = random.choice(self.container_names)
        image = random.choice(self.images)
        suspicious_ips = ["192.168.1.100", "10.0.0.50", "172.16.0.10"]
        ports = [22, 23, 80, 443, 8080, 9090]
        
        return {
            "rule": "Outbound connection to C2 server",
            "priority": "critical",
            "output": f"Outbound connection to a known C2 server (user=root user_loginuid=-1 command=curl http://{random.choice(suspicious_ips)}:{random.choice(ports)} connection={random.choice(suspicious_ips)}:{random.choice(ports)} container_id={container_name})",
            "time": datetime.now().isoformat(),
            "output_fields": {
                "container.id": f"{''.join(random.choices('0123456789abcdef', k=12))}",
                "container.name": container_name,
                "container.image.repository": image.split(':')[0],
                "fd.cip": random.choice(suspicious_ips),
                "fd.cport": random.choice(ports),
                "fd.sip": "172.17.0.2",
                "fd.sport": random.randint(32768, 65535),
                "proc.cmdline": f"curl http://{random.choice(suspicious_ips)}:{random.choice(ports)}",
                "proc.name": "curl",
                "user.name": "root"
            }
        }
    
    def generate_privilege_escalation_event(self) -> Dict:
        """Generate privilege escalation event"""
        container_name = random.choice(self.container_names)
        image = random.choice(self.images)
        
        return {
            "rule": "Privilege escalation attempt",
            "priority": "critical",
            "output": f"Privilege escalation attempt detected (user=www-data user_loginuid=1000 command=sudo su - proc.name=sudo proc.pname=bash container_id={container_name})",
            "time": datetime.now().isoformat(),
            "output_fields": {
                "container.id": f"{''.join(random.choices('0123456789abcdef', k=12))}",
                "container.name": container_name,
                "container.image.repository": image.split(':')[0],
                "proc.cmdline": "sudo su -",
                "proc.name": "sudo",
                "proc.pname": "bash",
                "user.name": "www-data",
                "user.loginuid": "1000"
            }
        }
    
    def generate_suspicious_process_event(self) -> Dict:
        """Generate suspicious process event"""
        container_name = random.choice(self.container_names)
        image = random.choice(self.images)
        suspicious_procs = ["nc", "ncat", "socat", "python", "perl", "ruby"]
        proc = random.choice(suspicious_procs)
        
        return {
            "rule": "Suspicious process activity",
            "priority": "warning",
            "output": f"Suspicious process detected (user=root user_loginuid=-1 command={proc} -e /bin/bash -l -p 4444 proc.name={proc} container_id={container_name})",
            "time": datetime.now().isoformat(),
            "output_fields": {
                "container.id": f"{''.join(random.choices('0123456789abcdef', k=12))}",
                "container.name": container_name,
                "container.image.repository": image.split(':')[0],
                "proc.cmdline": f"{proc} -e /bin/bash -l -p 4444",
                "proc.name": proc,
                "proc.pname": "bash",
                "user.name": "root",
                "user.loginuid": "-1"
            }
        }
    
    def generate_container_escape_event(self) -> Dict:
        """Generate container escape attempt event"""
        container_name = random.choice(self.container_names)
        image = random.choice(self.images)
        
        return {
            "rule": "Container escape attempt",
            "priority": "critical",
            "output": f"Container escape attempt detected (user=root user_loginuid=-1 command=docker exec -it {container_name} /bin/bash proc.name=docker container_id={container_name})",
            "time": datetime.now().isoformat(),
            "output_fields": {
                "container.id": f"{''.join(random.choices('0123456789abcdef', k=12))}",
                "container.name": container_name,
                "container.image.repository": image.split(':')[0],
                "proc.cmdline": f"docker exec -it {container_name} /bin/bash",
                "proc.name": "docker",
                "proc.pname": "systemd",
                "user.name": "root",
                "user.loginuid": "-1"
            }
        }
    
    def send_event(self, event: Dict) -> bool:
        """Send event to webhook"""
        try:
            response = requests.post(
                self.webhook_url,
                json=event,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"✅ Event sent: {event['rule']} - {event['priority']}")
                return True
            else:
                print(f"❌ Failed to send event: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending event: {e}")
            return False
    
    def run(self, interval: int = 30):
        """Run event generator continuously"""
        print(f"🚀 Starting Security Event Generator...")
        print(f"📡 Webhook URL: {self.webhook_url}")
        print(f"⏰ Generation interval: {interval} seconds")
        
        event_count = 0
        
        while True:
            try:
                # Generate and send event
                event = self.generate_event()
                if self.send_event(event):
                    event_count += 1
                    print(f"📊 Total events sent: {event_count}")
                
                # Wait for next interval
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print(f"\n🛑 Stopping event generator. Total events sent: {event_count}")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                time.sleep(5)  # Wait before retry

def main():
    """Main function"""
    webhook_url = os.getenv("WEBHOOK_URL", "http://falco-ai-alerts:8080/falco-webhook")
    interval = int(os.getenv("GENERATION_INTERVAL", "30"))
    
    generator = SecurityEventGenerator(webhook_url)
    generator.run(interval)

if __name__ == "__main__":
    main() 