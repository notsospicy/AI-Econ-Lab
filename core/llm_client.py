import streamlit as st
import google.generativeai as genai
import os

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
            # st.sidebar.success("LLM Client Configured.")
            return True
        except Exception as e:
            st.sidebar.error(f"Failed to configure LLM client: {e}")
            # Invalidate the stored key if configuration fails
            if "api_key" in st.session_state:
                del st.session_state.api_key
            return False
    return False

def generate_text(prompt: str, model_name: str = "gemini-pro", temperature: float = 0.7) -> str | None:
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
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=temperature))
        return response.text
    except Exception as e:
        st.error(f"Error generating text: {e}")
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