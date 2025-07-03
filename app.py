import os
from flask import Flask, request, jsonify, render_template
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import logging
import datetime
import portkey_config
from slack import post_to_slack, format_slack_message_basic, send_slack_message
import json
import openai_parser
import gemini_parser
import requests
from dotenv import load_dotenv
import sqlite3
import threading

# Load environment variables from .env file
load_dotenv()

# --- Configure Logging ---
log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, static_folder='static', template_folder='templates')

# --- Web UI Configuration ---
WEB_UI_ENABLED = os.environ.get("WEB_UI_ENABLED", "true").lower() == "true"
WEB_UI_PORT = int(os.environ.get("WEB_UI_PORT", 8081))
DB_PATH = os.getenv('DB_PATH', '/app/data/alerts.db')

# --- Initialize Portkey clients ---
portkey_client_openai, portkey_client_gemini = portkey_config.initialize_portkey_clients()

# Initialize Slack client
slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
slack_channel_name = os.environ.get("SLACK_CHANNEL_NAME", "#general")
falco_ai_port = int(os.environ.get("FALCO_AI_PORT", 8080))

if not slack_bot_token or slack_bot_token == "xoxb-your-token-here":
    logging.warning("SLACK_BOT_TOKEN not properly configured. Slack notifications disabled.")
    slack_client = None
else:
    slack_client = WebClient(token=slack_bot_token)

# --- Configure Minimum Priority Level ---
VALID_PRIORITIES = ["debug", "informational", "notice", "warning", "error", "critical", "alert", "emergency"]
MIN_PRIORITY_ENV = os.environ.get("MIN_PRIORITY", "warning").lower()
if MIN_PRIORITY_ENV not in VALID_PRIORITIES:
    logging.warning(f"Invalid MIN_PRIORITY '{MIN_PRIORITY_ENV}'. Using 'warning'.")
    MIN_FALCO_PRIORITY = "warning"
else:
    MIN_FALCO_PRIORITY = MIN_PRIORITY_ENV

# --- Configure Alert Age ---
IGNORE_OLDER_MINUTES = int(os.environ.get("IGNORE_OLDER", "1"))

# LLM Provider constants
LLM_PROVIDER_OPENAI = "OpenAI via Portkey"
LLM_PROVIDER_GEMINI = "Gemini via Portkey"
LLM_PROVIDER_OLLAMA = "Ollama"

# Alert deduplication
alert_counts = {}

# --- Web UI Database Functions ---
def init_database():
    """Initialize SQLite database to store alerts."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            rule TEXT NOT NULL,
            priority TEXT NOT NULL,
            output TEXT NOT NULL,
            source TEXT,
            fields TEXT,
            ai_analysis TEXT,
            processed BOOLEAN DEFAULT FALSE,
            status TEXT DEFAULT 'unread'
        )
    ''')
    
    # Add status column to existing tables if it doesn't exist
    try:
        cursor.execute('ALTER TABLE alerts ADD COLUMN status TEXT DEFAULT "unread"')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            message_type TEXT NOT NULL,
            content TEXT NOT NULL,
            context TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS slack_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_name TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            setting_type TEXT DEFAULT 'string',
            description TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Initialize default Slack settings
    cursor.execute('''
        INSERT OR IGNORE INTO slack_config (setting_name, setting_value, setting_type, description)
        VALUES 
        ('bot_token', '', 'password', 'Slack Bot Token (xoxb-...)'),
        ('channel_name', '#security-alerts', 'string', 'Slack Channel Name'),
        ('enabled', 'true', 'boolean', 'Enable Slack Notifications'),
        ('username', 'Falco AI Alerts', 'string', 'Bot Display Name'),
        ('icon_emoji', ':shield:', 'string', 'Bot Icon Emoji'),
        ('template_style', 'detailed', 'select', 'Message Template Style'),
        ('min_priority_slack', 'warning', 'select', 'Minimum Priority for Slack'),
        ('include_commands', 'true', 'boolean', 'Include Suggested Commands'),
        ('thread_alerts', 'false', 'boolean', 'Use Threading for Related Alerts')
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_name TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            setting_type TEXT DEFAULT 'string',
            description TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Initialize default AI settings
    cursor.execute('''
        INSERT OR IGNORE INTO ai_config (setting_name, setting_value, setting_type, description)
        VALUES 
        ('provider_name', 'ollama', 'select', 'AI Provider (openai, gemini, ollama)'),
        ('model_name', 'tinyllama', 'string', 'Model Name'),
        ('openai_model_name', 'gpt-3.5-turbo', 'string', 'OpenAI Model Name'),
        ('gemini_model_name', 'gemini-pro', 'string', 'Gemini Model Name'),
        ('portkey_api_key', '', 'password', 'Portkey API Key (Security Layer for Cloud AI)'),
        ('openai_virtual_key', '', 'password', 'OpenAI Virtual Key (Portkey)'),
        ('gemini_virtual_key', '', 'password', 'Gemini Virtual Key (Portkey)'),
        ('ollama_api_url', 'http://prod-ollama:11434/api/generate', 'string', 'Ollama API URL'),
        ('ollama_model_name', 'tinyllama', 'string', 'Ollama Model Name'),
        ('ollama_timeout', '30', 'number', 'Ollama Request Timeout (seconds)'),
        ('ollama_keep_alive', '10', 'number', 'Ollama Keep Alive (minutes)'),
        ('ollama_parallel', '1', 'number', 'Ollama Parallel Requests'),
        ('max_tokens', '500', 'number', 'Maximum Response Tokens'),
        ('temperature', '0.7', 'number', 'Response Temperature (0.0-1.0)'),
        ('enabled', 'true', 'boolean', 'Enable AI Analysis'),
        ('system_prompt', '', 'textarea', 'AI System Prompt (leave empty for default)')
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS general_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_name TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            setting_type TEXT DEFAULT 'string',
            description TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Initialize default General settings
    cursor.execute('''
        INSERT OR IGNORE INTO general_config (setting_name, setting_value, setting_type, description)
        VALUES 
        ('min_priority', 'warning', 'select', 'Minimum Alert Priority to Process'),
        ('ignore_older_minutes', '1', 'number', 'Ignore Alerts Older Than (minutes)'),
        ('web_ui_enabled', 'true', 'boolean', 'Enable Web UI Dashboard'),
        ('web_ui_port', '8081', 'number', 'Web UI Port Number'),
        ('falco_ai_port', '8080', 'number', 'Main Webhook Port Number'),
        ('log_level', 'INFO', 'select', 'System Log Level'),
        ('deduplication_enabled', 'true', 'boolean', 'Enable Alert Deduplication'),
        ('deduplication_window_minutes', '60', 'number', 'Deduplication Window (minutes)'),
        ('max_alerts_storage', '10000', 'number', 'Maximum Alerts to Store in Database'),
        ('alert_retention_days', '30', 'number', 'Delete Alerts Older Than (days)')
    ''')
    
    conn.commit()
    conn.close()
    logging.info("Database initialized")

def store_alert(alert_data, ai_analysis=None):
    """Store alert in database for analysis."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO alerts (rule, priority, output, source, fields, ai_analysis)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        alert_data.get('rule', ''),
        alert_data.get('priority', ''),
        alert_data.get('output', ''),
        alert_data.get('output_fields', {}).get('container.name', 'unknown'),
        json.dumps(alert_data.get('output_fields', {})),
        json.dumps(ai_analysis) if ai_analysis else None
    ))
    
    conn.commit()
    conn.close()
    logging.info(f"Stored alert: {alert_data.get('rule', 'Unknown')}")

def get_alerts(filters=None):
    """Retrieve alerts from database with optional filters."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = 'SELECT * FROM alerts'
    params = []
    
    if filters:
        conditions = []
        
        if filters.get('time_range') and filters['time_range'] != 'all':
            time_map = {
                '1h': 1,
                '24h': 24,
                '7d': 24 * 7,
                '30d': 24 * 30
            }
            hours = time_map.get(filters['time_range'], 24)
            cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)
            conditions.append('timestamp > ?')
            params.append(cutoff.isoformat())
        
        if filters.get('priority') and filters['priority'] != 'all':
            conditions.append('priority = ?')
            params.append(filters['priority'])
        
        if filters.get('rule') and filters['rule'] != 'all':
            conditions.append('rule = ?')
            params.append(filters['rule'])
        
        if filters.get('status') and filters['status'] != 'all':
            conditions.append('status = ?')
            params.append(filters['status'])
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' ORDER BY timestamp DESC'
    
    # Add limit if specified
    limit = filters.get('limit') if filters else None
    if limit and limit.isdigit():
        query += f' LIMIT {limit}'
    
    cursor.execute(query, params)
    alerts = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    alert_list = []
    for alert in alerts:
        # Handle both old and new database schemas
        status = 'unread'  # default for old records
        if len(alert) > 9:  # new schema with status field
            status = alert[9] or 'unread'
        
        alert_dict = {
            'id': alert[0],
            'timestamp': alert[1],
            'rule': alert[2],
            'priority': alert[3],
            'output': alert[4],
            'source': alert[5] or 'unknown',
            'fields': json.loads(alert[6]) if alert[6] else {},
            'ai_analysis': json.loads(alert[7]) if alert[7] else None,
            'processed': bool(alert[8]),
            'status': status
        }
        alert_list.append(alert_dict)
    
    return alert_list

def load_system_prompt():
    """Load system prompt from database, with fallback to file, then default."""
    # First try to get from database
    try:
        ai_config = get_ai_config()
        db_prompt = ai_config.get('system_prompt', {}).get('value', '').strip()
        
        if db_prompt:
            logging.info("✅ Loaded system prompt from database configuration")
            return db_prompt
    except Exception as e:
        logging.warning(f"⚠️ Could not load system prompt from database: {e}")
    
    # Fallback to file
    try:
        with open("templates/system_prompt.txt", 'r') as f:
            system_prompt = f.read().strip()
            logging.info("✅ Loaded system prompt from templates/system_prompt.txt")
            return system_prompt
    except FileNotFoundError:
        logging.warning("⚠️ System prompt file not found, using default prompt")
    
    # Final fallback to hardcoded default
    default_prompt = """You are an expert in cloud security and Falco alerts. Analyze the provided Falco security alert and provide a comprehensive but concise security assessment.

Structure your response with the following sections:

**Security Impact:** Briefly describe the potential security risks and possible exploits related to this Falco alert (1-2 sentences).

**Next Steps:** Provide immediate investigation steps that security teams should take (1-2 sentences). Include relevant reference links within these recommendations whenever possible.

**Remediation Steps:** Explain how to fix or mitigate the issue (1-2 sentences). Focus on actionable steps that can be implemented immediately.

**Commands:** If there are safe, specific commands that can help investigate or remediate this issue, include them on separate lines starting with "Command:" - use placeholders like <container_id>, <pod_name>, <namespace> for values that need to be filled in. Only include commands that are safe and directly relevant to this security alert.

Guidelines:
- Keep responses concise and actionable
- Focus on Kubernetes and container security context
- Prioritize immediate security concerns
- Provide practical, implementable solutions
- Include relevant security best practices
- Consider the alert priority level in your response severity"""
    
    logging.info("✅ Using default system prompt")
    return default_prompt

def generate_explanation_portkey(alert_payload):
    """Generate explanation using configured AI provider from database."""
    # Get AI configuration from database
    ai_config = get_ai_config()
    
    # Check if AI is enabled
    if ai_config.get('enabled', {}).get('value') != 'true':
        return {"error": "AI analysis is disabled"}
    
    provider_name = ai_config.get('provider_name', {}).get('value', 'openai').lower()
    model_name = ai_config.get('model_name', {}).get('value')
    max_tokens = int(ai_config.get('max_tokens', {}).get('value', '500'))
    temperature = float(ai_config.get('temperature', {}).get('value', '0.7'))
    
    logging.info(f"🤖 Using AI provider: {provider_name} with model: {model_name}")

    # Load configurable system prompt
    system_prompt = load_system_prompt()

    user_prompt = f"""Falco Alert:
Rule: {alert_payload.get('rule', 'N/A')}
Priority: {alert_payload.get('priority', 'N/A')}
Details: {alert_payload.get('output', 'N/A')}
Command: {alert_payload.get('output_fields', {}).get('proc.cmdline', 'N/A')}"""

    try:
        explanation_text = ""
        
        if provider_name == "openai":
            # Get OpenAI configuration from database
            portkey_api_key = ai_config.get('portkey_api_key', {}).get('value', '')
            openai_virtual_key = ai_config.get('openai_virtual_key', {}).get('value', '')
            
            if not portkey_api_key or not openai_virtual_key:
                return {"error": "OpenAI configuration incomplete - missing API keys"}
            
            from portkey_ai import Portkey
            
            # Create Portkey client for this request
            client = Portkey(
                api_key=portkey_api_key,
                virtual_key=openai_virtual_key
            )
            
            logging.info("🤖 Calling OpenAI via Portkey...")
            response = client.chat.completions.create(
                model=model_name or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Handle both object and dict response formats
            logging.info(f"📦 Response type: {type(response)}")
            
            # Try object access first
            try:
                explanation_text = response.choices[0].message.content
                logging.info(f"✅ Extracted via object access: {explanation_text[:100]}...")
            except (AttributeError, TypeError):
                # Fallback to dictionary access
                logging.info("🔄 Trying dictionary access...")
                explanation_text = response['choices'][0]['message']['content']
                logging.info(f"✅ Extracted via dict access: {explanation_text[:100]}...")
            
            llm_provider_string = LLM_PROVIDER_OPENAI
            parser_function = openai_parser.parse_explanation_text_regex_openai

        elif provider_name == "gemini":
            # Get Gemini configuration from database
            portkey_api_key = ai_config.get('portkey_api_key', {}).get('value', '')
            gemini_virtual_key = ai_config.get('gemini_virtual_key', {}).get('value', '')
            
            if not portkey_api_key or not gemini_virtual_key:
                return {"error": "Gemini configuration incomplete - missing API keys"}
            
            from portkey_ai import Portkey
            
            # Create Portkey client for this request
            client = Portkey(
                api_key=portkey_api_key,
                virtual_key=gemini_virtual_key
            )
            
            logging.info("🤖 Calling Gemini via Portkey...")
            response = client.chat.completions.create(
                model=model_name or "gemini-pro",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Validate Gemini response
            logging.info(f"📦 Gemini response type: {type(response)}")
            
            # Extract content with validation
            try:
                explanation_text = response.choices[0].message.content
                logging.info("✅ Extracted via object access")
            except (AttributeError, TypeError):
                logging.info("🔄 Trying dictionary access...")
                try:
                    explanation_text = response['choices'][0]['message']['content']
                    logging.info("✅ Extracted via dict access")
                except (KeyError, TypeError) as e:
                    logging.error(f"❌ Failed to extract content from Gemini response: {e}")
                    logging.error(f"Response structure: {response}")
                    return {"error": f"Invalid Gemini response format: {e}"}
            
            # Validate content
            if not explanation_text or not isinstance(explanation_text, str):
                logging.error(f"❌ Invalid Gemini content: {type(explanation_text)} - {explanation_text}")
                return {"error": "Empty or invalid content from Gemini"}
            
            if len(explanation_text.strip()) < 50:
                logging.warning(f"⚠️ Suspiciously short Gemini response: {explanation_text}")
                return {"error": f"Gemini response too short: {explanation_text}"}
            
            # Check for expected sections in response
            expected_sections = ["Security Impact", "Next Steps", "Remediation"]
            found_sections = [section for section in expected_sections if section.lower() in explanation_text.lower()]
            
            if len(found_sections) < 2:
                logging.warning(f"⚠️ Gemini response missing expected sections. Found: {found_sections}")
                logging.warning(f"Response: {explanation_text[:200]}...")
            
            logging.info(f"✅ Gemini content validated: {len(explanation_text)} chars, sections: {found_sections}")
            logging.info(f"🔍 Gemini response preview: {explanation_text[:150]}...")
            
            llm_provider_string = LLM_PROVIDER_GEMINI
            parser_function = gemini_parser.parse_explanation_text_regex_gemini

        elif provider_name == "ollama":
            # Get Ollama configuration from database
            ollama_api_url = ai_config.get('ollama_api_url', {}).get('value', 'http://ollama:11434/api/generate')
            ollama_model_name = ai_config.get('ollama_model_name', {}).get('value', 'llama3')
            
            if not ollama_api_url:
                return {"error": "Ollama API URL not configured"}
            
            logging.info(f"🤖 Calling Ollama at {ollama_api_url} with model {ollama_model_name}...")

            ollama_payload = {
                "model": ollama_model_name,
                "prompt": system_prompt + "\n\n" + user_prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }

            # Get configurable timeout from database configuration
            ollama_timeout = int(ai_config.get('ollama_timeout', {}).get('value', '30'))
            response = requests.post(ollama_api_url, json=ollama_payload, timeout=ollama_timeout)
            response.raise_for_status()
            
            response_data = response.json()
            explanation_text = response_data.get('response', '')
            logging.info(f"✅ Ollama response: {explanation_text[:100]}...")
            
            llm_provider_string = LLM_PROVIDER_OLLAMA
            parser_function = openai_parser.parse_explanation_text_regex_openai

        else:
            return {"error": f"Unsupported provider: {provider_name}"}

        if not explanation_text:
            return {"error": f"Empty response from {provider_name}"}

        # Parse the explanation
        explanation_dict = parser_function(explanation_text)
        explanation_dict["llm_provider"] = llm_provider_string
        
        logging.info(f"🎯 Successfully generated explanation with {provider_name}")
        return explanation_dict

    except AttributeError as e:
        logging.error(f"❌ Attribute error accessing response: {e}")
        logging.error(f"Response object: {response}")
        return {"error": f"Response format error: {e}"}
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Network error with {provider_name}: {e}")
        return {"error": f"Network error: {e}"}
    except Exception as e:
        logging.error(f"❌ Unexpected error with {provider_name}: {e}")
        logging.error(f"Response object: {response if 'response' in locals() else 'No response'}")
        return {"error": f"LLM error: {e}"}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "falco-ai-alerts"}), 200

@app.route('/falco-webhook', methods=['POST'])
def falco_webhook():
    """Main webhook endpoint for Falco alerts."""
    
    # Validate request
    if request.headers.get('Content-Type') != 'application/json':
        logging.warning("🚫 REJECTED: Invalid Content-Type header - expected application/json")
        return jsonify({"error": "Content-Type must be application/json"}), 400
        
    alert_payload = request.json
    if not alert_payload:
        logging.warning("🚫 REJECTED: Empty or invalid JSON payload")
        return jsonify({"error": "Invalid JSON payload"}), 400

    # Extract alert metadata for logging
    rule_name = alert_payload.get('rule', 'Unknown')
    alert_priority = alert_payload.get('priority', 'unknown').lower()
    alert_time = alert_payload.get('time', 'Unknown')
    source_ip = request.remote_addr
    
    # Initial logging with alert metadata
    logging.info(f"📥 RECEIVED: Alert '{rule_name}' | Priority: {alert_priority} | Time: {alert_time} | Source: {source_ip}")

    # Get current configuration from database
    min_priority = get_general_setting('min_priority', 'warning')
    ignore_older_minutes = int(get_general_setting('ignore_older_minutes', '1'))
    deduplication_enabled = get_general_setting('deduplication_enabled', 'true') == 'true'
    
    # Priority filtering
    try:
        priority_rank_alert = VALID_PRIORITIES.index(alert_priority)
        priority_rank_min = VALID_PRIORITIES.index(min_priority)
        
        if priority_rank_alert < priority_rank_min:
            logging.info(f"🔽 FILTERED: Priority '{alert_priority}' below minimum '{min_priority}' | Rule: {rule_name} | IGNORED")
            return jsonify({"status": "ignored", "reason": "priority_too_low"}), 200
        else:
            logging.info(f"✅ PASSED: Priority check '{alert_priority}' >= '{min_priority}' | Rule: {rule_name}")
    except ValueError:
        logging.warning(f"⚠️ UNKNOWN: Priority '{alert_priority}' not recognized, processing anyway | Rule: {rule_name}")

    # Age filtering
    if ignore_older_minutes > 0:
        alert_time_str = alert_payload.get('time')
        if alert_time_str:
            try:
                alert_datetime = datetime.datetime.fromisoformat(alert_time_str.replace('Z', '+00:00'))
                current_datetime = datetime.datetime.now(datetime.timezone.utc)
                age_minutes = (current_datetime - alert_datetime).total_seconds() / 60
                
                if age_minutes > ignore_older_minutes:
                    logging.info(f"⏰ FILTERED: Alert age {age_minutes:.1f}min > {ignore_older_minutes}min threshold | Rule: {rule_name} | IGNORED")
                    return jsonify({"status": "ignored", "reason": "too_old"}), 200
                else:
                    logging.info(f"✅ PASSED: Age check {age_minutes:.1f}min <= {ignore_older_minutes}min | Rule: {rule_name}")
            except ValueError as e:
                logging.warning(f"⚠️ TIMESTAMP: Error parsing timestamp '{alert_time_str}': {e} | Rule: {rule_name} | Processing anyway")
        else:
            logging.info(f"⚠️ NO_TIME: Alert has no timestamp, skipping age check | Rule: {rule_name}")

    # Deduplication
    if deduplication_enabled:
        alert_key = f"{alert_payload.get('rule', '')}-{alert_payload.get('output', '')[:50]}"
        if alert_key in alert_counts:
            alert_counts[alert_key] += 1
            logging.info(f"🔁 DUPLICATE: Alert #{alert_counts[alert_key]} | Rule: {rule_name} | Key: {alert_key[:100]}... | IGNORED")
            return jsonify({"status": "duplicate", "count": alert_counts[alert_key]}), 200
        else:
            alert_counts[alert_key] = 1
            logging.info(f"✅ PASSED: Deduplication check (first occurrence) | Rule: {rule_name}")
    else:
        logging.info(f"⚠️ DEDUP_DISABLED: Deduplication disabled, processing alert | Rule: {rule_name}")

    # Generate AI explanation
    logging.info(f"🤖 AI_ANALYSIS: Starting AI explanation generation | Rule: {rule_name}")
    explanation_sections = generate_explanation_portkey(alert_payload)
    
    ai_success = explanation_sections and not explanation_sections.get("error")
    if ai_success:
        ai_provider = explanation_sections.get("llm_provider", "Unknown")
        logging.info(f"✅ AI_SUCCESS: Generated explanation using {ai_provider} | Rule: {rule_name}")
    else:
        error_msg = explanation_sections.get("error", "Unknown error") if explanation_sections else "No response"
        logging.warning(f"❌ AI_FAILED: {error_msg} | Rule: {rule_name}")
    
    # Store alert in database for Web UI
    if WEB_UI_ENABLED:
        try:
            store_alert(alert_payload, explanation_sections if ai_success else None)
            logging.info(f"💾 DB_STORED: Alert saved to database | Rule: {rule_name}")
        except Exception as e:
            logging.error(f"❌ DB_ERROR: Failed to store alert: {e} | Rule: {rule_name}")
    else:
        logging.info(f"⚠️ DB_SKIP: Web UI disabled, not storing alert | Rule: {rule_name}")

    # Send to Slack
    if slack_client:
        try:
            if ai_success:
                post_to_slack(alert_payload, explanation_sections, slack_client, slack_channel_name)
                logging.info(f"📢 SLACK_SUCCESS: Alert sent with AI analysis to {slack_channel_name} | Rule: {rule_name}")
                return jsonify({"status": "success", "message": "Alert sent with AI analysis"}), 200
            else:
                error_msg = explanation_sections.get("error", "AI analysis failed") if explanation_sections else "AI analysis failed"
                basic_message = format_slack_message_basic(alert_payload, error_msg)
                send_slack_message(basic_message, slack_client, slack_channel_name)
                logging.warning(f"📢 SLACK_PARTIAL: Alert sent without AI analysis to {slack_channel_name} | Rule: {rule_name} | Reason: {error_msg}")
                return jsonify({"status": "partial_success", "message": "Alert sent without AI analysis", "error": error_msg}), 200
        except Exception as e:
            logging.error(f"❌ SLACK_ERROR: Failed to send to Slack: {e} | Rule: {rule_name}")
            return jsonify({"status": "slack_error", "message": "Alert processed but Slack delivery failed", "error": str(e)}), 200
    else:
        logging.warning(f"⚠️ SLACK_DISABLED: Alert processed but Slack not configured | Rule: {rule_name}")
        return jsonify({"status": "no_slack", "message": "Alert processed but Slack not configured"}), 200

# --- Web UI Functions ---
def store_chat_message(message_type, content, context=None):
    """Store chat message for conversation history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO chat_messages (message_type, content, context)
        VALUES (?, ?, ?)
    ''', (message_type, content, json.dumps(context) if context else None))
    
    conn.commit()
    conn.close()

def get_chat_history(limit=50):
    """Retrieve chat message history."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM chat_messages 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    
    messages = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries and reverse to get chronological order
    message_list = []
    for msg in reversed(messages):
        message_dict = {
            'id': msg[0],
            'timestamp': msg[1],
            'type': msg[2],
            'content': msg[3],
            'context': json.loads(msg[4]) if msg[4] else None
        }
        message_list.append(message_dict)
    
    return message_list

def generate_ai_response(question, alert_context=None):
    """Generate AI response based on question and alert context."""
    alerts = get_alerts()
    
    # Analyze the question and generate appropriate response
    question_lower = question.lower()
    
    if 'critical' in question_lower or 'most important' in question_lower:
        critical_alerts = [a for a in alerts if a['priority'] == 'critical']
        if critical_alerts:
            return f"🚨 You have {len(critical_alerts)} critical alerts. The most recent is '{critical_alerts[0]['rule']}' which requires immediate attention. These alerts indicate serious security threats that could compromise your system."
        else:
            return "✅ Good news! You currently have no critical alerts. Your system appears to be operating securely."
    
    elif 'trend' in question_lower or 'pattern' in question_lower:
        total_alerts = len(alerts)
        recent_alerts = len([a for a in alerts if (datetime.datetime.now() - datetime.datetime.fromisoformat(a['timestamp'])).total_seconds() < 3600])
        
        # Analyze rule patterns
        rule_counts = {}
        for alert in alerts:
            rule_counts[alert['rule']] = rule_counts.get(alert['rule'], 0) + 1
        
        top_rule = max(rule_counts.items(), key=lambda x: x[1]) if rule_counts else None
        
        response = f"📈 Analysis of {total_alerts} alerts shows {recent_alerts} in the last hour. "
        if top_rule:
            response += f"Most common alert: '{top_rule[0]}' ({top_rule[1]} occurrences). "
        
        response += "I recommend monitoring these patterns for potential security incidents."
        return response
    
    elif 'recommend' in question_lower or 'next steps' in question_lower:
        high_priority = len([a for a in alerts if a['priority'] in ['critical', 'error']])
        
        recommendations = [
            f"📋 Investigate {high_priority} high-priority alerts immediately",
            "🛡️ Implement automated response for critical alerts",
            "📊 Set up regular security review meetings",
            "🚀 Consider deploying this system to production for real-time monitoring"
        ]
        
        return "💡 Based on your alert data, here are my recommendations:\n\n" + "\n".join(recommendations)
    
    else:
        # Default analytical response
        total_alerts = len(alerts)
        priorities = {}
        for alert in alerts:
            priorities[alert['priority']] = priorities.get(alert['priority'], 0) + 1
        
        priority_text = ", ".join([f"{count} {priority}" for priority, count in priorities.items()])
        
        return f"🤔 I've analyzed your {total_alerts} alerts. Priority breakdown: {priority_text}. What specific aspect would you like me to explore? I can analyze trends, provide recommendations, or help with deployment planning."

# --- Web UI Routes ---
from flask import render_template, send_from_directory

@app.route('/dashboard')
def dashboard():
    """Main dashboard page."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    return render_template('dashboard.html')

@app.route('/')
def index():
    """Redirect root to dashboard."""
    if WEB_UI_ENABLED:
        return dashboard()
    else:
        return jsonify({"message": "Falco AI Alert System", "status": "running", "webhook": "/falco-webhook"})

@app.route('/api/alerts')
def api_alerts():
    """Return alerts as JSON for dashboard."""
    try:
        # Get filters from request args
        filters = {
            'time_range': request.args.get('time_range', 'all'),
            'priority': request.args.get('priority', 'all'), 
            'rule': request.args.get('rule', 'all'),
            'status': request.args.get('status', 'all'),
            'limit': request.args.get('limit', '100')
        }
        
        alerts = get_alerts(filters)
        return jsonify(alerts)
    except Exception as e:
        logging.error(f"Error fetching alerts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts/<uuid>')
def api_get_alert(uuid):
    """Get a specific alert by UUID."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Try to find alert by UUID in the output or rule name
        cursor.execute('''
            SELECT * FROM alerts 
            WHERE output LIKE ? OR rule LIKE ?
            ORDER BY timestamp DESC LIMIT 1
        ''', (f'%{uuid}%', f'%{uuid}%'))
        
        alert = cursor.fetchone()
        conn.close()
        
        if not alert:
            return jsonify({"error": "Alert not found"}), 404
        
        # Convert to dictionary format
        alert_dict = {
            'id': alert[0],
            'uuid': uuid,  # Include the requested UUID
            'time': alert[1],
            'rule': alert[2],
            'priority': alert[3],
            'output': alert[4],
            'source': alert[5] or 'unknown',
            'output_fields': json.loads(alert[6]) if alert[6] else {},
            'ai_analysis': json.loads(alert[7]) if alert[7] else None,
            'processed': bool(alert[8])
        }
        
        return jsonify(alert_dict)
        
    except Exception as e:
        logging.error(f"Error fetching alert {uuid}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """API endpoint to get alert statistics."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
        
    alerts = get_alerts()
    
    stats = {
        'total_alerts': len(alerts),
        'critical_alerts': len([a for a in alerts if a['priority'] == 'critical']),
        'unique_rules': len(set(a['rule'] for a in alerts)),
        'recent_alerts': len([a for a in alerts if (datetime.datetime.now() - datetime.datetime.fromisoformat(a['timestamp'])).total_seconds() < 3600])
    }
    
    return jsonify(stats)

@app.route('/api/rules')
def api_rules():
    """API endpoint to get unique alert rules."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
        
    alerts = get_alerts()
    rules = list(set(a['rule'] for a in alerts))
    return jsonify(rules)

@app.route('/api/alerts/<int:alert_id>/reprocess', methods=['POST'])
def api_reprocess_alert(alert_id):
    """API endpoint to reprocess an alert with AI analysis."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    try:
        # Get the alert from database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM alerts WHERE id = ?', (alert_id,))
        alert_row = cursor.fetchone()
        
        if not alert_row:
            conn.close()
            return jsonify({'success': False, 'error': 'Alert not found'}), 404
        
        # Convert alert row to dict for AI processing
        alert_data = {
            'id': alert_row[0],
            'rule': alert_row[2],
            'priority': alert_row[3],
            'output': alert_row[4],
            'output_fields': json.loads(alert_row[6]) if alert_row[6] else {}
        }
        
        logging.info(f"🔄 Reprocessing alert {alert_id}: {alert_data['rule']}")
        
        # Generate new AI analysis
        ai_analysis = generate_explanation_portkey(alert_data)
        
        if ai_analysis and 'error' not in ai_analysis:
            # Update the alert with new AI analysis
            cursor.execute('''
                UPDATE alerts 
                SET ai_analysis = ?, processed = TRUE
                WHERE id = ?
            ''', (json.dumps(ai_analysis), alert_id))
            
            conn.commit()
            conn.close()
            
            logging.info(f"✅ Successfully reprocessed alert {alert_id}")
            return jsonify({
                'success': True, 
                'message': 'Alert reprocessed successfully',
                'ai_analysis': ai_analysis
            })
        else:
            conn.close()
            error_msg = ai_analysis.get('error', 'Unknown error') if ai_analysis else 'AI analysis failed'
            logging.error(f"❌ Failed to reprocess alert {alert_id}: {error_msg}")
            return jsonify({
                'success': False, 
                'error': f'AI analysis failed: {error_msg}'
            }), 500
            
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        logging.error(f"❌ Error reprocessing alert {alert_id}: {e}")
        return jsonify({
            'success': False, 
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/alerts/<int:alert_id>/status', methods=['POST'])
def api_update_alert_status(alert_id):
    """API endpoint to update alert status (read, dismissed, etc.)."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    data = request.json
    status = data.get('status', 'read')
    
    if status not in ['unread', 'read', 'dismissed']:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE alerts SET status = ? WHERE id = ?', (status, alert_id))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Alert not found'}), 404
        
        conn.commit()
        conn.close()
        
        logging.info(f"✅ Updated alert {alert_id} status to {status}")
        return jsonify({'success': True, 'status': status})
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        logging.error(f"❌ Error updating alert status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts/bulk-status', methods=['POST'])
def api_bulk_update_status():
    """API endpoint to bulk update alert status."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    data = request.json
    alert_ids = data.get('alert_ids', [])
    status = data.get('status', 'read')
    
    if not alert_ids:
        return jsonify({'success': False, 'error': 'No alert IDs provided'}), 400
    
    if status not in ['unread', 'read', 'dismissed']:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create placeholders for the IN clause
        placeholders = ','.join('?' * len(alert_ids))
        query = f'UPDATE alerts SET status = ? WHERE id IN ({placeholders})'
        
        cursor.execute(query, [status] + alert_ids)
        
        conn.commit()
        updated_count = cursor.rowcount
        conn.close()
        
        logging.info(f"✅ Bulk updated {updated_count} alerts to status {status}")
        return jsonify({'success': True, 'updated_count': updated_count, 'status': status})
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        logging.error(f"❌ Error bulk updating alert status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts/counts')
def api_alert_counts():
    """API endpoint to get alert counts by status."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get counts by status
        cursor.execute('''
            SELECT 
                COALESCE(status, 'unread') as status,
                COUNT(*) as count
            FROM alerts 
            GROUP BY COALESCE(status, 'unread')
        ''')
        
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM alerts')
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total': total_count,
            'unread': status_counts.get('unread', 0),
            'read': status_counts.get('read', 0),
            'dismissed': status_counts.get('dismissed', 0)
        })
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        logging.error(f"❌ Error getting alert counts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for chat interactions."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
        
    data = request.json
    question = data.get('message', '')
    context = data.get('context', {})
    
    if not question.strip():
        return jsonify({'error': 'Empty message'}), 400
    
    # Store user message
    store_chat_message('user', question, context)
    
    # Generate AI response
    response = generate_ai_response(question, context.get('selected_alert'))
    
    # Store AI response
    store_chat_message('ai', response, {'question': question})
    
    return jsonify({
        'response': response,
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/chat/history')
def api_chat_history():
    """API endpoint to get chat history."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
        
    messages = get_chat_history()
    return jsonify(messages)

@app.route('/api/export')
def api_export():
    """API endpoint to export analysis data."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
        
    alerts = get_alerts()
    
    # Generate comprehensive analysis
    analysis = {
        'export_timestamp': datetime.datetime.now().isoformat(),
        'summary': {
            'total_alerts': len(alerts),
            'time_range': f"{alerts[-1]['timestamp']} to {alerts[0]['timestamp']}" if alerts else "No alerts",
            'unique_rules': len(set(a['rule'] for a in alerts))
        },
        'priority_breakdown': {},
        'rule_frequency': {},
        'recommendations': []
    }
    
    # Priority breakdown
    for alert in alerts:
        priority = alert['priority']
        analysis['priority_breakdown'][priority] = analysis['priority_breakdown'].get(priority, 0) + 1
    
    # Rule frequency
    for alert in alerts:
        rule = alert['rule']
        analysis['rule_frequency'][rule] = analysis['rule_frequency'].get(rule, 0) + 1
    
    # Sort rules by frequency
    analysis['rule_frequency'] = dict(sorted(analysis['rule_frequency'].items(), key=lambda x: x[1], reverse=True))
    
    # Generate recommendations
    critical_count = analysis['priority_breakdown'].get('critical', 0)
    error_count = analysis['priority_breakdown'].get('error', 0)
    
    if critical_count > 0:
        analysis['recommendations'].append(f"🚨 {critical_count} critical alerts require immediate investigation")
    
    if error_count > 5:
        analysis['recommendations'].append("⚠️ High error rate detected - review system security")
    
    analysis['recommendations'].extend([
        "🛡️ Implement automated incident response",
        "📊 Set up regular security monitoring",
        "🚀 Deploy to production for real-time protection"
    ])
    
    return jsonify(analysis)

# --- Slack Configuration Routes ---
@app.route('/config/slack')
def slack_config_ui():
    """Slack configuration page."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    return render_template('slack_config.html', page='slack')

@app.route('/api/slack/config')
def api_slack_config():
    """API endpoint to get Slack configuration."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    config = get_slack_config()
    return jsonify(config)

@app.route('/api/slack/config', methods=['POST'])
def api_update_slack_config():
    """API endpoint to update Slack configuration."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        for setting_name, setting_value in data.items():
            if setting_name in ['bot_token', 'channel_name', 'enabled', 'username', 'icon_emoji', 
                              'template_style', 'min_priority_slack', 'include_commands', 'thread_alerts']:
                update_slack_config(setting_name, setting_value)
        
        return jsonify({"success": True, "message": "Configuration updated successfully"})
    except Exception as e:
        logging.error(f"Error updating Slack config: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/slack/test', methods=['POST'])
def api_test_slack():
    """API endpoint to test Slack connection."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    data = request.json
    bot_token = data.get('bot_token', '')
    channel_name = data.get('channel_name', '#general')
    
    if not bot_token:
        return jsonify({"error": "Bot token is required"}), 400
    
    result = test_slack_connection(bot_token, channel_name)
    return jsonify(result)

@app.route('/api/slack/preview', methods=['POST'])
def api_slack_preview():
    """API endpoint to preview Slack message format."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    data = request.json
    template_style = data.get('template_style', 'detailed')
    
    # Sample alert for preview
    sample_alert = {
        'rule': 'Terminal shell in container',
        'priority': 'warning',
        'output': 'A shell was used as the entrypoint/exec point into a container (user=root)',
        'time': datetime.datetime.now().isoformat(),
        'output_fields': {
            'proc.cmdline': '/bin/bash',
            'container.id': 'abc123'
        }
    }
    
    # Sample AI analysis
    sample_analysis = {
        'Security Impact': {'content': 'An interactive shell session in a container may indicate unauthorized access or legitimate administrative activity.'},
        'Next Steps': {'content': 'Verify if this shell access was authorized and investigate recent container activities.'},
        'Remediation Steps': {'content': 'Review container security policies and consider implementing runtime protection rules.'},
        'Suggested Commands': {'content': 'docker logs abc123\nkubectl describe pod <pod-name>'},
        'llm_provider': 'OpenAI via Portkey'
    }
    
    # Generate preview based on template style
    if template_style == 'basic':
        preview = {
            'type': 'basic',
            'content': f"⚠️ **Falco Alert**\n**Rule:** {sample_alert['rule']}\n**Priority:** {sample_alert['priority']}\n**Details:** {sample_alert['output']}"
        }
    else:
        preview = {
            'type': 'detailed',
            'content': {
                'header': f"🚨 Falco Security Alert - {sample_alert['rule']}",
                'priority': sample_alert['priority'].capitalize(),
                'security_impact': sample_analysis['Security Impact']['content'],
                'next_steps': sample_analysis['Next Steps']['content'],
                'remediation': sample_analysis['Remediation Steps']['content'],
                'commands': sample_analysis['Suggested Commands']['content'] if data.get('include_commands') else None
            }
        }
    
    return jsonify(preview)

@app.route('/api/slack/channels')
def api_slack_channels():
    """API endpoint to get available Slack channels."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    config = get_slack_config()
    bot_token = config.get('bot_token', {}).get('value', '')
    
    if not bot_token:
        return jsonify({"error": "Bot token not configured"}), 400
    
    try:
        test_client = WebClient(token=bot_token)
        response = test_client.conversations_list(types="public_channel,private_channel")
        
        channels = []
        for channel in response['channels']:
            channels.append({
                'id': channel['id'],
                'name': f"#{channel['name']}",
                'is_private': channel['is_private'],
                'is_member': channel.get('is_member', False)
            })
        
        return jsonify(channels)
    except SlackApiError as e:
        return jsonify({"error": f"Failed to fetch channels: {e.response['error']}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- AI Configuration Routes ---
@app.route('/config/ai')
def ai_config_ui():
    """Serve the AI configuration UI."""
    return render_template('ai_config.html', page='ai')

@app.route('/chat')
def chat_ui():
    """Serve the AI Chat UI."""
    return render_template('chat.html', page='chat')

@app.route('/api/ai/config')
def api_ai_config():
    """API endpoint to get AI configuration."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    config = get_ai_config()
    return jsonify(config)

@app.route('/api/ai/config', methods=['POST'])
def api_update_ai_config():
    """API endpoint to update AI configuration."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        valid_settings = ['provider_name', 'model_name', 'openai_model_name', 'gemini_model_name', 
                         'portkey_api_key', 'openai_virtual_key', 'gemini_virtual_key', 'ollama_api_url', 
                         'ollama_model_name', 'max_tokens', 'temperature', 'enabled', 'system_prompt', 
                         'ollama_timeout', 'ollama_keep_alive', 'ollama_parallel']
        
        for setting_name, setting_value in data.items():
            if setting_name in valid_settings:
                update_ai_config(setting_name, setting_value)
        
        return jsonify({"success": True, "message": "AI configuration updated successfully"})
    except Exception as e:
        logging.error(f"Error updating AI config: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai/test', methods=['POST'])
def api_test_ai():
    """API endpoint to test AI provider connection."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    data = request.json
    provider_name = data.get('provider_name', '').lower()
    
    if not provider_name:
        return jsonify({"error": "Provider name is required"}), 400
    
    if provider_name not in ['openai', 'gemini', 'ollama']:
        return jsonify({"error": "Invalid provider. Must be 'openai', 'gemini', or 'ollama'"}), 400
    
    result = test_ai_connection(provider_name, data)
    return jsonify(result)

@app.route('/api/ai/models')
def api_ai_models():
    """API endpoint to get available models for each provider."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    models = {
        'openai': [
            'gpt-4o', 'gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo', 
            'gpt-3.5-turbo-16k', 'gpt-4-32k'
        ],
        'gemini': [
            'gemini-pro', 'gemini-pro-vision', 'gemini-1.5-pro',
            'gemini-1.5-flash'
        ],
        'ollama': [
            'jimscard/whiterabbit-neo:latest', 'llama3', 'llama2', 'mistral', 'codellama', 'phi', 
            'neural-chat', 'starling-lm', 'orca-mini'
        ]
    }
    
    return jsonify(models)

@app.route('/api/ai/generate-sample', methods=['POST'])
def api_generate_sample():
    """API endpoint to generate a sample AI response for testing."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    data = request.json
    provider_name = data.get('provider_name', '').lower()
    
    if not provider_name:
        return jsonify({"error": "Provider name is required"}), 400
    
    # Sample Falco alert for testing
    sample_alert = {
        'rule': 'Terminal shell in container',
        'priority': 'warning',
        'output': 'A shell was used as the entrypoint/exec point into a container (user=root)',
        'output_fields': {
            'proc.cmdline': '/bin/bash',
            'container.id': 'test123'
        }
    }
    
    try:
        # Generate explanation using current configuration
        explanation = generate_explanation_portkey(sample_alert)
        
        if explanation and not explanation.get('error'):
            return jsonify({
                'success': True,
                'sample_response': explanation,
                'provider_used': explanation.get('llm_provider', provider_name)
            })
        else:
            return jsonify({
                'success': False,
                'error': explanation.get('error', 'Failed to generate sample response')
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Sample generation failed: {str(e)}'
        }), 500

@app.route('/api/ai/chat', methods=['POST'])
def api_ai_chat():
    """Handle AI chat requests about specific alerts."""
    try:
        data = request.json or {}
        message = data.get('message', '').strip()
        alert = data.get('alert', {})
        chat_history = data.get('chat_history', [])
        
        if not message:
            return jsonify({"success": False, "error": "Message is required"}), 400
        
        if not alert:
            return jsonify({"success": False, "error": "Alert context is required"}), 400
        
        # Get AI configuration
        ai_config = get_ai_config()
        
        # Check if AI is enabled
        if ai_config.get('enabled', {}).get('value') != 'true':
            return jsonify({"success": False, "error": "AI analysis is disabled"}), 400
        
        provider_name = ai_config.get('provider_name', {}).get('value', 'openai').lower()
        model_name = ai_config.get('model_name', {}).get('value')
        max_tokens = int(ai_config.get('max_tokens', {}).get('value', '500'))
        temperature = float(ai_config.get('temperature', {}).get('value', '0.7'))
        
        # Build context-aware prompt
        system_prompt = f"""You are a cybersecurity expert assistant helping analyze Falco security alerts. 

Current Alert Context:
- Rule: {alert.get('rule', 'N/A')}
- Priority: {alert.get('priority', 'N/A')}
- Description: {alert.get('output', 'N/A')}
- Time: {alert.get('time', 'N/A')}

Additional Fields:
{json.dumps(alert.get('output_fields', {}), indent=2)}

Please provide helpful, accurate information about this security alert. Keep responses concise and actionable."""

        # Build conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add previous chat history
        for hist in chat_history[-5:]:  # Last 5 exchanges
            messages.append({"role": "user", "content": hist.get('user', '')})
            messages.append({"role": "assistant", "content": hist.get('ai', '')})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Generate response based on provider
        response_text = ""
        
        if provider_name == "openai":
            portkey_api_key = ai_config.get('portkey_api_key', {}).get('value', '')
            openai_virtual_key = ai_config.get('openai_virtual_key', {}).get('value', '')
            
            if not portkey_api_key or not openai_virtual_key:
                return jsonify({"success": False, "error": "OpenAI configuration incomplete"}), 400
            
            from portkey_ai import Portkey
            client = Portkey(api_key=portkey_api_key, virtual_key=openai_virtual_key)
            
            response = client.chat.completions.create(
                model=model_name or "gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            response_text = response.choices[0].message.content
            
        elif provider_name == "gemini":
            portkey_api_key = ai_config.get('portkey_api_key', {}).get('value', '')
            gemini_virtual_key = ai_config.get('gemini_virtual_key', {}).get('value', '')
            
            if not portkey_api_key or not gemini_virtual_key:
                return jsonify({"success": False, "error": "Gemini configuration incomplete"}), 400
            
            from portkey_ai import Portkey
            client = Portkey(api_key=portkey_api_key, virtual_key=gemini_virtual_key)
            
            response = client.chat.completions.create(
                model=model_name or "gemini-pro",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            response_text = response.choices[0].message.content
            
        elif provider_name == "ollama":
            ollama_api_url = ai_config.get('ollama_api_url', {}).get('value', 'http://ollama:11434/api/generate')
            ollama_model_name = ai_config.get('ollama_model_name', {}).get('value', 'tinyllama')
            ollama_timeout = int(ai_config.get('ollama_timeout', {}).get('value', '30'))
            
            # Convert messages to single prompt for Ollama
            conversation = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            ollama_payload = {
                "model": ollama_model_name,
                "prompt": conversation,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
            
            response = requests.post(ollama_api_url, json=ollama_payload, timeout=ollama_timeout)
            response.raise_for_status()
            
            response_data = response.json()
            response_text = response_data.get('response', '')
            
        else:
            return jsonify({"success": False, "error": f"Unsupported provider: {provider_name}"}), 400
        
        if not response_text:
            return jsonify({"success": False, "error": "Empty response from AI"}), 400
        
        return jsonify({
            "success": True,
            "response": response_text,
            "provider": provider_name,
            "model": model_name
        })
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error in AI chat: {e}")
        return jsonify({"success": False, "error": f"Network error: {e}"}), 500
    except Exception as e:
        logging.error(f"Error in AI chat: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ollama/models')
def api_ollama_models():
    """API endpoint to get locally available Ollama models."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    try:
        import requests
        ai_config = get_ai_config()
        ollama_api_url = ai_config.get('ollama_api_url', {}).get('value', 'http://ollama:11434/api/generate')
        
        # Extract base URL from generate endpoint
        base_url = ollama_api_url.replace('/api/generate', '')
        
        response = requests.get(f"{base_url}/api/tags", timeout=10)
        response.raise_for_status()
        
        models_data = response.json()
        models = [model['name'] for model in models_data.get('models', [])]
        
        return jsonify({
            'success': True,
            'models': models,
            'count': len(models)
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Could not connect to Ollama: {str(e)}',
            'models': []
        }), 200  # Return 200 but with error info
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error fetching models: {str(e)}',
            'models': []
        }), 500

@app.route('/api/ollama/pull', methods=['POST'])
def api_ollama_pull():
    """API endpoint to download/pull an Ollama model."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    data = request.json
    model_name = data.get('model_name', '').strip()
    
    if not model_name:
        return jsonify({"error": "Model name is required"}), 400
    
    try:
        import requests
        ai_config = get_ai_config()
        ollama_api_url = ai_config.get('ollama_api_url', {}).get('value', 'http://ollama:11434/api/generate')
        
        # Extract base URL from generate endpoint
        base_url = ollama_api_url.replace('/api/generate', '')
        
        # Start the pull request (this returns immediately with a stream)
        response = requests.post(
            f"{base_url}/api/pull",
            json={"name": model_name},
            timeout=5
        )
        response.raise_for_status()
        
        return jsonify({
            'success': True,
            'message': f'Download started for {model_name}',
            'model_name': model_name
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Could not start download: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Download failed: {str(e)}'
        }), 500

@app.route('/api/ollama/status')
def api_ollama_status():
    """API endpoint to check if a specific Ollama model is available."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    model_name = request.args.get('model_name')
    if not model_name:
        return jsonify({"error": "model_name parameter is required"}), 400
    
    try:
        import requests
        ai_config = get_ai_config()
        ollama_api_url = ai_config.get('ollama_api_url', {}).get('value', 'http://ollama:11434/api/generate')
        
        # Extract base URL from generate endpoint
        base_url = ollama_api_url.replace('/api/generate', '')
        
        response = requests.get(f"{base_url}/api/tags", timeout=10)
        response.raise_for_status()
        
        models_data = response.json()
        available_models = [model['name'] for model in models_data.get('models', [])]
        
        is_available = model_name in available_models
        
        return jsonify({
            'model_name': model_name,
            'available': is_available,
            'status': 'downloaded' if is_available else 'not_found'
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'model_name': model_name,
            'available': False,
            'status': 'ollama_unavailable',
            'error': str(e)
        }), 200
    except Exception as e:
        return jsonify({
            'model_name': model_name,
            'available': False,
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/ollama/download-progress')
def api_ollama_download_progress():
    """API endpoint to check download progress for a specific Ollama model."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    model_name = request.args.get('model_name')
    if not model_name:
        return jsonify({"error": "model_name parameter is required"}), 400
    
    try:
        import requests
        ai_config = get_ai_config()
        ollama_api_url = ai_config.get('ollama_api_url', {}).get('value', 'http://ollama:11434/api/generate')
        
        # Extract base URL from generate endpoint
        base_url = ollama_api_url.replace('/api/generate', '')
        
        # First check if model is already downloaded
        try:
            tags_response = requests.get(f"{base_url}/api/tags", timeout=5)
            tags_response.raise_for_status()
            models_data = tags_response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            
            if model_name in available_models:
                return jsonify({
                    'model_name': model_name,
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Model downloaded and ready'
                })
        except:
            pass
        
        # Try to get download progress by checking if model is being pulled
        # Ollama doesn't provide real-time progress via REST API, but we can infer download status
        try:
            # Check if we can generate with the model (will fail if not downloaded)
            test_response = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "test",
                    "stream": False,
                    "options": {"num_predict": 1}
                },
                timeout=5
            )
            
            if test_response.status_code == 200:
                return jsonify({
                    'model_name': model_name,
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Model downloaded and ready'
                })
            else:
                return jsonify({
                    'model_name': model_name,
                    'status': 'downloading',
                    'progress': -1,  # Unknown progress
                    'message': 'Model is downloading...'
                })
                
        except requests.exceptions.RequestException:
            return jsonify({
                'model_name': model_name,
                'status': 'not_started',
                'progress': 0,
                'message': 'Model not found or download not started'
            })
            
    except Exception as e:
        return jsonify({
            'model_name': model_name,
            'status': 'error',
            'progress': 0,
            'message': f'Error checking progress: {str(e)}'
        }), 500

@app.route('/api/ai/system-prompt/reset', methods=['POST'])
def api_reset_system_prompt():
    """API endpoint to reset system prompt to default."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI disabled"}), 404
    
    try:
        # Clear the system prompt in database (empty string means use default)
        update_ai_config('system_prompt', '')
        
        # Get the default prompt that will be used
        default_prompt = load_system_prompt()
        
        return jsonify({
            'success': True,
            'message': 'System prompt reset to default',
            'default_prompt': default_prompt
        })
        
    except Exception as e:
        logging.error(f"Error resetting system prompt: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to reset system prompt: {str(e)}'
        }), 500

def get_slack_config():
    """Get all Slack configuration settings."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT setting_name, setting_value, setting_type, description FROM slack_config')
    settings = cursor.fetchall()
    conn.close()
    
    config = {}
    for setting in settings:
        config[setting[0]] = {
            'value': setting[1],
            'type': setting[2],
            'description': setting[3]
        }
    
    return config

def update_slack_config(setting_name, setting_value):
    """Update a Slack configuration setting."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE slack_config 
        SET setting_value = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE setting_name = ?
    ''', (setting_value, setting_name))
    
    conn.commit()
    conn.close()
    logging.info(f"Updated Slack config: {setting_name} = {setting_value}")

def test_slack_connection(bot_token, channel_name):
    """Test Slack connection with provided credentials."""
    try:
        test_client = WebClient(token=bot_token)
        
        # Test API connection
        auth_response = test_client.auth_test()
        if not auth_response['ok']:
            return {'success': False, 'error': 'Invalid bot token'}
        
        # Test channel access
        try:
            test_response = test_client.chat_postMessage(
                channel=channel_name,
                text="🧪 Falco AI Alert System - Connection Test Successful! 🎉",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*🧪 Connection Test*\n✅ Falco AI Alert System is successfully connected to Slack!\n\n*Bot Info:*\n• User: " + auth_response.get('user', 'Unknown') + "\n• Team: " + auth_response.get('team', 'Unknown') + "\n• URL: " + auth_response.get('url', 'Unknown')
                        }
                    }
                ]
            )
            
            return {
                'success': True, 
                'message': 'Connection successful!',
                'bot_info': {
                    'user': auth_response.get('user'),
                    'team': auth_response.get('team'),
                    'url': auth_response.get('url')
                }
            }
        except SlackApiError as e:
            if e.response['error'] == 'channel_not_found':
                return {'success': False, 'error': f'Channel {channel_name} not found or bot not invited'}
            elif e.response['error'] == 'not_in_channel':
                return {'success': False, 'error': f'Bot not invited to channel {channel_name}'}
            else:
                return {'success': False, 'error': f'Channel error: {e.response["error"]}'}
                
    except SlackApiError as e:
        return {'success': False, 'error': f'Slack API error: {e.response["error"]}'}
    except Exception as e:
        return {'success': False, 'error': f'Connection error: {str(e)}'}

def get_ai_config():
    """Get all AI configuration settings."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT setting_name, setting_value, setting_type, description FROM ai_config')
    settings = cursor.fetchall()
    conn.close()
    
    config = {}
    for setting in settings:
        config[setting[0]] = {
            'value': setting[1],
            'type': setting[2],
            'description': setting[3]
        }
    
    return config

def update_ai_config(setting_name, setting_value):
    """Update an AI configuration setting."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE ai_config 
        SET setting_value = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE setting_name = ?
    ''', (setting_value, setting_name))
    
    conn.commit()
    conn.close()
    logging.info(f"Updated AI config: {setting_name} = {setting_value}")

def test_ai_connection(provider_name, config_data):
    """Test AI provider connection with provided configuration."""
    try:
        # Load system prompt for testing
        system_prompt = load_system_prompt()
        test_prompt = "This is a connection test. Please respond with 'Connection successful!' and a brief confirmation."
        
        if provider_name.lower() == "openai":
            try:
                from portkey_ai import Portkey
                
                portkey_api_key = config_data.get('portkey_api_key', '')
                openai_virtual_key = config_data.get('openai_virtual_key', '')
                model_name = config_data.get('model_name', 'gpt-3.5-turbo')
                
                if not portkey_api_key or not openai_virtual_key:
                    return {'success': False, 'error': 'Portkey API key and OpenAI virtual key are required'}
                
                client = Portkey(
                    api_key=portkey_api_key,
                    virtual_key=openai_virtual_key
                )
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": test_prompt}
                    ],
                    max_tokens=100
                )
                
                # Handle response format
                if hasattr(response, 'choices'):
                    content = response.choices[0].message.content
                else:
                    content = response['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'message': 'OpenAI connection successful!',
                    'response_preview': content[:200] + '...' if len(content) > 200 else content,
                    'model_used': model_name
                }
                
            except Exception as e:
                return {'success': False, 'error': f'OpenAI connection failed: {str(e)}'}
                
        elif provider_name.lower() == "gemini":
            try:
                from portkey_ai import Portkey
                
                portkey_api_key = config_data.get('portkey_api_key', '')
                gemini_virtual_key = config_data.get('gemini_virtual_key', '')
                model_name = config_data.get('model_name', 'gemini-pro')
                
                if not portkey_api_key or not gemini_virtual_key:
                    return {'success': False, 'error': 'Portkey API key and Gemini virtual key are required'}
                
                client = Portkey(
                    api_key=portkey_api_key,
                    virtual_key=gemini_virtual_key
                )
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": test_prompt}
                    ],
                    max_tokens=100
                )
                
                # Handle response format
                if hasattr(response, 'choices'):
                    content = response.choices[0].message.content
                else:
                    content = response['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'message': 'Gemini connection successful!',
                    'response_preview': content[:200] + '...' if len(content) > 200 else content,
                    'model_used': model_name
                }
                
            except Exception as e:
                return {'success': False, 'error': f'Gemini connection failed: {str(e)}'}
                
        elif provider_name.lower() == "ollama":
            try:
                import requests
                
                ollama_api_url = config_data.get('ollama_api_url', 'http://ollama:11434/api/generate')
                ollama_model_name = config_data.get('ollama_model_name', 'llama3')
                
                if not ollama_api_url:
                    return {'success': False, 'error': 'Ollama API URL is required'}
                
                # Test payload
                ollama_payload = {
                    "model": ollama_model_name,
                    "prompt": system_prompt + "\n\n" + test_prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 100
                    }
                }
                
                # Get configurable timeout from provided config
                ollama_timeout = int(config_data.get('ollama_timeout', '30'))
                response = requests.post(ollama_api_url, json=ollama_payload, timeout=ollama_timeout)
                response.raise_for_status()
                
                response_data = response.json()
                content = response_data.get('response', '')
                
                if not content:
                    return {'success': False, 'error': 'Empty response from Ollama'}
                
                return {
                    'success': True,
                    'message': 'Ollama connection successful!',
                    'response_preview': content[:200] + '...' if len(content) > 200 else content,
                    'model_used': ollama_model_name
                }
                
            except requests.exceptions.RequestException as e:
                return {'success': False, 'error': f'Ollama connection failed: {str(e)}'}
            except Exception as e:
                return {'success': False, 'error': f'Ollama error: {str(e)}'}
                
        else:
            return {'success': False, 'error': f'Unsupported provider: {provider_name}'}
            
    except Exception as e:
        return {'success': False, 'error': f'Configuration test failed: {str(e)}'}

# --- General Configuration Functions ---
def get_general_config():
    """Get general configuration settings from database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT setting_name, setting_value, setting_type, description FROM general_config')
    rows = cursor.fetchall()
    conn.close()
    
    config = {}
    for row in rows:
        config[row[0]] = {
            'value': row[1],
            'type': row[2],
            'description': row[3]
        }
    
    return config

def update_general_config(setting_name, setting_value):
    """Update a general configuration setting."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE general_config 
        SET setting_value = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE setting_name = ?
    ''', (setting_value, setting_name))
    
    conn.commit()
    conn.close()
    
    logging.info(f"Updated general config: {setting_name} = {setting_value}")

def get_cached_general_config():
    """Get general configuration with caching for performance."""
    global _general_config_cache, _general_config_last_updated
    
    # Initialize cache if needed
    if '_general_config_cache' not in globals():
        _general_config_cache = None
        _general_config_last_updated = 0
    
    current_time = datetime.datetime.now().timestamp()
    
    # Refresh cache every 60 seconds
    if _general_config_cache is None or (current_time - _general_config_last_updated) > 60:
        _general_config_cache = get_general_config()
        _general_config_last_updated = current_time
    
    return _general_config_cache

def get_general_setting(setting_name, default_value=None):
    """Get a specific general configuration setting with fallback to default."""
    config = get_cached_general_config()
    setting = config.get(setting_name, {})
    return setting.get('value', default_value)

# --- General Configuration Endpoints ---
@app.route('/config/general')
def general_config_ui():
    """Render general configuration page."""
    if not WEB_UI_ENABLED:
        return "Web UI is disabled", 404
    return render_template('general_config.html', page='general')

@app.route('/api/general/config')
def api_general_config():
    """Get general configuration settings."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI is disabled"}), 404
    
    config = get_general_config()
    return jsonify(config)

@app.route('/api/general/config', methods=['POST'])
def api_update_general_config():
    """Update general configuration settings."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI is disabled"}), 404
    
    data = request.json
    if not data:
        return jsonify({"error": "No configuration data provided"}), 400
    
    # Update multiple settings at once
    for setting_name, setting_value in data.items():
        update_general_config(setting_name, setting_value)
    
    return jsonify({"message": "General configuration updated successfully"})

@app.route('/api/general/test', methods=['POST'])
def api_test_general_config():
    """Test general configuration settings."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI is disabled"}), 404
    
    data = request.json
    if not data:
        return jsonify({"error": "No configuration data provided"}), 400
    
    # Test log level setting
    log_level = data.get('log_level', 'INFO')
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    if log_level not in valid_log_levels:
        return jsonify({
            "success": False, 
            "message": f"Invalid log level '{log_level}'. Valid levels: {', '.join(valid_log_levels)}"
        })
    
    # Test priority setting
    min_priority = data.get('min_priority', 'warning')
    valid_priorities = ["debug", "informational", "notice", "warning", "error", "critical", "alert", "emergency"]
    
    if min_priority not in valid_priorities:
        return jsonify({
            "success": False,
            "message": f"Invalid priority '{min_priority}'. Valid priorities: {', '.join(valid_priorities)}"
        })
    
    # Test numeric settings
    numeric_settings = {
        'ignore_older_minutes': 'Ignore Older Minutes',
        'web_ui_port': 'Web UI Port',
        'falco_ai_port': 'Falco AI Port',
        'deduplication_window_minutes': 'Deduplication Window',
        'max_alerts_storage': 'Max Alerts Storage',
        'alert_retention_days': 'Alert Retention Days'
    }
    
    for setting_key, setting_label in numeric_settings.items():
        if setting_key in data:
            try:
                value = int(data[setting_key])
                if value < 0:
                    return jsonify({
                        "success": False,
                        "message": f"{setting_label} must be a positive number"
                    })
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": f"{setting_label} must be a valid number"
                })
    
    return jsonify({
        "success": True,
        "message": "General configuration validation successful"
    })

@app.route('/api/general/reset', methods=['POST'])
def api_reset_general_config():
    """Reset general configuration to defaults."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI is disabled"}), 404
    
    # Reset to default values
    defaults = {
        'min_priority': 'warning',
        'ignore_older_minutes': '1',
        'web_ui_enabled': 'true',
        'web_ui_port': '8081',
        'falco_ai_port': '8080',
        'log_level': 'INFO',
        'deduplication_enabled': 'true',
        'deduplication_window_minutes': '60',
        'max_alerts_storage': '10000',
        'alert_retention_days': '30'
    }
    
    for setting_name, setting_value in defaults.items():
        update_general_config(setting_name, setting_value)
    
    return jsonify({"message": "General configuration reset to defaults"})

@app.route('/api/falco/config')
def api_falco_config():
    """Get Falco webhook configuration."""
    if not WEB_UI_ENABLED:
        return jsonify({"error": "Web UI is disabled"}), 404
    
    try:
        # Get the actual port from configuration
        general_config = get_cached_general_config()
        webhook_port = general_config.get('falco_ai_port', {}).get('value', '8080')
        
        # Get request host and protocol
        host = request.host.split(':')[0]  # Remove port if present
        protocol = 'https' if request.is_secure else 'http'
        
        # Build webhook URL
        webhook_url = f"{protocol}://{host}:{webhook_port}/falco-webhook"
        
        # Generate Falco YAML configuration
        falco_yaml = f"""# Falco HTTP Output Configuration
# Add this to your falco.yaml file

http_output:
  enabled: true
  url: "{webhook_url}"
  user_agent: "Falco Webhook"
  # Optional: Add custom headers if needed
  # headers:
  #   X-Custom-Header: "value"

# Optional: JSON output formatting
json_output: true
json_include_output_property: true
json_include_tags_property: true

# Optional: Configure log level and priority
log_level: info
priority: warning

# Optional: Configure buffering for better performance
# buffered_outputs: true
# outputs:
#   rate: 1000
#   max_burst: 10000"""
        
        return jsonify({
            'success': True,
            'webhook_url': webhook_url,
            'webhook_port': webhook_port,
            'falco_yaml': falco_yaml,
            'host': host,
            'protocol': protocol
        })
        
    except Exception as e:
        logging.error(f"Error getting Falco config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Initialize database if Web UI is enabled
    if WEB_UI_ENABLED:
        init_database()
        
        # Add some sample data for demonstration
        sample_alerts = [
            {
                'rule': 'Terminal shell in container',
                'priority': 'warning',
                'output': 'A shell was used as the entrypoint/exec point into a container (user=root container_id=abc123)',
                'output_fields': {'proc.cmdline': '/bin/bash', 'container.id': 'abc123', 'container.name': 'web-app-container'}
            },
            {
                'rule': 'Write below binary dir',
                'priority': 'critical',
                'output': 'File below a known binary directory opened for writing (user=root command=touch /bin/malicious)',
                'output_fields': {'proc.cmdline': 'touch /bin/malicious', 'fd.name': '/bin/malicious', 'container.name': 'database-container'}
            }
        ]
        
        # Only add sample data if no alerts exist
        existing_alerts = get_alerts()
        if not existing_alerts:
            for alert in sample_alerts:
                store_alert(alert)
    
    logging.info(f"Starting Falco AI Alert System on port {falco_ai_port}")
    logging.info(f"Provider: {os.environ.get('PROVIDER_NAME', 'openai')}")
    logging.info(f"Min Priority: {MIN_FALCO_PRIORITY}")
    logging.info(f"Slack: {'✅ Configured' if slack_client else '❌ Not configured'}")
    logging.info(f"Web UI: {'✅ Enabled at http://localhost:{falco_ai_port}/dashboard' if WEB_UI_ENABLED else '❌ Disabled'}")
    
    app.run(debug=True, host='0.0.0.0', port=falco_ai_port, threaded=True)