"""
Weaviate Service Layer for Falco AI Alert System

This module provides vector storage and semantic search capabilities
for security alerts, enabling pattern recognition and contextual analysis.
"""

import weaviate
import weaviate.classes as wvc
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeaviateService:
    """Service class for managing Weaviate operations for security alerts."""
    
    def __init__(self, host: str = "localhost", port: int = 8080, grpc_port: int = 50051):
        """
        Initialize Weaviate service.
        
        Args:
            host: Weaviate host
            port: Weaviate HTTP port
            grpc_port: Weaviate gRPC port
        """
        self.host = host
        self.port = port
        self.grpc_port = grpc_port
        self.client = None
        
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
                existing = collection.query.fetch_objects(
                    limit=1,
                    where=wvc.query.Filter.by_property("alertHash").equal(alert_hash)
                )
            except Exception as e:
                logger.warning(f"Could not check for existing alert: {e}")
                existing = wvc.query.QueryReturn(objects=[])
            
            if existing.objects:
                logger.info(f"🔄 Alert already exists with hash {alert_hash}")
                return str(existing.objects[0].uuid)
            
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
            
            # Prepare the data object
            properties = {
                "rule": alert_data.get("rule", ""),
                "priority": alert_data.get("priority", ""),
                "output": alert_data.get("output", ""),
                "source": alert_data.get("output_fields", {}).get("container.name", "unknown"),
                "timestamp": alert_data.get("time", datetime.now().isoformat()),
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
                    
                    # Query with text filters
                    result = collection.query.fetch_objects(
                        limit=limit,
                        where=combined_filter,
                        return_properties=[
                            "rule", "priority", "output", "source", "timestamp", 
                            "securityImpact", "nextSteps", "remediationSteps", 
                            "suggestedCommands", "aiProvider", "command"
                        ]
                    )
                else:
                    # No keywords, return recent alerts
                    result = collection.query.fetch_objects(
                        limit=limit,
                        return_properties=[
                            "rule", "priority", "output", "source", "timestamp", 
                            "securityImpact", "nextSteps", "remediationSteps", 
                            "suggestedCommands", "aiProvider", "command"
                        ]
                    )
            
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
            # Get recent alerts
            from_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get the collection
            collection = self.client.collections.get("SecurityAlert")
            
            # Query using v4 API - fix syntax
            try:
                result = collection.query.fetch_objects(
                    limit=1000,
                    return_properties=["rule", "priority", "timestamp", "source"],
                    where=wvc.query.Filter.by_property("timestamp").greater_than(from_date)
                )
            except Exception as e:
                logger.warning(f"Could not fetch alerts for pattern analysis: {e}")
                result = wvc.query.QueryReturn(objects=[])
            
            alerts = result.objects
            
            # Analyze patterns
            patterns = {
                "total_alerts": len(alerts),
                "rule_frequency": {},
                "priority_distribution": {},
                "source_distribution": {},
                "timeline": []
            }
            
            for alert in alerts:
                properties = alert.properties
                
                # Rule frequency
                rule = properties.get("rule", "Unknown")
                patterns["rule_frequency"][rule] = patterns["rule_frequency"].get(rule, 0) + 1
                
                # Priority distribution
                priority = properties.get("priority", "Unknown")
                patterns["priority_distribution"][priority] = patterns["priority_distribution"].get(priority, 0) + 1
                
                # Source distribution
                source = properties.get("source", "Unknown")
                patterns["source_distribution"][source] = patterns["source_distribution"].get(source, 0) + 1
            
            logger.info(f"📊 Analyzed {len(alerts)} alerts from the last {days} days")
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze patterns: {e}")
            return {}
    
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
                # Check if collection exists
                collection_exists = self.client.collections.exists("SecurityAlert")
                
                # Get basic stats using v4 API
                count = 0
                if collection_exists:
                    try:
                        collection = self.client.collections.get("SecurityAlert")
                        # Use aggregate to get count
                        result = collection.aggregate.over_all(total_count=True)
                        count = result.total_count if result.total_count else 0
                    except Exception as e:
                        logger.warning(f"Could not get count: {e}")
                        count = 0
                
                return {
                    "status": "healthy",
                    "connected": True,
                    "total_alerts": count,
                    "schema_exists": collection_exists
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