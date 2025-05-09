import yaml
import os
from typing import Dict, Any, Optional

# Base directory for prompts, relative to the project root.
PROMPT_CONFIG_BASE_DIR = "config/prompts"

def load_yaml_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Loads a YAML file and returns its content as a dictionary."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
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

def get_prompt(prompt_key: str, module: str = "marketplace") -> Optional[Dict[str, Any]]:
    """
    Retrieves a prompt structure from a YAML file.

    Args:
        prompt_key (str): The key or name of the prompt file (e.g., "buyer_default").
                          The ".yaml" extension is added automatically.
        module (str): The module directory under PROMPT_CONFIG_BASE_DIR
                      (e.g., "marketplace").

    Returns:
        Optional[Dict[str, Any]]: The loaded prompt structure as a dictionary,
                                   or None if an error occurs.
    """
    if not prompt_key.endswith(".yaml"):
        prompt_filename = f"{prompt_key}.yaml"
    else:
        prompt_filename = prompt_key

    # Construct the full path to the YAML file.
    # Assumes this script (prompt_manager.py) is in core/
    # and the AI-Econ-Lab directory is the current working directory or project root.
    # For robustness, especially if run from different locations, consider absolute paths
    # or paths relative to a known project root marker.
    # For now, assuming execution from project root.
    
    # project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Gets AI-Econ-Lab if core/prompt_manager.py
    # For Streamlit apps, os.getcwd() is usually the project root.
    project_root = os.getcwd() 
    file_path = os.path.join(project_root, PROMPT_CONFIG_BASE_DIR, module, prompt_filename)
    
    # print(f"Attempting to load prompt from: {file_path}") # For debugging path issues

    prompt_data = load_yaml_file(file_path)

    if prompt_data is None:
        # Try looking in the module directory directly without a sub-module if not found
        # e.g. config/prompts/some_general_prompt.yaml
        file_path_direct = os.path.join(project_root, PROMPT_CONFIG_BASE_DIR, prompt_filename)
        # print(f"Prompt not found in module '{module}', trying direct path: {file_path_direct}")
        prompt_data = load_yaml_file(file_path_direct)

    return prompt_data

# Example usage (for testing this file directly):
if __name__ == "__main__":
    # Ensure you run this from the AI-Econ-Lab project root directory for paths to work.
    print(f"Current working directory: {os.getcwd()}")
    print(f"Prompt base directory: {os.path.join(os.getcwd(), PROMPT_CONFIG_BASE_DIR)}")

    buyer_prompt = get_prompt("buyer_default", module="marketplace")
    if buyer_prompt:
        print("\nSuccessfully loaded buyer_default.yaml:")
        print(f"Persona: {buyer_prompt.get('persona')}")
        # print(f"Instructions: {buyer_prompt.get('instructions')}")
    else:
        print("\nFailed to load buyer_default.yaml")

    seller_prompt = get_prompt("seller_default.yaml", module="marketplace") # Test with .yaml extension
    if seller_prompt:
        print("\nSuccessfully loaded seller_default.yaml:")
        # print(yaml.dump(seller_prompt, indent=2))
        print(f"Persona: {seller_prompt.get('persona')}")

    non_existent_prompt = get_prompt("non_existent_prompt", module="marketplace")
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