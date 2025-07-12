import re
import logging

def parse_explanation_text_regex_ollama(explanation_text):
    """
    Parses the LLM explanation text from Ollama, handling variations in formatting.
    Ollama responses tend to be more conversational and may not follow strict markdown formatting.
    """
    explanation_sections = {
        "Security Impact": {"content": "", "code_blocks": []},
        "Next Steps": {"content": "", "code_blocks": []},
        "Remediation Steps": {"content": "", "code_blocks": []},
        "Suggested Commands": {"content": "", "code_blocks": []}
    }

    # Extract suggested commands first (Ollama often includes these)
    command_matches = re.findall(r"Command:\s*(.+)", explanation_text, re.IGNORECASE)
    if command_matches:
        cleaned_commands = []
        for cmd in command_matches:
            # Clean up command formatting
            cleaned_cmd = re.sub(r'\*\*(.*?)\*\*', r'\1', cmd)  # Remove **bold**
            cleaned_cmd = re.sub(r'\*(.*?)\*', r'\1', cleaned_cmd)  # Remove *italic*
            cleaned_cmd = re.sub(r'`(.*?)`', r'\1', cleaned_cmd)  # Remove `code`
            cleaned_cmd = re.sub(r'^\*+', '', cleaned_cmd)  # Remove leading *
            cleaned_cmd = re.sub(r'\*+$', '', cleaned_cmd)  # Remove trailing *
            cleaned_cmd = cleaned_cmd.strip()
            if cleaned_cmd:
                cleaned_commands.append(cleaned_cmd)
        
        if cleaned_commands:
            explanation_sections["Suggested Commands"]["content"] = "\n".join(cleaned_commands)
            explanation_sections["Suggested Commands"]["code_blocks"] = cleaned_commands
            logging.info(f"Extracted {len(cleaned_commands)} commands from Ollama response")

    # More flexible section detection for Ollama responses
    sections = {
        "Security Impact": [
            r'\*\*Security Impact:\*\*\s*(.*?)(?=\*\*Next Steps|\*\*Remediation|Command:|$)',
            r'Security Impact:\s*(.*?)(?=Next Steps|Remediation|Command:|$)',
            r'Security Impact[:\s]*(.*?)(?=Next Steps|Remediation|Command:|$)',
            r'This alert indicates[:\s]*(.*?)(?=Next Steps|Remediation|Command:|$)',
            r'The security risk[:\s]*(.*?)(?=Next Steps|Remediation|Command:|$)'
        ],
        "Next Steps": [
            r'\*\*Next Steps:\*\*\s*(.*?)(?=\*\*Remediation|\*\*Security|Command:|$)',
            r'Next Steps:\s*(.*?)(?=Remediation|Security|Command:|$)',
            r'Next Steps[:\s]*(.*?)(?=Remediation|Security|Command:|$)',
            r'You should[:\s]*(.*?)(?=Remediation|Security|Command:|$)',
            r'Immediate actions[:\s]*(.*?)(?=Remediation|Security|Command:|$)'
        ],
        "Remediation Steps": [
            r'\*\*Remediation Steps:\*\*\s*(.*?)(?=\*\*Next|\*\*Security|Command:|$)',
            r'Remediation Steps:\s*(.*?)(?=Next|Security|Command:|$)',
            r'Remediation Steps[:\s]*(.*?)(?=Next|Security|Command:|$)',
            r'To fix this[:\s]*(.*?)(?=Next|Security|Command:|$)',
            r'Remediation[:\s]*(.*?)(?=Next|Security|Command:|$)'
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
                    logging.info(f"Extracted {section_name} from Ollama response: {content[:50]}...")
                    break

    # If no structured sections found, try to extract content from the overall response
    if not any(section["content"] for section in explanation_sections.values() if section["content"]):
        # Try to extract meaningful content from the response
        lines = explanation_text.split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line indicates a new section
            if re.search(r'Security Impact|Next Steps|Remediation|Command:', line, re.IGNORECASE):
                # Save previous section content
                if current_section and section_content:
                    explanation_sections[current_section]["content"] = '\n'.join(section_content).strip()
                
                # Start new section
                if 'Security Impact' in line or 'security' in line.lower():
                    current_section = "Security Impact"
                elif 'Next Steps' in line or 'next' in line.lower():
                    current_section = "Next Steps"
                elif 'Remediation' in line or 'fix' in line.lower():
                    current_section = "Remediation Steps"
                elif 'Command:' in line:
                    current_section = "Suggested Commands"
                
                section_content = []
            elif current_section:
                section_content.append(line)
        
        # Save the last section
        if current_section and section_content:
            explanation_sections[current_section]["content"] = '\n'.join(section_content).strip()
        
        # If still no content, try to extract meaningful information from the entire response
        if not any(section["content"] for section in explanation_sections.values() if section["content"]):
            # Try to identify security-related content in the response
            response_lower = explanation_text.lower()
            
            # Look for security impact indicators
            security_keywords = ['security risk', 'vulnerability', 'threat', 'attack', 'exploit', 'compromise', 'breach']
            if any(keyword in response_lower for keyword in security_keywords):
                # Extract sentences containing security keywords
                sentences = re.split(r'[.!?]+', explanation_text)
                security_sentences = []
                for sentence in sentences:
                    if any(keyword in sentence.lower() for keyword in security_keywords):
                        security_sentences.append(sentence.strip())
                
                if security_sentences:
                    explanation_sections["Security Impact"]["content"] = '. '.join(security_sentences[:2]) + '.'
            
            # Look for action indicators
            action_keywords = ['should', 'must', 'need to', 'recommend', 'investigate', 'check', 'verify']
            if any(keyword in response_lower for keyword in action_keywords):
                sentences = re.split(r'[.!?]+', explanation_text)
                action_sentences = []
                for sentence in sentences:
                    if any(keyword in sentence.lower() for keyword in action_keywords):
                        action_sentences.append(sentence.strip())
                
                if action_sentences:
                    explanation_sections["Next Steps"]["content"] = '. '.join(action_sentences[:2]) + '.'
            
            # Look for fix/remediation indicators
            fix_keywords = ['fix', 'remediate', 'mitigate', 'prevent', 'stop', 'block', 'remove']
            if any(keyword in response_lower for keyword in fix_keywords):
                sentences = re.split(r'[.!?]+', explanation_text)
                fix_sentences = []
                for sentence in sentences:
                    if any(keyword in sentence.lower() for keyword in fix_keywords):
                        fix_sentences.append(sentence.strip())
                
                if fix_sentences:
                    explanation_sections["Remediation Steps"]["content"] = '. '.join(fix_sentences[:2]) + '.'
            
            # If we still have no content, use the first few sentences as general analysis
            if not any(section["content"] for section in explanation_sections.values() if section["content"]):
                sentences = re.split(r'[.!?]+', explanation_text)
                meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
                
                if meaningful_sentences:
                    # Use first sentence for security impact
                    explanation_sections["Security Impact"]["content"] = meaningful_sentences[0] + '.'
                    
                    # Use second sentence for next steps if available
                    if len(meaningful_sentences) > 1:
                        explanation_sections["Next Steps"]["content"] = meaningful_sentences[1] + '.'
                    
                    # Use third sentence for remediation if available
                    if len(meaningful_sentences) > 2:
                        explanation_sections["Remediation Steps"]["content"] = meaningful_sentences[2] + '.'

    return explanation_sections 