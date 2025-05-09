from typing import List, Dict, Any, Optional
from core.models import AgentConfig, RuleBasedAgent, LLMAgent, MarketState
from core.simulation_engine import MarketSimulation
# For LLMAgents, we'd need these, but RuleBasedAgent doesn't need them directly here.
# from core.llm_client import generate_text # Or the client instance
# from core.prompt_manager import get_prompt

def setup_simulation_agents(
    num_buyers: int,
    buyer_config_template: Dict[str, Any], # e.g., initial_funds, valuation_or_cost_range
    num_sellers: int,
    seller_config_template: Dict[str, Any], # e.g., initial_inventory, valuation_or_cost_range
    agent_type: str = "rule_based", # "rule_based" or "llm"
    llm_client_instance: Optional[Any] = None, # Required if agent_type is "llm"
    prompt_manager_instance: Optional[Any] = None # Required if agent_type is "llm"
) -> List[RuleBasedAgent | LLMAgent]:
    """
    Creates and configures a list of agents for the simulation.
    For rule-based agents, valuation/cost can be randomized within a range if specified.
    """
    agents: List[RuleBasedAgent | LLMAgent] = []
    
    # Create Buyers
    for i in range(num_buyers):
        agent_id = f"buyer_{i+1}"
        # Deep copy template to avoid modifying it for subsequent agents
        specific_buyer_config = buyer_config_template.copy()
        specific_buyer_config["agent_id"] = agent_id
        specific_buyer_config["agent_type"] = "buyer"

        # Handle potential randomization for valuation_or_cost
        if "valuation_or_cost_range" in specific_buyer_config and \
           isinstance(specific_buyer_config["valuation_or_cost_range"], tuple) and \
           len(specific_buyer_config["valuation_or_cost_range"]) == 2:
            min_val, max_val = specific_buyer_config["valuation_or_cost_range"]
            specific_buyer_config["valuation_or_cost"] = round(random.uniform(min_val, max_val), 2)
            del specific_buyer_config["valuation_or_cost_range"] # Remove range after use

        config = AgentConfig(**specific_buyer_config)
        if agent_type == "rule_based":
            agents.append(RuleBasedAgent(config=config))
        elif agent_type == "llm":
            if not llm_client_instance or not prompt_manager_instance:
                raise ValueError("LLMClient and PromptManager instances are required for LLMAgents.")
            # Ensure llm_persona_prompt_key is set, e.g. from buyer_config_template
            if "llm_persona_prompt_key" not in specific_buyer_config:
                 specific_buyer_config["llm_persona_prompt_key"] = "buyer_default" # Default if not specified
            config_llm = AgentConfig(**specific_buyer_config) # Re-create with potentially added key
            agents.append(LLMAgent(config=config_llm, llm_client=llm_client_instance, prompt_manager=prompt_manager_instance))
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")

    # Create Sellers
    for i in range(num_sellers):
        agent_id = f"seller_{i+1}"
        specific_seller_config = seller_config_template.copy()
        specific_seller_config["agent_id"] = agent_id
        specific_seller_config["agent_type"] = "seller"

        if "valuation_or_cost_range" in specific_seller_config and \
           isinstance(specific_seller_config["valuation_or_cost_range"], tuple) and \
           len(specific_seller_config["valuation_or_cost_range"]) == 2:
            min_cost, max_cost = specific_seller_config["valuation_or_cost_range"]
            specific_seller_config["valuation_or_cost"] = round(random.uniform(min_cost, max_cost), 2)
            del specific_seller_config["valuation_or_cost_range"]

        config = AgentConfig(**specific_seller_config)
        if agent_type == "rule_based":
            agents.append(RuleBasedAgent(config=config))
        elif agent_type == "llm":
            if not llm_client_instance or not prompt_manager_instance:
                raise ValueError("LLMClient and PromptManager instances are required for LLMAgents.")
            if "llm_persona_prompt_key" not in specific_seller_config:
                 specific_seller_config["llm_persona_prompt_key"] = "seller_default" # Default if not specified
            config_llm = AgentConfig(**specific_seller_config)
            agents.append(LLMAgent(config=config_llm, llm_client=llm_client_instance, prompt_manager=prompt_manager_instance))
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")
            
    return agents

def run_marketplace_simulation(
    num_buyers: int,
    buyer_config_params: Dict[str, Any],
    num_sellers: int,
    seller_config_params: Dict[str, Any],
    num_rounds: int,
    agent_creation_type: str = "rule_based", # "rule_based" or "llm"
    # Pass llm client and prompt manager if using LLM agents
    llm_client: Optional[Any] = None, 
    prompt_manager: Optional[Any] = None
) -> List[MarketState]:
    """
    Sets up and runs a complete marketplace simulation.

    Args:
        num_buyers (int): Number of buyer agents.
        buyer_config_params (Dict[str, Any]): Configuration parameters for buyers.
            Example: {"initial_funds": 1000, "valuation_or_cost": 110} or
                     {"initial_funds": 1000, "valuation_or_cost_range": (90, 130)}
        num_sellers (int): Number of seller agents.
        seller_config_params (Dict[str, Any]): Configuration parameters for sellers.
            Example: {"initial_inventory": 10, "valuation_or_cost": 90} or
                     {"initial_inventory": 10, "valuation_or_cost_range": (70, 100)}
        num_rounds (int): Number of simulation rounds.
        agent_creation_type (str): Type of agents to create ("rule_based" or "llm").
        llm_client (Optional[Any]): Instance of LLM client, required for LLM agents.
        prompt_manager (Optional[Any]): Instance of PromptManager, required for LLM agents.


    Returns:
        List[MarketState]: The history of market states throughout the simulation.
    """
    import random # For valuation/cost randomization if used in AgentConfig

    agents = setup_simulation_agents(
        num_buyers, buyer_config_params,
        num_sellers, seller_config_params,
        agent_type=agent_creation_type,
        llm_client_instance=llm_client,
        prompt_manager_instance=prompt_manager
    )
    
    simulation = MarketSimulation(agents=agents, num_rounds=num_rounds)
    simulation_history = simulation.run_simulation()
    
    return simulation_history

def process_simulation_results_for_display(simulation_history: List[MarketState]) -> Dict[str, Any]:
    """
    Processes the simulation history to extract data suitable for UI display,
    like data for charts.

    Returns:
        A dictionary containing data like price trends, volume trends, etc.
    """
    results = {
        "rounds": [],
        "average_prices": [],
        "volumes": [],
        "num_transactions_per_round": [],
        "all_transactions": []
    }
    if not simulation_history:
        return results

    for state in simulation_history:
        results["rounds"].append(state.current_round)
        
        # Price and volume from price_history if available for that round
        price_info_for_round = next((ph for ph in reversed(state.price_history) if ph["round"] == state.current_round), None)
        if price_info_for_round:
            results["average_prices"].append(price_info_for_round.get("average_price"))
            results["volumes"].append(price_info_for_round.get("volume"))
            results["num_transactions_per_round"].append(price_info_for_round.get("num_transactions"))
        else: # No transactions in this round
            # Find the last known average price to carry forward for smoother charts, or use None/NaN
            last_avg_price = results["average_prices"][-1] if results["average_prices"] else None
            results["average_prices"].append(last_avg_price) 
            results["volumes"].append(0)
            results["num_transactions_per_round"].append(0)

        for tx in state.transaction_log:
            if tx.round == state.current_round: # Only add transactions from the current state's round
                 results["all_transactions"].append({
                    "round": tx.round,
                    "buyer_id": tx.buyer_id,
                    "seller_id": tx.seller_id,
                    "price": tx.price,
                    "quantity": tx.quantity
                })
                
    # Ensure all lists have the same length for plotting
    max_len = len(results["rounds"])
    for key in ["average_prices", "volumes", "num_transactions_per_round"]:
        if len(results[key]) < max_len:
            # Pad with Nones or last known value if appropriate
            padding = [None] * (max_len - len(results[key]))
            if results[key] and key == "average_prices": # Carry forward last price
                 padding = [results[key][-1]] * (max_len - len(results[key]))
            elif key != "average_prices": # Pad with 0 for volume/tx count
                 padding = [0] * (max_len - len(results[key]))

            results[key].extend(padding)
            
    return results


# Example Usage (for testing this file directly):
if __name__ == "__main__":
    import random # Required for setup_simulation_agents if using ranges

    print("Running Rule-Based Marketplace Simulation Example...")
    
    buyer_params = {"initial_funds": 1000, "valuation_or_cost_range": (100, 150)}
    seller_params = {"initial_inventory": 50, "valuation_or_cost_range": (80, 120)}
    
    history = run_marketplace_simulation(
        num_buyers=5,
        buyer_config_params=buyer_params,
        num_sellers=5,
        seller_config_params=seller_params,
        num_rounds=20,
        agent_creation_type="rule_based"
    )

    if history:
        print(f"\nSimulation completed for {history[-1].current_round} rounds.")
        
        processed_data = process_simulation_results_for_display(history)
        # print("\nProcessed Data for UI:")
        # print(f"Rounds: {processed_data['rounds']}")
        # print(f"Avg Prices: {processed_data['average_prices']}")
        # print(f"Volumes: {processed_data['volumes']}")
        # print(f"Transactions per round: {processed_data['num_transactions_per_round']}")
        
        # print("\nSample of all transactions (first 5):")
        # for tx_data in processed_data['all_transactions'][:5]:
        #     print(tx_data)

        # Print summary of last round
        last_round_state = history[-1]
        print(f"\n--- Summary for Last Round ({last_round_state.current_round}) ---")
        last_round_tx = [tx for tx in last_round_state.transaction_log if tx.round == last_round_state.current_round]
        if last_round_tx:
            print(f"  Transactions ({len(last_round_tx)}):")
            for tx in last_round_tx:
                print(f"    {tx.buyer_id} buys from {tx.seller_id} - Qty: {tx.quantity}, Price: {tx.price:.2f}")
        else:
            print("  No transactions in the last round.")
        
        last_price_info = next((ph for ph in reversed(last_round_state.price_history) if ph["round"] == last_round_state.current_round), None)
        if last_price_info:
            print(f"  Avg Price: {last_price_info['average_price']:.2f}, Volume: {last_price_info['volume']}")

    else:
        print("Simulation did not produce any history.")

    # Placeholder for LLM agent simulation test (requires dummy/mock llm_client and prompt_manager)
    # print("\nAttempting LLM-Based Marketplace Simulation Example (will fail without mocks)...")
    # try:
    #     from core.llm_client import LLMClient # Assuming a class
    #     from core.prompt_manager import PromptManager # Assuming a class
    #     # dummy_llm_client = LLMClient(...)
    #     # dummy_prompt_manager = PromptManager(...)
    #     history_llm = run_marketplace_simulation(
    #         num_buyers=2,
    #         buyer_config_params={"initial_funds": 1000, "valuation_or_cost": 120, "llm_persona_prompt_key": "buyer_default"},
    #         num_sellers=2,
    #         seller_config_params={"initial_inventory": 10, "valuation_or_cost": 100, "llm_persona_prompt_key": "seller_default"},
    #         num_rounds=5,
    #         agent_creation_type="llm",
    #         llm_client=None, # Replace with dummy_llm_client
    #         prompt_manager=None # Replace with dummy_prompt_manager
    #     )
    # except (ImportError, ValueError) as e:
    #     print(f"LLM simulation test skipped/failed as expected: {e}")