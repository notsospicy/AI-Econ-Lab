import pytest
import sys
import os

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.models import BidAsk, AgentConfig, RuleBasedAgent
from core.simulation_engine import MarketSimulation

class TestMarketSimulationMatching:

    def test_no_match_bid_lower_than_ask(self):
        sim = MarketSimulation(agents=[], num_rounds=1) # Agents not needed for direct matching test
        bids = [BidAsk(agent_id="b1", bid_ask_type="bid", price=90, quantity=1, round=1)]
        asks = [BidAsk(agent_id="s1", bid_ask_type="ask", price=100, quantity=1, round=1)]
        transactions = sim._match_orders_simple_CDA(bids, asks)
        assert len(transactions) == 0

    def test_simple_match_one_buyer_one_seller(self):
        sim = MarketSimulation(agents=[], num_rounds=1)
        sim.market_state.current_round = 1 # Set current round for transaction
        bids = [BidAsk(agent_id="b1", bid_ask_type="bid", price=100, quantity=1, round=1)]
        asks = [BidAsk(agent_id="s1", bid_ask_type="ask", price=90, quantity=1, round=1)]
        transactions = sim._match_orders_simple_CDA(bids, asks)
        
        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.buyer_id == "b1"
        assert tx.seller_id == "s1"
        assert tx.quantity == 1
        assert tx.price == 95.00 # Midpoint of 100 and 90

    def test_match_partial_fill_buyer_wants_more(self):
        sim = MarketSimulation(agents=[], num_rounds=1)
        sim.market_state.current_round = 1
        bids = [BidAsk(agent_id="b1", bid_ask_type="bid", price=100, quantity=5, round=1)]
        asks = [BidAsk(agent_id="s1", bid_ask_type="ask", price=90, quantity=2, round=1)]
        transactions = sim._match_orders_simple_CDA(bids, asks)
        
        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.quantity == 2 # Limited by seller's quantity
        assert tx.price == 95.00
        # Original bid/ask objects are modified by _match_orders_simple_CDA
        assert bids[0].quantity == 3 # Remaining quantity for buyer
        assert asks[0].quantity == 0 # Seller fully matched

    def test_match_partial_fill_seller_wants_more(self):
        sim = MarketSimulation(agents=[], num_rounds=1)
        sim.market_state.current_round = 1
        bids = [BidAsk(agent_id="b1", bid_ask_type="bid", price=100, quantity=2, round=1)]
        asks = [BidAsk(agent_id="s1", bid_ask_type="ask", price=90, quantity=5, round=1)]
        transactions = sim._match_orders_simple_CDA(bids, asks)
        
        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.quantity == 2 # Limited by buyer's quantity
        assert tx.price == 95.00
        assert bids[0].quantity == 0
        assert asks[0].quantity == 3

    def test_multiple_matches(self):
        sim = MarketSimulation(agents=[], num_rounds=1)
        sim.market_state.current_round = 1
        bids = [
            BidAsk(agent_id="b1", bid_ask_type="bid", price=105, quantity=2, round=1), # Best bid
            BidAsk(agent_id="b2", bid_ask_type="bid", price=100, quantity=3, round=1)
        ]
        asks = [
            BidAsk(agent_id="s1", bid_ask_type="ask", price=90, quantity=1, round=1),  # Best ask
            BidAsk(agent_id="s2", bid_ask_type="ask", price=95, quantity=4, round=1)
        ]
        transactions = sim._match_orders_simple_CDA(bids, asks)
        
        assert len(transactions) == 2 # b1-s1, then b1-s2 (or b2-s2 depending on remaining qty)
        
        total_quantity_traded = sum(tx.quantity for tx in transactions)
        assert total_quantity_traded > 0
        
        # Detailed checks for multiple matches can be complex due to order of matching.
        # For this simple CDA:
        # 1. b1 (105) vs s1 (90). Qty 1 at (105+90)/2 = 97.5. b1 has 1 left. s1 done.
        # 2. b1 (105, 1 left) vs s2 (95). Qty 1 at (105+95)/2 = 100. b1 done. s2 has 3 left.
        # 3. b2 (100, 3 left) vs s2 (95, 3 left). Qty 3 at (100+95)/2 = 97.5. b2 done. s2 done.
        # So, 3 transactions expected.
        
        # Let's re-verify the logic of _match_orders_simple_CDA:
        # It iterates while bid_idx < len(bids) and ask_idx < len(asks)
        # If match, it reduces quantities and increments idx if qty becomes 0.

        # Sorted bids: (b1, 105, 2), (b2, 100, 3)
        # Sorted asks: (s1, 90, 1), (s2, 95, 4)

        # Match 1: b1 vs s1. Price (105+90)/2 = 97.5. Qty 1.
        #   b1: qty becomes 1. s1: qty becomes 0 (s1_idx++)
        #   tx1: b1, s1, 97.5, 1
        # Remaining bids: (b1, 105, 1), (b2, 100, 3)
        # Remaining asks: (s2, 95, 4)

        # Match 2: b1 vs s2. Price (105+95)/2 = 100. Qty 1.
        #   b1: qty becomes 0 (b1_idx++). s2: qty becomes 3.
        #   tx2: b1, s2, 100, 1
        # Remaining bids: (b2, 100, 3)
        # Remaining asks: (s2, 95, 3)

        # Match 3: b2 vs s2. Price (100+95)/2 = 97.5. Qty 3.
        #   b2: qty becomes 0 (b2_idx++). s2: qty becomes 0 (s2_idx++).
        #   tx3: b2, s2, 97.5, 3
        
        assert len(transactions) == 3
        assert transactions[0].buyer_id == "b1" and transactions[0].seller_id == "s1" and transactions[0].quantity == 1
        assert transactions[1].buyer_id == "b1" and transactions[1].seller_id == "s2" and transactions[1].quantity == 1
        assert transactions[2].buyer_id == "b2" and transactions[2].seller_id == "s2" and transactions[2].quantity == 3


    def test_update_agent_states_after_transaction(self):
        buyer_config = AgentConfig(agent_id="buyer_update", agent_type="buyer", initial_funds=1000, valuation_or_cost=100)
        seller_config = AgentConfig(agent_id="seller_update", agent_type="seller", initial_inventory=10, valuation_or_cost=80)
        buyer = RuleBasedAgent(config=buyer_config)
        seller = RuleBasedAgent(config=seller_config)
        
        sim = MarketSimulation(agents=[buyer, seller], num_rounds=1)
        sim.market_state.current_round = 1

        # Manually create a transaction
        tx = BidAsk(agent_id=buyer.agent_id, bid_ask_type="bid", price=90, quantity=2, round=1) # Buyer's bid
        # Assume this bid was matched with an ask at price 90 for quantity 2
        transaction = sim._match_orders_simple_CDA(
            [tx], 
            [BidAsk(agent_id=seller.agent_id, bid_ask_type="ask", price=90, quantity=5, round=1)]
        )
        assert len(transaction) == 1
        
        sim._update_agent_states(transaction)

        assert buyer.funds == 1000 - (transaction[0].price * 2) # 1000 - 180 = 820
        assert buyer.inventory == 2
        assert seller.funds == (transaction[0].price * 2) # 180
        assert seller.inventory == 10 - 2 # 8

# To run these tests:
# pytest tests/core/test_simulation_engine.py