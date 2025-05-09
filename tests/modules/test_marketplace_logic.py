import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from modules.marketplace.logic import (
    setup_simulation_agents,
    run_marketplace_simulation,
    process_simulation_results_for_display,
)
from core.models import AgentConfig, RuleBasedAgent, LLMAgent, MarketState, Transaction
from core.simulation_engine import MarketSimulation # For mocking

# --- Fixtures ---

@pytest.fixture
def rule_based_buyer_config_template():
    return {"initial_funds": 1000, "valuation_or_cost_range": (90, 110), "max_quantity_per_round": 5, "min_price_adjustment_factor": 0.95, "max_price_adjustment_factor": 1.05}

@pytest.fixture
def rule_based_seller_config_template():
    return {"initial_inventory": 100, "valuation_or_cost_range": (80, 100), "min_quantity_per_round": 1, "max_quantity_per_round": 10, "min_price_adjustment_factor": 0.98, "max_price_adjustment_factor": 1.10}

@pytest.fixture
def llm_buyer_config_template():
    return {"initial_funds": 1000, "llm_persona_prompt_key": "buyer_default", "max_quantity_per_round": 3}

@pytest.fixture
def llm_seller_config_template():
    return {"initial_inventory": 50, "llm_persona_prompt_key": "seller_default", "min_quantity_per_round": 1, "max_quantity_per_round": 8}

@pytest.fixture
def mock_llm_client():
    return MagicMock()

@pytest.fixture
def mock_prompt_manager():
    mock = MagicMock()
    mock.get_prompt.return_value = "This is a test prompt for {role}."
    return mock

# --- Tests for setup_simulation_agents ---

def test_setup_rule_based_agents(rule_based_buyer_config_template, rule_based_seller_config_template):
    num_buyers = 2
    num_sellers = 3
    agents = setup_simulation_agents(
        num_buyers, rule_based_buyer_config_template,
        num_sellers, rule_based_seller_config_template,
        agent_type="rule_based"
    )
    assert len(agents) == num_buyers + num_sellers
    assert sum(1 for agent in agents if agent.config.agent_type == "buyer") == num_buyers
    assert sum(1 for agent in agents if agent.config.agent_type == "seller") == num_sellers
    assert all(isinstance(agent, RuleBasedAgent) for agent in agents)

    for agent in agents:
        if agent.config.agent_type == "buyer":
            assert agent.config.initial_funds == rule_based_buyer_config_template["initial_funds"]
            assert 90 <= agent.config.valuation_or_cost <= 110
            assert agent.config.max_quantity_per_round == rule_based_buyer_config_template["max_quantity_per_round"]
        elif agent.config.agent_type == "seller":
            assert agent.config.initial_inventory == rule_based_seller_config_template["initial_inventory"]
            assert 80 <= agent.config.valuation_or_cost <= 100
            assert agent.config.min_quantity_per_round == rule_based_seller_config_template["min_quantity_per_round"]

def test_setup_llm_agents(llm_buyer_config_template, llm_seller_config_template, mock_llm_client, mock_prompt_manager):
    num_buyers = 1
    num_sellers = 1
    agents = setup_simulation_agents(
        num_buyers, llm_buyer_config_template,
        num_sellers, llm_seller_config_template,
        agent_type="llm",
        llm_client_instance=mock_llm_client,
        prompt_manager_instance=mock_prompt_manager
    )
    assert len(agents) == num_buyers + num_sellers
    assert sum(1 for agent in agents if agent.config.agent_type == "buyer") == num_buyers
    assert sum(1 for agent in agents if agent.config.agent_type == "seller") == num_sellers
    assert all(isinstance(agent, LLMAgent) for agent in agents)

    for agent in agents:
        assert agent.llm_client == mock_llm_client
        assert agent.prompt_manager == mock_prompt_manager
        if agent.config.agent_type == "buyer":
            assert agent.config.initial_funds == llm_buyer_config_template["initial_funds"]
            assert agent.config.llm_persona_prompt_key == llm_buyer_config_template["llm_persona_prompt_key"]
        elif agent.config.agent_type == "seller":
            assert agent.config.initial_inventory == llm_seller_config_template["initial_inventory"]
            assert agent.config.llm_persona_prompt_key == llm_seller_config_template["llm_persona_prompt_key"]

def test_setup_llm_agents_missing_dependencies(llm_buyer_config_template, llm_seller_config_template):
    with pytest.raises(ValueError, match="LLMClient and PromptManager instances are required for LLMAgents."):
        setup_simulation_agents(
            1, llm_buyer_config_template,
            1, llm_seller_config_template,
            agent_type="llm",
            llm_client_instance=None, # Missing
            prompt_manager_instance=MagicMock()
        )
    with pytest.raises(ValueError, match="LLMClient and PromptManager instances are required for LLMAgents."):
        setup_simulation_agents(
            1, llm_buyer_config_template,
            1, llm_seller_config_template,
            agent_type="llm",
            llm_client_instance=MagicMock(),
            prompt_manager_instance=None # Missing
        )

def test_setup_agents_unsupported_type(rule_based_buyer_config_template, rule_based_seller_config_template):
    with pytest.raises(ValueError, match="Unsupported agent type: unknown_type"):
        setup_simulation_agents(
            1, rule_based_buyer_config_template,
            1, rule_based_seller_config_template,
            agent_type="unknown_type"
        )

# --- Tests for run_marketplace_simulation ---

@patch('modules.marketplace.logic.MarketSimulation')
@patch('modules.marketplace.logic.setup_simulation_agents')
def test_run_marketplace_simulation_basic(mock_setup_agents, mock_market_simulation_cls, rule_based_buyer_config_template, rule_based_seller_config_template):
    mock_agents = [MagicMock(spec=RuleBasedAgent), MagicMock(spec=RuleBasedAgent)]
    mock_setup_agents.return_value = mock_agents

    mock_sim_instance = MagicMock(spec=MarketSimulation)
    sample_history = [
        MarketState(current_round=0, total_rounds=1, transaction_log=[], price_history=[], agent_data={}),
        MarketState(current_round=1, total_rounds=1, transaction_log=[], price_history=[], agent_data={})
    ]
    mock_sim_instance.run_simulation.return_value = (sample_history, None) # history, error
    mock_market_simulation_cls.return_value = mock_sim_instance

    num_buyers = 1
    num_sellers = 1
    num_rounds = 1

    history, error = run_marketplace_simulation(
        num_buyers, rule_based_buyer_config_template,
        num_sellers, rule_based_seller_config_template,
        num_rounds,
        agent_creation_type="rule_based"
    )

    mock_setup_agents.assert_called_once_with(
        num_buyers, rule_based_buyer_config_template,
        num_sellers, rule_based_seller_config_template,
        agent_type="rule_based",
        llm_client_instance=None,
        prompt_manager_instance=None
    )
    mock_market_simulation_cls.assert_called_once_with(agents=mock_agents, num_rounds=num_rounds)
    mock_sim_instance.run_simulation.assert_called_once()
    assert history == sample_history
    assert error is None

@patch('modules.marketplace.logic.MarketSimulation')
@patch('modules.marketplace.logic.setup_simulation_agents')
def test_run_marketplace_simulation_setup_failure(mock_setup_agents, mock_market_simulation_cls, rule_based_buyer_config_template, rule_based_seller_config_template):
    # Simulate setup_simulation_agents raising an error (e.g., invalid agent type)
    mock_setup_agents.side_effect = ValueError("Setup failed due to invalid agent type")

    num_buyers = 1
    num_sellers = 1
    num_rounds = 1

    # Check that the ValueError from setup_simulation_agents propagates
    with pytest.raises(ValueError, match="Setup failed due to invalid agent type"):
        run_marketplace_simulation(
            num_buyers, rule_based_buyer_config_template,
            num_sellers, rule_based_seller_config_template,
            num_rounds,
            agent_creation_type="invalid_type" # This would cause setup_simulation_agents to fail
        )
    mock_market_simulation_cls.assert_not_called() # Simulation should not be created if setup fails

@patch('modules.marketplace.logic.MarketSimulation')
@patch('modules.marketplace.logic.setup_simulation_agents')
def test_run_marketplace_simulation_llm_error(mock_setup_agents, mock_market_simulation_cls, llm_buyer_config_template, llm_seller_config_template, mock_llm_client, mock_prompt_manager):
    mock_agents = [MagicMock(spec=LLMAgent)]
    mock_setup_agents.return_value = mock_agents

    mock_sim_instance = MagicMock(spec=MarketSimulation)
    llm_error_message = "LLM API unavailable"
    mock_sim_instance.run_simulation.return_value = ([], llm_error_message) # Empty history, error
    mock_market_simulation_cls.return_value = mock_sim_instance

    history, error = run_marketplace_simulation(
        1, llm_buyer_config_template,
        0, {}, # No sellers for simplicity
        1,
        agent_creation_type="llm",
        llm_client=mock_llm_client,
        prompt_manager=mock_prompt_manager
    )

    assert history == []
    assert error == llm_error_message
    mock_setup_agents.assert_called_once()
    mock_market_simulation_cls.assert_called_once()
    mock_sim_instance.run_simulation.assert_called_once()


# --- Tests for process_simulation_results_for_display ---

def test_process_simulation_results_empty_history():
    results = process_simulation_results_for_display([])
    assert results["rounds"] == []
    assert results["average_prices"] == []
    assert results["volumes"] == []
    assert results["num_transactions_per_round"] == []
    assert results["all_transactions"] == []

def test_process_simulation_results_basic():
    history = [
        MarketState(
            current_round=0, total_rounds=2,
            transaction_log=[
                Transaction(round=0, buyer_id="b1", seller_id="s1", price=10, quantity=2, timestamp=0),
                Transaction(round=0, buyer_id="b2", seller_id="s2", price=12, quantity=1, timestamp=1)
            ],
            price_history=[{"round": 0, "average_price": 10.67, "volume": 3, "num_transactions": 2}],
            agent_data={}
        ),
        MarketState(
            current_round=1, total_rounds=2,
            transaction_log=[
                Transaction(round=1, buyer_id="b1", seller_id="s2", price=11, quantity=3, timestamp=2)
            ],
            price_history=[
                {"round": 0, "average_price": 10.67, "volume": 3, "num_transactions": 2}, # from previous round
                {"round": 1, "average_price": 11.00, "volume": 3, "num_transactions": 1}
            ],
            agent_data={}
        )
    ]
    results = process_simulation_results_for_display(history)

    assert results["rounds"] == [0, 1]
    assert results["average_prices"] == [10.67, 11.00]
    assert results["volumes"] == [3, 3]
    assert results["num_transactions_per_round"] == [2, 1]
    assert len(results["all_transactions"]) == 3
    assert results["all_transactions"][0] == {"round": 0, "buyer_id": "b1", "seller_id": "s1", "price": 10, "quantity": 2}
    assert results["all_transactions"][1] == {"round": 0, "buyer_id": "b2", "seller_id": "s2", "price": 12, "quantity": 1}
    assert results["all_transactions"][2] == {"round": 1, "buyer_id": "b1", "seller_id": "s2", "price": 11, "quantity": 3}

def test_process_simulation_results_no_transactions_in_a_round():
    history = [
        MarketState(
            current_round=0, total_rounds=2,
            transaction_log=[Transaction(round=0, buyer_id="b1", seller_id="s1", price=10, quantity=2, timestamp=0)],
            price_history=[{"round": 0, "average_price": 10.00, "volume": 2, "num_transactions": 1}],
            agent_data={}
        ),
        MarketState( # Round 1 has no transactions
            current_round=1, total_rounds=2,
            transaction_log=[], # No transactions for round 1 in this state's log
            price_history=[{"round": 0, "average_price": 10.00, "volume": 2, "num_transactions": 1}], # Only round 0 price history
            agent_data={}
        ),
         MarketState(
            current_round=2, total_rounds=2,
            transaction_log=[Transaction(round=2, buyer_id="b2", seller_id="s2", price=15, quantity=1, timestamp=0)],
            price_history=[
                {"round": 0, "average_price": 10.00, "volume": 2, "num_transactions": 1},
                {"round": 2, "average_price": 15.00, "volume": 1, "num_transactions": 1} # No entry for round 1
            ],
            agent_data={}
        )
    ]
    results = process_simulation_results_for_display(history)

    assert results["rounds"] == [0, 1, 2]
    # Price from round 0 is carried to round 1, then round 2 has its own price
    assert results["average_prices"] == [10.00, 10.00, 15.00]
    assert results["volumes"] == [2, 0, 1] # Volume is 0 for round 1
    assert results["num_transactions_per_round"] == [1, 0, 1] # Num transactions is 0 for round 1
    assert len(results["all_transactions"]) == 2
    assert results["all_transactions"][0]["round"] == 0
    assert results["all_transactions"][1]["round"] == 2


def test_process_simulation_results_padding_logic():
    # Test case where a round might be missing price_history entry entirely,
    # or where lists might end up with different lengths before padding.
    # The function logic tries to find price_info_for_round for the current_round.
    # If not found, it pads.
    history = [
        MarketState(current_round=0, total_rounds=3, transaction_log=[],
                    price_history=[{"round": 0, "average_price": 10, "volume": 1, "num_transactions": 1}], agent_data={}),
        MarketState(current_round=1, total_rounds=3, transaction_log=[],
                    price_history=[{"round": 0, "average_price": 10, "volume": 1, "num_transactions": 1}], agent_data={}), # No price_history for round 1
        MarketState(current_round=2, total_rounds=3, transaction_log=[],
                    price_history=[
                        {"round": 0, "average_price": 10, "volume": 1, "num_transactions": 1},
                        {"round": 2, "average_price": 12, "volume": 1, "num_transactions": 1}
                    ], agent_data={}),
    ]
    results = process_simulation_results_for_display(history)
    assert results["rounds"] == [0, 1, 2]
    assert results["average_prices"] == [10, 10, 12] # 10 carried from round 0 to 1
    assert results["volumes"] == [1, 0, 1]
    assert results["num_transactions_per_round"] == [1, 0, 1]

# Note: The original request mentioned testing calculation of `price_over_rounds_df`
# and `volume_over_rounds_df` and `transaction_stats`.
# The current `process_simulation_results_for_display` returns a dictionary
# with lists: "rounds", "average_prices", "volumes", "num_transactions_per_round", "all_transactions".
# The tests above cover these outputs. If DataFrame outputs or specific "transaction_stats"
# were intended, the `process_simulation_results_for_display` function would need to be
# updated, and then tests for those specific outputs would be added.
# For now, tests align with the current implementation.