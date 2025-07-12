import os
import json
import sqlite3
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

def normalize_ai_options(provider_name, options):
    """Normalize AI provider options to use correct parameter names."""
    if provider_name.lower() == "ollama":
        # For Ollama, convert max_tokens to num_predict to avoid warnings
        normalized = options.copy()
        if 'max_tokens' in normalized:
            normalized['num_predict'] = normalized.pop('max_tokens')
        return normalized
    else:
        # For OpenAI and Gemini, use max_tokens as-is
        return options

class SupportedLanguage(Enum):
    """Supported languages in multilingual system"""
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
    def from_code(cls, code: str) -> Optional['SupportedLanguage']:
        """Get language from code"""
        for lang in cls:
            if lang.code == code:
                return lang
        return None

    @classmethod
    def get_supported_languages(cls) -> Dict[str, Dict[str, str]]:
        """Get all supported languages in format for templates"""
        return {
            lang.code: {
                "name": lang.display_name,
                "flag": lang.flag
            }
            for lang in cls
        }

@dataclass
class TranslationResponse:
    """Response from translation service"""
    content: str
    source_language: str
    target_language: str
    confidence: float
    model_used: str
    provider_used: str
    translation_quality: Optional[str] = None

class TranslationProvider:
    """Base class for translation providers"""
    
    def translate(self, text: str, target_language: str, source_language: str = "en") -> str:
        raise NotImplementedError
    
    def is_available(self) -> bool:
        raise NotImplementedError
    
    def get_name(self) -> str:
        raise NotImplementedError

class GoogleTranslateProvider(TranslationProvider):
    """Google Translate provider"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GOOGLE_TRANSLATE_API_KEY")
    
    def translate(self, text: str, target_language: str, source_language: str = "en") -> str:
        if not self.api_key:
            raise Exception("Google Translate API key not configured")
        
        try:
            import requests
            url = f"https://translation.googleapis.com/language/translate/v2?key={self.api_key}"
            
            payload = {
                'q': text,
                'target': target_language,
                'source': source_language,
                'format': 'text'
            }
            
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result['data']['translations'][0]['translatedText']
            
        except Exception as e:
            logger.error(f"Google Translate error: {e}")
            raise Exception(f"Google Translate failed: {str(e)}")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def get_name(self) -> str:
        return "Google Translate"

class DeepLProvider(TranslationProvider):
    """DeepL translation provider"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPL_API_KEY")
    
    def translate(self, text: str, target_language: str, source_language: str = "en") -> str:
        if not self.api_key:
            raise Exception("DeepL API key not configured")
        
        try:
            import requests
            
            # DeepL language code mapping
            deepl_codes = {
                'en': 'EN', 'de': 'DE', 'fr': 'FR', 'it': 'IT', 'ja': 'JA',
                'es': 'ES', 'nl': 'NL', 'pl': 'PL', 'pt': 'PT', 'ru': 'RU',
                'zh': 'ZH', 'bg': 'BG', 'cs': 'CS', 'da': 'DA', 'el': 'EL',
                'et': 'ET', 'fi': 'FI', 'hu': 'HU', 'lv': 'LV', 'lt': 'LT',
                'ro': 'RO', 'sk': 'SK', 'sl': 'SL', 'sv': 'SV'
            }
            
            target_code = deepl_codes.get(target_language, target_language.upper())
            source_code = deepl_codes.get(source_language, source_language.upper())
            
            url = "https://api-free.deepl.com/v2/translate"
            
            payload = {
                'text': text,
                'target_lang': target_code,
                'source_lang': source_code,
                'auth_key': self.api_key
            }
            
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result['translations'][0]['text']
            
        except Exception as e:
            logger.error(f"DeepL translation error: {e}")
            raise Exception(f"DeepL translation failed: {str(e)}")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def get_name(self) -> str:
        return "DeepL"

class AzureTranslatorProvider(TranslationProvider):
    """Azure Translator provider"""
    
    def __init__(self, api_key: str = None, region: str = None):
        self.api_key = api_key or os.getenv("AZURE_TRANSLATOR_API_KEY")
        self.region = region or os.getenv("AZURE_TRANSLATOR_REGION", "global")
    
    def translate(self, text: str, target_language: str, source_language: str = "en") -> str:
        if not self.api_key:
            raise Exception("Azure Translator API key not configured")
        
        try:
            import requests
            import uuid
            
            endpoint = "https://api.cognitive.microsofttranslator.com"
            path = '/translate'
            constructed_url = endpoint + path
            
            params = {
                'api-version': '3.0',
                'from': source_language,
                'to': target_language
            }
            
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key,
                'Ocp-Apim-Subscription-Region': self.region,
                'Content-type': 'application/json',
                'X-ClientTraceId': str(uuid.uuid4())
            }
            
            body = [{'text': text}]
            
            response = requests.post(constructed_url, params=params, headers=headers, json=body, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result[0]['translations'][0]['text']
            
        except Exception as e:
            logger.error(f"Azure Translator error: {e}")
            raise Exception(f"Azure Translator failed: {str(e)}")
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def get_name(self) -> str:
        return "Azure Translator"

class LocalLLMProvider(TranslationProvider):
    """Local LLM translation provider"""
    
    def __init__(self, ollama_url: str = None, model_name: str = None):
        self.ollama_url = ollama_url or os.getenv("OLLAMA_API_URL", "http://ollama:11434")
        if self.ollama_url.endswith("/api/generate"):
            self.ollama_url = self.ollama_url[:-13]
        self.model_name = model_name or "llama3:latest"
    
    def translate(self, text: str, target_language: str, source_language: str = "en") -> str:
        try:
            # Get language info
            target_lang = SupportedLanguage.from_code(target_language)
            target_name = target_lang.display_name if target_lang else target_language
            
            prompt = f"""Translate the following text from {source_language} to {target_name}. 
Provide only the translation, no explanations or additional text.

Text to translate: {text}

Translation:"""
            
            # Normalize options for Ollama
            options = normalize_ai_options("ollama", {
                "temperature": 0.3,
                "top_p": 0.9,
                "max_tokens": 1000
            })
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": options
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                translation = result.get("response", "").strip()
                return translation if translation else text
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Local LLM translation error: {e}")
            return text  # Return original on error
    
    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(self.model_name in model.get("name", "") for model in models)
        except:
            pass
        return False
    
    def get_name(self) -> str:
        return f"Local LLM ({self.model_name})"

class MultilingualService:
    """Dynamic multilingual service for AI translation and analysis"""
    
    def __init__(self):
        # Translation preferences
        self.ui_translation_provider = "google"
        self.ai_analysis_provider = "local"
        
        # Load main AI configuration
        self._load_main_ai_config()
        
        # Initialize translation providers
        self.translation_providers = {
            "google": GoogleTranslateProvider(),
            "deepl": DeepLProvider(),
            "azure": AzureTranslatorProvider(),
            "local": LocalLLMProvider(self.ollama_url, self.model_name)
        }
        
        # Language-specific system prompts
        self.system_prompts = {
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
    
    def _load_main_ai_config(self):
        """Load configuration from main AI config system"""
        try:
            import sqlite3
            DB_PATH = os.getenv("DATABASE_PATH", "data/falco_alerts.db")
            
            # Default values
            self.provider_name = "ollama"
            self.model_name = "llama3:latest"
            self.ollama_url = "http://ollama:11434"
            self.openai_model_name = "gpt-3.5-turbo"
            self.gemini_model_name = "gemini-1.5-flash"
            self.timeout = 60
            self.max_tokens = 500
            self.temperature = 0.7
            self.enabled = True
            
            if os.path.exists(DB_PATH):
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                try:
                    # Read from main AI config table
                    cursor.execute('SELECT setting_name, setting_value FROM ai_config')
                    settings = cursor.fetchall()
                    
                    ai_config = {}
                    for setting_name, setting_value in settings:
                        ai_config[setting_name] = setting_value
                    
                    # Load main AI configuration
                    self.provider_name = ai_config.get('provider_name', self.provider_name).lower()
                    self.enabled = ai_config.get('enabled', 'true').lower() == 'true'
                    
                    # Provider-specific settings
                    if self.provider_name == "ollama":
                        self.ollama_url = ai_config.get('ollama_api_url', 'http://ollama:11434/api/generate')
                        if self.ollama_url.endswith("/api/generate"):
                            self.ollama_url = self.ollama_url[:-13]
                        self.model_name = ai_config.get('ollama_model_name', 'llama3:latest')
                        self.timeout = int(ai_config.get('ollama_timeout', 60))
                    elif self.provider_name == "openai":
                        self.model_name = ai_config.get('openai_model_name', 'gpt-3.5-turbo')
                        self.openai_virtual_key = ai_config.get('openai_virtual_key', '')
                        self.portkey_api_key = ai_config.get('portkey_api_key', '')
                    elif self.provider_name == "gemini":
                        self.model_name = ai_config.get('gemini_model_name', 'gemini-1.5-flash')
                        self.gemini_virtual_key = ai_config.get('gemini_virtual_key', '')
                        self.portkey_api_key = ai_config.get('portkey_api_key', '')
                    
                    # Common settings
                    self.max_tokens = int(ai_config.get('max_tokens', 500))
                    self.temperature = float(ai_config.get('temperature', 0.7))
                    
                    # Check for multilingual-specific overrides (optional)
                    try:
                        cursor.execute('SELECT setting_name, setting_value FROM multilingual_config')
                        multilingual_settings = cursor.fetchall()
                        
                        for setting_name, setting_value in multilingual_settings:
                            if setting_name == 'translation_ui_provider':
                                self.ui_translation_provider = setting_value
                            elif setting_name == 'translation_ai_provider':
                                self.ai_analysis_provider = setting_value
                    except sqlite3.OperationalError:
                        # Multilingual config table doesn't exist - that's okay
                        pass
                    
                    logger.debug(f"📋 Loaded AI config for multilingual: provider={self.provider_name}, model={self.model_name}")
                    
                except sqlite3.OperationalError:
                    logger.debug("📋 AI config table not found, using defaults")
                finally:
                    conn.close()
            else:
                logger.debug("📋 Database file not found, using defaults")
                
        except Exception as e:
            logger.warning(f"⚠️ Error loading AI config: {e}")
    
    def reload_config(self):
        """Reload configuration from database"""
        self._load_main_ai_config()
        # Reinitialize local provider with new config
        self.translation_providers["local"] = LocalLLMProvider(self.ollama_url, self.model_name)
    
    def is_available(self) -> bool:
        """Check if AI translation model is available"""
        if not self.enabled:
            return False
        
        # For OpenAI/Gemini providers, assume available if keys are set
        if self.provider_name in ["openai", "gemini"]:
            return bool(getattr(self, f'{self.provider_name}_virtual_key', '') and 
                       getattr(self, 'portkey_api_key', ''))
        
        # For Ollama, check if model is available
        if self.provider_name == "ollama":
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [model.get("name", "") for model in models]
                    return any(self.model_name in name for name in model_names)
            except Exception as e:
                logger.warning(f"Failed to check Ollama model availability: {e}")
        
        return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available AI models"""
        if self.provider_name == "ollama":
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    ai_models = []
                    for model in models:
                        name = model.get("name", "")
                        if any(x in name for x in ["llama3", "qwen2", "gemma", "phi", "mistral"]):
                            ai_models.append(name)
                    return ai_models
            except Exception as e:
                logger.error(f"Failed to get available Ollama models: {e}")
                
        elif self.provider_name == "openai":
            return ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]
        elif self.provider_name == "gemini":
            return ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
            
        return []
    
    def get_available_translation_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get available translation providers with their status"""
        providers = {}
        for name, provider in self.translation_providers.items():
            providers[name] = {
                "name": provider.get_name(),
                "available": provider.is_available(),
                "type": "cloud" if name != "local" else "local"
            }
        return providers
    
    def get_best_translation_provider(self, use_case: str = "ui") -> TranslationProvider:
        """Get the best available translation provider for the use case"""
        if use_case == "ui":
            preferred_order = [self.ui_translation_provider, "google", "deepl", "azure", "local"]
        else:
            preferred_order = [self.ai_analysis_provider, "local", "google", "deepl", "azure"]
        
        for provider_name in preferred_order:
            if provider_name in self.translation_providers:
                provider = self.translation_providers[provider_name]
                if provider.is_available():
                    return provider
        
        # Fallback to local provider
        return self.translation_providers["local"]
    
    def pull_model(self, model_name: str = None) -> bool:
        """Pull AI model via Ollama (only works for Ollama provider)"""
        if self.provider_name != "ollama":
            logger.warning(f"Model pulling not supported for provider: {self.provider_name}")
            return False
            
        if not model_name:
            model_name = self.model_name
        
        try:
            logger.info(f"🌍 Pulling Ollama model: {model_name}")
            response = requests.post(
                f"{self.ollama_url}/api/pull",
                json={"name": model_name},
                timeout=1800  # 30 minutes timeout
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully pulled Ollama model: {model_name}")
                return True
            else:
                logger.error(f"❌ Failed to pull Ollama model: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error pulling Ollama model: {e}")
            return False
    
    def analyze_security_alert_multilingual(
        self,
        alert_payload: Dict[str, Any],
        target_language: str = "en",
        model_name: str = None
    ) -> TranslationResponse:
        """Analyze security alert in specified language using configured AI provider"""
        if not model_name:
            model_name = self.model_name
        
        # Get language info
        language = SupportedLanguage.from_code(target_language)
        if not language:
            logger.warning(f"Unsupported language: {target_language}, falling back to English")
            language = SupportedLanguage.ENGLISH
            target_language = "en"
        
        # Get language-specific system prompt
        system_prompt = self.system_prompts.get(target_language, self.system_prompts["en"])
        
        # Prepare alert context
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
        
        try:
            logger.info(f"🌍 Analyzing security alert in {language.display_name} using {self.provider_name}: {model_name}")
            
            # Use the configured AI provider
            if self.provider_name == "openai":
                analysis = self._call_openai_analysis(system_prompt, alert_context, language_instruction, model_name)
            elif self.provider_name == "gemini":
                analysis = self._call_gemini_analysis(system_prompt, alert_context, language_instruction, model_name)
            elif self.provider_name == "ollama":
                analysis = self._call_ollama_analysis(system_prompt, alert_context, language_instruction, model_name)
            else:
                raise Exception(f"Unsupported AI provider: {self.provider_name}")
                
            if analysis:
                logger.info(f"✅ Generated multilingual analysis in {language.display_name}")
                return TranslationResponse(
                    content=analysis,
                    source_language="en",
                    target_language=target_language,
                    confidence=0.9,
                    model_used=model_name,
                    provider_used=self.provider_name,
                    translation_quality="native"
                )
            else:
                raise Exception("Empty response from AI model")
                
        except Exception as e:
            logger.error(f"❌ Error in multilingual analysis: {e}")
            
            # Fallback to English analysis
            if target_language != "en":
                logger.info("🔄 Falling back to English analysis")
                return self.analyze_security_alert_multilingual(alert_payload, "en", model_name)
            else:
                # Return error response
                return TranslationResponse(
                    content=f"Error analyzing security alert: {str(e)}",
                    source_language="en",
                    target_language=target_language,
                    confidence=0.0,
                    model_used=model_name,
                    provider_used=self.provider_name,
                    translation_quality="error"
                )
    
    def _call_openai_analysis(self, system_prompt: str, alert_context: str, language_instruction: str, model_name: str) -> str:
        """Call OpenAI API via Portkey for analysis"""
        try:
            import requests
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{alert_context}\n\n{language_instruction}"}
            ]
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.portkey_api_key}",
                "x-portkey-virtual-key": self.openai_virtual_key
            }
            
            payload = {
                "model": model_name,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            response = requests.post(
                "https://api.portkey.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"OpenAI analysis error: {e}")
            raise e
    
    def _call_gemini_analysis(self, system_prompt: str, alert_context: str, language_instruction: str, model_name: str) -> str:
        """Call Gemini API via Portkey for analysis"""
        try:
            import requests
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{alert_context}\n\n{language_instruction}"}
            ]
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.portkey_api_key}",
                "x-portkey-virtual-key": self.gemini_virtual_key
            }
            
            payload = {
                "model": model_name,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            response = requests.post(
                "https://api.portkey.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise Exception(f"Gemini API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Gemini analysis error: {e}")
            raise e
    
    def _call_ollama_analysis(self, system_prompt: str, alert_context: str, language_instruction: str, model_name: str) -> str:
        """Call Ollama for analysis"""
        try:
            import requests
            
            prompt = f"{system_prompt}\n\n{alert_context}\n\n{language_instruction}"
            
            # Normalize options for Ollama
            options = normalize_ai_options("ollama", {
                "temperature": self.temperature,
                "top_p": 0.9,
                "max_tokens": self.max_tokens,
                "stop": ["Human:", "Assistant:"]
            })
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": options
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Ollama analysis error: {e}")
            raise e
    
    def translate_ui_string(self, text: str, target_language: str, provider: str = None) -> str:
        """Translate UI strings using the best available provider"""
        if target_language == "en":
            return text
        
        # Get the best provider for UI translation
        if provider and provider in self.translation_providers:
            translation_provider = self.translation_providers[provider]
        else:
            translation_provider = self.get_best_translation_provider("ui")
        
        try:
            translated = translation_provider.translate(text, target_language, "en")
            if translated and translated != text:
                logger.debug(f"🌍 UI Translation ({translation_provider.get_name()}): '{text}' → '{translated}' ({target_language})")
                return translated
        except Exception as e:
            logger.warning(f"UI translation failed with {translation_provider.get_name()}: {e}")
            
            # Fallback to local provider if cloud provider fails
            if translation_provider != self.translation_providers["local"]:
                try:
                    translated = self.translation_providers["local"].translate(text, target_language, "en")
                    if translated and translated != text:
                        logger.debug(f"🌍 UI Translation (Local Fallback): '{text}' → '{translated}' ({target_language})")
                        return translated
                except Exception as fallback_error:
                    logger.warning(f"Local fallback translation also failed: {fallback_error}")
        
        return text

    def translate_ui_batch(self, batch_prompt: str, target_language: str) -> str:
        """Translate multiple UI strings in a single batch request"""
        if target_language == "en":
            return batch_prompt
        
        # Only use batch translation for Ollama (local provider)
        if self.provider_name != "ollama":
            logger.warning("Batch translation only supported for Ollama provider")
            return batch_prompt
            
        try:
            logger.info(f"🌍 Batch translating UI strings to {target_language}")
            
            # Normalize options for Ollama
            options = normalize_ai_options("ollama", {
                "temperature": 0.3,  # Lower temperature for consistent translations
                "top_p": 0.9,
                "max_tokens": 1000  # Optimized for smaller batch translations
            })
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": batch_prompt,
                    "stream": False,
                    "options": options
                },
                timeout=min(30, self.timeout)  # Shorter timeout for batch operations
            )
            
            if response.status_code == 200:
                result = response.json()
                batch_translation = result.get("response", "").strip()
                
                if batch_translation:
                    logger.info(f"✅ Batch translation completed for {target_language}")
                    return batch_translation
                else:
                    raise Exception("Empty response from AI model")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error in batch translation: {e}")
            raise e
    
    def get_multilingual_chat_response(
        self,
        question: str,
        alert_context: Dict[str, Any],
        language: str = "en",
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """Generate multilingual chat response about security alerts"""
        lang_info = SupportedLanguage.from_code(language)
        if not lang_info:
            lang_info = SupportedLanguage.ENGLISH
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
        system_prompt = self.system_prompts.get(language, self.system_prompts["en"])
        
        # Build the prompt
        prompt = f"""{system_prompt}

{context}

User Question: {question}

Please provide a helpful response about this security alert in {lang_info.display_name} ({lang_info.flag}). Be professional, clear, and actionable.

Response:"""
        
        try:
            # Use the configured AI provider for chat response
            if self.provider_name == "openai":
                chat_response = self._call_openai_chat(prompt)
            elif self.provider_name == "gemini":
                chat_response = self._call_gemini_chat(prompt)
            elif self.provider_name == "ollama":
                chat_response = self._call_ollama_chat(prompt)
            else:
                raise Exception(f"Unsupported provider: {self.provider_name}")
                
            if chat_response:
                logger.info(f"💬 Generated multilingual chat response in {lang_info.display_name}")
                return chat_response
                    
        except Exception as e:
            logger.error(f"❌ Error generating multilingual chat response: {e}")
        
    def _call_openai_chat(self, prompt: str) -> str:
        """Call OpenAI for chat response"""
        try:
            import requests
            
            messages = [{"role": "user", "content": prompt}]
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.portkey_api_key}",
                "x-portkey-virtual-key": self.openai_virtual_key
            }
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 500,
                "temperature": min(1.0, self.temperature + 0.1)
            }
            
            response = requests.post(
                "https://api.portkey.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise e
    
    def _call_gemini_chat(self, prompt: str) -> str:
        """Call Gemini for chat response"""
        try:
            import requests
            
            messages = [{"role": "user", "content": prompt}]
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.portkey_api_key}",
                "x-portkey-virtual-key": self.gemini_virtual_key
            }
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 500,
                "temperature": min(1.0, self.temperature + 0.1)
            }
            
            response = requests.post(
                "https://api.portkey.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                raise Exception(f"Gemini API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            raise e
    
    def _call_ollama_chat(self, prompt: str) -> str:
        """Call Ollama for chat response"""
        try:
            import requests
            
            # Normalize options for Ollama
            options = normalize_ai_options("ollama", {
                "temperature": min(1.0, self.temperature + 0.1),
                "top_p": 0.9,
                "max_tokens": 500
            })
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": options
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise e

        # Fallback response
        fallback_responses = {
            "en": "I apologize, but I'm having trouble processing your question right now. Please try again or contact support.",
            "es": "Me disculpo, pero estoy teniendo problemas para procesar tu pregunta en este momento. Por favor intenta de nuevo o contacta soporte.",
            "fr": "Je m'excuse, mais j'ai des difficultés à traiter votre question en ce moment. Veuillez réessayer ou contacter le support.",
            "de": "Entschuldigung, aber ich habe Schwierigkeiten, Ihre Frage zu bearbeiten. Bitte versuchen Sie es erneut oder kontaktieren Sie den Support.",
            "pt": "Peço desculpas, mas estou tendo dificuldades para processar sua pergunta. Por favor, tente novamente ou entre em contato com o suporte."
        }
        
        return fallback_responses.get(language, fallback_responses["en"])

# Global service instance
multilingual_service = MultilingualService()

def get_multilingual_service() -> MultilingualService:
    """Get the global multilingual service instance"""
    return multilingual_service

# Legacy compatibility function
def get_multilingual_service() -> MultilingualService:
    """Legacy compatibility function - returns multilingual service"""
    return multilingual_service 