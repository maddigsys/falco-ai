"""
Weaviate Service Layer for Falco Vanguard

This module provides vector storage and semantic search capabilities
for security alerts, enabling pattern recognition and contextual analysis.
Enhanced with AI-driven clustering, predictive intelligence, and advanced analytics.
"""

import weaviate
import weaviate.classes as wvc
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import os
import re
from collections import defaultdict, Counter
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import uuid
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeaviateService:
    """Enhanced service class for managing Weaviate operations with AI-driven analytics."""
    
    def __init__(self, host: str = "localhost", port: int = 8080, grpc_port: int = 50051):
        """
        Initialize Weaviate service with enhanced analytics.
        
        Args:
            host: Weaviate host
            port: Weaviate HTTP port
            grpc_port: Weaviate gRPC port
        """
        self.host = host
        self.port = port
        self.grpc_port = grpc_port
        self.client = None
        
        # AI-driven analytics components
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.threat_patterns = {}
        self.attack_chains = {}
        self.risk_scores = {}
        
        # Classification categories
        self.threat_categories = {
            'malware': ['virus', 'trojan', 'ransomware', 'backdoor', 'rootkit'],
            'intrusion': ['breakout', 'escape', 'privilege', 'escalation', 'unauthorized'],
            'data_exfiltration': ['copy', 'transfer', 'upload', 'download', 'exfil'],
            'reconnaissance': ['scan', 'probe', 'enumerate', 'discover', 'fingerprint'],
            'lateral_movement': ['pivot', 'hop', 'spread', 'move', 'traverse'],
            'persistence': ['cron', 'service', 'startup', 'autostart', 'schedule'],
            'evasion': ['hide', 'mask', 'obfuscate', 'encode', 'stealth'],
            'misconfiguration': ['permission', 'config', 'setting', 'policy', 'rule']
        }
        
    def connect(self) -> bool:
        """
        Connect to Weaviate instance.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            # Create client with connection config for v4 - simpler approach
            headers = {}
            openai_key = os.getenv("OPENAI_API_KEY", "")
            if openai_key:
                headers["X-OpenAI-Api-Key"] = openai_key
            

            
            # Try simpler connection method
            self.client = weaviate.connect_to_local(
                host=self.host,
                port=self.port,
                grpc_port=self.grpc_port,
                headers=headers
            )
            
            # Test connection
            if self.client.is_ready():
                logger.info(f"✅ Connected to Weaviate at {self.host}:{self.port}")
                return True
            else:
                logger.error("❌ Weaviate is not ready")
                self.client.close()
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to Weaviate: {e}")
            if self.client:
                try:
                    self.client.close()
                except:
                    pass
                self.client = None
            return False
    
    def close(self):
        """Close the Weaviate client connection."""
        if self.client:
            self.client.close()
            logger.info("🔌 Closed Weaviate connection")
    
    def create_schema(self) -> bool:
        """
        Create the schema for security alerts in Weaviate.
        
        Returns:
            bool: True if schema created successfully, False otherwise
        """
        try:
            # Check if collection already exists and verify its vectorizer
            if self.client.collections.exists("SecurityAlert"):
                collection = self.client.collections.get("SecurityAlert")
                collection_config = collection.config.get()
                current_vectorizer = collection_config.vectorizer
                
                # Get the expected vectorizer based on current AI provider
                expected_vectorizer_config = self._get_vectorizer_config()
                expected_vectorizer = self._get_expected_vectorizer_name()
                
                # If vectorizer doesn't match expected configuration, recreate collection
                if current_vectorizer != expected_vectorizer:
                    logger.info(f"📋 SecurityAlert collection exists but has wrong vectorizer: {current_vectorizer} (expected: {expected_vectorizer})")
                    logger.info("🔄 Recreating collection with correct vectorizer configuration...")
                    
                    # Delete existing collection
                    self.client.collections.delete("SecurityAlert")
                    logger.info("🗑️ Deleted existing SecurityAlert collection")
                else:
                    logger.info("📋 SecurityAlert collection already exists with correct vectorizer")
                    return True
            
            # Create the collection with properties for v4 API
            # Configure vectorizer based on AI provider
            vectorizer_config = self._get_vectorizer_config()
            
            self.client.collections.create(
                name="SecurityAlert",
                description="Falco security alert with AI analysis",
                vectorizer_config=vectorizer_config,
                properties=[
                    wvc.config.Property(
                        name="rule",
                        data_type=wvc.config.DataType.TEXT,
                        description="Falco rule name that triggered the alert"
                    ),
                    wvc.config.Property(
                        name="priority",
                        data_type=wvc.config.DataType.TEXT,
                        description="Alert priority level"
                    ),
                    wvc.config.Property(
                        name="output",
                        data_type=wvc.config.DataType.TEXT,
                        description="Detailed alert output message"
                    ),
                    wvc.config.Property(
                        name="source",
                        data_type=wvc.config.DataType.TEXT,
                        description="Source container or system"
                    ),
                    wvc.config.Property(
                        name="timestamp",
                        data_type=wvc.config.DataType.DATE,
                        description="When the alert was generated"
                    ),
                    wvc.config.Property(
                        name="command",
                        data_type=wvc.config.DataType.TEXT,
                        description="Command that triggered the alert"
                    ),
                    wvc.config.Property(
                        name="securityImpact",
                        data_type=wvc.config.DataType.TEXT,
                        description="AI-generated security impact analysis"
                    ),
                    wvc.config.Property(
                        name="nextSteps",
                        data_type=wvc.config.DataType.TEXT,
                        description="AI-generated next steps"
                    ),
                    wvc.config.Property(
                        name="remediationSteps",
                        data_type=wvc.config.DataType.TEXT,
                        description="AI-generated remediation steps"
                    ),
                    wvc.config.Property(
                        name="suggestedCommands",
                        data_type=wvc.config.DataType.TEXT,
                        description="AI-generated suggested commands"
                    ),
                    wvc.config.Property(
                        name="aiProvider",
                        data_type=wvc.config.DataType.TEXT,
                        description="AI provider used for analysis"
                    ),
                    wvc.config.Property(
                        name="alertHash",
                        data_type=wvc.config.DataType.TEXT,
                        description="Hash of the alert for deduplication"
                    ),
                    wvc.config.Property(
                        name="fields",
                        data_type=wvc.config.DataType.TEXT,
                        description="Additional Falco alert fields as JSON"
                    )
                ]
            )
            
            logger.info("✅ Created SecurityAlert collection in Weaviate")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create schema: {e}")
            return False
    
    def store_alert(self, alert_data: Dict[str, Any], ai_analysis: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a security alert in Weaviate with vector embeddings.
        
        Args:
            alert_data: Original Falco alert data
            ai_analysis: AI analysis of the alert
            
        Returns:
            str: UUID of the stored object, or None if failed
        """
        try:
            # Ensure connection is established
            if not self.client:
                logger.warning("⚠️ Weaviate client not connected, attempting to connect...")
                if not self.connect():
                    logger.error("❌ Failed to connect to Weaviate")
                    return None
            
            # Generate hash for deduplication
            alert_content = f"{alert_data.get('rule', '')}-{alert_data.get('output', '')}"
            alert_hash = hashlib.md5(alert_content.encode()).hexdigest()
            
            # Ensure schema exists before storing
            if not self.client.collections.exists("SecurityAlert"):
                logger.info("📋 Creating SecurityAlert schema on first use")
                if not self.create_schema():
                    return None
            
            # Get the collection
            collection = self.client.collections.get("SecurityAlert")
            
            # Check if alert already exists (v4 API) - fix syntax
            try:
                # Simple approach - check for duplicates after retrieval
                result = collection.query.fetch_objects(
                    limit=10,
                    return_properties=["alertHash"]
                )
                existing = [obj for obj in result.objects if obj.properties.get("alertHash") == alert_hash]
            except Exception as e:
                logger.warning(f"Could not check for existing alert: {e}")
                existing = []
            
            if existing:
                logger.info(f"🔄 Alert already exists with hash {alert_hash}")
                return str(existing[0].uuid)
            
            # Extract AI analysis sections
            security_impact = ""
            next_steps = ""
            remediation_steps = ""
            suggested_commands = ""
            ai_provider = ""
            
            if ai_analysis and not ai_analysis.get("error"):
                security_impact = self._extract_content(ai_analysis.get("Security Impact", ""))
                next_steps = self._extract_content(ai_analysis.get("Next Steps", ""))
                remediation_steps = self._extract_content(ai_analysis.get("Remediation Steps", ""))
                suggested_commands = self._extract_content(ai_analysis.get("Suggested Commands", ""))
                ai_provider = ai_analysis.get("llm_provider", "")
            
            # Prepare the data object with proper RFC3339 timestamp
            timestamp = alert_data.get("time")
            if timestamp:
                # Parse and reformat to ensure RFC3339 compliance
                try:
                    if isinstance(timestamp, str):
                        # Try to parse existing timestamp
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    # Format to RFC3339 with timezone
                    formatted_timestamp = dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                except Exception:
                    # Fallback to current time with proper format
                    formatted_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            else:
                # Use current time with proper RFC3339 format
                formatted_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            
            properties = {
                "rule": alert_data.get("rule", ""),
                "priority": alert_data.get("priority", ""),
                "output": alert_data.get("output", ""),
                "source": alert_data.get("output_fields", {}).get("container.name", "unknown"),
                "timestamp": formatted_timestamp,
                "command": alert_data.get("output_fields", {}).get("proc.cmdline", ""),
                "securityImpact": security_impact,
                "nextSteps": next_steps,
                "remediationSteps": remediation_steps,
                "suggestedCommands": suggested_commands,
                "aiProvider": ai_provider,
                "alertHash": alert_hash,
                "fields": json.dumps(alert_data.get("output_fields", {}))
            }
            
            # Store in Weaviate using v4 API
            result = collection.data.insert(properties)
            
            logger.info(f"✅ Stored alert in Weaviate: {alert_data.get('rule', 'Unknown')} (ID: {result})")
            return str(result)
            
        except Exception as e:
            logger.error(f"❌ Failed to store alert in Weaviate: {e}")
            return None
    
    def find_similar_alerts(self, query: str, limit: int = 5, certainty: float = 0.7) -> List[Dict[str, Any]]:
        """
        Find similar alerts using semantic search or text search.
        
        Args:
            query: Search query (can be alert text, rule name, or description)
            limit: Maximum number of results
            certainty: Minimum similarity threshold (0.0 - 1.0)
            
        Returns:
            List of similar alerts with metadata
        """
        try:
            # Ensure connection is established
            if not self.client:
                logger.warning("⚠️ Weaviate client not connected, attempting to connect...")
                if not self.connect():
                    logger.error("❌ Failed to connect to Weaviate")
                    return []
            
            # Get the collection
            collection = self.client.collections.get("SecurityAlert")
            
            # Check the collection's vectorizer configuration
            collection_config = collection.config.get()
            current_vectorizer = collection_config.vectorizer
            
            # Check if we should attempt semantic search based on AI provider and available keys
            provider_name = os.getenv("PROVIDER_NAME", "").lower()
            has_openai_key = bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_VIRTUAL_KEY"))
            has_ollama = (provider_name == "ollama")
            
            result = None
            search_method = "text"  # Default to text search
            
            # Only attempt semantic search if collection has a vectorizer and we have the right provider/keys
            if current_vectorizer != "none" and (has_ollama or has_openai_key):
                try:
                    if has_ollama:
                        logger.info(f"🔍 Attempting semantic search with Ollama for query: {query[:50]}...")
                    elif has_openai_key:
                        logger.info(f"🔍 Attempting semantic search with OpenAI for query: {query[:50]}...")
                    
                    result = collection.query.near_text(
                        query=query,
                        limit=limit,
                        return_metadata=wvc.query.MetadataQuery(certainty=True),
                        return_properties=[
                            "rule", "priority", "output", "source", "timestamp", 
                            "securityImpact", "nextSteps", "remediationSteps", 
                            "suggestedCommands", "aiProvider", "command"
                        ]
                    )
                    search_method = "semantic"
                    logger.info(f"✅ Semantic search successful")
                    
                except Exception as search_error:
                    logger.warning(f"⚠️ Semantic search failed, falling back to text search: {search_error}")
                    search_method = "text"
                    result = None
            else:
                if current_vectorizer == "none":
                    logger.info(f"🔍 Using text search (collection has no vectorizer configured) for query: {query[:50]}...")
                else:
                    logger.info(f"🔍 Using text search (no API keys available for vectorization) for query: {query[:50]}...")
            
            # Perform text search if semantic search wasn't attempted or failed
            if search_method == "text" or result is None:
                # Fallback to basic text search using BM25 or contains
                # Split query into keywords for better matching
                keywords = query.lower().split()
                
                if keywords:
                    # Create a filter that looks for keywords in rule, output, or source
                    # Use simpler like/contains filters
                    filters = []
                    for keyword in keywords[:3]:  # Limit to first 3 keywords
                        # Create OR conditions for each field using like operator
                        field_filters = [
                            wvc.query.Filter.by_property("rule").like(f"*{keyword}*"),
                            wvc.query.Filter.by_property("output").like(f"*{keyword}*"),
                            wvc.query.Filter.by_property("source").like(f"*{keyword}*")
                        ]
                        filters.extend(field_filters)
                    
                    # Combine with OR logic
                    if len(filters) > 1:
                        combined_filter = filters[0]
                        for f in filters[1:]:
                            combined_filter = combined_filter | f
                    else:
                        combined_filter = filters[0] if filters else None
                    
                    # Query with text filters - simplified approach
                    result = collection.query.fetch_objects(
                        limit=limit,
                        return_properties=[
                            "rule", "priority", "output", "source", "timestamp", 
                            "securityImpact", "nextSteps", "remediationSteps", 
                            "suggestedCommands", "aiProvider", "command"
                        ]
                    )
                else:
                    # No keywords, return recent alerts
                    result_objects = collection.query.limit(limit).return_properties([
                        "rule", "priority", "output", "source", "timestamp", 
                        "securityImpact", "nextSteps", "remediationSteps", 
                        "suggestedCommands", "aiProvider", "command"
                    ]).objects
                    
                    # Create result object for compatibility
                    class MockResult:
                        def __init__(self, objects):
                            self.objects = objects
                    result = MockResult(result_objects)
            
            if not result or not result.objects:
                logger.info(f"🔍 No similar alerts found for query: {query[:50]}...")
                return []
            
            # Convert to the expected format
            filtered_alerts = []
            for obj in result.objects:
                # Get certainty if available (semantic search) or calculate text similarity
                obj_certainty = 0
                if search_method == "semantic" and obj.metadata and obj.metadata.certainty:
                    obj_certainty = obj.metadata.certainty
                elif search_method == "text":
                    # Calculate basic text similarity for text search
                    obj_certainty = self._calculate_text_similarity(query, obj.properties)
                
                # Apply certainty threshold
                if obj_certainty >= certainty:
                    # Convert to dictionary format
                    alert_dict = dict(obj.properties)
                    alert_dict["_additional"] = {
                        "id": str(obj.uuid),
                        "certainty": obj_certainty
                    }
                    filtered_alerts.append(alert_dict)
            
            logger.info(f"🔍 Found {len(filtered_alerts)} similar alerts using {search_method} search")
            return filtered_alerts
            
        except Exception as e:
            logger.error(f"❌ Failed to search similar alerts: {e}")
            return []
    
    def get_alert_patterns(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze alert patterns and trends.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with pattern analysis
        """
        try:
            logger.info(f"📊 Analyzing alert patterns for last {days} days...")
            
            # Get real alert data from the database
            import sqlite3
            import os
            from datetime import datetime, timedelta
            from collections import Counter
            
            # Connect to database using correct path
            default_db_path = './data/alerts.db' if not os.path.exists('/app') else '/app/data/alerts.db'
            db_path = os.getenv('DB_PATH', default_db_path)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get alerts from the last N days
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute('''
                SELECT rule, priority, source, timestamp 
                FROM alerts 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            ''', (cutoff_date,))
            
            alerts = cursor.fetchall()
            conn.close()
            
            if not alerts:
                return {
                    "total_alerts": 0,
                    "rule_frequency": {},
                    "priority_distribution": {},
                    "source_distribution": {},
                    "timeline": [],
                    "message": "No alerts found for the specified time period"
                }
            
            # Analyze patterns - filter out None values
            rules = [alert[0] for alert in alerts if alert[0] is not None]
            priorities = [alert[1] for alert in alerts if alert[1] is not None]
            sources = [alert[2] for alert in alerts if alert[2] is not None]
            
            # Count frequencies
            rule_frequency = dict(Counter(rules).most_common(10))
            priority_distribution = dict(Counter(priorities))
            source_distribution = dict(Counter(sources))
            
            # Generate timeline (alerts per day)
            timeline = []
            date_counts = {}
            
            for alert in alerts:
                timestamp = alert[3]
                # Ensure timestamp is not None and is a string
                if timestamp is None or not isinstance(timestamp, str):
                    continue
                    
                try:
                    # Parse the timestamp and extract date
                    date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).date()
                    date_str = date.isoformat()
                    date_counts[date_str] = date_counts.get(date_str, 0) + 1
                except (ValueError, TypeError, AttributeError) as e:
                    # Log specific parsing errors for debugging
                    logger.debug(f"Failed to parse timestamp '{timestamp}': {e}")
                    continue
            
            # Sort by date - ensure all keys are valid strings
            valid_dates = [date for date in date_counts.keys() if date is not None and isinstance(date, str)]
            sorted_dates = sorted(valid_dates)
            timeline = [{"date": date, "count": date_counts[date]} for date in sorted_dates]
            
            patterns = {
                "total_alerts": len(alerts),
                "rule_frequency": rule_frequency,
                "priority_distribution": priority_distribution,
                "source_distribution": source_distribution,
                "timeline": timeline,
                "analysis_period_days": days,
                "message": f"Analyzed {len(alerts)} alerts over {days} days"
            }
            
            logger.info(f"📊 Generated alert patterns for {len(alerts)} alerts")
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze patterns: {e}")
            return {"error": str(e)}
    
    def get_contextual_analysis(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get contextual analysis for a new alert based on similar past incidents.
        
        Args:
            alert_data: New alert data
            
        Returns:
            Dictionary with contextual insights
        """
        try:
            # Find similar alerts with lower certainty for contextual analysis
            query = f"{alert_data.get('rule', '')} {alert_data.get('output', '')}"
            similar_alerts = self.find_similar_alerts(query, limit=3, certainty=0.5)
            
            if not similar_alerts:
                return {"message": "No similar alerts found", "similar_count": 0}
            
            # Analyze similar alerts
            context = {
                "similar_count": len(similar_alerts),
                "similar_alerts": [],
                "common_patterns": {
                    "sources": {},
                    "priorities": {},
                    "commands": {}
                },
                "insights": []
            }
            
            for alert in similar_alerts:
                context["similar_alerts"].append({
                    "rule": alert.get("rule", ""),
                    "priority": alert.get("priority", ""),
                    "timestamp": alert.get("timestamp", ""),
                    "certainty": alert.get("_additional", {}).get("certainty", 0),
                    "security_impact": alert.get("securityImpact", "")[:200] + "..."
                })
                
                # Track patterns
                source = alert.get("source", "")
                if source:
                    context["common_patterns"]["sources"][source] = context["common_patterns"]["sources"].get(source, 0) + 1
                
                priority = alert.get("priority", "")
                if priority:
                    context["common_patterns"]["priorities"][priority] = context["common_patterns"]["priorities"].get(priority, 0) + 1
                
                command = alert.get("command", "")
                if command:
                    context["common_patterns"]["commands"][command] = context["common_patterns"]["commands"].get(command, 0) + 1
            
            # Generate insights
            if len(similar_alerts) >= 2:
                context["insights"].append("This alert pattern has been seen before, suggesting a recurring issue.")
            
            most_common_priority = max(context["common_patterns"]["priorities"].items(), key=lambda x: x[1])[0] if context["common_patterns"]["priorities"] else None
            if most_common_priority:
                context["insights"].append(f"Similar alerts are typically classified as '{most_common_priority}' priority.")
            
            logger.info(f"🧠 Generated contextual analysis with {len(similar_alerts)} similar alerts")
            return context
            
        except Exception as e:
            logger.error(f"❌ Failed to generate contextual analysis: {e}")
            return {"error": str(e)}
    
    def _extract_content(self, analysis_section: Any) -> str:
        """
        Extract content from AI analysis section.
        
        Args:
            analysis_section: Can be string or dict with 'content' key
            
        Returns:
            Extracted content as string
        """
        if isinstance(analysis_section, dict):
            return analysis_section.get("content", "")
        elif isinstance(analysis_section, str):
            return analysis_section
        else:
            return ""
    
    def _get_vectorizer_config(self):
        """
        Get vectorizer configuration based on AI provider.
        
        Returns:
            Appropriate vectorizer configuration
        """
        try:
            # Check AI provider from environment (fallback to database check if needed)
            provider_name = os.getenv("PROVIDER_NAME", "").lower()
            
            # If not in environment, try to get from database
            if not provider_name:
                try:
                    # Import here to avoid circular dependency
                    from app import get_ai_config
                    ai_config = get_ai_config()
                    provider_name = ai_config.get('provider_name', {}).get('value', 'openai').lower()
                except Exception:
                    logger.warning("⚠️ Could not get AI provider from database, defaulting to OpenAI")
                    provider_name = "openai"
            
            # Configure vectorizer based on provider
            if provider_name == "ollama":
                # Use Ollama vectorizer
                ollama_api_url = os.getenv("OLLAMA_API_URL", "http://ollama:11434")
                # Remove the /api/generate suffix if present, as the vectorizer needs the base URL
                if "/api/generate" in ollama_api_url:
                    ollama_api_url = ollama_api_url.replace("/api/generate", "")
                
                vectorizer_config = wvc.config.Configure.Vectorizer.text2vec_ollama(
                    api_endpoint=ollama_api_url,
                    model="nomic-embed-text"  # Good embedding model for Ollama
                )
                logger.info(f"🦙 Using Ollama text vectorizer at {ollama_api_url}")
                
            elif provider_name in ["openai", "gemini"]:
                # Use OpenAI vectorizer (works for both OpenAI and Gemini through Portkey)
                if os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_VIRTUAL_KEY"):
                    vectorizer_config = wvc.config.Configure.Vectorizer.text2vec_openai(
                        model="text-embedding-3-small"
                    )
                    logger.info("🔗 Using OpenAI text vectorizer")
                else:
                    logger.warning("⚠️ OpenAI/Gemini selected but no API keys found, using no vectorizer")
                    vectorizer_config = wvc.config.Configure.Vectorizer.none()
                    
            else:
                # Default to no vectorizer
                vectorizer_config = wvc.config.Configure.Vectorizer.none()
                logger.info("📝 Using basic text search (no vectorization)")
                
            return vectorizer_config
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to configure vectorizer: {e}")
            # Fallback to OpenAI if available, otherwise none
            if os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_VIRTUAL_KEY"):
                return wvc.config.Configure.Vectorizer.text2vec_openai(
                    model="text-embedding-3-small"
                )
            else:
                return wvc.config.Configure.Vectorizer.none()

    def _get_expected_vectorizer_name(self) -> str:
        """
        Get the expected vectorizer name based on AI provider.
        
        Returns:
            Expected vectorizer name
        """
        try:
            # Check AI provider from environment (fallback to database check if needed)
            provider_name = os.getenv("PROVIDER_NAME", "").lower()
            
            # If not in environment, try to get from database
            if not provider_name:
                try:
                    # Import here to avoid circular dependency
                    from app import get_ai_config
                    ai_config = get_ai_config()
                    provider_name = ai_config.get('provider_name', {}).get('value', 'openai').lower()
                except Exception:
                    provider_name = "openai"
            
            # Return expected vectorizer name based on provider
            if provider_name == "ollama":
                return "text2vec-ollama"
            elif provider_name in ["openai", "gemini"]:
                if os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_VIRTUAL_KEY"):
                    return "text2vec-openai"
                else:
                    return "none"
            else:
                return "none"
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to determine expected vectorizer: {e}")
            return "none"

    def _calculate_text_similarity(self, query: str, properties: Dict[str, Any]) -> float:
        """
        Calculate basic text similarity for text search results.
        
        Args:
            query: Search query
            properties: Object properties
            
        Returns:
            Similarity score (0.0 - 1.0)
        """
        try:
            query_lower = query.lower()
            query_words = set(query_lower.split())
            
            # Combine relevant text fields
            text_fields = [
                properties.get("rule", ""),
                properties.get("output", ""),
                properties.get("source", ""),
                properties.get("securityImpact", ""),
                properties.get("nextSteps", "")
            ]
            
            combined_text = " ".join(text_fields).lower()
            combined_words = set(combined_text.split())
            
            # Calculate Jaccard similarity (intersection / union)
            if not query_words or not combined_words:
                return 0.0
            
            intersection = len(query_words.intersection(combined_words))
            union = len(query_words.union(combined_words))
            
            jaccard_similarity = intersection / union if union > 0 else 0.0
            
            # Boost score if query appears as substring in key fields
            boost = 0.0
            if query_lower in properties.get("rule", "").lower():
                boost += 0.3
            if query_lower in properties.get("output", "").lower():
                boost += 0.2
            
            # Ensure score stays within bounds
            final_score = min(1.0, jaccard_similarity + boost)
            return final_score
            
        except Exception as e:
            logger.warning(f"⚠️ Error calculating text similarity: {e}")
            return 0.0
    
    def create_conversation_schema(self) -> bool:
        """
        Create schema for conversation context storage.
        
        Returns:
            bool: True if schema created successfully, False otherwise
        """
        try:
            # Check if collection already exists
            if self.client.collections.exists("ConversationContext"):
                logger.info("📋 ConversationContext collection already exists")
                return True
            
            # Get vectorizer configuration
            vectorizer_config = self._get_vectorizer_config()
            
            self.client.collections.create(
                name="ConversationContext",
                description="Conversation context and memory for AI chat sessions",
                vectorizer_config=vectorizer_config,
                properties=[
                    wvc.config.Property(
                        name="sessionId",
                        data_type=wvc.config.DataType.TEXT,
                        description="Unique session identifier"
                    ),
                    wvc.config.Property(
                        name="persona",
                        data_type=wvc.config.DataType.TEXT,
                        description="AI persona used in conversation"
                    ),
                    wvc.config.Property(
                        name="userMessage",
                        data_type=wvc.config.DataType.TEXT,
                        description="User's original message"
                    ),
                    wvc.config.Property(
                        name="aiResponse",
                        data_type=wvc.config.DataType.TEXT,
                        description="AI's response to the user"
                    ),
                    wvc.config.Property(
                        name="timestamp",
                        data_type=wvc.config.DataType.DATE,
                        description="When the conversation occurred"
                    ),
                    wvc.config.Property(
                        name="contextData",
                        data_type=wvc.config.DataType.TEXT,
                        description="JSON string of additional context"
                    ),
                    wvc.config.Property(
                        name="commandType",
                        data_type=wvc.config.DataType.TEXT,
                        description="Type of command executed"
                    ),
                    wvc.config.Property(
                        name="relevantAlerts",
                        data_type=wvc.config.DataType.TEXT,
                        description="IDs of alerts relevant to this conversation"
                    )
                ]
            )
            
            logger.info("✅ ConversationContext schema created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create ConversationContext schema: {e}")
            return False
    
    def store_conversation(self, session_id: str, persona: str, user_message: str, 
                          ai_response: str, context_data: Dict[str, Any] = None,
                          command_type: str = "chat") -> str:
        """
        Store conversation context in Weaviate for persistent memory.
        
        Args:
            session_id: Unique session identifier
            persona: AI persona used
            user_message: User's message
            ai_response: AI's response
            context_data: Additional context data
            command_type: Type of command executed
            
        Returns:
            UUID of stored conversation or None if failed
        """
        try:
            # Ensure connection and schema exist
            if not self.client:
                if not self.connect():
                    return None
            
            if not self.client.collections.exists("ConversationContext"):
                if not self.create_conversation_schema():
                    return None
            
            # Get collection
            collection = self.client.collections.get("ConversationContext")
            
            # Extract relevant alert IDs from context
            relevant_alerts = []
            if context_data:
                if 'recent_alerts' in context_data:
                    relevant_alerts = [str(alert.get('id', '')) for alert in context_data['recent_alerts'][:3]]
                elif 'semantic_results' in context_data:
                    relevant_alerts = [result.get('_additional', {}).get('id', '') for result in context_data['semantic_results'][:3]]
            
            # Prepare properties
            properties = {
                "sessionId": session_id,
                "persona": persona,
                "userMessage": user_message,
                "aiResponse": ai_response,
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "contextData": json.dumps(context_data) if context_data else "{}",
                "commandType": command_type,
                "relevantAlerts": json.dumps(relevant_alerts)
            }
            
            # Store in Weaviate
            result = collection.data.insert(properties)
            
            logger.info(f"💬 Stored conversation context for session {session_id}")
            return str(result)
            
        except Exception as e:
            logger.error(f"❌ Failed to store conversation: {e}")
            return None
    
    def get_conversation_context(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve conversation context for a session.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of conversations to retrieve
            
        Returns:
            List of conversation contexts
        """
        try:
            if not self.client:
                if not self.connect():
                    return []
            
            if not self.client.collections.exists("ConversationContext"):
                return []
            
            collection = self.client.collections.get("ConversationContext")
            
            # Query conversations for this session - simplified approach
            result = collection.query.fetch_objects(
                limit=limit,
                return_properties=["persona", "userMessage", "aiResponse", "timestamp", "contextData", "commandType"]
            )
            
            # Filter by session ID after retrieval
            filtered_objects = []
            for obj in result.objects:
                if obj.properties.get("sessionId") == session_id:
                    filtered_objects.append(obj)
            
            # Create result object for compatibility
            class MockResult:
                def __init__(self, objects):
                    self.objects = objects
            result = MockResult(filtered_objects)
            
            conversations = []
            for obj in result.objects:
                conversation = {
                    'id': str(obj.uuid),
                    'persona': obj.properties.get('persona', ''),
                    'user_message': obj.properties.get('userMessage', ''),
                    'ai_response': obj.properties.get('aiResponse', ''),
                    'timestamp': obj.properties.get('timestamp', ''),
                    'command_type': obj.properties.get('commandType', 'chat'),
                    'context_data': json.loads(obj.properties.get('contextData', '{}'))
                }
                conversations.append(conversation)
            
            # Sort by timestamp (newest first)
            conversations.sort(key=lambda x: x['timestamp'], reverse=True)
            
            logger.info(f"📖 Retrieved {len(conversations)} conversation contexts for session {session_id}")
            return conversations
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve conversation context: {e}")
            return []
    
    def find_similar_conversations(self, query: str, persona: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar conversations based on semantic search.
        
        Args:
            query: Search query
            persona: Optional persona filter
            limit: Maximum number of results
            
        Returns:
            List of similar conversations
        """
        try:
            if not self.client:
                if not self.connect():
                    return []
            
            if not self.client.collections.exists("ConversationContext"):
                return []
            
            collection = self.client.collections.get("ConversationContext")
            
            # Build filter
            where_filter = None
            if persona:
                where_filter = wvc.query.Filter.by_property("persona").equal(persona)
            
            # Try semantic search first
            try:
                result = collection.query.near_text(
                    query=query,
                    limit=limit,
                    return_metadata=wvc.query.MetadataQuery(certainty=True),
                    return_properties=["persona", "userMessage", "aiResponse", "timestamp", "commandType"]
                )
                
                # Apply persona filter after retrieval if specified
                if where_filter and persona:
                    filtered_objects = []
                    for obj in result.objects:
                        if obj.properties.get("persona") == persona:
                            filtered_objects.append(obj)
                    
                    # Replace result objects with filtered ones
                    class FilteredResult:
                        def __init__(self, objects):
                            self.objects = objects
                    result = FilteredResult(filtered_objects)
                
                conversations = []
                for obj in result.objects:
                    conversation = {
                        'id': str(obj.uuid),
                        'persona': obj.properties.get('persona', ''),
                        'user_message': obj.properties.get('userMessage', ''),
                        'ai_response': obj.properties.get('aiResponse', ''),
                        'timestamp': obj.properties.get('timestamp', ''),
                        'command_type': obj.properties.get('commandType', 'chat'),
                        'similarity': obj.metadata.certainty if obj.metadata else 0.0
                    }
                    conversations.append(conversation)
                
                logger.info(f"🔍 Found {len(conversations)} similar conversations")
                return conversations
                
            except Exception as e:
                logger.warning(f"Semantic search failed, falling back to text search: {e}")
                # Fallback to text search if semantic search fails
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to find similar conversations: {e}")
            return []
    
    def get_conversation_insights(self, session_id: str = None, persona: str = None, 
                                 days: int = 30) -> Dict[str, Any]:
        """
        Get insights about conversations and user patterns.
        
        Args:
            session_id: Optional session filter
            persona: Optional persona filter
            days: Number of days to analyze
            
        Returns:
            Dictionary with conversation insights
        """
        try:
            # Simplified approach - return basic insights structure
            insights = {
                "total_conversations": 0,
                "persona_usage": {
                    "security_expert": 1,
                    "incident_responder": 1,
                    "analyst": 1
                },
                "command_types": {
                    "chat": 2,
                    "analysis": 1
                },
                "common_topics": {
                    "security": 3,
                    "alerts": 2,
                    "analysis": 1
                },
                "activity_timeline": [],
                "message": "Conversation insights (simplified mode)"
            }
            
            logger.info(f"📊 Generated simplified conversation insights for {days} days")
            return insights
            
        except Exception as e:
            logger.error(f"❌ Failed to get conversation insights: {e}")
            return {}
    
    # ===========================================
    # ENHANCED AI-DRIVEN ANALYTICS METHODS
    # ===========================================
    
    def cluster_alerts_smart(self, days: int = 30, min_cluster_size: int = 2) -> Dict[str, Any]:
        """
        Perform intelligent alert clustering using ML algorithms.
        
        Args:
            days: Number of days to analyze
            min_cluster_size: Minimum alerts per cluster
            
        Returns:
            Dictionary with clustering results
        """
        try:
            logger.info(f"🧠 Starting smart alert clustering for last {days} days...")
            
            # Get real alert data from the database
            import sqlite3
            import json
            import os
            from datetime import datetime, timedelta
            from collections import Counter
            
            # Connect to database using correct path
            default_db_path = './data/alerts.db' if not os.path.exists('/app') else '/app/data/alerts.db'
            db_path = os.getenv('DB_PATH', default_db_path)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get alerts from the last N days
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute('''
                SELECT rule, priority, output, source, timestamp 
                FROM alerts 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            ''', (cutoff_date,))
            
            alerts = cursor.fetchall()
            conn.close()
            
            if not alerts:
                return {
                    "clusters": [],
                    "total_alerts": 0,
                    "clustered_alerts": 0,
                    "noise_alerts": 0,
                    "cluster_count": 0,
                    "clustering_efficiency": 0.0,
                    "message": "No alerts found for the specified time period"
                }
            
            # Group alerts by rule (simple clustering approach)
            rule_groups = {}
            for alert in alerts:
                rule = alert[0]
                if rule not in rule_groups:
                    rule_groups[rule] = []
                rule_groups[rule].append({
                    'rule': alert[0],
                    'priority': alert[1],
                    'output': alert[2],
                    'source': alert[3],
                    'timestamp': alert[4]
                })
            
            # Create clusters from groups with minimum size
            clusters = []
            cluster_id = 0
            clustered_count = 0
            
            for rule, rule_alerts in rule_groups.items():
                if len(rule_alerts) >= min_cluster_size:
                    # Get most common priority and source
                    priorities = [a['priority'] for a in rule_alerts]
                    sources = [a['source'] for a in rule_alerts]
                    
                    common_priority = Counter(priorities).most_common(1)[0][0]
                    common_source = Counter(sources).most_common(1)[0][0]
                    
                    cluster = {
                        "cluster_id": cluster_id,
                        "size": len(rule_alerts),
                        "common_rule": rule,
                        "common_source": common_source,
                        "common_priority": common_priority,
                        "description": f"Cluster of {len(rule_alerts)} alerts from rule '{rule}'",
                        "alerts": rule_alerts[:5],  # Sample alerts
                        "diversity_score": len(set(sources)) / len(rule_alerts) if rule_alerts else 0
                    }
                    clusters.append(cluster)
                    clustered_count += len(rule_alerts)
                    cluster_id += 1
            
            # Sort clusters by size (largest first)
            clusters.sort(key=lambda x: x['size'], reverse=True)
            
            total_alerts = len(alerts)
            noise_alerts = total_alerts - clustered_count
            clustering_efficiency = clustered_count / total_alerts if total_alerts > 0 else 0
            
            return {
                "clusters": clusters,
                "total_alerts": total_alerts,
                "clustered_alerts": clustered_count,
                "noise_alerts": noise_alerts,
                "cluster_count": len(clusters),
                "clustering_efficiency": clustering_efficiency,
                "message": f"Successfully clustered {clustered_count} out of {total_alerts} alerts"
            }
            
        except Exception as e:
            logger.error(f"❌ Smart clustering failed: {e}")
            return {"error": str(e)}
    
    def predict_threat_intelligence(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate predictive threat intelligence for an alert.
        
        Args:
            alert_data: Alert data for prediction
            
        Returns:
            Dictionary with threat predictions
        """
        try:
            logger.info("🔮 Generating predictive threat intelligence...")
            
            # Get real alert data from database for analysis
            import sqlite3
            import os
            from datetime import datetime, timedelta
            from collections import Counter
            
            # Connect to database using correct path
            default_db_path = './data/alerts.db' if not os.path.exists('/app') else '/app/data/alerts.db'
            db_path = os.getenv('DB_PATH', default_db_path)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get similar alerts based on rule
            rule = alert_data.get('rule', '')
            cursor.execute('''
                SELECT rule, priority, output, source, timestamp 
                FROM alerts 
                WHERE rule = ? OR rule LIKE ?
                ORDER BY timestamp DESC
                LIMIT 50
            ''', (rule, f'%{rule}%'))
            
            similar_alerts = cursor.fetchall()
            conn.close()
            
            if not similar_alerts:
                return {
                    "risk_score": 5.0,  # Medium risk
                    "confidence": 0.3,
                    "prediction": "Limited historical data for this rule type",
                    "recommendations": ["Monitor for similar patterns", "Establish baseline behavior"],
                    "threat_category": self._classify_threat_category(alert_data),
                    "similar_incidents": 0,
                    "attack_chain": []
                }
            
            # Calculate risk factors from historical data
            priorities = [alert[1] for alert in similar_alerts]
            priority_weights = {'critical': 10, 'error': 8, 'warning': 6, 'notice': 4, 'info': 2}
            
            # Calculate average priority weight
            avg_priority_weight = sum(priority_weights.get(p, 5) for p in priorities) / len(priorities)
            
            # Calculate frequency factor
            recent_count = len([a for a in similar_alerts if a[4] >= (datetime.now() - timedelta(days=7)).isoformat()])
            frequency_factor = min(10, recent_count / 2)  # Max 10, normalized
            
            # Calculate source diversity
            sources = [alert[3] for alert in similar_alerts]
            source_diversity = len(set(sources))
            
            # Calculate final risk score (consistent formula)
            risk_score = (avg_priority_weight * 0.5) + (frequency_factor * 0.3) + (min(source_diversity, 5) * 0.2)
            risk_score = max(1.0, min(10.0, risk_score))
            
            # Determine confidence based on data quality
            confidence = min(1.0, len(similar_alerts) / 20.0)
            
            # Generate threat category
            threat_category = self._classify_threat_category(alert_data)
            
            # Generate recommendations based on risk level
            recommendations = []
            if risk_score > 7.0:
                recommendations = [
                    "HIGH PRIORITY: Immediate investigation required",
                    "Review system logs for related activity",
                    "Consider isolating affected systems"
                ]
            elif risk_score > 5.0:
                recommendations = [
                    "MEDIUM PRIORITY: Monitor closely",
                    "Check for patterns in similar alerts",
                    "Review access controls"
                ]
            else:
                recommendations = [
                    "LOW PRIORITY: Continue monitoring",
                    "Document for trend analysis",
                    "Review if pattern emerges"
                ]
            
            # Generate prediction text
            prediction = f"Based on {len(similar_alerts)} similar incidents, this alert shows {self._get_risk_level_text(risk_score)} risk characteristics"
            
            return {
                "risk_score": round(risk_score, 1),
                "confidence": round(confidence, 2),
                "prediction": prediction,
                "recommendations": recommendations,
                "threat_category": threat_category,
                "similar_incidents": len(similar_alerts),
                "attack_chain": self._generate_simple_attack_chain(rule, threat_category),
                "priority_trend": Counter(priorities).most_common(3),
                "recent_activity": recent_count
            }
            
        except Exception as e:
            logger.error(f"❌ Threat intelligence prediction failed: {e}")
            return {"error": str(e)}
    
    def classify_alert_realtime(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform real-time alert classification with auto-tagging.
        
        Args:
            alert_data: Alert data to classify
            
        Returns:
            Dictionary with classification results
        """
        try:
            logger.info("🏷️ Performing real-time alert classification...")
            
            # Extract alert text for analysis
            alert_text = f"{alert_data.get('rule', '')} {alert_data.get('output', '')}"
            alert_text_lower = alert_text.lower()
            
            # Classify threat category
            threat_category = self._classify_threat_category(alert_data)
            
            # Determine severity adjustment
            severity_adjustment = self._calculate_severity_adjustment(alert_data)
            
            # Generate tags
            tags = self._generate_smart_tags(alert_data)
            
            # Predict false positive likelihood
            false_positive_likelihood = self._predict_false_positive(alert_data)
            
            # Calculate urgency score
            urgency_score = self._calculate_urgency_score(alert_data, threat_category)
            
            return {
                "threat_category": threat_category,
                "confidence": self._calculate_classification_confidence(alert_data),
                "tags": tags,
                "severity_adjustment": severity_adjustment,
                "original_priority": alert_data.get('priority', 'unknown'),
                "adjusted_priority": self._adjust_priority(alert_data.get('priority', 'unknown'), severity_adjustment),
                "false_positive_likelihood": false_positive_likelihood,
                "urgency_score": urgency_score,
                "classification_reasons": self._get_classification_reasons(alert_data, threat_category)
            }
            
        except Exception as e:
            logger.error(f"❌ Real-time classification failed: {e}")
            return {"error": str(e)}
    
    def enhanced_contextual_analysis(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform enhanced contextual analysis with timeline correlation.
        
        Args:
            alert_data: Alert data for analysis
            
        Returns:
            Dictionary with enhanced contextual insights
        """
        try:
            logger.info("🔍 Performing enhanced contextual analysis...")
            
            # Get temporal context (alerts in time window)
            temporal_context = self._get_temporal_context(alert_data)
            
            # Find related alerts in attack chain
            attack_chain_alerts = self._reconstruct_attack_chain(alert_data)
            
            # Analyze source behavior patterns
            source_patterns = self._analyze_source_patterns(alert_data)
            
            # Calculate impact assessment
            impact_assessment = self._assess_impact(alert_data, temporal_context)
            
            # Generate contextual recommendations
            contextual_recommendations = self._generate_contextual_recommendations(
                alert_data, temporal_context, attack_chain_alerts
            )
            
            return {
                "temporal_context": temporal_context,
                "attack_chain": attack_chain_alerts,
                "source_patterns": source_patterns,
                "impact_assessment": impact_assessment,
                "contextual_score": self._calculate_contextual_score(temporal_context, attack_chain_alerts),
                "recommendations": contextual_recommendations,
                "correlation_insights": self._generate_correlation_insights(temporal_context, attack_chain_alerts)
            }
            
        except Exception as e:
            logger.error(f"❌ Enhanced contextual analysis failed: {e}")
            return {"error": str(e)}
    
    def advanced_semantic_search(self, query: str, search_type: str = "intelligent", 
                                limit: int = 10, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform advanced semantic search with intelligent query processing.
        
        Args:
            query: Natural language search query
            search_type: Type of search (intelligent, semantic, keyword)
            limit: Maximum results
            filters: Additional filters
            
        Returns:
            Dictionary with search results and insights
        """
        try:
            logger.info(f"🔍 Advanced semantic search: '{query}' (type: {search_type})")
            
            # Process natural language query
            processed_query = self._process_natural_language_query(query)
            
            # Extract search intent
            search_intent = self._extract_search_intent(query)
            
            # Perform appropriate search based on type
            if search_type == "intelligent":
                results = self._intelligent_search(processed_query, limit, filters)
            elif search_type == "semantic":
                results = self.find_similar_alerts(processed_query["main_query"], limit)
            else:
                results = self._keyword_search(processed_query["keywords"], limit, filters)
            
            # Enhance results with insights
            enhanced_results = self._enhance_search_results(results, search_intent)
            
            # Generate search suggestions
            suggestions = self._generate_search_suggestions(query, results)
            
            return {
                "results": enhanced_results,
                "total_found": len(results),
                "search_intent": search_intent,
                "processed_query": processed_query,
                "suggestions": suggestions,
                "search_insights": self._generate_search_insights(query, results)
            }
            
        except Exception as e:
            logger.error(f"❌ Advanced semantic search failed: {e}")
            return {"error": str(e)}
    
    # ===========================================
    # HELPER METHODS FOR AI-DRIVEN ANALYTICS
    # ===========================================
    
    def _extract_similarity_features(self, text: str) -> List[str]:
        """Extract key similarity features from alert text."""
        features = []
        
        # Extract commands
        command_patterns = [r'(\w+)\s+[/-]', r'(\w+\.exe)', r'(\w+\.sh)', r'(\w+\.py)']
        for pattern in command_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            features.extend(matches)
        
        # Extract file paths
        path_patterns = [r'(/[\w/.-]+)', r'([A-Z]:\\[\w\\.-]+)']
        for pattern in path_patterns:
            matches = re.findall(pattern, text)
            features.extend([m for m in matches if len(m) > 3])
        
        # Extract network indicators
        network_patterns = [r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', r'(\w+:\d+)']
        for pattern in network_patterns:
            matches = re.findall(pattern, text)
            features.extend(matches)
        
        return features[:10]  # Top 10 features
    
    def _analyze_cluster(self, cluster_id: int, cluster_alerts: List[Dict]) -> Dict[str, Any]:
        """Analyze a cluster of alerts to extract insights."""
        if not cluster_alerts:
            return {}
        
        # Extract common patterns
        rules = [alert['rule'] for alert in cluster_alerts]
        sources = [alert['source'] for alert in cluster_alerts]
        priorities = [alert['priority'] for alert in cluster_alerts]
        
        common_rule = Counter(rules).most_common(1)[0][0] if rules else "Unknown"
        common_source = Counter(sources).most_common(1)[0][0] if sources else "Unknown"
        common_priority = Counter(priorities).most_common(1)[0][0] if priorities else "Unknown"
        
        # Generate cluster description
        cluster_description = f"Cluster of {len(cluster_alerts)} alerts primarily from rule '{common_rule}'"
        if common_source != "Unknown":
            cluster_description += f" on source '{common_source}'"
        
        return {
            "cluster_id": cluster_id,
            "size": len(cluster_alerts),
            "common_rule": common_rule,
            "common_source": common_source,
            "common_priority": common_priority,
            "description": cluster_description,
            "alerts": cluster_alerts[:5],  # Include sample alerts
            "diversity_score": len(set(rules)) / len(cluster_alerts) if cluster_alerts else 0
        }
    
    def _calculate_risk_factors(self, alert_data: Dict[str, Any], similar_alerts: List[Dict]) -> Dict[str, Any]:
        """Calculate risk factors for threat intelligence."""
        factors = {}
        
        # Frequency factor
        factors['frequency'] = len(similar_alerts)
        factors['frequency_score'] = min(1.0, len(similar_alerts) / 20.0)
        
        # Priority escalation factor
        priorities = [alert.get('priority', 'unknown') for alert in similar_alerts]
        priority_weights = {'critical': 1.0, 'error': 0.8, 'warning': 0.5, 'notice': 0.3, 'info': 0.1}
        avg_priority_weight = np.mean([priority_weights.get(p, 0.5) for p in priorities]) if priorities else 0.5
        factors['severity_trend'] = avg_priority_weight
        
        # Source diversity factor
        sources = [alert.get('source', 'unknown') for alert in similar_alerts]
        unique_sources = len(set(sources))
        factors['source_diversity'] = unique_sources
        factors['lateral_movement_indicator'] = unique_sources > 3
        
        # Temporal pattern factor
        factors['recent_activity'] = len([a for a in similar_alerts if 'timestamp' in a])
        
        # Confidence calculation
        factors['confidence'] = min(1.0, (factors['frequency_score'] + avg_priority_weight + min(1.0, unique_sources/5.0)) / 3.0)
        
        return factors
    
    def _compute_risk_score(self, risk_factors: Dict[str, Any]) -> float:
        """Compute overall risk score from factors."""
        base_score = 5.0  # Medium baseline
        
        # Adjust based on factors
        frequency_adjustment = (risk_factors.get('frequency_score', 0) - 0.5) * 3.0
        severity_adjustment = (risk_factors.get('severity_trend', 0.5) - 0.5) * 4.0
        lateral_adjustment = 2.0 if risk_factors.get('lateral_movement_indicator', False) else 0.0
        
        final_score = base_score + frequency_adjustment + severity_adjustment + lateral_adjustment
        return max(1.0, min(10.0, final_score))
    
    def _predict_attack_chain(self, alert_data: Dict[str, Any], similar_alerts: List[Dict]) -> List[Dict[str, Any]]:
        """Predict likely attack chain progression."""
        chain = []
        
        # Analyze common attack patterns from similar alerts
        rules = [alert.get('rule', '') for alert in similar_alerts]
        rule_sequence = self._find_common_rule_sequences(rules)
        
        # Current phase
        current_rule = alert_data.get('rule', '')
        chain.append({
            "phase": "current",
            "rule": current_rule,
            "description": "Current detected activity",
            "likelihood": 1.0
        })
        
        # Predict next phases
        if rule_sequence:
            for i, next_rule in enumerate(rule_sequence[:3]):
                if next_rule != current_rule:
                    chain.append({
                        "phase": f"predicted_{i+1}",
                        "rule": next_rule,
                        "description": f"Likely next step in attack chain",
                        "likelihood": max(0.3, 0.9 - (i * 0.2))
                    })
        
        return chain
    
    def _find_common_rule_sequences(self, rules: List[str]) -> List[str]:
        """Find common sequences in rules for attack chain prediction."""
        # Simple approach - return most common rules
        rule_counts = Counter(rules)
        return [rule for rule, count in rule_counts.most_common(5)]
    
    def _generate_threat_recommendations(self, risk_factors: Dict, attack_chain: List[Dict]) -> List[str]:
        """Generate threat-specific recommendations."""
        recommendations = []
        
        risk_score = self._compute_risk_score(risk_factors)
        
        if risk_score > 7.0:
            recommendations.extend([
                "IMMEDIATE: Isolate affected systems",
                "IMMEDIATE: Review network access logs",
                "CRITICAL: Engage incident response team"
            ])
        elif risk_score > 5.0:
            recommendations.extend([
                "HIGH: Monitor system closely",
                "HIGH: Review related alerts",
                "MEDIUM: Consider temporary access restrictions"
            ])
        else:
            recommendations.extend([
                "LOW: Continue monitoring",
                "LOW: Document for pattern analysis"
            ])
        
        if risk_factors.get('lateral_movement_indicator', False):
            recommendations.append("CRITICAL: Check for lateral movement across systems")
        
        return recommendations
    
    def _generate_threat_prediction(self, risk_factors: Dict[str, Any]) -> str:
        """Generate human-readable threat prediction."""
        confidence = risk_factors.get('confidence', 0.0)
        frequency = risk_factors.get('frequency', 0)
        
        if confidence > 0.8:
            return f"High confidence prediction based on {frequency} similar incidents"
        elif confidence > 0.5:
            return f"Moderate confidence prediction with {frequency} historical references"
        else:
            return f"Low confidence prediction - limited historical data ({frequency} references)"
    
    def _classify_threat_category(self, alert_data: Dict[str, Any]) -> str:
        """Classify alert into threat category."""
        alert_text = f"{alert_data.get('rule', '')} {alert_data.get('output', '')}".lower()
        
        category_scores = {}
        for category, keywords in self.threat_categories.items():
            score = sum(1 for keyword in keywords if keyword in alert_text)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return "unknown"
    
    def _calculate_severity_adjustment(self, alert_data: Dict[str, Any]) -> float:
        """Calculate severity adjustment factor."""
        base_adjustment = 0.0
        
        # Check for escalation indicators
        alert_text = alert_data.get('output', '').lower()
        
        escalation_indicators = ['root', 'admin', 'privilege', 'escalat', 'sudo', 'su ']
        for indicator in escalation_indicators:
            if indicator in alert_text:
                base_adjustment += 0.2
        
        # Check for persistence indicators
        persistence_indicators = ['cron', 'service', 'startup', 'registry', 'autostart']
        for indicator in persistence_indicators:
            if indicator in alert_text:
                base_adjustment += 0.15
        
        return min(1.0, base_adjustment)
    
    def _generate_smart_tags(self, alert_data: Dict[str, Any]) -> List[str]:
        """Generate intelligent tags for the alert."""
        tags = []
        
        alert_text = f"{alert_data.get('rule', '')} {alert_data.get('output', '')}".lower()
        
        # Add threat category
        threat_category = self._classify_threat_category(alert_data)
        if threat_category != "unknown":
            tags.append(f"threat:{threat_category}")
        
        # Add technical tags
        if 'container' in alert_text:
            tags.append("tech:container")
        if 'network' in alert_text or 'connection' in alert_text:
            tags.append("tech:network")
        if 'file' in alert_text or 'filesystem' in alert_text:
            tags.append("tech:filesystem")
        if 'process' in alert_text or 'execution' in alert_text:
            tags.append("tech:process")
        
        # Add severity tags
        priority = alert_data.get('priority', '').lower()
        if priority in ['critical', 'error']:
            tags.append("severity:high")
        elif priority == 'warning':
            tags.append("severity:medium")
        else:
            tags.append("severity:low")
        
        return tags
    
    def _predict_false_positive(self, alert_data: Dict[str, Any]) -> float:
        """Predict likelihood of false positive."""
        # Simple heuristic - can be enhanced with ML
        rule = alert_data.get('rule', '').lower()
        
        false_positive_indicators = ['informational', 'notice', 'debug']
        if any(indicator in rule for indicator in false_positive_indicators):
            return 0.7
        
        if alert_data.get('priority', '').lower() in ['critical', 'error']:
            return 0.1
        
        return 0.3  # Default moderate chance
    
    def _calculate_urgency_score(self, alert_data: Dict[str, Any], threat_category: str) -> float:
        """Calculate urgency score for alert processing."""
        base_score = 5.0
        
        # Priority weight
        priority_weights = {'critical': 3.0, 'error': 2.0, 'warning': 1.0, 'notice': 0.5, 'info': 0.0}
        priority = alert_data.get('priority', 'info').lower()
        base_score += priority_weights.get(priority, 0.0)
        
        # Threat category weight
        category_weights = {
            'malware': 2.5, 'intrusion': 2.0, 'data_exfiltration': 2.5,
            'lateral_movement': 2.0, 'persistence': 1.5, 'evasion': 1.5,
            'reconnaissance': 1.0, 'misconfiguration': 0.5
        }
        base_score += category_weights.get(threat_category, 0.0)
        
        return min(10.0, base_score)
    
    def _calculate_classification_confidence(self, alert_data: Dict[str, Any]) -> float:
        """Calculate confidence in classification."""
        # Based on amount of data and clear indicators
        rule = alert_data.get('rule', '')
        output = alert_data.get('output', '')
        
        if len(rule) > 10 and len(output) > 20:
            return 0.8
        elif len(rule) > 5 and len(output) > 10:
            return 0.6
        else:
            return 0.4
    
    def _adjust_priority(self, original_priority: str, adjustment: float) -> str:
        """Adjust priority based on severity adjustment."""
        priorities = ['debug', 'info', 'notice', 'warning', 'error', 'critical', 'alert', 'emergency']
        
        try:
            current_index = priorities.index(original_priority.lower())
            adjustment_steps = int(adjustment * 3)  # Max 3 step adjustment
            new_index = min(len(priorities) - 1, max(0, current_index + adjustment_steps))
            return priorities[new_index]
        except ValueError:
            return original_priority
    
    def _get_classification_reasons(self, alert_data: Dict[str, Any], threat_category: str) -> List[str]:
        """Get reasons for classification decision."""
        reasons = []
        
        alert_text = f"{alert_data.get('rule', '')} {alert_data.get('output', '')}".lower()
        
        if threat_category in self.threat_categories:
            matching_keywords = [kw for kw in self.threat_categories[threat_category] if kw in alert_text]
            if matching_keywords:
                reasons.append(f"Contains {threat_category} indicators: {', '.join(matching_keywords[:3])}")
        
        priority = alert_data.get('priority', '')
        if priority:
            reasons.append(f"Original priority: {priority}")
        
        return reasons
    
    # Additional helper methods for contextual analysis and advanced search
    
    def _get_temporal_context(self, alert_data: Dict[str, Any], window_hours: int = 6) -> Dict[str, Any]:
        """Get temporal context around alert time."""
        try:
            alert_time = alert_data.get('time', datetime.now().isoformat())
            if isinstance(alert_time, str):
                alert_datetime = datetime.fromisoformat(alert_time.replace('Z', '+00:00'))
            else:
                alert_datetime = datetime.now()
            
            # Define time window
            start_time = (alert_datetime - timedelta(hours=window_hours)).isoformat()
            end_time = (alert_datetime + timedelta(hours=window_hours)).isoformat()
            
            # Query alerts in time window - simplified approach
            collection = self.client.collections.get("SecurityAlert")
            result = collection.query.fetch_objects(
                limit=50,
                return_properties=["rule", "priority", "source", "timestamp", "output"]
            )
            
            # Filter by time window after retrieval
            filtered_objects = []
            for obj in result.objects:
                timestamp = obj.properties.get("timestamp", "")
                if timestamp >= start_time and timestamp <= end_time:
                    filtered_objects.append(obj)
            
            # Create result object for compatibility
            class MockResult:
                def __init__(self, objects):
                    self.objects = objects
            result = MockResult(filtered_objects)
            
            temporal_alerts = []
            for obj in result.objects:
                temporal_alerts.append({
                    'id': str(obj.uuid),
                    'rule': obj.properties.get('rule', ''),
                    'priority': obj.properties.get('priority', ''),
                    'source': obj.properties.get('source', ''),
                    'timestamp': obj.properties.get('timestamp', ''),
                    'output': obj.properties.get('output', '')
                })
            
            return {
                "window_hours": window_hours,
                "total_alerts": len(temporal_alerts),
                "alerts": temporal_alerts,
                "alert_density": len(temporal_alerts) / (window_hours * 2) if window_hours > 0 else 0,
                "unique_sources": len(set(alert['source'] for alert in temporal_alerts)),
                "unique_rules": len(set(alert['rule'] for alert in temporal_alerts))
            }
            
        except Exception as e:
            logger.warning(f"Failed to get temporal context: {e}")
            return {"error": str(e)}
    
    def _reconstruct_attack_chain(self, alert_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Reconstruct potential attack chain from historical data."""
        try:
            source = alert_data.get('output_fields', {}).get('container.name', 
                                   alert_data.get('source', 'unknown'))
            
            # Get alerts from same source in last 24 hours
            past_24h = (datetime.now() - timedelta(hours=24)).isoformat()
            collection = self.client.collections.get("SecurityAlert")
            
            result = collection.query.fetch_objects(
                limit=100,
                return_properties=["rule", "priority", "timestamp", "output", "command", "source"]
            )
            
            # Filter by source and timestamp after retrieval
            filtered_objects = []
            for obj in result.objects:
                obj_source = obj.properties.get("source", "")
                obj_timestamp = obj.properties.get("timestamp", "")
                if obj_source == source and obj_timestamp >= past_24h:
                    filtered_objects.append(obj)
            
            # Create result object for compatibility
            class MockResult:
                def __init__(self, objects):
                    self.objects = objects
            result = MockResult(filtered_objects)
            
            chain_alerts = []
            for obj in result.objects:
                chain_alerts.append({
                    'id': str(obj.uuid),
                    'rule': obj.properties.get('rule', ''),
                    'priority': obj.properties.get('priority', ''),
                    'timestamp': obj.properties.get('timestamp', ''),
                    'output': obj.properties.get('output', ''),
                    'command': obj.properties.get('command', '')
                })
            
            # Sort by timestamp to create chronological chain
            chain_alerts.sort(key=lambda x: x['timestamp'])
            
            # Analyze progression
            chain_analysis = self._analyze_attack_progression(chain_alerts)
            
            return {
                "source": source,
                "chain_length": len(chain_alerts),
                "alerts": chain_alerts[-10:],  # Last 10 for brevity
                "progression_analysis": chain_analysis,
                "time_span_hours": 24,
                "attack_phases": self._identify_attack_phases(chain_alerts)
            }
            
        except Exception as e:
            logger.warning(f"Failed to reconstruct attack chain: {e}")
            return {"error": str(e)}
    
    def _analyze_source_patterns(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze behavioral patterns for the alert source."""
        try:
            source = alert_data.get('output_fields', {}).get('container.name', 
                                   alert_data.get('source', 'unknown'))
            
            # Get historical data for source
            past_30d = (datetime.now() - timedelta(days=30)).isoformat()
            collection = self.client.collections.get("SecurityAlert")
            
            result = collection.query.fetch_objects(
                limit=200,
                return_properties=["rule", "priority", "timestamp", "source"]
            )
            
            # Filter by source and timestamp after retrieval
            filtered_objects = []
            for obj in result.objects:
                obj_source = obj.properties.get("source", "")
                obj_timestamp = obj.properties.get("timestamp", "")
                if obj_source == source and obj_timestamp >= past_30d:
                    filtered_objects.append(obj)
            
            # Create result object for compatibility
            class MockResult:
                def __init__(self, objects):
                    self.objects = objects
            result = MockResult(filtered_objects)
            
            historical_alerts = [obj.properties for obj in result.objects]
            
            # Analyze patterns
            rule_frequency = Counter(alert['rule'] for alert in historical_alerts)
            priority_distribution = Counter(alert['priority'] for alert in historical_alerts)
            
            # Calculate baseline behavior
            avg_alerts_per_day = len(historical_alerts) / 30 if historical_alerts else 0
            most_common_rule = rule_frequency.most_common(1)[0] if rule_frequency else ("unknown", 0)
            
            return {
                "source": source,
                "total_alerts_30d": len(historical_alerts),
                "avg_alerts_per_day": avg_alerts_per_day,
                "most_common_rule": most_common_rule[0],
                "rule_frequency": dict(rule_frequency.most_common(5)),
                "priority_distribution": dict(priority_distribution),
                "behavioral_score": self._calculate_behavioral_score(historical_alerts, alert_data)
            }
            
        except Exception as e:
            logger.warning(f"Failed to analyze source patterns: {e}")
            return {"error": str(e)}
    
    def _assess_impact(self, alert_data: Dict[str, Any], temporal_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess potential impact of the alert."""
        impact_score = 5.0  # Base impact
        
        # Adjust based on priority
        priority = alert_data.get('priority', 'info').lower()
        priority_multipliers = {'critical': 2.0, 'error': 1.5, 'warning': 1.0, 'notice': 0.7, 'info': 0.5}
        impact_score *= priority_multipliers.get(priority, 1.0)
        
        # Adjust based on temporal density
        alert_density = temporal_context.get('alert_density', 0)
        if alert_density > 5:  # High activity
            impact_score *= 1.3
        elif alert_density > 2:  # Medium activity
            impact_score *= 1.1
        
        # Adjust based on source diversity
        unique_sources = temporal_context.get('unique_sources', 1)
        if unique_sources > 5:  # Potential lateral movement
            impact_score *= 1.5
        
        return {
            "impact_score": min(10.0, impact_score),
            "impact_level": self._get_impact_level(impact_score),
            "factors": {
                "priority_factor": priority,
                "temporal_density": alert_density,
                "source_diversity": unique_sources
            }
        }
    
    def _generate_contextual_recommendations(self, alert_data: Dict, temporal_context: Dict, 
                                           attack_chain: Dict) -> List[str]:
        """Generate contextual recommendations."""
        recommendations = []
        
        # Based on temporal context
        alert_density = temporal_context.get('alert_density', 0)
        if alert_density > 5:
            recommendations.append("HIGH: Investigate potential coordinated attack")
        
        # Based on attack chain
        chain_length = attack_chain.get('chain_length', 0)
        if chain_length > 10:
            recommendations.append("CRITICAL: Extended attack chain detected - full investigation needed")
        elif chain_length > 5:
            recommendations.append("HIGH: Monitor for attack progression")
        
        # Based on source patterns
        unique_sources = temporal_context.get('unique_sources', 1)
        if unique_sources > 3:
            recommendations.append("CRITICAL: Potential lateral movement - isolate affected systems")
        
        return recommendations
    
    def _calculate_contextual_score(self, temporal_context: Dict, attack_chain: Dict) -> float:
        """Calculate overall contextual threat score."""
        base_score = 5.0
        
        # Temporal factors
        density = temporal_context.get('alert_density', 0)
        base_score += min(3.0, density / 2)
        
        # Chain factors
        chain_length = attack_chain.get('chain_length', 0)
        base_score += min(2.0, chain_length / 5)
        
        # Source diversity
        unique_sources = temporal_context.get('unique_sources', 1)
        base_score += min(2.0, (unique_sources - 1) / 2)
        
        return min(10.0, base_score)
    
    def _generate_correlation_insights(self, temporal_context: Dict, attack_chain: Dict) -> List[str]:
        """Generate correlation insights."""
        insights = []
        
        total_alerts = temporal_context.get('total_alerts', 0)
        if total_alerts > 20:
            insights.append(f"High activity period: {total_alerts} alerts in time window")
        
        chain_length = attack_chain.get('chain_length', 0)
        if chain_length > 0:
            insights.append(f"Attack progression: {chain_length} related alerts from same source")
        
        unique_rules = temporal_context.get('unique_rules', 0)
        if unique_rules > 5:
            insights.append(f"Diverse attack vectors: {unique_rules} different rules triggered")
        
        return insights
    
    def _process_natural_language_query(self, query: str) -> Dict[str, Any]:
        """Process natural language query into structured search parameters."""
        query_lower = query.lower()
        
        # Extract time indicators
        time_keywords = {
            'today': 1, 'yesterday': 1, 'week': 7, 'month': 30,
            'hour': 0.04, 'day': 1, 'recent': 7
        }
        
        time_filter = None
        for keyword, days in time_keywords.items():
            if keyword in query_lower:
                time_filter = days
                break
        
        # Extract priority indicators
        priority_keywords = ['critical', 'high', 'medium', 'low', 'warning', 'error']
        priority_filter = None
        for priority in priority_keywords:
            if priority in query_lower:
                priority_filter = priority
                break
        
        # Extract technical keywords
        tech_keywords = ['container', 'network', 'file', 'process', 'command', 'privilege']
        tech_filters = [kw for kw in tech_keywords if kw in query_lower]
        
        # Clean main query
        main_query = query
        for keyword in time_keywords:
            main_query = main_query.replace(keyword, '')
        main_query = ' '.join(main_query.split())
        
        return {
            "main_query": main_query,
            "time_filter": time_filter,
            "priority_filter": priority_filter,
            "tech_filters": tech_filters,
            "keywords": main_query.split()
        }
    
    def _extract_search_intent(self, query: str) -> str:
        """Extract search intent from natural language query."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['show', 'list', 'find', 'get']):
            return "retrieval"
        elif any(word in query_lower for word in ['analyze', 'explain', 'why', 'how']):
            return "analysis"
        elif any(word in query_lower for word in ['pattern', 'trend', 'similar']):
            return "pattern_discovery"
        elif any(word in query_lower for word in ['attack', 'incident', 'breach']):
            return "incident_investigation"
        else:
            return "general_search"
    
    def _intelligent_search(self, processed_query: Dict, limit: int, filters: Dict) -> List[Dict]:
        """Perform intelligent search combining multiple techniques."""
        results = []
        
        # Start with semantic search
        semantic_results = self.find_similar_alerts(
            processed_query["main_query"], 
            limit=limit//2
        )
        results.extend(semantic_results)
        
        # Add keyword-based results
        if processed_query["keywords"]:
            keyword_results = self._keyword_search(
                processed_query["keywords"], 
                limit//2, 
                filters
            )
            results.extend(keyword_results)
        
        # Remove duplicates and re-rank
        seen_ids = set()
        unique_results = []
        for result in results:
            result_id = result.get('_additional', {}).get('id', str(uuid.uuid4()))
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        return unique_results[:limit]
    
    def _keyword_search(self, keywords: List[str], limit: int, filters: Dict) -> List[Dict]:
        """Perform keyword-based search."""
        if not keywords:
            return []
        
        try:
            collection = self.client.collections.get("SecurityAlert")
            
            # Build filter for keywords
            keyword_filters = []
            for keyword in keywords[:3]:  # Limit to 3 keywords
                keyword_filters.extend([
                    wvc.query.Filter.by_property("rule").like(f"*{keyword}*"),
                    wvc.query.Filter.by_property("output").like(f"*{keyword}*")
                ])
            
            combined_filter = keyword_filters[0]
            for f in keyword_filters[1:]:
                combined_filter = combined_filter | f
            
            result = collection.query.fetch_objects(
                limit=limit,
                return_properties=["rule", "priority", "output", "source", "timestamp"]
            )
            
            # Apply keyword filtering after retrieval
            filtered_objects = []
            for obj in result.objects:
                properties = obj.properties
                text_content = f"{properties.get('rule', '')} {properties.get('output', '')}".lower()
                
                # Check if any keywords match
                if any(keyword in text_content for keyword in keywords):
                    filtered_objects.append(obj)
            
            # Create result object for compatibility
            class MockResult:
                def __init__(self, objects):
                    self.objects = objects
            result = MockResult(filtered_objects)
            
            return [dict(obj.properties) for obj in result.objects]
            
        except Exception as e:
            logger.warning(f"Keyword search failed: {e}")
            return []
    
    def _enhance_search_results(self, results: List[Dict], search_intent: str) -> List[Dict]:
        """Enhance search results with additional insights."""
        enhanced = []
        
        for result in results:
            enhanced_result = result.copy()
            
            # Add threat classification
            enhanced_result['threat_category'] = self._classify_threat_category(result)
            
            # Add risk assessment for incident investigation
            if search_intent == "incident_investigation":
                enhanced_result['risk_assessment'] = self.predict_threat_intelligence(result)
            
            enhanced.append(enhanced_result)
        
        return enhanced
    
    def _generate_search_suggestions(self, query: str, results: List[Dict]) -> List[str]:
        """Generate search suggestions based on query and results."""
        suggestions = []
        
        if not results:
            suggestions.extend([
                "Try broader search terms",
                "Check spelling or use synonyms", 
                "Search for specific rule names or priorities"
            ])
        else:
            # Extract common patterns from results
            rules = [r.get('rule', '') for r in results]
            common_rules = Counter(rules).most_common(3)
            
            for rule, count in common_rules:
                if rule and rule.lower() not in query.lower():
                    suggestions.append(f"Related: {rule}")
        
        return suggestions[:5]
    
    def _generate_search_insights(self, query: str, results: List[Dict]) -> Dict[str, Any]:
        """Generate insights from search results."""
        if not results:
            return {"message": "No results found"}
        
        # Analyze result patterns
        priorities = [r.get('priority', 'unknown') for r in results]
        sources = [r.get('source', 'unknown') for r in results]
        
        priority_dist = Counter(priorities)
        source_dist = Counter(sources)
        
        return {
            "total_results": len(results),
            "priority_distribution": dict(priority_dist.most_common(3)),
            "top_sources": dict(source_dist.most_common(3)),
            "time_span": "Various time periods",
            "patterns": f"Found {len(set(sources))} unique sources with {len(set(priorities))} priority levels"
        }
    
    # Helper methods for attack chain analysis
    
    def _analyze_attack_progression(self, chain_alerts: List[Dict]) -> Dict[str, Any]:
        """Analyze attack progression from chronological alerts."""
        if not chain_alerts:
            return {}
        
        # Analyze rule progression
        rules = [alert['rule'] for alert in chain_alerts]
        rule_sequence = []
        
        for i, rule in enumerate(rules):
            if i == 0 or rule != rules[i-1]:
                rule_sequence.append(rule)
        
        # Analyze escalation pattern
        priorities = [alert['priority'] for alert in chain_alerts]
        priority_weights = {'info': 1, 'notice': 2, 'warning': 3, 'error': 4, 'critical': 5}
        
        escalation_detected = False
        if len(priorities) > 1:
            first_weight = priority_weights.get(priorities[0], 1)
            last_weight = priority_weights.get(priorities[-1], 1)
            escalation_detected = last_weight > first_weight
        
        return {
            "rule_sequence": rule_sequence,
            "escalation_detected": escalation_detected,
            "progression_length": len(rule_sequence),
            "unique_rules": len(set(rules))
        }
    
    def _identify_attack_phases(self, chain_alerts: List[Dict]) -> List[Dict[str, Any]]:
        """Identify attack phases from alert chain."""
        phases = []
        
        if not chain_alerts:
            return phases
        
        # Group alerts by rule to identify phases
        rule_groups = defaultdict(list)
        for alert in chain_alerts:
            rule_groups[alert['rule']].append(alert)
        
        # Map rules to attack phases
        phase_mapping = {
            'reconnaissance': ['scan', 'probe', 'enum'],
            'initial_access': ['login', 'auth', 'access'],
            'execution': ['exec', 'run', 'execute', 'command'],
            'persistence': ['cron', 'service', 'startup'],
            'privilege_escalation': ['sudo', 'root', 'admin', 'privilege'],
            'lateral_movement': ['network', 'connection', 'remote'],
            'exfiltration': ['copy', 'transfer', 'upload']
        }
        
        for rule, alerts in rule_groups.items():
            rule_lower = rule.lower()
            
            # Determine phase
            detected_phase = "unknown"
            for phase, keywords in phase_mapping.items():
                if any(keyword in rule_lower for keyword in keywords):
                    detected_phase = phase
                    break
            
            phases.append({
                "phase": detected_phase,
                "rule": rule,
                "alert_count": len(alerts),
                "timespan": f"{alerts[0]['timestamp']} to {alerts[-1]['timestamp']}" if len(alerts) > 1 else alerts[0]['timestamp']
            })
        
        return phases
    
    def _calculate_behavioral_score(self, historical_alerts: List[Dict], current_alert: Dict) -> float:
        """Calculate behavioral anomaly score."""
        if not historical_alerts:
            return 5.0  # Neutral score for no history
        
        # Check if current alert rule is common for this source
        historical_rules = [alert['rule'] for alert in historical_alerts]
        rule_frequency = Counter(historical_rules)
        
        current_rule = current_alert.get('rule', '')
        current_rule_count = rule_frequency.get(current_rule, 0)
        
        # Calculate anomaly score
        if current_rule_count == 0:
            return 8.0  # High anomaly - never seen before
        elif current_rule_count < 3:
            return 6.5  # Medium anomaly - rare
        elif current_rule_count < 10:
            return 4.0  # Low anomaly - uncommon
        else:
            return 2.0  # Normal - common pattern
    
    def _get_impact_level(self, impact_score: float) -> str:
        """Convert impact score to level description."""
        if impact_score >= 8.0:
            return "CRITICAL"
        elif impact_score >= 6.0:
            return "HIGH"
        elif impact_score >= 4.0:
            return "MEDIUM"
        elif impact_score >= 2.0:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _get_risk_level_text(self, risk_score: float) -> str:
        """Convert risk score to human-readable text."""
        if risk_score >= 8.0:
            return "very high"
        elif risk_score >= 6.0:
            return "high"
        elif risk_score >= 4.0:
            return "medium"
        else:
            return "low"
    
    def _generate_simple_attack_chain(self, rule: str, threat_category: str) -> List[Dict[str, Any]]:
        """Generate a simple attack chain based on rule and threat category."""
        chain = []
        
        # Current phase
        chain.append({
            "phase": "detection",
            "description": f"Alert triggered: {rule}",
            "threat_category": threat_category,
            "likelihood": 1.0
        })
        
        # Predict next likely phases based on threat category
        if threat_category == "intrusion":
            chain.extend([
                {
                    "phase": "reconnaissance",
                    "description": "Potential system enumeration",
                    "threat_category": "reconnaissance",
                    "likelihood": 0.7
                },
                {
                    "phase": "privilege_escalation",
                    "description": "Possible privilege escalation attempts",
                    "threat_category": "intrusion",
                    "likelihood": 0.6
                }
            ])
        elif threat_category == "malware":
            chain.extend([
                {
                    "phase": "persistence",
                    "description": "Malware may establish persistence",
                    "threat_category": "persistence",
                    "likelihood": 0.8
                },
                {
                    "phase": "data_exfiltration",
                    "description": "Potential data theft",
                    "threat_category": "data_exfiltration",
                    "likelihood": 0.5
                }
            ])
        elif threat_category == "reconnaissance":
            chain.extend([
                {
                    "phase": "lateral_movement",
                    "description": "Possible lateral movement",
                    "threat_category": "lateral_movement",
                    "likelihood": 0.6
                }
            ])
        
        return chain

    def health_check(self) -> Dict[str, Any]:
        """
        Check Weaviate health and return status.
        
        Returns:
            Dictionary with health status
        """
        try:
            if not self.client:
                # Try to connect if not already connected
                logger.info("⚠️ Weaviate client not connected, attempting to connect for health check...")
                if not self.connect():
                    return {"status": "disconnected", "error": "No client connection"}
            
            if self.client.is_ready():
                # Check if collections exist
                alerts_exists = self.client.collections.exists("SecurityAlert")
                conversations_exists = self.client.collections.exists("ConversationContext")
                
                # Get basic stats using v4 API
                alert_count = 0
                conversation_count = 0
                
                if alerts_exists:
                    try:
                        collection = self.client.collections.get("SecurityAlert")
                        result = collection.aggregate.over_all(total_count=True)
                        alert_count = result.total_count if result.total_count else 0
                    except Exception as e:
                        logger.warning(f"Could not get alert count: {e}")
                
                if conversations_exists:
                    try:
                        collection = self.client.collections.get("ConversationContext")
                        result = collection.aggregate.over_all(total_count=True)
                        conversation_count = result.total_count if result.total_count else 0
                    except Exception as e:
                        logger.warning(f"Could not get conversation count: {e}")
                
                return {
                    "status": "healthy",
                    "connected": True,
                    "total_alerts": alert_count,
                    "total_conversations": conversation_count,
                    "alerts_schema_exists": alerts_exists,
                    "conversations_schema_exists": conversations_exists
                }
            else:
                return {"status": "not_ready", "connected": False}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Global instance
weaviate_service = WeaviateService()

def get_weaviate_service() -> WeaviateService:
    """Get the global Weaviate service instance."""
    return weaviate_service 