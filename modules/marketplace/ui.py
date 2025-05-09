import streamlit as st
from .logic import run_marketplace_simulation, process_simulation_results_for_display
from core.llm_client import get_api_key, configure_llm_client # For LLM agent type
from core.prompt_manager import get_prompt # For LLM agent type, to pass to LLMAgent
from core import llm_client as llm_client_module # To pass the module itself
from core import prompt_manager as prompt_manager_module # To pass the module itself


def render_marketplace_module():
    """
    Renders the Streamlit UI for the Marketplace Module.
    Allows users to configure and run a market simulation.
    """
    st.header("Module 1: The Multi-Agent LLM Marketplace")
    st.markdown("""
    Observe how supply, demand, and price discovery mechanisms function in a market.
    LLM agents (buyers, sellers) interact over rounds to trade a good, demonstrating price discovery.
    """)

    st.sidebar.subheader("Marketplace Simulation Setup")
    
    # Agent Type Selection
    agent_type_options = ["rule_based", "llm"]
    # Ensure session state for agent_type is initialized
    if "marketplace_agent_type" not in st.session_state:
        st.session_state.marketplace_agent_type = "rule_based"

    selected_agent_type = st.sidebar.selectbox(
        "Select Agent Type:",
        options=agent_type_options,
        index=agent_type_options.index(st.session_state.marketplace_agent_type),
        key="marketplace_agent_type_selector"
    )
    st.session_state.marketplace_agent_type = selected_agent_type


    # LLM Configuration (only if agent_type is 'llm')
    llm_configured_successfully = False
    if st.session_state.marketplace_agent_type == "llm":
        st.sidebar.markdown("---")
        st.sidebar.markdown("**LLM Configuration**")
        # Use the get_api_key and configure_llm_client from core.llm_client
        # This will prompt for API key if not already set in session_state
        if "llm_client_configured_marketplace" not in st.session_state:
             st.session_state.llm_client_configured_marketplace = False
        
        if not st.session_state.llm_client_configured_marketplace:
            # This will render the API key input if needed
            st.session_state.llm_client_configured_marketplace = configure_llm_client() 
        
        if st.session_state.get("api_key") and st.session_state.llm_client_configured_marketplace:
            st.sidebar.success("LLM Client Ready (using Google AI Studio).")
            llm_configured_successfully = True
        else:
            st.sidebar.warning("LLM Client not configured. Please enter API key above.")
            # No need to call get_api_key() again here, configure_llm_client() handles it.

    st.sidebar.markdown("---")
    # Simulation Parameters
    num_buyers = st.sidebar.number_input("Number of Buyer Agents:", min_value=1, max_value=50, value=st.session_state.get("mp_num_buyers", 5), key="mp_num_buyers")
    buyer_initial_funds = st.sidebar.number_input("Buyer Initial Funds:", min_value=100, max_value=10000, value=st.session_state.get("mp_buyer_funds", 1000), step=100, key="mp_buyer_funds")
    buyer_valuation_min = st.sidebar.number_input("Buyer Valuation (Min):", min_value=50, max_value=500, value=st.session_state.get("mp_buyer_val_min", 100), step=10, key="mp_buyer_val_min")
    buyer_valuation_max = st.sidebar.number_input("Buyer Valuation (Max):", min_value=buyer_valuation_min + 10, max_value=600, value=st.session_state.get("mp_buyer_val_max", 150), step=10, key="mp_buyer_val_max")

    st.sidebar.markdown("---")
    num_sellers = st.sidebar.number_input("Number of Seller Agents:", min_value=1, max_value=50, value=st.session_state.get("mp_num_sellers", 5), key="mp_num_sellers")
    seller_initial_inventory = st.sidebar.number_input("Seller Initial Inventory (per agent):", min_value=1, max_value=1000, value=st.session_state.get("mp_seller_inv", 50), step=10, key="mp_seller_inv")
    seller_cost_min = st.sidebar.number_input("Seller Cost (Min):", min_value=10, max_value=400, value=st.session_state.get("mp_seller_cost_min", 70), step=10, key="mp_seller_cost_min")
    seller_cost_max = st.sidebar.number_input("Seller Cost (Max):", min_value=seller_cost_min + 10, max_value=500, value=st.session_state.get("mp_seller_cost_max", 120), step=10, key="mp_seller_cost_max")
    
    st.sidebar.markdown("---")
    num_rounds = st.sidebar.number_input("Number of Simulation Rounds:", min_value=1, max_value=100, value=st.session_state.get("mp_num_rounds", 20), key="mp_num_rounds")

    # Store params in session state to persist them across reruns
    st.session_state.mp_num_buyers = num_buyers
    st.session_state.mp_buyer_funds = buyer_initial_funds
    st.session_state.mp_buyer_val_min = buyer_valuation_min
    st.session_state.mp_buyer_val_max = buyer_valuation_max
    st.session_state.mp_num_sellers = num_sellers
    st.session_state.mp_seller_inv = seller_initial_inventory
    st.session_state.mp_seller_cost_min = seller_cost_min
    st.session_state.mp_seller_cost_max = seller_cost_max
    st.session_state.mp_num_rounds = num_rounds


    if st.sidebar.button("Run Simulation", key="mp_run_simulation_button"):
        if st.session_state.marketplace_agent_type == "llm" and not llm_configured_successfully:
            st.error("Cannot run LLM-based simulation: LLM Client is not configured. Please enter your API key.")
        else:
            buyer_config = {
                "initial_funds": buyer_initial_funds,
                "valuation_or_cost_range": (buyer_valuation_min, buyer_valuation_max)
            }
            seller_config = {
                "initial_inventory": seller_initial_inventory,
                "valuation_or_cost_range": (seller_cost_min, seller_cost_max)
            }
            
            # Add prompt keys if LLM agents are used
            if st.session_state.marketplace_agent_type == "llm":
                buyer_config["llm_persona_prompt_key"] = "buyer_default" # Or make this configurable
                seller_config["llm_persona_prompt_key"] = "seller_default"


            with st.spinner("Running simulation..."):
                simulation_history = run_marketplace_simulation(
                    num_buyers=num_buyers,
                    buyer_config_params=buyer_config,
                    num_sellers=num_sellers,
                    seller_config_params=seller_config,
                    num_rounds=num_rounds,
                    agent_creation_type=st.session_state.marketplace_agent_type,
                    llm_client=llm_client_module if st.session_state.marketplace_agent_type == "llm" else None,
                    prompt_manager=prompt_manager_module if st.session_state.marketplace_agent_type == "llm" else None
                )
            st.session_state.simulation_history = simulation_history
            st.session_state.simulation_run_for_display = True # Flag to indicate results are ready
            st.rerun() # Rerun to display results immediately

    if st.session_state.get("simulation_run_for_display", False) and "simulation_history" in st.session_state:
        st.subheader("Simulation Results")
        history = st.session_state.simulation_history
        
        if not history:
            st.warning("Simulation completed but produced no history data.")
            return

        processed_data = process_simulation_results_for_display(history)

        # Basic display of results (Phase 1)
        st.write(f"Simulation completed for {history[-1].current_round} rounds.")
        
        # Display Price Chart (Placeholder for Phase 2, using st.line_chart for now)
        st.markdown("#### Price Convergence Over Rounds")
        if processed_data["average_prices"]:
            # Create a DataFrame for st.line_chart
            import pandas as pd
            price_df = pd.DataFrame({
                "Round": processed_data["rounds"],
                "Average Price": processed_data["average_prices"]
            })
            price_df = price_df.set_index("Round")
            # Filter out None values before plotting if any (though logic.py tries to avoid them)
            price_df_cleaned = price_df.dropna(subset=['Average Price'])
            if not price_df_cleaned.empty:
                st.line_chart(price_df_cleaned["Average Price"])
            else:
                st.info("No transaction data to plot average prices.")

        else:
            st.info("No average price data to display.")

        # Display Volume Chart (Placeholder for Phase 2)
        st.markdown("#### Transaction Volume Over Rounds")
        if processed_data["volumes"]:
            volume_df = pd.DataFrame({
                "Round": processed_data["rounds"],
                "Volume": processed_data["volumes"]
            })
            volume_df = volume_df.set_index("Round")
            st.bar_chart(volume_df["Volume"])
        else:
            st.info("No volume data to display.")

        # Display Transaction Log (Basic table for Phase 1)
        st.markdown("#### Transaction Log (Last 100)")
        if processed_data["all_transactions"]:
            # Convert to DataFrame for better display
            tx_df = pd.DataFrame(processed_data["all_transactions"])
            st.dataframe(tx_df.tail(100)) # Show last 100 transactions
        else:
            st.info("No transactions occurred during the simulation.")

        # Educational Content & Reflection (Placeholders)
        st.markdown("---")
        st.subheader("Reflection & Learning")
        st.markdown("""
        *   What patterns do you observe in the price and volume charts?
        *   How quickly did the market reach a stable price (if at all)?
        *   Consider how real-world markets might differ from this simplified model.
        """)
        user_reflection = st.text_area("Your thoughts and observations:", height=100, key="mp_reflection_area")


# This allows running this module UI directly for testing if needed,
# though it's meant to be called from app.py
if __name__ == "__main__":
    # To make core modules findable when running this directly:
    import sys
    import os
    # Add project root to sys.path
    # This assumes ui.py is in AI-Econ-Lab/modules/marketplace/
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Initialize session state for direct run if not already done by Streamlit
    if "marketplace_agent_type" not in st.session_state:
        st.session_state.marketplace_agent_type = "rule_based"
    if "simulation_run_for_display" not in st.session_state:
        st.session_state.simulation_run_for_display = False


    render_marketplace_module()