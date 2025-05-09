import pytest
import sys
import os

# Add project root to sys.path to allow importing core modules
# This assumes test_agents.py is in AI-Econ-Lab/tests/core/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.models import AgentConfig, RuleBasedAgent, MarketState, BidAsk

class TestRuleBasedAgent:
    def test_buyer_creation(self):
        config = AgentConfig(agent_id="buyer_test_1", agent_type="buyer", initial_funds=100, valuation_or_cost=120)
        agent = RuleBasedAgent(config=config)
        assert agent.agent_id == "buyer_test_1"
        assert agent.agent_type == "buyer"
        assert agent.funds == 100
        assert agent.inventory == 0
        assert agent.valuation_or_cost == 120

    def test_seller_creation(self):
        config = AgentConfig(agent_id="seller_test_1", agent_type="seller", initial_inventory=10, valuation_or_cost=80)
        agent = RuleBasedAgent(config=config)
        assert agent.agent_id == "seller_test_1"
        assert agent.agent_type == "seller"
        assert agent.funds == 0
        assert agent.inventory == 10
        assert agent.valuation_or_cost == 80

    def test_buyer_decide_action_sufficient_funds(self):
        config = AgentConfig(agent_id="b1", agent_type="buyer", initial_funds=200, valuation_or_cost=100)
        agent = RuleBasedAgent(config=config)
        market_state = MarketState(current_round=1)
        action = agent.decide_action(market_state)
        
        assert isinstance(action, BidAsk)
        assert action.bid_ask_type == "bid"
        assert action.agent_id == "b1"
        assert 0 < action.price <= 100 # Should bid at or below valuation
        assert action.quantity == 1 # Simple agent bids for 1 unit

    def test_buyer_decide_action_insufficient_funds(self):
        config = AgentConfig(agent_id="b2", agent_type="buyer", initial_funds=10, valuation_or_cost=100)
        agent = RuleBasedAgent(config=config)
        # Agent's logic might bid e.g. 80, but funds are only 10
        market_state = MarketState(current_round=1)
        action = agent.decide_action(market_state)
        assert action is None # Cannot afford its typical bid

    def test_seller_decide_action_has_inventory(self):
        config = AgentConfig(agent_id="s1", agent_type="seller", initial_inventory=5, valuation_or_cost=50)
        agent = RuleBasedAgent(config=config)
        market_state = MarketState(current_round=1)
        action = agent.decide_action(market_state)

        assert isinstance(action, BidAsk)
        assert action.bid_ask_type == "ask"
        assert action.agent_id == "s1"
        assert action.price >= 50 # Should ask at or above cost
        assert action.quantity == 1

    def test_seller_decide_action_no_inventory(self):
        config = AgentConfig(agent_id="s2", agent_type="seller", initial_inventory=0, valuation_or_cost=50)
        agent = RuleBasedAgent(config=config)
        market_state = MarketState(current_round=1)
        action = agent.decide_action(market_state)
        assert action is None

    def test_update_state_after_transaction_buyer(self):
        config = AgentConfig(agent_id="b_tx_test", agent_type="buyer", initial_funds=100, valuation_or_cost=80)
        agent = RuleBasedAgent(config=config)
        agent.update_state_after_transaction(transaction_price=70, transaction_quantity=1, is_buyer=True)
        assert agent.funds == 30
        assert agent.inventory == 1

    def test_update_state_after_transaction_seller(self):
        config = AgentConfig(agent_id="s_tx_test", agent_type="seller", initial_inventory=5, valuation_or_cost=60)
        agent = RuleBasedAgent(config=config)
        agent.update_state_after_transaction(transaction_price=70, transaction_quantity=2, is_buyer=False)
        assert agent.funds == 140
        assert agent.inventory == 3

# To run these tests, navigate to the AI-Econ-Lab directory and run:
# pytest tests/core/test_agents.py