import pytest
import yaml
import os
from unittest.mock import patch
from core.prompt_manager import get_prompt, PROMPT_CONFIG_BASE_DIR

class TestPromptManager:

    @pytest.fixture(autouse=True)
    def mock_getcwd(self, tmp_path, monkeypatch):
        """Fixture to mock os.getcwd() to return tmp_path for all tests in this class."""
        monkeypatch.setattr('core.prompt_manager.os.getcwd', lambda: str(tmp_path))

    def test_load_valid_prompt_from_module(self, tmp_path):
        module_name = "test_module"
        prompt_key = "valid_prompt"
        prompts_module_dir = tmp_path / PROMPT_CONFIG_BASE_DIR / module_name
        prompts_module_dir.mkdir(parents=True, exist_ok=True)
        
        valid_prompt_file = prompts_module_dir / f"{prompt_key}.yaml"
        valid_prompt_content = {
            "name": "Test Valid Prompt",
            "description": "A test prompt from module.",
            "instructions": "These are test instructions.",
        }
        with open(valid_prompt_file, 'w') as f:
            yaml.dump(valid_prompt_content, f)

        prompt_data = get_prompt(prompt_key, module=module_name)
        assert prompt_data is not None
        assert prompt_data["name"] == "Test Valid Prompt"
        assert prompt_data["description"] == "A test prompt from module."

    def test_load_valid_prompt_from_module_with_extension(self, tmp_path):
        module_name = "test_module_ext"
        prompt_key_with_ext = "valid_prompt_ext.yaml"
        prompts_module_dir = tmp_path / PROMPT_CONFIG_BASE_DIR / module_name
        prompts_module_dir.mkdir(parents=True, exist_ok=True)
        
        valid_prompt_file = prompts_module_dir / prompt_key_with_ext
        valid_prompt_content = {"name": "Test Valid Prompt Ext"}
        with open(valid_prompt_file, 'w') as f:
            yaml.dump(valid_prompt_content, f)

        prompt_data = get_prompt(prompt_key_with_ext, module=module_name)
        assert prompt_data is not None
        assert prompt_data["name"] == "Test Valid Prompt Ext"

    def test_load_valid_prompt_from_base_config_fallback(self, tmp_path):
        # This test relies on the fallback mechanism in get_prompt
        prompt_key = "direct_prompt"
        prompts_base_dir = tmp_path / PROMPT_CONFIG_BASE_DIR
        prompts_base_dir.mkdir(parents=True, exist_ok=True) # Ensure base prompt dir exists

        # Create a module dir to make the first lookup fail
        module_name = "non_existent_module_for_fallback"
        # (tmp_path / PROMPT_CONFIG_BASE_DIR / module_name).mkdir(parents=True, exist_ok=True)


        valid_prompt_file = prompts_base_dir / f"{prompt_key}.yaml"
        valid_prompt_content = {
            "name": "Test Direct Prompt",
            "description": "A test prompt from base config.",
        }
        with open(valid_prompt_file, 'w') as f:
            yaml.dump(valid_prompt_content, f)
        
        # Call get_prompt with a module that won't contain the file, to trigger fallback
        prompt_data = get_prompt(prompt_key, module=module_name)
        assert prompt_data is not None
        assert prompt_data["name"] == "Test Direct Prompt"
        assert prompt_data["description"] == "A test prompt from base config."

    def test_get_prompt_file_not_found(self, tmp_path):
        # Ensure no file exists for this key
        prompt_data = get_prompt("non_existent_prompt", module="test_module_not_found")
        assert prompt_data is None

    def test_get_prompt_malformed_yaml(self, tmp_path):
        module_name = "test_malformed_module"
        prompt_key = "malformed_prompt"
        prompts_module_dir = tmp_path / PROMPT_CONFIG_BASE_DIR / module_name
        prompts_module_dir.mkdir(parents=True, exist_ok=True)
        
        malformed_prompt_file = prompts_module_dir / f"{prompt_key}.yaml"
        with open(malformed_prompt_file, 'w') as f:
            f.write("name: Test Malformed\ndescription: Bad YAML format because of this tab:\t- item")

        prompt_data = get_prompt(prompt_key, module=module_name)
        assert prompt_data is None

    def test_get_prompt_non_existent_module_dir(self, tmp_path):
        # Attempt to load a prompt from a module directory that doesn't exist
        # This should also result in the prompt not being found and returning None
        prompt_data = get_prompt("some_prompt_in_ghost_module", module="ghost_module")
        assert prompt_data is None