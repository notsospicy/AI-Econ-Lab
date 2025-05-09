from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Optional
import random # For RuleBasedAgent decisions

# Placeholder imports - these modules will be created/fleshed out later
# from .llm_client import generate_text # Assuming direct import for now
# from .prompt_manager import get_prompt # Assuming direct import for now
# For now, to avoid import errors, we'll define dummy functions if needed by LLMAgent
# or structure LLMAgent to accept client/prompt_manager as arguments.

class AgentConfig(BaseModel):
    """Configuration for an agent in the simulation."""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    agent_type: Literal["buyer", "seller"] = Field(..., description="Type of agent")
    initial_funds: Optional[float] = Field(None, description="Initial funds for a buyer agent", ge=0)
    initial_inventory: Optional[int] = Field(None, description="Initial inventory for a seller agent", ge=0)
    llm_persona_prompt_key: Optional[str] = Field(None, description="Key to retrieve LLM persona/prompt for this agent")
    # For rule-based agents, we might have other parameters, e.g., valuation/cost
    valuation_or_cost: Optional[float] = Field(None, description="Valuation for buyer or cost for seller (for rule-based agents)")

class BidAsk(BaseModel):
    """Represents a bid or an ask in the market."""
    agent_id: str
    bid_ask_type: Literal["bid", "ask"]
    price: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    round: int # The round in which this bid/ask was placed

class Transaction(BaseModel):
    """Represents a completed transaction in the market."""
    buyer_id: str
    seller_id: str
    price: float
    quantity: int
    round: int # The round in which this transaction occurred

class MarketState(BaseModel):
    """Represents the state of the market at a given point in time."""
    current_round: int = Field(0, description="The current simulation round")
    bids: List[BidAsk] = Field(default_factory=list, description="List of active bids in the current round")
    asks: List[BidAsk] = Field(default_factory=list, description="List of active asks in the current round")
    # For MVP, price_history could be simple list of average prices or all transaction prices
    price_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of prices, e.g., average transaction price per round")
    transaction_log: List[Transaction] = Field(default_factory=list, description="Log of all transactions that have occurred")
    # Potentially add agent states here or keep them separate
    # agent_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Current states of all agents")

# Forward reference resolution for Pydantic models if they are defined later or in circular dependencies
# (Not strictly necessary here as they are in order, but good practice)
MarketState.update_forward_refs()


# --- Agent Base Classes (as per section 4.1 of DETAILED_IMPLEMENTATION_PLAN.MD) ---
# These are more than just "initial Pydantic models" for Phase 0,
# but good to stub out as they are part of core/models.py.
# Full implementation will be in Phase 1.

class Agent(BaseModel):
    """Base class for all agents in the simulation."""
    agent_id: str
    agent_type: Literal["buyer", "seller"]
    
    # Attributes that will be updated during simulation
    funds: Optional[float] = None
    inventory: Optional[int] = None

    class Config:
        arbitrary_types_allowed = True # To allow methods if we add them later

    def __init__(self, config: AgentConfig, **data: Any):
        super().__init__(agent_id=config.agent_id, agent_type=config.agent_type, **data)
        if self.agent_type == "buyer":
            self.funds = config.initial_funds
            self.inventory = 0 # Buyers start with 0 inventory of the good
        elif self.agent_type == "seller":
            self.funds = 0 # Sellers start with 0 funds (or some initial capital if needed)
            self.inventory = config.initial_inventory
        # Store config for reference if needed
        self._config = config


    def decide_action(self, market_state: MarketState) -> Optional[BidAsk]:
        """
        Abstract method for an agent to decide its action (bid or ask)
        based on the current market state.
        To be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement decide_action")

    def update_state_after_transaction(self, transaction_price: float, transaction_quantity: int, is_buyer: bool):
        """
        Updates the agent's funds and inventory after a successful transaction.
        """
        if is_buyer:
            if self.funds is not None:
                self.funds -= transaction_price * transaction_quantity
            if self.inventory is not None:
                self.inventory += transaction_quantity
        else: # Seller
            if self.funds is not None:
                self.funds += transaction_price * transaction_quantity
            if self.inventory is not None:
                self.inventory -= transaction_quantity


#     buyer_config_data = {
#         "agent_id": "buyer_001",
#         "agent_type": "buyer",
#         "initial_funds": 1000.0,
#         "llm_persona_prompt_key": "buyer_conservative_persona"
#     }
#     buyer_config = AgentConfig(**buyer_config_data)
#     # agent_instance = Agent(config=buyer_config) # This would fail as Agent is abstract
#     # print(agent_instance)

class RuleBasedAgent(Agent):
    """An agent that makes decisions based on simple hardcoded rules."""

    def __init__(self, config: AgentConfig, **data: Any):
        super().__init__(config=config, **data)
        if config.valuation_or_cost is None:
            raise ValueError("RuleBasedAgent requires valuation_or_cost in its config.")
        self.valuation_or_cost = config.valuation_or_cost

    def decide_action(self, market_state: MarketState) -> Optional[BidAsk]:
        """
        Makes a decision based on simple rules:
        - Buyers bid a random amount below their valuation if they have funds.
        - Sellers ask a random amount above their cost if they have inventory.
        - For simplicity, quantity is 1.
        """
        if self.agent_type == "buyer":
            if self.funds is not None and self.funds > 0 and self.valuation_or_cost is not None:
                # Simple strategy: bid a random percentage (e.g., 80-95%) of valuation
                # if funds allow for at least one unit at that price.
                potential_bid_price = round(random.uniform(0.80, 0.95) * self.valuation_or_cost, 2)
                if self.funds >= potential_bid_price and potential_bid_price > 0:
                    return BidAsk(
                        agent_id=self.agent_id,
                        bid_ask_type="bid",
                        price=potential_bid_price,
                        quantity=1, # Simple: always bid for 1 unit
                        round=market_state.current_round
                    )
        elif self.agent_type == "seller":
            if self.inventory is not None and self.inventory > 0 and self.valuation_or_cost is not None:
                # Simple strategy: ask a random percentage (e.g., 105-120%) of cost.
                potential_ask_price = round(random.uniform(1.05, 1.20) * self.valuation_or_cost, 2)
                if potential_ask_price > 0:
                    return BidAsk(
                        agent_id=self.agent_id,
                        bid_ask_type="ask",
                        price=potential_ask_price,
                        quantity=1, # Simple: always offer 1 unit if available
                        round=market_state.current_round
                    )
        return None


class LLMAgent(Agent):
    """An agent that uses an LLM to make decisions."""

    def __init__(self, config: AgentConfig, llm_client: Any, prompt_manager: Any, **data: Any):
        super().__init__(config=config, **data)
        if not config.llm_persona_prompt_key:
            raise ValueError("LLMAgent requires llm_persona_prompt_key in its config.")
        self.llm_persona_prompt_key = config.llm_persona_prompt_key
        self.llm_client = llm_client # Injected dependency
        self.prompt_manager = prompt_manager # Injected dependency

    def _format_market_summary(self, items: List[BidAsk], top_n: int = 3) -> str:
        if not items:
            return "None"
        # Sort bids descending by price, asks ascending by price
        sorted_items = sorted(items, key=lambda x: x.price, reverse=(items[0].bid_ask_type == 'bid' if items else False))
        summary = []
        for item in sorted_items[:top_n]:
            summary.append(f"  - Price: {item.price:.2f}, Qty: {item.quantity}")
        return "\n".join(summary)

    def _format_transaction_summary(self, transactions: List[Transaction], top_n: int = 3) -> str:
        if not transactions:
            return "None"
        summary = []
        # Show most recent transactions
        for tx in transactions[-top_n:]:
            summary.append(f"  - Price: {tx.price:.2f}, Qty: {tx.quantity}, Round: {tx.round}")
        return "\n".join(summary)

    def decide_action(self, market_state: MarketState) -> Optional[BidAsk]:
        """
        Uses the LLM to decide an action.
        This involves:
        1. Getting the base prompt using prompt_manager.
        2. Formatting the prompt with current market_state and agent state.
        3. Sending the prompt to the LLM via llm_client.
        4. Parsing the LLM's response to create a BidAsk object.
        """
        # This is a simplified placeholder for Phase 2.
        # Actual implementation will involve calling prompt_manager and llm_client.
        
        prompt_template = self.prompt_manager.get_prompt(
            self.llm_persona_prompt_key,
            agent_type=self.agent_type
        )
        if not prompt_template:
            print(f"Error: Could not find prompt for key {self.llm_persona_prompt_key}")
            return None

        # Prepare context for the prompt
        context = {
            "current_round": market_state.current_round,
            "agent_funds": self.funds,
            "agent_inventory": self.inventory,
            "valuation": self._config.valuation_or_cost if self.agent_type == "buyer" else "N/A",
            "cost": self._config.valuation_or_cost if self.agent_type == "seller" else "N/A",
            "recent_transactions_summary": self._format_transaction_summary(market_state.transaction_log),
            "market_bids_summary": self._format_market_summary([b for b in market_state.bids if b.bid_ask_type == 'bid']),
            "market_asks_summary": self._format_market_summary([a for a in market_state.asks if a.bid_ask_type == 'ask']),
        }
        
        # Remove keys from context that are not in the prompt template to avoid errors with .format()
        # A more robust templating engine like Jinja2 would handle this better.
        # For f-strings or .format(), all keys in the template must be in the context.
        # For now, assume prompt_template.format will handle missing keys gracefully or
        # that prompts are designed to use available keys.
        # A simple way is to filter context based on what's in the prompt string, but that's fragile.
        # Let's assume the prompt YAML has placeholders for all these.
        
        try:
            # The prompt YAMLs have sections like 'persona', 'instructions', 'output_format_notes'
            # We need to decide how to combine these and format them.
            # For now, let's assume get_prompt returns a dictionary and we use 'instructions'.
            if isinstance(prompt_template, dict) and "instructions" in prompt_template:
                formatted_prompt = prompt_template["instructions"].format(**context)
                if "persona" in prompt_template:
                     formatted_prompt = f"{prompt_template['persona']}\n\n{formatted_prompt}"
                if "output_format_notes" in prompt_template:
                    formatted_prompt = f"{formatted_prompt}\n\n{prompt_template['output_format_notes']}"

            elif isinstance(prompt_template, str): # If get_prompt just returns the full string
                 formatted_prompt = prompt_template.format(**context)
            else:
                print(f"Error: Prompt for key {self.llm_persona_prompt_key} is not a string or expected dict.")
                return None

        except KeyError as e:
            print(f"Error formatting prompt {self.llm_persona_prompt_key}: Missing key {e}")
            # Potentially log the prompt and context for debugging
            # print(f"Prompt template: {prompt_template}")
            # print(f"Context: {context}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during prompt formatting: {e}")
            return None


        # print(f"--- LLM Agent {self.agent_id} Prompt for Round {market_state.current_round} ---")
        # print(formatted_prompt)
        # print("--------------------------------------------------------------------")

        llm_response_text = self.llm_client.generate_text(prompt=formatted_prompt)

        if not llm_response_text:
            print(f"LLM Agent {self.agent_id} received no response from LLM.")
            return None

        # print(f"LLM Agent {self.agent_id} Response: {llm_response_text}")

        # Parse the LLM response (this is a critical and potentially complex step)
        # For MVP, expect a very specific format like "BID: price QUANTITY: quantity" or "ASK: price QUANTITY: quantity"
        try:
            action_type_str = None
            price = None
            quantity = None

            lines = llm_response_text.strip().split('\n')
            for line in lines:
                line_lower = line.lower()
                if "bid:" in line_lower and "quantity:" in line_lower: # BID: 100 QUANTITY: 1
                    parts = line.split()
                    try:
                        price_idx = parts.index("BID:") + 1 if "BID:" in parts else parts.index("bid:") + 1
                        qty_idx = parts.index("QUANTITY:") + 1 if "QUANTITY:" in parts else parts.index("quantity:") + 1
                        price = float(parts[price_idx])
                        quantity = int(parts[qty_idx])
                        action_type_str = "bid"
                        break
                    except (ValueError, IndexError):
                        continue # Try next line or parsing method
                elif "ask:" in line_lower and "quantity:" in line_lower: # ASK: 100 QUANTITY: 1
                    parts = line.split()
                    try:
                        price_idx = parts.index("ASK:") + 1 if "ASK:" in parts else parts.index("ask:") + 1
                        qty_idx = parts.index("QUANTITY:") + 1 if "QUANTITY:" in parts else parts.index("quantity:") + 1
                        price = float(parts[price_idx])
                        quantity = int(parts[qty_idx])
                        action_type_str = "ask"
                        break
                    except (ValueError, IndexError):
                        continue # Try next line or parsing method
                # Simpler parsing for lines like "BID: 100" and "QUANTITY: 1" on separate lines
                if "bid:" in line_lower and price is None:
                    try: price = float(line.split(":")[1].strip())
                    except: pass
                if "ask:" in line_lower and price is None:
                    try: price = float(line.split(":")[1].strip())
                    except: pass
                if "quantity:" in line_lower and quantity is None:
                    try: quantity = int(line.split(":")[1].strip())
                    except: pass
            
            # If parsed separately, determine action type
            if price is not None and quantity is not None:
                if action_type_str: # Already determined
                    pass
                elif self.agent_type == "buyer": # Infer from agent type if not explicit
                    action_type_str = "bid"
                elif self.agent_type == "seller":
                    action_type_str = "ask"

            if action_type_str and price is not None and quantity is not None and price > 0 and quantity > 0:
                # Validate against agent's capabilities
                if action_type_str == "bid" and self.agent_type == "buyer":
                    if self.funds is not None and self.funds >= price * quantity:
                         return BidAsk(agent_id=self.agent_id, bid_ask_type="bid", price=price, quantity=quantity, round=market_state.current_round)
                    else:
                        # print(f"LLM Agent {self.agent_id} wanted to bid {quantity} at {price} but has insufficient funds ({self.funds}).")
                        pass # Not enough funds
                elif action_type_str == "ask" and self.agent_type == "seller":
                    if self.inventory is not None and self.inventory >= quantity:
                        return BidAsk(agent_id=self.agent_id, bid_ask_type="ask", price=price, quantity=quantity, round=market_state.current_round)
                    else:
                        # print(f"LLM Agent {self.agent_id} wanted to ask {quantity} at {price} but has insufficient inventory ({self.inventory}).")
                        pass # Not enough inventory
            # else:
                # print(f"LLM Agent {self.agent_id} did not provide a valid action in response: '{llm_response_text}'")

        except Exception as e:
            print(f"Error parsing LLM response for agent {self.agent_id}: {e}. Response: '{llm_response_text}'")
            return None

        return None # If parsing fails or LLM decides not to act

# Example of how AgentConfig might be used with Agent (conceptual for now)
# if __name__ == "__main__":
#     buyer_config_data = {
#         "agent_id": "buyer_001",
#         "agent_type": "buyer",
#         "initial_funds": 1000.0,
#         "llm_persona_prompt_key": "buyer_conservative_persona",
#         "valuation_or_cost": 120.0
#     }
#     buyer_config = AgentConfig(**buyer_config_data)
    
#     # Dummy LLM Client and Prompt Manager for testing
#     class DummyLLMClient:
#         def generate_text(self, prompt: str, model_name: str = "gemini-pro", temperature: float = 0.7) -> str | None:
#             print(f"\n---DummyLLMClient received prompt---\n{prompt}\n------------------------------------")
#             if "buyer" in prompt:
#                 return "BID: 105.50\nQUANTITY: 1"
#             return "ASK: 115.00\nQUANTITY: 1"

#     class DummyPromptManager:
#         def get_prompt(self, prompt_name: str, **kwargs) -> Dict[str, str] | str | None:
#             if prompt_name == "buyer_conservative_persona":
#                 return {
#                     "persona": "You are a careful buyer.",
#                     "instructions": "Current Round: {current_round}. Funds: {agent_funds}. Valuation: {valuation}. Bids: {market_bids_summary}. Asks: {market_asks_summary}. Decide: BID: [price] QUANTITY: [qty]",
#                     "output_format_notes": "Format: BID: price QUANTITY: quantity"
#                 }
#             return None

#     rule_agent = RuleBasedAgent(config=buyer_config)
#     llm_agent = LLMAgent(config=buyer_config, llm_client=DummyLLMClient(), prompt_manager=DummyPromptManager())

#     market_now = MarketState(
#         current_round=1,
#         bids=[BidAsk(agent_id="b2", bid_ask_type="bid", price=100, quantity=2, round=1)],
#         asks=[BidAsk(agent_id="s2", bid_ask_type="ask", price=110, quantity=3, round=1)]
#     )
    
#     rule_action = rule_agent.decide_action(market_now)
#     print(f"RuleBasedAgent action: {rule_action}")

#     llm_action = llm_agent.decide_action(market_now)
#     print(f"LLMAgent action: {llm_action}")

#     # Test transaction update
#     if rule_action and rule_agent.funds is not None:
#         print(f"Rule agent funds before: {rule_agent.funds}")
#         rule_agent.update_state_after_transaction(rule_action.price, rule_action.quantity, is_buyer=True)
#         print(f"Rule agent funds after: {rule_agent.funds}, inventory: {rule_agent.inventory}")