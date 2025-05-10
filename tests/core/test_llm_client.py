import pytest
from unittest.mock import patch, MagicMock, call
import streamlit as st # Required for st.session_state access pattern
from google.api_core import exceptions as google_api_exceptions
import google.generativeai as genai
from google.auth import exceptions as google_auth_exceptions # For DefaultCredentialsError

# Functions to test
from core.llm_client import get_api_key, configure_llm_client, generate_text

# Initialize st.session_state if it's not already a MagicMock (for test environment)
if not isinstance(st.session_state, MagicMock):
    st.session_state = MagicMock()

class TestLLMClientFunctions:

    def setup_method(self, method):
        """
        Reset st.session_state for each test to ensure independence.
        """
        # Using a dictionary for st.session_state allows direct key access
        # and checking for key existence, which is how Streamlit's SessionState works.
        st.session_state = {}

    @patch('core.llm_client.st.sidebar.text_input')
    @patch('core.llm_client.st.sidebar.warning')
    @patch('core.llm_client.st.rerun')
    def test_get_api_key_from_session_state(self, mock_rerun, mock_warning, mock_text_input):
        st.session_state.api_key = "test_api_key_from_state"
        api_key = get_api_key()
        assert api_key == "test_api_key_from_state"
        mock_text_input.assert_not_called()
        mock_warning.assert_not_called()
        mock_rerun.assert_not_called()

    @patch('core.llm_client.st.sidebar.text_input')
    @patch('core.llm_client.st.sidebar.warning')
    @patch('core.llm_client.st.rerun')
    def test_get_api_key_from_user_input(self, mock_rerun, mock_warning, mock_text_input):
        # Simulate user entering text
        mock_text_input.return_value = "test_api_key_from_input"
        
        # First call to get_api_key when key is not in session_state
        # This call will set the key and call rerun
        get_api_key()

        # Assertions for the first call
        mock_text_input.assert_called_once_with(
            "Enter your Google AI Studio API Key:",
            type="password",
            help="You can get your API key from Google AI Studio.",
            key="api_key_input_widget"
        )
        assert st.session_state.api_key == "test_api_key_from_input"
        mock_rerun.assert_called_once() # Rerun is called after setting the key
        mock_warning.assert_not_called() # Warning should not be called if key is provided

    @patch('core.llm_client.st.sidebar.text_input')
    @patch('core.llm_client.st.sidebar.warning')
    @patch('core.llm_client.st.rerun')
    def test_get_api_key_no_input_provided(self, mock_rerun, mock_warning, mock_text_input):
        mock_text_input.return_value = "" # Simulate user providing no input
        api_key = get_api_key()
        assert api_key is None
        mock_text_input.assert_called_once()
        mock_warning.assert_called_once_with("API Key is required to use LLM features.")
        mock_rerun.assert_not_called()
        assert "api_key" not in st.session_state or not st.session_state.api_key

    @patch('core.llm_client.get_api_key')
    @patch('core.llm_client.genai.configure')
    @patch('core.llm_client.st.sidebar.error')
    def test_configure_llm_client_success(self, mock_sidebar_error, mock_genai_configure, mock_get_api_key):
        mock_get_api_key.return_value = "valid_api_key"
        result = configure_llm_client()
        assert result is True
        mock_genai_configure.assert_called_once_with(api_key="valid_api_key")
        mock_sidebar_error.assert_not_called()
        assert "api_key" not in st.session_state # api_key is not deleted on success

    @patch('core.llm_client.get_api_key')
    @patch('core.llm_client.genai.configure')
    @patch('core.llm_client.st.sidebar.error')
    def test_configure_llm_client_no_api_key(self, mock_sidebar_error, mock_genai_configure, mock_get_api_key):
        mock_get_api_key.return_value = None
        result = configure_llm_client()
        assert result is False
        mock_genai_configure.assert_not_called()
        mock_sidebar_error.assert_not_called() # Error handled by get_api_key or generate_text

    @patch('core.llm_client.get_api_key')
    @patch('core.llm_client.genai.configure', side_effect=google_api_exceptions.PermissionDenied("Permission Denied"))
    @patch('core.llm_client.st.sidebar.error')
    def test_configure_llm_client_permission_denied(self, mock_sidebar_error, mock_genai_configure, mock_get_api_key):
        mock_get_api_key.return_value = "invalid_api_key"
        st.session_state.api_key = "invalid_api_key" # Simulate key was set
        result = configure_llm_client()
        assert result is False
        mock_genai_configure.assert_called_once_with(api_key="invalid_api_key")
        mock_sidebar_error.assert_called_once()
        assert "Permission denied" in mock_sidebar_error.call_args[0][0]
        assert "api_key" not in st.session_state # API key should be deleted

    @patch('core.llm_client.get_api_key')
    @patch('core.llm_client.genai.configure', side_effect=google_auth_exceptions.DefaultCredentialsError("Default Credentials Error"))
    @patch('core.llm_client.st.sidebar.error')
    def test_configure_llm_client_default_credentials_error(self, mock_sidebar_error, mock_genai_configure, mock_get_api_key):
        # Note: The current code catches generic Exception for this, not specifically DefaultCredentialsError.
        # This test assumes we want to test if DefaultCredentialsError (as an Exception subclass) is handled.
        mock_get_api_key.return_value = "some_api_key"
        st.session_state.api_key = "some_api_key"
        result = configure_llm_client()
        assert result is False
        mock_genai_configure.assert_called_once_with(api_key="some_api_key")
        mock_sidebar_error.assert_called_once()
        assert "DefaultCredentialsError" in mock_sidebar_error.call_args[0][0]
        assert "api_key" not in st.session_state

    @patch('core.llm_client.get_api_key')
    @patch('core.llm_client.genai.configure', side_effect=Exception("Some other configuration error"))
    @patch('core.llm_client.st.sidebar.error')
    def test_configure_llm_client_other_exception(self, mock_sidebar_error, mock_genai_configure, mock_get_api_key):
        mock_get_api_key.return_value = "another_api_key"
        st.session_state.api_key = "another_api_key"
        result = configure_llm_client()
        assert result is False
        mock_genai_configure.assert_called_once_with(api_key="another_api_key")
        mock_sidebar_error.assert_called_once_with("Failed to configure LLM client: Exception - Some other configuration error")
        assert "api_key" not in st.session_state

    @patch('core.llm_client.configure_llm_client')
    @patch('core.llm_client.genai.GenerativeModel')
    @patch('core.llm_client.st.error')
    def test_generate_text_success(self, mock_st_error, mock_generative_model, mock_configure_llm):
        mock_configure_llm.return_value = True
        mock_model_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Generated text"
        mock_model_instance.generate_content.return_value = mock_response
        mock_generative_model.return_value = mock_model_instance

        prompt = "Test prompt"
        model_name = "test-model"
        temperature = 0.5
        
        result = generate_text(prompt, model_name=model_name, temperature=temperature)

        assert result == "Generated text"
        mock_configure_llm.assert_called_once()
        mock_generative_model.assert_called_once_with(model_name)
        
        # Check that GenerationConfig was created and passed correctly
        args, kwargs = mock_model_instance.generate_content.call_args
        assert args[0] == prompt
        assert 'generation_config' in kwargs
        gen_config = kwargs['generation_config']
        assert isinstance(gen_config, genai.types.GenerationConfig)
        assert gen_config.temperature == temperature
        
        mock_st_error.assert_not_called()

    @patch('core.llm_client.configure_llm_client')
    @patch('core.llm_client.st.error')
    def test_generate_text_config_failed(self, mock_st_error, mock_configure_llm):
        mock_configure_llm.return_value = False
        result = generate_text("Test prompt")
        assert result is None
        mock_configure_llm.assert_called_once()
        mock_st_error.assert_called_once_with("LLM client not configured. Please enter your API key.")

    @patch('core.llm_client.configure_llm_client', return_value=True)
    @patch('core.llm_client.genai.GenerativeModel')
    @patch('core.llm_client.st.error')
    def test_generate_text_google_api_error_resource_exhausted(self, mock_st_error, mock_generative_model, mock_configure_llm):
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = google_api_exceptions.ResourceExhausted("Rate limit")
        mock_generative_model.return_value = mock_model_instance

        result = generate_text("Test prompt")
        assert result is None
        mock_st_error.assert_called_once()
        assert "API Error: Rate limit exceeded or quota exhausted." in mock_st_error.call_args[0][0]

    @patch('core.llm_client.configure_llm_client', return_value=True)
    @patch('core.llm_client.genai.GenerativeModel')
    @patch('core.llm_client.st.error')
    def test_generate_text_other_exception(self, mock_st_error, mock_generative_model, mock_configure_llm):
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = Exception("Unexpected error")
        mock_generative_model.return_value = mock_model_instance

        result = generate_text("Test prompt")
        assert result is None
        mock_st_error.assert_called_once_with("An unexpected error occurred while generating text: Exception - Unexpected error")

    @patch('core.llm_client.configure_llm_client', return_value=True)
    @patch('core.llm_client.genai.GenerativeModel')
    @patch('core.llm_client.st.error')
    def test_generate_text_attribute_error_on_response(self, mock_st_error, mock_generative_model, mock_configure_llm):
        mock_model_instance = MagicMock()
        # Simulate a response object that doesn't have a .text attribute directly
        # This could happen if generate_content returns something unexpected or if .text itself raises an error
        mock_response_without_text = MagicMock()
        del mock_response_without_text.text # Ensure .text is not present
        # OR, make .text raise an AttributeError when accessed
        # type(mock_response_without_text).text = PropertyMock(side_effect=AttributeError("no text"))

        mock_model_instance.generate_content.return_value = mock_response_without_text
        # To more directly test the AttributeError catch block for response.text:
        # We can make the .text access raise the error.
        # The current code has `return response.text`. If response itself is fine, but .text access fails:
        
        mock_response_problematic_text = MagicMock()
        # Make accessing .text raise an AttributeError
        type(mock_response_problematic_text).text = MagicMock(side_effect=AttributeError("Simulated error accessing text"))
        mock_model_instance.generate_content.return_value = mock_response_problematic_text

        mock_generative_model.return_value = mock_model_instance

        result = generate_text("Test prompt for attribute error")
        assert result is None
        mock_st_error.assert_called_once()
        assert "Error processing LLM response: Simulated error accessing text" in mock_st_error.call_args[0][0]

    # Example for a specific GoogleAPIError like InvalidArgument
    @patch('core.llm_client.configure_llm_client', return_value=True)
    @patch('core.llm_client.genai.GenerativeModel')
    @patch('core.llm_client.st.error')
    def test_generate_text_google_api_error_invalid_argument(self, mock_st_error, mock_generative_model, mock_configure_llm):
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = google_api_exceptions.InvalidArgument("Invalid arg")
        mock_generative_model.return_value = mock_model_instance

        result = generate_text("Test prompt")
        assert result is None
        mock_st_error.assert_called_once()
        assert "API Error: Invalid argument in the request." in mock_st_error.call_args[0][0]

    @patch('core.llm_client.configure_llm_client', return_value=True)
    @patch('core.llm_client.genai.GenerativeModel')
    @patch('core.llm_client.st.error')
    def test_generate_text_google_api_error_permission_denied(self, mock_st_error, mock_generative_model, mock_configure_llm):
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = google_api_exceptions.PermissionDenied("Permission denied by API")
        mock_generative_model.return_value = mock_model_instance

        result = generate_text("Test prompt for permission denied")
        assert result is None
        mock_st_error.assert_called_once()
        assert "API Error: Permission denied. Check your API key." in mock_st_error.call_args[0][0]

    @patch('core.llm_client.configure_llm_client', return_value=True)
    @patch('core.llm_client.genai.GenerativeModel')
    @patch('core.llm_client.st.error')
    def test_generate_text_google_api_error_failed_precondition(self, mock_st_error, mock_generative_model, mock_configure_llm):
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = google_api_exceptions.FailedPrecondition("Failed precondition")
        mock_generative_model.return_value = mock_model_instance

        result = generate_text("Test prompt for failed precondition")
        assert result is None
        mock_st_error.assert_called_once()
        assert "API Error: Failed precondition." in mock_st_error.call_args[0][0]

    @patch('core.llm_client.configure_llm_client', return_value=True)
    @patch('core.llm_client.genai.GenerativeModel')
    @patch('core.llm_client.st.error')
    def test_generate_text_google_api_error_not_found(self, mock_st_error, mock_generative_model, mock_configure_llm):
        mock_model_instance = MagicMock()
        model_name_used = "non-existent-model"
        mock_model_instance.generate_content.side_effect = google_api_exceptions.NotFound(f"Model {model_name_used} not found")
        mock_generative_model.return_value = mock_model_instance

        result = generate_text("Test prompt for not found", model_name=model_name_used)
        assert result is None
        mock_st_error.assert_called_once()
        assert f"API Error: Resource not found (e.g., model name '{model_name_used}' is incorrect)." in mock_st_error.call_args[0][0]

    @patch('core.llm_client.configure_llm_client', return_value=True)
    @patch('core.llm_client.genai.GenerativeModel')
    @patch('core.llm_client.st.error')
    def test_generate_text_google_api_error_internal_server_error(self, mock_st_error, mock_generative_model, mock_configure_llm):
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = google_api_exceptions.InternalServerError("Internal server error")
        mock_generative_model.return_value = mock_model_instance

        result = generate_text("Test prompt for internal server error")
        assert result is None
        mock_st_error.assert_called_once()
        assert "API Error: Internal server error on Google's side." in mock_st_error.call_args[0][0]

    @patch('core.llm_client.configure_llm_client', return_value=True)
    @patch('core.llm_client.genai.GenerativeModel')
    @patch('core.llm_client.st.error')
    def test_generate_text_google_api_error_service_unavailable(self, mock_st_error, mock_generative_model, mock_configure_llm):
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = google_api_exceptions.ServiceUnavailable("Service unavailable")
        mock_generative_model.return_value = mock_model_instance

        result = generate_text("Test prompt for service unavailable")
        assert result is None
        mock_st_error.assert_called_once()
        assert "API Error: Service unavailable." in mock_st_error.call_args[0][0]

    # Test for ValueError (as requested, though not explicitly handled for blocked content in current code)
    # The current code catches general Exception for this.
    @patch('core.llm_client.configure_llm_client', return_value=True)
    @patch('core.llm_client.genai.GenerativeModel')
    @patch('core.llm_client.st.error')
    def test_generate_text_value_error(self, mock_st_error, mock_generative_model, mock_configure_llm):
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.side_effect = ValueError("Simulated Value Error")
        mock_generative_model.return_value = mock_model_instance

        result = generate_text("Test prompt for value error")
        assert result is None
        mock_st_error.assert_called_once()
        # This will be caught by the generic Exception handler
        assert "An unexpected error occurred while generating text: ValueError - Simulated Value Error" in mock_st_error.call_args[0][0]