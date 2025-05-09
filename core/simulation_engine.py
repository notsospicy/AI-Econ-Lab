# Component of Phase 1: Core Simulation Logic & Rule-Based Agents
from typing import List, Dict, Any, Optional, Tuple
from .models import Agent, MarketState, BidAsk, Transaction, AgentConfig, RuleBasedAgent, LLMAgent
# from .llm_client import generate_text # Not directly used by engine, but by LLMAgent
# from .prompt_manager import get_prompt # Not directly used by engine, but by LLMAgent
import random # For shuffling agents

class MarketSimulation:
    """
    Manages the execution of a market simulation over multiple rounds.
    """
    def __init__(self, agents: List[Agent], num_rounds: int):
        """
        Initializes the market simulation.

        Args:
            agents (List[Agent]): A list of agent objects participating in the simulation.
            num_rounds (int): The total number of rounds to simulate.
        """
        self.agents = agents
        self.num_rounds = num_rounds
        self.market_state = MarketState(current_round=0)
        self.simulation_history: List[MarketState] = [] # To store state after each round
        self.llm_operational_error: Optional[str] = None # To store the first LLM operational error

    def _gather_actions_from_agents(self) -> List[BidAsk]:
        """
        Collects bids and asks from all agents for the current round.
        Agents' decisions are made sequentially in a random order to avoid bias.
        """
        actions: List[BidAsk] = []
        # Shuffle agents to vary the order of decision-making each round
        # This can be important if agent decisions depend on prior actions within the same round,
        # though our current MarketState is based on the *previous* round's outcome.
        # For now, it's good practice.
        shuffled_agents = random.sample(self.agents, len(self.agents))

        for agent in shuffled_agents:
            # Pass a copy of the market state so agents can't directly mutate the shared state
            # during their decision process.
            action = agent.decide_action(self.market_state.copy(deep=True))
            
            if action:
                # Basic validation: buyer bids, seller asks
                if (action.bid_ask_type == "bid" and agent.agent_type == "buyer") or \
                   (action.bid_ask_type == "ask" and agent.agent_type == "seller"):
                    # Ensure agent has resources for the action (double check, though agent should handle)
                    if agent.agent_type == "buyer" and agent.funds is not None and agent.funds < action.price * action.quantity:
                        # print(f"Warning: Agent {agent.agent_id} bid without sufficient funds. Action ignored.")
                        continue
                    if agent.agent_type == "seller" and agent.inventory is not None and agent.inventory < action.quantity:
                        # print(f"Warning: Agent {agent.agent_id} asked without sufficient inventory. Action ignored.")
                        continue
                    actions.append(action)
                # else:
                #     # print(f"Warning: Agent {agent.agent_id} type {agent.agent_type} tried to {action.bid_ask_type}. Action ignored.")
            elif isinstance(agent, LLMAgent) and self.llm_operational_error is None:
                # LLM Agent failed to produce an action
                # self.market_state.current_round is already incremented in run_round before this method is called.
                self.llm_operational_error = f"LLM Agent '{agent.agent_id}' failed to decide an action in round {self.market_state.current_round}."
                # print(f"DEBUG: LLM Error recorded: {self.llm_operational_error}") # For debugging
        return actions

    def _match_orders_simple_CDA(self, bids: List[BidAsk], asks: List[BidAsk]) -> List[Transaction]:
        """
        A simplified continuous double auction (CDA) matching engine.
        It sorts bids high-to-low and asks low-to-high, then matches.
        Transactions occur at the bid price or ask price (or midpoint, configurable).
        For MVP, let's use the price of the standing order that gets hit (e.g. if new bid hits existing ask, price is ask price).
        This version will be a simple clearing mechanism: sort and match.
        A true CDA would process orders as they arrive. This is a periodic clearing.
        """
        transactions: List[Transaction] = []
        
        # Sort bids: highest price first, then by round (earlier first - though not used in this simple match)
        sorted_bids = sorted(bids, key=lambda b: (-b.price, b.round))
        # Sort asks: lowest price first, then by round
        sorted_asks = sorted(asks, key=lambda a: (a.price, a.round))

        bid_idx = 0
        ask_idx = 0

        while bid_idx < len(sorted_bids) and ask_idx < len(sorted_asks):
            current_bid = sorted_bids[bid_idx]
            current_ask = sorted_asks[ask_idx]

            if current_bid.price >= current_ask.price:
                # A trade is possible
                trade_quantity = min(current_bid.quantity, current_ask.quantity)
                
                # For MVP, let's set trade price to be the midpoint for simplicity,
                # or one of the existing prices. A common CDA rule is k-pricing.
                # Let's use the price of the earlier order, or if same round, midpoint.
                # Simpler: use the ask price if a bid hits it, or bid price if an ask hits it.
                # For this batch clearing, let's use the ask price as the transaction price.
                # This favors sellers slightly if bid > ask. Or midpoint.
                # Let's try midpoint for now.
                trade_price = round((current_bid.price + current_ask.price) / 2.0, 2)
                # Alternative: current_ask.price (if bid is aggressive) or current_bid.price (if ask is aggressive)

                if trade_quantity > 0:
                    transaction = Transaction(
                        buyer_id=current_bid.agent_id,
                        seller_id=current_ask.agent_id,
                        price=trade_price,
                        quantity=trade_quantity,
                        round=self.market_state.current_round
                    )
                    transactions.append(transaction)

                    # Update quantities for the original BidAsk objects (or rather, track consumed quantity)
                    # This simple version assumes full or partial fill and then the order is "done"
                    # A more complex CDA would handle remaining quantities.
                    # For now, let's assume orders are for their full quantity or are removed.
                    # This means we need to adjust the original bid/ask objects if they are to persist.
                    # However, our agents submit new bids/asks each round.
                    # So, we just need to update agent states based on the transaction.

                    # Decrement quantities (or remove if fully matched)
                    current_bid.quantity -= trade_quantity
                    current_ask.quantity -= trade_quantity

                if current_bid.quantity == 0:
                    bid_idx += 1
                if current_ask.quantity == 0:
                    ask_idx += 1
            else:
                # No more matches possible as highest bid is lower than lowest ask
                break
        
        return transactions

    def _update_agent_states(self, transactions: List[Transaction]):
        """Updates agent funds and inventory based on completed transactions."""
        for tx in transactions:
            buyer = next((agent for agent in self.agents if agent.agent_id == tx.buyer_id), None)
            seller = next((agent for agent in self.agents if agent.agent_id == tx.seller_id), None)

            if buyer:
                buyer.update_state_after_transaction(tx.price, tx.quantity, is_buyer=True)
            if seller:
                seller.update_state_after_transaction(tx.price, tx.quantity, is_buyer=False)

    def run_round(self):
        """
        Executes a single round of the market simulation.
        1. Increment round number.
        2. Gather actions (bids/asks) from agents.
        3. Match orders to create transactions.
        4. Update market state (transaction log, price history).
        5. Update agent states (funds, inventory).
        6. Store the market state for this round.
        """
        self.market_state.current_round += 1
        # print(f"\n--- Starting Round {self.market_state.current_round} ---")

        # Get actions from agents based on the state *before* this round's trades
        all_actions = self._gather_actions_from_agents()
        
        current_bids = [action for action in all_actions if action.bid_ask_type == "bid"]
        current_asks = [action for action in all_actions if action.bid_ask_type == "ask"]
        
        # Update market state with the new bids and asks for this round
        self.market_state.bids = current_bids
        self.market_state.asks = current_asks
        
        # Match orders
        transactions_this_round = self._match_orders_simple_CDA(current_bids, current_asks)
        
        # Update market state with transactions
        self.market_state.transaction_log.extend(transactions_this_round)
        
        # Update price history (e.g., average transaction price this round)
        if transactions_this_round:
            avg_price_this_round = sum(tx.price * tx.quantity for tx in transactions_this_round) / sum(tx.quantity for tx in transactions_this_round)
            total_volume_this_round = sum(tx.quantity for tx in transactions_this_round)
            self.market_state.price_history.append({
                "round": self.market_state.current_round,
                "average_price": round(avg_price_this_round, 2),
                "volume": total_volume_this_round,
                "num_transactions": len(transactions_this_round)
            })
            # print(f"Round {self.market_state.current_round} Transactions: {len(transactions_this_round)}, Avg Price: {avg_price_this_round:.2f}, Volume: {total_volume_this_round}")

        # Update agent states (funds, inventory) based on these transactions
        self._update_agent_states(transactions_this_round)

        # Store a deep copy of the market state for this round's history
        self.simulation_history.append(self.market_state.copy(deep=True))

        # Clear bids and asks for the next round (as agents will submit new ones)
        # self.market_state.bids = [] # Agents resubmit each round
        # self.market_state.asks = [] # Agents resubmit each round


    def run_simulation(self) -> Tuple[List[MarketState], Optional[str]]:
        """
        Runs the market simulation for the specified number of rounds.
        Returns the simulation history and any critical LLM operational error encountered.
        """
        # print(f"Starting simulation with {len(self.agents)} agents for {self.num_rounds} rounds.")
        self.llm_operational_error = None # Reset error at the beginning of a full simulation run
        for _ in range(self.num_rounds):
            if self.market_state.current_round >= self.num_rounds:
                break # Ensure we don't exceed num_rounds if called multiple times
            self.run_round()
            if self.llm_operational_error:
                # If a critical LLM error occurred, we might stop early or just report it.
                # For now, we continue simulation but ensure the error is reported.
                # If we wanted to stop early: break
                pass 
        # print("\n--- Simulation Ended ---")
        return self.simulation_history, self.llm_operational_error


# Example Usage (for testing this file directly):
if __name__ == "__main__":
    # Create some RuleBasedAgent configurations
    agent_configs = [
        AgentConfig(agent_id="buyer_1", agent_type="buyer", initial_funds=1000, valuation_or_cost=110),
        AgentConfig(agent_id="buyer_2", agent_type="buyer", initial_funds=1000, valuation_or_cost=120),
        AgentConfig(agent_id="seller_1", agent_type="seller", initial_inventory=10, valuation_or_cost=90),
        AgentConfig(agent_id="seller_2", agent_type="seller", initial_inventory=10, valuation_or_cost=100),
    ]

    # Create agent instances
    sim_agents = [RuleBasedAgent(config=ac) for ac in agent_configs]

    # Initialize and run the simulation
    num_simulation_rounds = 10
    simulation = MarketSimulation(agents=sim_agents, num_rounds=num_simulation_rounds)
    history, error = simulation.run_simulation() # Adjusted for new return type

    print("\n--- Simulation Results ---")
    if error:
        print(f"Simulation encountered an error: {error}")

    for round_state in history:
        print(f"\nRound: {round_state.current_round}")
        # print(f"  Bids: {[(b.agent_id, b.price, b.quantity) for b in round_state.bids]}")
        # print(f"  Asks: {[(a.agent_id, a.price, a.quantity) for a in round_state.asks]}")
        round_tx = [tx for tx in round_state.transaction_log if tx.round == round_state.current_round]
        if round_tx:
            print(f"  Transactions ({len(round_tx)}):")
            for tx in round_tx:
                print(f"    {tx.buyer_id} buys from {tx.seller_id} - Qty: {tx.quantity}, Price: {tx.price:.2f}")
        else:
            print("  No transactions this round.")
        
        if round_state.price_history:
            last_price_info = next((ph for ph in reversed(round_state.price_history) if ph["round"] == round_state.current_round), None)
            if last_price_info:
                 print(f"  Avg Price: {last_price_info['average_price']:.2f}, Volume: {last_price_info['volume']}")


    print("\n--- Final Agent States ---")
    for agent in sim_agents:
        print(f"Agent ID: {agent.agent_id}, Type: {agent.agent_type}")
        print(f"  Funds: {agent.funds:.2f}" if agent.funds is not None else "  Funds: N/A")
        print(f"  Inventory: {agent.inventory}" if agent.inventory is not None else "  Inventory: N/A")