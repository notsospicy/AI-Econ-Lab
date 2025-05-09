import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Base directory for prompts, relative to the project root.
PROMPT_CONFIG_BASE_DIR = "config/prompts"

# Project root directory, assuming this script is in core/
# AI-Econ-Lab/
# |-- core/
# |   |-- prompt_manager.py  <- __file__
# |-- config/
# |   |-- prompts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_yaml_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Loads a YAML file and returns its content as a dictionary."""
    try:
        with file_path.open('r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Prompt file not found at {file_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {file_path}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading {file_path}: {e}")
        return None

def get_prompt(prompt_key: str, module_name: str = "marketplace") -> Optional[Dict[str, Any]]:
    """
    Retrieves a prompt structure from a YAML file.

    Args:
        prompt_key (str): The key or name of the prompt file (e.g., "buyer_default").
                          The ".yaml" extension is added automatically.
        module_name (str): The module directory under PROMPT_CONFIG_BASE_DIR
                           (e.g., "marketplace").

    Returns:
        Optional[Dict[str, Any]]: The loaded prompt structure as a dictionary,
                                   or None if an error occurs.
    """
    if not prompt_key.endswith(".yaml"):
        prompt_filename = f"{prompt_key}.yaml"
    else:
        prompt_filename = prompt_key

    # Construct the path using pathlib
    # Path is relative to PROJECT_ROOT defined at the top of the file.
    file_path = PROJECT_ROOT / PROMPT_CONFIG_BASE_DIR / module_name / prompt_filename
    
    # print(f"Attempting to load prompt from: {file_path}") # For debugging path issues

    prompt_data = load_yaml_file(file_path)

    if prompt_data is None:
        # Fallback: Try looking in the PROMPT_CONFIG_BASE_DIR directly
        # (without the module_name subdirectory)
        file_path_direct = PROJECT_ROOT / PROMPT_CONFIG_BASE_DIR / prompt_filename
        # print(f"Prompt not found in module '{module_name}', trying direct path: {file_path_direct}")
        prompt_data = load_yaml_file(file_path_direct)
        
        if prompt_data is None:
            # Fallback 2: Try with base_path if PromptManager instance is used (not applicable here directly)
            # This part is more relevant if this function is part of a class with a base_path attribute.
            # For now, this function is standalone.
            # If a PromptManager class existed and had self.base_path:
            # if hasattr(self, 'base_path') and self.base_path:
            #    alt_path = Path(self.base_path) / module_name / prompt_filename
            #    prompt_data = load_yaml_file(alt_path)
            #    if prompt_data is None:
            #        alt_path_direct = Path(self.base_path) / prompt_filename
            #        prompt_data = load_yaml_file(alt_path_direct)
            pass


    return prompt_data

# Example usage (for testing this file directly):
if __name__ == "__main__":
    print(f"Project root directory: {PROJECT_ROOT}")
    print(f"Prompt base directory: {PROJECT_ROOT / PROMPT_CONFIG_BASE_DIR}")

    buyer_prompt = get_prompt("buyer_default", module_name="marketplace")
    if buyer_prompt:
        print("\nSuccessfully loaded buyer_default.yaml:")
        print(f"Persona: {buyer_prompt.get('persona')}")
        # print(f"Instructions: {buyer_prompt.get('instructions')}")
    else:
        print("\nFailed to load buyer_default.yaml")

    seller_prompt = get_prompt("seller_default.yaml", module_name="marketplace") # Test with .yaml extension
    if seller_prompt:
        print("\nSuccessfully loaded seller_default.yaml:")
        # print(yaml.dump(seller_prompt, indent=2))
        print(f"Persona: {seller_prompt.get('persona')}")

    non_existent_prompt = get_prompt("non_existent_prompt", module_name="marketplace")
    if not non_existent_prompt:
        print("\nCorrectly failed to load non_existent_prompt.yaml")

    # To test formatting (though formatting is done by the agent):
    # if buyer_prompt and isinstance(buyer_prompt.get("instructions"), str):
    #     try:
    #         formatted = buyer_prompt["instructions"].format(
    #             current_round=1,
    #             agent_funds=100,
    #             agent_inventory=0,
    #             recent_transactions_summary="None",
    #             market_bids_summary="None",
    #             market_asks_summary="Price: 150, Qty: 2",
    #             valuation=120
    #         )
    #         print("\nFormatted buyer instructions example:")
    #         print(formatted)
    #     except KeyError as e:
    #         print(f"\nError during example formatting (expected if not all keys provided): {e}")