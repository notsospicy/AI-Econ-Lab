import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions # For specific error handling
import os

# Regarding SDK usage:
# The provided research report emphasizes using `google-genai` SDK and a `client = genai.Client()` pattern.
# The `google-genai` package is `google-generativeai` (pip install google-generativeai).
# The `import google.generativeai as genai` is standard.
# For direct Google AI Studio API access (not Vertex AI), the common pattern involves:
# 1. `genai.configure(api_key="YOUR_KEY")`
# 2. `model = genai.GenerativeModel("model-name")`
# 3. `response = model.generate_content(...)`
# A `genai.Client()` object can be created after `genai.configure()`, and models can be accessed
# via `client.get_model("model-name")`. The `client.models.generate_content(...)` syntax
# from the report seems to be a slight simplification; actual calls are typically on the model object itself.
# This implementation uses the standard `genai.GenerativeModel()` approach which is correct and documented.

# Placeholder for API key name in environment variables for more secure deployment
# For local development, we'll use session state.
# GOOGLE_API_KEY_ENV_VAR = "GOOGLE_API_KEY"

def get_api_key():
    """
    Prompts the user for their Google AI Studio API key and stores it in session_state.
    Returns the API key.
    """
    if "api_key" not in st.session_state or not st.session_state.api_key:
        api_key_input = st.sidebar.text_input(
            "Enter your Google AI Studio API Key:",
            type="password",
            help="You can get your API key from Google AI Studio.",
            key="api_key_input_widget" # Unique key for the widget
        )
        if api_key_input:
            st.session_state.api_key = api_key_input
            # Clear the input widget after storing the key
            # This is a common pattern but might require a rerun.
            # For now, let's keep it simple.
            st.rerun() # Rerun to reflect the key being stored and potentially hide the input
        else:
            st.sidebar.warning("API Key is required to use LLM features.")
            return None
    return st.session_state.api_key

def configure_llm_client():
    """
    Configures the Google Generative AI client with the API key.
    Returns True if configuration is successful, False otherwise.
    """
    api_key = get_api_key()
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Store a client instance if we decide to use client.get_model() pattern later
            # For now, genai.configure() is sufficient for genai.GenerativeModel()
            # st.session_state.gemini_client = genai.Client()
            # st.sidebar.success("LLM Client Configured.")
            return True
        except google_exceptions.PermissionDenied as e:
            st.sidebar.error(f"API Key Error: Permission denied. Please check your API key. Details: {e}")
            if "api_key" in st.session_state:
                del st.session_state.api_key
            return False
        except Exception as e: # Catch other potential configuration errors
            st.sidebar.error(f"Failed to configure LLM client: {type(e).__name__} - {e}")
            if "api_key" in st.session_state:
                del st.session_state.api_key
            return False
    return False

def generate_text(prompt: str, model_name: str = "models/gemini-2.0-flash-latest", temperature: float = 0.7) -> str | None:
    """
    Generates text using the configured Google AI model.

    Args:
        prompt (str): The prompt to send to the LLM.
        model_name (str): The name of the model to use (e.g., "gemini-pro").
        temperature (float): The temperature for generation.

    Returns:
        str | None: The generated text, or None if an error occurs.
    """
    if not configure_llm_client(): # Ensure client is configured before trying to generate
        st.error("LLM client not configured. Please enter your API key.")
        return None

    try:
        # Safety settings can be added here if needed, e.g.:
        # safety_settings = [
        #     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        #     {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        # ]
        model = genai.GenerativeModel(model_name) # safety_settings=safety_settings
        
        # Ensure generation_config is correctly formed
        gen_config = genai.types.GenerationConfig(
            temperature=temperature
            # max_output_tokens= can be added here, e.g., 2048
        )
        
        response = model.generate_content(
            prompt,
            generation_config=gen_config
        )
        return response.text
    except google_exceptions.ResourceExhausted as e:
        st.error(f"API Error: Rate limit exceeded or quota exhausted. Please try again later. Details: {e}")
    except google_exceptions.InvalidArgument as e:
        st.error(f"API Error: Invalid argument in the request. Check prompt or model. Details: {e}")
    except google_exceptions.PermissionDenied as e:
        st.error(f"API Error: Permission denied. Check your API key. Details: {e}")
    except google_exceptions.FailedPrecondition as e:
        # This can happen if, for example, billing is not enabled for a project using Vertex AI models,
        # or other preconditions are not met.
        st.error(f"API Error: Failed precondition. Details: {e}")
    except google_exceptions.NotFound as e:
        st.error(f"API Error: Resource not found (e.g., model name '{model_name}' is incorrect). Details: {e}")
    except google_exceptions.InternalServerError as e:
        st.error(f"API Error: Internal server error on Google's side. Please try again later. Details: {e}")
    except google_exceptions.ServiceUnavailable as e:
        st.error(f"API Error: Service unavailable. Please try again later. Details: {e}")
    except AttributeError as e:
        # Handles cases where response might not have .text (e.g. blocked content)
        # More specific check for response.prompt_feedback might be needed if safety settings are active
        st.error(f"Error processing LLM response: {e}. The response might have been blocked or is empty.")
        # Example: if response.candidates and response.candidates[0].finish_reason == genai.types.FinishReason.SAFETY:
        #    st.error("Response blocked due to safety settings.")
    except Exception as e: # Catch any other unexpected errors
        st.error(f"An unexpected error occurred while generating text: {type(e).__name__} - {e}")
    return None

if __name__ == "__main__":
    # Example usage within Streamlit app context (for testing this file directly)
    st.title("LLM Client Test")

    if "llm_configured" not in st.session_state:
        st.session_state.llm_configured = False

    if not st.session_state.llm_configured:
        st.session_state.llm_configured = configure_llm_client()

    if st.session_state.llm_configured:
        st.success("LLM Client is configured and ready.")
        
        example_prompt = st.text_area("Enter a prompt for the LLM:", "Explain the concept of supply and demand in simple terms.")
        
        if st.button("Generate Text"):
            if example_prompt:
                with st.spinner("Generating response..."):
                    generated_response = generate_text(example_prompt)
                if generated_response:
                    st.subheader("LLM Response:")
                    st.markdown(generated_response)
                else:
                    st.error("Failed to get a response from the LLM.")
            else:
                st.warning("Please enter a prompt.")
    else:
        st.info("Please enter your Google AI Studio API Key in the sidebar to configure the LLM client.")