import re
import logging

def parse_explanation_text_regex_openai(explanation_text):
    """
    Parses the LLM explanation text from OpenAI, handling variations in formatting,
    including more robust header detection and code block handling.
    """
    explanation_sections = {
        "Security Impact": {"content": "", "code_blocks": []},
        "Next Steps": {"content": "", "code_blocks": []},
        "Remediation Steps": {"content": "", "code_blocks": []},
        "Suggested Commands": {"content": "", "code_blocks": []}
    }

    # --- Improved Header Detection ---
    header_patterns = {
        "Security Impact": re.compile(r"\**[ ]*Security Impact[ ]*\**[:\s]*", re.IGNORECASE),
        "Next Steps": re.compile(r"\**[ ]*Next Steps[ ]*\**[:\s]*", re.IGNORECASE),
        "Remediation Steps": re.compile(r"\**[ ]*Remediation Steps[ ]*\**[:\s]*", re.IGNORECASE),
    }

    # Extract suggested commands
    command_matches = re.findall(r"Command:\s*(.+)", explanation_text, re.IGNORECASE)
    if command_matches:
        explanation_sections["Suggested Commands"]["content"] = "\n".join(command_matches)
        explanation_sections["Suggested Commands"]["code_blocks"] = command_matches

    start_index = 0
    section_order = ["Security Impact", "Next Steps", "Remediation Steps"]

    for section_name in section_order:
        header_regex = header_patterns[section_name]
        header_match = header_regex.search(explanation_text, pos=start_index)

        if header_match:
            logging.debug(f"Found header: {section_name}")
            section_start = header_match.end()
            next_header_start = len(explanation_text)

            next_section_index = section_order.index(section_name) + 1
            if next_section_index < len(section_order):
                next_section_name = section_order[next_section_index]
                next_header_regex = header_patterns[next_section_name]
                next_header_match = next_header_regex.search(explanation_text, pos=section_start)
                if next_header_match:
                    next_header_start = next_header_match.start()

            section_content = explanation_text[section_start:next_header_start].strip()

            # Extract code blocks within sections
            code_blocks_in_section = re.findall(r"```(.*?)```", section_content, re.DOTALL)
            explanation_sections[section_name]["code_blocks"].extend([block.strip() for block in code_blocks_in_section])

            # Remove code blocks and command lines from section content for cleaner processing
            section_content_no_code = re.sub(r"```.*?```", '', section_content, flags=re.DOTALL)
            section_content_no_code = re.sub(r"Command:\s*.+", '', section_content_no_code, flags=re.IGNORECASE)
            explanation_sections[section_name]["content"] = section_content_no_code.strip()

            start_index = next_header_start

    return explanation_sections