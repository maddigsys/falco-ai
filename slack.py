import json
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

LLM_PROVIDER_OPENAI = "OpenAI via Portkey"
LLM_PROVIDER_GEMINI = "Gemini via Portkey"


def format_slack_message_basic(alert_payload, error_message=""):
    """
    Formats a basic Slack message with key Falco alert details.
    Used when explanation generation fails.
    """
    rule = alert_payload.get('rule', 'N/A')
    priority = alert_payload.get('priority', 'N/A')
    output = alert_payload.get('output', 'N/A')
    time = alert_payload.get('time', 'N/A')

    message = (
        f":warning: *Falco Alert (Basic Notification - Explanation Failed)* :warning:\n"
        f"*Rule:* {rule}\n"
        f"*Priority:* {priority}\n"
        f"*Details:* {output}\n"
        f"*Time:* {time}\n"
    )
    if error_message:
        message += f"\n*Explanation Error:* {error_message}"
    return message


def send_slack_message(message_content, slack_client, slack_channel_name):
    """
    Sends a Slack message to the specified channel.
    """
    try:
        response = slack_client.chat_postMessage(
            channel=slack_channel_name,
            text=message_content
        )
        logging.info(f"Basic Slack message sent successfully to channel '{slack_channel_name}'")
        return response
    except SlackApiError as e:
        logging.error(f"Error sending basic Slack message: {e.response['error']}")
        return None


def post_to_slack(falco_alert, explanation_sections, slack_client, slack_channel_name):
    """
    Posts a formatted Falco alert message to Slack, including LLM explanations.
    """
    try:
        template_file = "templates/falco_alert_template.json"
        with open(template_file, 'r') as f:
            template = json.load(f)
    except FileNotFoundError:
        logging.error(f"Template file '{template_file}' not found.")
        return None

    # --- Extract relevant information ---
    rule = falco_alert.get('rule', 'N/A')
    priority = falco_alert.get('priority', 'N/A')
    output = falco_alert.get('output', 'N/A')
    time = falco_alert.get('time', 'N/A')
    llm_provider = explanation_sections.get('llm_provider', 'N/A') if explanation_sections else 'N/A'
    falco_command = falco_alert.get('output_fields', {}).get('proc.cmdline', 'N/A')
    urgency_emoji = ":white_circle:"  # Default

    if priority.lower() == "critical" or priority.lower() == "emergency":
        urgency_emoji = ":fire:"
    elif priority.lower() == "error" or priority.lower() == "alert":
        urgency_emoji = ":red_circle:"
    elif priority.lower() == "warning":
        urgency_emoji = ":warning:"
    elif priority.lower() == "notice":
        urgency_emoji = ":information_source:"

    template_vars = {
        'rule': rule,
        'priority': priority.capitalize(),
        'urgency_emoji': urgency_emoji,
        'output': output,
        'time': time,
        'llm_provider': llm_provider,
        'falco_command': falco_command,
        'explanation_sections': {
            'Security_Impact': {'content': explanation_sections.get('Security Impact', {}).get('content', 'N/A') if explanation_sections else 'N/A'},
            'Next_Steps': {'content': explanation_sections.get('Next Steps', {}).get('content', 'N/A') if explanation_sections else 'N/A'},
            'Remediation_Steps': {'content': explanation_sections.get('Remediation Steps', {}).get('content', 'N/A') if explanation_sections else 'N/A'},
            'Suggested_Commands': {'content': explanation_sections.get('Suggested Commands', {}).get('content', '') if explanation_sections else ''},
        }
    }

    message_blocks = []
    for block in template['blocks']:
        updated_block = replace_template_variables(block, template_vars)
        message_blocks.append(updated_block)

    # Add suggested commands section if commands are available
    suggested_commands = template_vars['explanation_sections']['Suggested_Commands']['content']
    if suggested_commands and suggested_commands.strip():
        commands_block = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*💻 Suggested Commands:*\n```{suggested_commands}```"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "📋 Copy Commands"
                },
                "action_id": "copy_commands"
            }
        }
        message_blocks.append(commands_block)

    logging.info(f"Sending Slack message with {len(message_blocks)} blocks")

    try:
        response = slack_client.chat_postMessage(
            channel=slack_channel_name,
            blocks=message_blocks,
            text=f"Falco Alert: {rule} - Priority: {priority}"
        )
        logging.info(f"Slack message sent successfully to channel '{slack_channel_name}'")
        return response
    except SlackApiError as e:
        logging.error(f"Error sending Slack message: {e.response['error']}")
        return None


def replace_template_variables(block, template_vars):
    """
    Recursively replaces template variables in a Slack message block with validation.
    """
    if isinstance(block, dict):
        updated_block = {}
        for key, value in block.items():
            updated_block[key] = replace_template_variables(value, template_vars)
        return updated_block
    elif isinstance(block, list):
        updated_block = [replace_template_variables(item, template_vars) for item in block]
        return updated_block
    elif isinstance(block, str):
        updated_block = block
        for var, value in template_vars.items():
            placeholder = "{{" + var + "}}"
            if placeholder in block:
                updated_block = updated_block.replace(placeholder, str(value))

        # Handle nested explanation_sections with underscores
        if 'explanation_sections' in template_vars and isinstance(template_vars['explanation_sections'], dict):
            for section_key, section_data in template_vars['explanation_sections'].items():
                if isinstance(section_data, dict) and 'content' in section_data:
                    nested_placeholder = "{{explanation_sections." + section_key + ".content}}"
                    nested_value = section_data['content']
                    if nested_placeholder in block:
                        updated_block = updated_block.replace(nested_placeholder, str(nested_value))

        return updated_block
    else:
        return block