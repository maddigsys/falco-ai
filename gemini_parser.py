import re
import logging
import json

def parse_explanation_text_regex_gemini(explanation_text):
    """
    Parses the LLM explanation text from Gemini, handling various formatting issues.
    """
    explanation_sections = {
        "Security Impact": {"content": "", "code_blocks": []},
        "Next Steps": {"content": "", "code_blocks": []},
        "Remediation Steps": {"content": "", "code_blocks": []},
        "Suggested Commands": {"content": "", "code_blocks": []}
    }

    # Extract suggested commands first
    command_matches = re.findall(r"Command:\s*(.+)", explanation_text, re.IGNORECASE)
    if command_matches:
        cleaned_commands = []
        for cmd in command_matches:
            # Remove all markdown formatting
            cleaned_cmd = re.sub(r'\*\*(.*?)\*\*', r'\1', cmd)  # **bold**
            cleaned_cmd = re.sub(r'\*(.*?)\*', r'\1', cleaned_cmd)  # *italic*
            cleaned_cmd = re.sub(r'`(.*?)`', r'\1', cleaned_cmd)  # `code`
            cleaned_cmd = re.sub(r'^\*+', '', cleaned_cmd)  # leading *
            cleaned_cmd = re.sub(r'\*+$', '', cleaned_cmd)  # trailing *
            cleaned_cmd = cleaned_cmd.strip()
            if cleaned_cmd:
                cleaned_commands.append(cleaned_cmd)
        
        if cleaned_commands:
            explanation_sections["Suggested Commands"]["content"] = "\n".join(cleaned_commands)
            explanation_sections["Suggested Commands"]["code_blocks"] = cleaned_commands
            logging.info(f"Extracted {len(cleaned_commands)} commands: {cleaned_commands}")

    # Simple pattern matching for sections
    sections = {
        "Security Impact": [
            r'\*\*Security Impact:\*\*\s*(.*?)(?=\*\*Next Steps|\*\*Remediation|Command:|$)',
            r'Security Impact:\s*(.*?)(?=Next Steps|Remediation|Command:|$)'
        ],
        "Next Steps": [
            r'\*\*Next Steps:\*\*\s*(.*?)(?=\*\*Remediation|\*\*Security|Command:|$)',
            r'Next Steps:\s*(.*?)(?=Remediation|Security|Command:|$)'
        ],
        "Remediation Steps": [
            r'\*\*Remediation Steps:\*\*\s*(.*?)(?=\*\*Next|\*\*Security|Command:|$)',
            r'Remediation Steps:\s*(.*?)(?=Next|Security|Command:|$)'
        ]
    }

    for section_name, patterns in sections.items():
        for pattern in patterns:
            match = re.search(pattern, explanation_text, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                
                # Clean up content
                content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Remove **bold**
                content = re.sub(r'\*(.*?)\*', r'\1', content)  # Remove *italic*
                content = re.sub(r'Command:.*', '', content, flags=re.IGNORECASE)  # Remove command lines
                content = re.sub(r'^\*+', '', content, flags=re.MULTILINE)  # Remove leading *
                content = re.sub(r'\*+$', '', content, flags=re.MULTILINE)  # Remove trailing *
                content = content.strip()
                
                if content:
                    explanation_sections[section_name]["content"] = content
                    logging.info(f"Extracted {section_name}: {content[:50]}...")
                    break

    return explanation_sections


if __name__ == '__main__':
    # Test with problematic output
    test_output = """**Security Impact:** ** An interactive shell can be a foothold for an attacker to explore the environment, steal credentials, or pivot to other services. This often indicates a container has been compromised or is being used for unauthorized manual access.**

**Next Steps:** ** Correlate this event with authorized user activity by checking Kubernetes audit logs for the `exec` command. If the activity is suspicious, isolate the pod and analyze running processes and network connections.**

**Remediation Steps:** ** Harden container images by removing shells and other unnecessary binaries (using distroless images). Enforce least-privilege by using RBAC to restrict which users or service accounts can `exec` into pods.**

Command: **`kubectl describe pod <pod_name> -n <namespace>`**"""
    
    print("Testing Gemini parser...")
    result = parse_explanation_text_regex_gemini(test_output)
    print(json.dumps(result, indent=2))