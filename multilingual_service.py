import os
import logging
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class BabelLanguage(Enum):
    """Supported languages in Babel LLM"""
    ENGLISH = ("en", "English", "🇺🇸")
    SPANISH = ("es", "Español", "🇪🇸")
    FRENCH = ("fr", "Français", "🇫🇷")
    GERMAN = ("de", "Deutsch", "🇩🇪")
    PORTUGUESE = ("pt", "Português", "🇵🇹")
    CHINESE = ("zh", "中文", "🇨🇳")
    HINDI = ("hi", "हिन्दी", "🇮🇳")
    ARABIC = ("ar", "العربية", "🇸🇦")
    BENGALI = ("bn", "বাংলা", "🇧🇩")
    RUSSIAN = ("ru", "Русский", "🇷🇺")
    URDU = ("ur", "اردو", "🇵🇰")
    INDONESIAN = ("id", "Bahasa Indonesia", "🇮🇩")
    JAPANESE = ("ja", "日本語", "🇯🇵")
    SWAHILI = ("sw", "Kiswahili", "🇰🇪")
    FILIPINO = ("tl", "Filipino", "🇵🇭")
    TAMIL = ("ta", "தமிழ்", "🇮🇳")
    VIETNAMESE = ("vi", "Tiếng Việt", "🇻🇳")
    TURKISH = ("tr", "Türkçe", "🇹🇷")
    ITALIAN = ("it", "Italiano", "🇮🇹")
    KOREAN = ("ko", "한국어", "🇰🇷")
    HAUSA = ("ha", "Hausa", "🇳🇬")
    PERSIAN = ("fa", "فارسی", "🇮🇷")
    THAI = ("th", "ภาษาไทย", "🇹🇭")
    BURMESE = ("my", "မြန်မာဘာသာ", "🇲🇲")

    def __init__(self, code: str, display_name: str, flag: str):
        self.code = code
        self.display_name = display_name
        self.flag = flag

    @classmethod
    def from_code(cls, code: str) -> Optional['BabelLanguage']:
        """Get language enum from language code"""
        for lang in cls:
            if lang.code == code:
                return lang
        return None

    @classmethod
    def get_supported_languages(cls) -> Dict[str, Dict[str, str]]:
        """Get all supported languages as a dictionary"""
        return {
            lang.code: {
                "name": lang.display_name,
                "flag": lang.flag
            }
            for lang in cls
        }

@dataclass
class MultilingualResponse:
    """Response from multilingual AI analysis"""
    content: str
    language: BabelLanguage
    confidence: float
    model_used: str
    translation_quality: Optional[str] = None

class BabelLLMService:
    """Service for multilingual AI analysis using Babel LLM via Ollama"""
    
    def __init__(self):
        # Set up models first
        self.babel_model_9b = "babel-9b"
        self.babel_model_83b = "babel-83b"
        
        # Load configuration from database if available
        self._load_config()
        
        # Language-specific system prompts
        self.language_prompts = {
            "en": "You are a cybersecurity expert. Analyze this security alert and provide clear, actionable insights in English.",
            "es": "Eres un experto en ciberseguridad. Analiza esta alerta de seguridad y proporciona información clara y procesable en español.",
            "fr": "Vous êtes un expert en cybersécurité. Analysez cette alerte de sécurité et fournissez des informations claires et exploitables en français.",
            "de": "Sie sind ein Cybersicherheitsexperte. Analysieren Sie diese Sicherheitswarnung und geben Sie klare, umsetzbare Erkenntnisse auf Deutsch.",
            "pt": "Você é um especialista em cibersegurança. Analise este alerta de segurança e forneça insights claros e acionáveis em português.",
            "zh": "你是一名网络安全专家。分析这个安全警报并用中文提供清晰、可操作的见解。",
            "hi": "आप एक साइबर सुरक्षा विशेषज्ञ हैं। इस सुरक्षा चेतावनी का विश्लेषण करें और हिंदी में स्पष्ट, कार्यात्मक अंतर्दृष्टि प्रदान करें।",
            "ar": "أنت خبير أمن سيبراني. قم بتحليل تنبيه الأمان هذا وقدم رؤى واضحة وقابلة للتنفيذ باللغة العربية।",
            "ru": "Вы эксперт по кибербезопасности. Проанализируйте это предупреждение безопасности и предоставьте четкие, практичные выводы на русском языке.",
            "ja": "あなたはサイバーセキュリティの専門家です。このセキュリティアラートを分析し、日本語で明確で実行可能な洞察を提供してください。",
        }
    
    def _load_config(self):
        """Load configuration from database or use defaults."""
        # Set defaults first
        self.ollama_url = os.getenv("OLLAMA_API_URL", "http://ollama:11434")
        if self.ollama_url.endswith("/api/generate"):
            self.ollama_url = self.ollama_url[:-13]
        
        self.default_model = self.babel_model_9b
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "60"))
        self.max_tokens = int(os.getenv("BABEL_MAX_TOKENS", "1000"))
        self.temperature = 0.7
        self.enabled = True
        
        # Try to load from database if available (will be done later via reload_config)
        logger.debug("📋 Using default Babel LLM config (database config loaded on demand)")
        
    def _load_database_config(self):
        """Load configuration from database if available."""
        try:
            # Import here to avoid circular dependencies
            import sqlite3
            import json
            
            # Try to connect to database directly
            DB_PATH = os.getenv("DATABASE_PATH", "data/falco_alerts.db")
            
            if os.path.exists(DB_PATH):
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                try:
                    cursor.execute('SELECT setting_name, setting_value FROM multilingual_config')
                    settings = cursor.fetchall()
                    
                    config = {}
                    for setting_name, setting_value in settings:
                        config[setting_name] = setting_value
                    
                    # Update configuration
                    if 'babel_ollama_endpoint' in config:
                        ollama_endpoint = config['babel_ollama_endpoint']
                        if ollama_endpoint.endswith("/api/generate"):
                            ollama_endpoint = ollama_endpoint[:-13]
                        self.ollama_url = ollama_endpoint
                    
                    if 'babel_babel_model' in config:
                        self.default_model = config['babel_babel_model']
                    
                    if 'babel_babel_timeout' in config:
                        self.timeout = int(config['babel_babel_timeout'])
                    
                    if 'babel_babel_max_tokens' in config:
                        self.max_tokens = int(config['babel_babel_max_tokens'])
                    
                    if 'babel_babel_temperature' in config:
                        self.temperature = float(config['babel_babel_temperature'])
                    
                    if 'babel_enable_babel_llm' in config:
                        self.enabled = config['babel_enable_babel_llm'].lower() == 'true'
                    
                    logger.debug(f"📋 Loaded Babel LLM config from database: model={self.default_model}, endpoint={self.ollama_url}")
                    
                except sqlite3.OperationalError:
                    # Table doesn't exist yet, use defaults
                    logger.debug("📋 Multilingual config table not found, using defaults")
                finally:
                    conn.close()
            else:
                logger.debug("📋 Database file not found, using defaults")
                
        except Exception as e:
            logger.warning(f"⚠️ Error loading database config: {e}")
            # Keep defaults
    
    def reload_config(self):
        """Reload configuration from database."""
        self._load_database_config()
    
    def is_babel_available(self) -> bool:
        """Check if Babel LLM model is available in Ollama"""
        # Load database config on first use if not already loaded
        if not hasattr(self, '_config_loaded'):
            self._load_database_config()
            self._config_loaded = True
        
        # Check if Babel LLM is enabled in configuration
        if not getattr(self, 'enabled', True):
            return False
            
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "").split(":")[0] for model in models]
                return any(self.babel_model_9b in name or self.babel_model_83b in name for name in model_names)
        except Exception as e:
            logger.warning(f"Failed to check Babel LLM availability: {e}")
        return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available Babel LLM models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                babel_models = []
                for model in models:
                    name = model.get("name", "")
                    if "babel" in name.lower():
                        babel_models.append(name)
                return babel_models
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
        return []
    
    def pull_babel_model(self, model_name: str = None) -> bool:
        """Pull Babel LLM model via Ollama"""
        if not model_name:
            model_name = self.default_model
        
        try:
            logger.info(f"🌍 Pulling Babel LLM model: {model_name}")
            response = requests.post(
                f"{self.ollama_url}/api/pull",
                json={"name": model_name},
                timeout=1800  # 30 minutes timeout for model download
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully pulled Babel LLM model: {model_name}")
                return True
            else:
                logger.error(f"❌ Failed to pull Babel LLM model: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error pulling Babel LLM model: {e}")
            return False
    
    def analyze_security_alert_multilingual(
        self,
        alert_payload: Dict[str, Any],
        target_language: str = "en",
        model_name: str = None
    ) -> MultilingualResponse:
        """
        Analyze security alert in the specified language using Babel LLM
        
        Args:
            alert_payload: Falco alert data
            target_language: Language code (e.g., 'es', 'fr', 'de')
            model_name: Specific Babel model to use
            
        Returns:
            MultilingualResponse with analysis in target language
        """
        if not model_name:
            model_name = self.default_model
        
        # Get language info
        language = BabelLanguage.from_code(target_language)
        if not language:
            logger.warning(f"Unsupported language: {target_language}, falling back to English")
            language = BabelLanguage.ENGLISH
            target_language = "en"
        
        # Get language-specific system prompt
        system_prompt = self.language_prompts.get(
            target_language, 
            self.language_prompts["en"]
        )
        
        # Prepare the alert context
        alert_context = f"""
Security Alert Analysis Request:

Rule: {alert_payload.get('rule', 'Unknown')}
Priority: {alert_payload.get('priority', 'unknown')}
Output: {alert_payload.get('output', 'No details available')}
Timestamp: {alert_payload.get('time', 'Unknown')}
Source: {alert_payload.get('source', 'Unknown')}

Output Fields:
"""
        
        # Add output fields
        output_fields = alert_payload.get('output_fields', {})
        for key, value in output_fields.items():
            alert_context += f"- {key}: {value}\n"
        
        # Language-specific analysis request
        language_instruction = f"""
Please analyze this security alert and provide a comprehensive response in {language.display_name} ({language.flag}) that includes:

1. **Security Impact** - What does this alert mean for security?
2. **Risk Assessment** - How serious is this threat?
3. **Next Steps** - What should the security team do immediately?
4. **Remediation** - How to fix or mitigate this issue?
5. **Prevention** - How to prevent similar incidents?

Respond entirely in {language.display_name}. Be clear, professional, and actionable.
"""
        
        prompt = f"{system_prompt}\n\n{alert_context}\n\n{language_instruction}"
        
        try:
            logger.info(f"🌍 Analyzing security alert in {language.display_name} using Babel LLM")
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "top_p": 0.9,
                        "max_tokens": self.max_tokens,
                        "stop": ["Human:", "Assistant:"]
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get("response", "").strip()
                
                if analysis:
                    logger.info(f"✅ Generated multilingual analysis in {language.display_name}")
                    return MultilingualResponse(
                        content=analysis,
                        language=language,
                        confidence=0.9,  # High confidence for Babel LLM
                        model_used=model_name,
                        translation_quality="native"
                    )
                else:
                    raise Exception("Empty response from Babel LLM")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error in multilingual analysis: {e}")
            
            # Fallback to English analysis
            if target_language != "en":
                logger.info("🔄 Falling back to English analysis")
                return self.analyze_security_alert_multilingual(
                    alert_payload, "en", model_name
                )
            else:
                # Return error response
                return MultilingualResponse(
                    content=f"Error analyzing security alert: {str(e)}",
                    language=language,
                    confidence=0.0,
                    model_used=model_name,
                    translation_quality="error"
                )
    
    def translate_ui_string(self, text: str, target_language: str) -> str:
        """
        Translate UI strings using Babel LLM
        
        Args:
            text: Text to translate
            target_language: Target language code
            
        Returns:
            Translated text
        """
        language = BabelLanguage.from_code(target_language)
        if not language or target_language == "en":
            return text
        
        prompt = f"""
Translate this user interface text to {language.display_name} ({language.flag}):

Original text: "{text}"

Requirements:
- Keep the same meaning and tone
- Use appropriate technical terminology
- Keep it concise and clear
- Respond with ONLY the translation, no explanations

Translation:"""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.default_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": max(0.3, self.temperature - 0.2),  # Lower temperature for more consistent translations
                        "max_tokens": 200,
                        "stop": ["\n\n", "Original:", "Translation:"]
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                translation = result.get("response", "").strip()
                
                if translation and translation != text:
                    logger.debug(f"🌍 Translated '{text}' to {language.display_name}: '{translation}'")
                    return translation
                    
        except Exception as e:
            logger.warning(f"Translation failed for '{text}' to {target_language}: {e}")
        
        # Return original text if translation fails
        return text
    
    def get_multilingual_chat_response(
        self,
        question: str,
        alert_context: Dict[str, Any],
        language: str = "en",
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate multilingual chat response about security alerts
        
        Args:
            question: User's question
            alert_context: Security alert context
            language: Target language code
            conversation_history: Previous conversation messages
            
        Returns:
            Response in target language
        """
        lang_info = BabelLanguage.from_code(language)
        if not lang_info:
            lang_info = BabelLanguage.ENGLISH
            language = "en"
        
        # Build conversation context
        context = ""
        if conversation_history:
            context += "Previous conversation:\n"
            for msg in conversation_history[-5:]:  # Last 5 messages
                role = msg.get("role", "")
                content = msg.get("content", "")
                context += f"{role}: {content}\n"
            context += "\n"
        
        # Add alert context
        if alert_context:
            context += f"""Current Security Alert:
Rule: {alert_context.get('rule', 'Unknown')}
Priority: {alert_context.get('priority', 'unknown')}
Description: {alert_context.get('output', 'No details available')}

"""
        
        # Language-specific system prompt
        system_prompt = self.language_prompts.get(language, self.language_prompts["en"])
        
        # Build the prompt
        prompt = f"""{system_prompt}

{context}

User Question: {question}

Please provide a helpful response about this security alert in {lang_info.display_name} ({lang_info.flag}). Be professional, clear, and actionable.

Response:"""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.default_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": min(1.0, self.temperature + 0.1),  # Slightly higher temperature for chat
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                chat_response = result.get("response", "").strip()
                
                if chat_response:
                    logger.info(f"💬 Generated multilingual chat response in {lang_info.display_name}")
                    return chat_response
                    
        except Exception as e:
            logger.error(f"❌ Error generating multilingual chat response: {e}")
        
        # Fallback response
        fallback_responses = {
            "en": "I apologize, but I'm having trouble processing your question right now. Please try again or contact support.",
            "es": "Me disculpo, pero estoy teniendo problemas para procesar tu pregunta en este momento. Por favor intenta de nuevo o contacta soporte.",
            "fr": "Je m'excuse, mais j'ai des difficultés à traiter votre question en ce moment. Veuillez réessayer ou contacter le support.",
            "de": "Entschuldigung, aber ich habe Schwierigkeiten, Ihre Frage zu bearbeiten. Bitte versuchen Sie es erneut oder kontaktieren Sie den Support.",
            "pt": "Peço desculpas, mas estou tendo dificuldades para processar sua pergunta. Por favor, tente novamente ou entre em contato com o suporte."
        }
        
        return fallback_responses.get(language, fallback_responses["en"])

# Global instance
babel_llm_service = BabelLLMService()

def get_babel_llm_service() -> BabelLLMService:
    """Get the global Babel LLM service instance"""
    return babel_llm_service 