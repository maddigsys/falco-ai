#!/bin/bash

# Generate Test Security Events for Falco
# This script creates activities that will trigger Falco security rules

echo "🚨 Generating test security events for Falco..."

# 1. Create a shell event in a container
echo "📋 Event 1: Shell spawned in container"
docker run --rm -it alpine:latest /bin/sh -c "echo 'Test shell activity'; whoami; ls -la" &

# 2. Create file write events in sensitive directories
echo "📋 Event 2: File operations in sensitive directories"
docker run --rm -v /tmp:/host/tmp alpine:latest /bin/sh -c "
  echo 'test content' > /tmp/test-file.txt
  touch /etc/test-config
  echo 'Creating files in sensitive locations'
" &

# 3. Create network activity
echo "📋 Event 3: Network activity"
docker run --rm alpine:latest /bin/sh -c "
  wget -q -O - http://www.google.com || true
  nc -l -p 8888 &
  sleep 2
  kill %1 || true
" &

# 4. Create privilege escalation attempt
echo "📋 Event 4: Privilege escalation attempt"
docker run --rm alpine:latest /bin/sh -c "
  su - root -c 'echo privilege escalation test' || true
  sudo echo 'sudo test' || true
" &

# 5. Create suspicious process activity
echo "📋 Event 5: Suspicious process activity"
docker run --rm alpine:latest /bin/sh -c "
  python3 -c 'import subprocess; subprocess.run([\"echo\", \"python exec test\"])' || true
  /bin/bash -c 'echo bash execution test'
" &

# 6. Create file modification in container
echo "📋 Event 6: File modifications"
docker run --rm alpine:latest /bin/sh -c "
  echo 'modified content' > /bin/test-binary || true
  chmod +x /usr/bin/test-script || true
  echo 'File modification tests'
" &

# Wait for all background processes to complete
wait

echo "✅ Test events generated! Check your Falco AI Gateway at http://localhost:8080/runtime-events"
echo "📊 Events should appear in the Runtime Events page within 30 seconds"
echo ""
echo "🔍 You can also check the logs with:"
echo "   docker compose logs -f falco"
echo "   docker compose logs -f falco-ai-alerts" 