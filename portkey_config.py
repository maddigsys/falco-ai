import os
from portkey_ai import Portkey
import logging

def initialize_portkey_clients():
    """
    Initializes Portkey clients for OpenAI and/or Gemini based on environment variables.

    Returns:
        tuple: A tuple containing (portkey_client_openai, portkey_client_gemini).
               Clients for providers not configured will be None.
    """
    portkey_api_key = os.environ.get("PORTKEY_API_KEY")
    provider_name = os.environ.get("PROVIDER_NAME") # Get PROVIDER_NAME, default to openai
    virtual_key_openai = os.environ.get("OPENAI_VIRTUAL_KEY")
    virtual_key_gemini = os.environ.get("GEMINI_VIRTUAL_KEY")

    portkey_client_openai = None # Initialize as None
    portkey_client_gemini = None # Initialize as None

    if not portkey_api_key:
        logging.error("PORTKEY_API_KEY environment variable is not set.")
        return None, None  # Return None tuple if API key is missing

    try:
        if provider_name == "openai":
            if virtual_key_openai:
                portkey_client_openai = Portkey(
                    api_key=portkey_api_key,
                    virtual_key=virtual_key_openai
                )
                logging.info("Portkey OpenAI client initialized.")
            else:
                logging.warning("OPENAI_VIRTUAL_KEY environment variable is not set, but PROVIDER_NAME is 'openai'. OpenAI client will not be initialized.")

        elif provider_name == "gemini":
            if virtual_key_gemini:
                portkey_client_gemini = Portkey(
                    api_key=portkey_api_key,
                    virtual_key=virtual_key_gemini
                )
                logging.info("Portkey Gemini client initialized.")
            else:
                logging.warning("GEMINI_VIRTUAL_KEY environment variable is not set, but PROVIDER_NAME is 'gemini'. Gemini client will not be initialized.")
        elif provider_name == "ollama":
            logging.info("Ollama provider selected - using local LLM (no Portkey required).")
            # Ollama doesn't use Portkey, so we return None for both clients
            return None, None
        else:
            logging.error(f"Invalid PROVIDER_NAME: '{provider_name}'. Please choose 'openai', 'gemini', or 'ollama'. No clients initialized.")
            return None, None # Return None tuple for invalid provider

        if provider_name == "openai" and portkey_client_openai: # Log success only if client was actually initialized
            logging.info("Portkey clients initialized successfully in portkey_config.py for OpenAI.")
        elif provider_name == "gemini" and portkey_client_gemini: # Log success only if client was actually initialized
             logging.info("Portkey clients initialized successfully in portkey_config.py for Gemini.")
        elif provider_name == "ollama":
            logging.info("Ollama provider configured - ready for local LLM inference.")
        elif provider_name not in ["openai", "gemini", "ollama"]: # No success log for invalid provider
            pass # Already logged error above
        elif not portkey_client_openai and not portkey_client_gemini: # Log warning if no clients initialized due to missing virtual keys for valid provider
            logging.warning("No Portkey clients were initialized. Check virtual key environment variables and PROVIDER_NAME.")


        return portkey_client_openai, portkey_client_gemini

    except Exception as e:
        logging.error(f"Error initializing Portkey clients in portkey_config.py: {e}")
        return None, None

if __name__ == '__main__':
    # Example usage to test initialization
    logging.basicConfig(level=logging.INFO) # Set logging level for testing in portkey_config.py
    openai_client, gemini_client = initialize_portkey_clients()
    if openai_client or gemini_client: # Check if at least one client is initialized
        print("Portkey clients initialized successfully when running portkey_config.py directly.")
    else:
        print("Portkey client initialization failed when running portkey_config.py directly. Check logs for errors.")