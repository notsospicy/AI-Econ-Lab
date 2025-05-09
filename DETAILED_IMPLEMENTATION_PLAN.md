# DETAILED_IMPLEMENTATION_PLAN.MD: AI Econ Lab (100-Hour MVP)

This document outlines a detailed plan for developing the Minimum Viable Product (MVP) of the AI Econ Lab within a ~100-hour timeframe. It synthesizes previous discussions and aims to provide an actionable roadmap.

## 1. Core Philosophy & MVP Scope

*   **Philosophy:** Adhere to the principles in `PLAN.MD`: Interactive Experimentation, Critical AI Engagement, Conceptual Depth, Clarity, and Modular Design (though MVP focuses on one module).
*   **MVP Focus:** Deliver a fully functional and polished version of **Module 1: The Multi-Agent LLM Marketplace**.
    *   **Key Labs:**
        1.  "Market Genesis": LLM agents (buyers, sellers) interact over rounds to trade a good, demonstrating price discovery.
        2.  "LLM Behavior Variant": Run the same market with agents powered by different LLM configurations (e.g., different models or prompting strategies) to compare outcomes.
*   **Target Audience:** Programmers and technically proficient individuals.
*   **Constraint:** Approximately 100 hours of development time.

## 2. Technology Stack

*   **Language:** Python
*   **Framework:** Streamlit (for UI, interactivity, and rapid development)
*   **LLM Integration:** Google AI Studio API (initially, with abstraction for potential future additions).
*   **Visualization:** Streamlit's native charting capabilities, Matplotlib/Seaborn (via `st.pyplot`), and potentially Plotly (via `st.plotly_chart`) if simple and time permits.
*   **Version Control:** Git

## 3. Detailed Folder Structure (Initial)

```
AI-Econ-Lab/
├── .streamlit/
│   └── config.toml        # Streamlit theme and app settings
├── app.py                   # Main Streamlit application entry point
├── config/
│   └── prompts/             # YAML files for LLM prompts
│       └── marketplace/
│           ├── buyer_default.yaml
│           └── seller_default.yaml
├── core/
│   ├── __init__.py
│   ├── llm_client.py        # Handles all interactions with LLM APIs
│   ├── prompt_manager.py    # Loads and formats prompts
│   ├── simulation_engine.py # Core logic for market simulation rounds
│   └── models.py            # Pydantic models for Agents, Transactions, MarketState
├── modules/
│   ├── __init__.py
│   ├── base_module.py       # Abstract base class or interface for modules (for future)
│   └── marketplace/
│       ├── __init__.py
│       ├── logic.py         # Specific simulation logic for the marketplace module
│       └── ui.py            # Streamlit UI components for the marketplace module
├── ui/
│   ├── __init__.py
│   └── shared_components.py # Reusable Streamlit widgets (e.g., LLM output display, charts)
├── utils/
│   ├── __init__.py
│   └── helpers.py           # General utility functions (e.g., state management wrappers)
├── tests/                   # Unit tests
│   ├── core/
│   └── modules/
├── requirements.txt         # Python dependencies (consider Poetry or pip-tools later)
├── .gitignore
└── README.md                # Project overview, setup, how to run
└── DETAILED_IMPLEMENTATION_PLAN.MD # This file
└── PLAN.MD                  # Original high-level vision
```

## 4. Core Services Design

### 4.1. `core/models.py`
*   Define data structures using Pydantic for validation and clarity.
    *   `AgentConfig`: id, type (buyer/seller), initial_funds/inventory, LLM persona/prompt_key.
    *   `Agent`: Base class with `decide_action(market_state)` method.
        *   `RuleBasedAgent(Agent)`: Simple hardcoded logic for baseline/testing.
        *   `LLMAgent(Agent)`: Uses `llm_client` to make decisions.
    *   `BidAsk`: agent_id, type (bid/ask), price, quantity.
    *   `Transaction`: buyer_id, seller_id, price, quantity, round.
    *   `MarketState`: current_round, bids (list[BidAsk]), asks (list[BidAsk]), price_history, transaction_log.

### 4.2. `core/llm_client.py`
*   **Responsibilities:**
    *   Initialize connection to Google AI Studio.
    *   Handle API key input securely (e.g., `st.text_input(type="password")` stored in `st.session_state`, not committed).
    *   Method to send prompt and context to LLM, receive response.
    *   Error handling and retries (basic).
    *   (Optional for MVP) Caching responses for identical prompts to save API calls during development.
    *   (Optional for MVP) Mock/Stub mode: Returns predefined responses for testing without API calls.

### 4.3. `core/prompt_manager.py`
*   **Responsibilities:**
    *   Load prompts from YAML files in `config/prompts/`.
    *   Simple templating if needed (e.g., injecting agent ID, current round, market history snippet). Python's `.format()` or f-strings might be sufficient initially over Jinja2.
    *   Provide a function like `get_prompt(prompt_name, **kwargs) -> str`.

### 4.4. `core/simulation_engine.py`
*   **Responsibilities:**
    *   `MarketSimulation` class:
        *   Initialize with agents, number of rounds.
        *   `run_round()`:
            1.  Gather actions (bids/asks) from all agents based on current `MarketState`.
            2.  Matching engine: Implement a simple price-time priority or continuous double auction mechanism to clear trades.
            3.  Update `MarketState` (transactions, price levels).
            4.  Update agent states (funds, inventory).
        *   `run_simulation()`: Loop `run_round()` for the specified number of rounds.
        *   Store history of market states and transactions.

## 5. Module Implementation: Marketplace (`modules/marketplace/`)

### 5.1. `modules/marketplace/logic.py`
*   Contains functions or classes that orchestrate the setup and execution of the marketplace simulation using `core` services.
*   `setup_simulation(user_params)`: Creates agent instances, initializes `MarketSimulation`.
*   Functions to process simulation results for UI display.

### 5.2. `modules/marketplace/ui.py`
*   **Streamlit UI components:**
    *   **Inputs (Sidebar):**
        *   Number of buyer/seller agents.
        *   Number of simulation rounds.
        *   (Lab 2) LLM configuration selection for different agent groups.
        *   Button to start/reset simulation.
    *   **Main Area Display:**
        *   **Market Overview:** Current round, key stats.
        *   **Visualizations (`ui/shared_components.py`):**
            *   Price convergence chart (line chart of average transaction price per round).
            *   Volume chart (bar chart of transactions per round).
            *   Order book visualization (optional, if time permits).
        *   **Transaction Log:** Table of completed trades.
        *   **Agent Inspector (Optional):** View individual agent's state, decisions.
        *   **(Lab 2) Comparative Display:** Side-by-side charts/stats for different LLM configurations using `st.columns` or `st.tabs`.
    *   **Educational Content:** `st.markdown` for explanations, `st.expander` for details.
    *   **Reflection Prompts:** `st.text_area` for user thoughts.

## 6. UI/UX & State Management (`utils/helpers.py`)

*   **State Management:**
    *   Wrap `st.session_state` access: `get_state(key, default_value)`, `set_state(key, value)`.
    *   Persist simulation state, user inputs, API keys (for session only).
*   **Navigation:** Streamlit's native sidebar for module selection (future) and current module controls.
*   **Theming:** Basic `config.toml` for primary color, font. Keep it simple.
*   **Responsiveness:** Rely on Streamlit's default responsiveness.

## 7. Development Phases & Timeline (100 Hours)

### Phase 0: Setup & Foundational Elements (5 Hours)
*   [ ] Project setup: Git repo, virtual environment, install Streamlit, Pydantic.
*   [ ] Create initial folder structure.
*   [ ] Basic Streamlit app (`app.py`) with a title.
*   [ ] `core/llm_client.py`: Basic function to call Google AI Studio with a hardcoded prompt and display response in Streamlit. Secure API key input.
*   [ ] `core/models.py`: Define initial Pydantic models (AgentConfig, basic MarketState).

### Phase 1: Core Simulation Logic & Rule-Based Agents (25 Hours)
*   [ ] `core/models.py`: Finalize all Pydantic models.
*   [ ] `core/prompt_manager.py`: Load simple prompts from YAML.
*   [ ] `core/simulation_engine.py`:
    *   [ ] Implement `MarketSimulation` class structure.
    *   [ ] Implement `RuleBasedAgent` (e.g., buyer bids below valuation, seller asks above cost).
    *   [ ] Implement basic matching engine logic within `run_round()`.
*   [ ] `modules/marketplace/logic.py`: Function to set up and run a simulation with rule-based agents.
*   [ ] `modules/marketplace/ui.py`: Basic UI to trigger rule-based simulation and display raw results (e.g., print transaction list).
*   [ ] `tests/`: Basic unit tests for `RuleBasedAgent` and matching logic.

### Phase 2: Marketplace Module - "Market Genesis" with LLM Agents (30 Hours)
*   [ ] `core/llm_client.py`: Refine to handle dynamic prompts and context.
*   [ ] `core/models.py`: Implement `LLMAgent` class, integrating `llm_client` and `prompt_manager`.
*   [ ] `config/prompts/marketplace/`: Create initial buyer and seller prompts.
*   [ ] `modules/marketplace/logic.py`: Update to allow `LLMAgent` instantiation.
*   [ ] `modules/marketplace/ui.py`:
    *   [ ] Develop UI for "Market Genesis" lab.
    *   [ ] Inputs for simulation parameters.
    *   [ ] `ui/shared_components.py`: Implement price convergence chart and transaction log display.
    *   [ ] Integrate educational content and reflection prompts.
*   [ ] `app.py`: Structure to load and display the marketplace module.
*   [ ] `tests/`: Unit tests for `prompt_manager` and `LLMAgent` (mocking LLM calls).

### Phase 3: "LLM Behavior Variant" Lab & Comparative Analysis (25 Hours)
*   [ ] `modules/marketplace/ui.py`:
    *   [ ] Add UI elements for selecting different LLM configurations for agent groups (e.g., different prompts, or if feasible, different models via `llm_client`).
    *   [ ] Implement comparative display (side-by-side charts/stats).
*   [ ] `config/prompts/marketplace/`: Add alternative prompts for behavior variants.
*   [ ] `modules/marketplace/logic.py`: Adapt to run simulations with mixed/varied agent configurations and collect results for comparison.
*   [ ] Refine visualizations for clarity in comparison.

### Phase 4: Testing, Documentation, Polish & Ethical Considerations (15 Hours)
*   [ ] Comprehensive testing of all features.
*   [ ] `README.md`: Write detailed setup, usage instructions.
*   [ ] Code comments and docstrings.
*   [ ] Basic UI theming via `.streamlit/config.toml`.
*   [ ] Integrate prominent disclaimers about LLM limitations, simulation simplifications, and not providing financial advice.
*   [ ] Final review of educational content for clarity and accuracy.
*   [ ] Ensure responsible AI usage principles are communicated.

## 8. Testing Strategy

*   **Unit Tests:** For core, deterministic logic (Pydantic models, rule-based agents, matching engine, prompt loading). Use `pytest`.
*   **Mocking:** Mock LLM API calls in `llm_client` for testing agent behavior and simulation flow without actual API costs or variability.
*   **Integration Tests (Manual):** Run through Streamlit UI to test full simulation flow and UI interactions.
*   **Focus:** Test business logic thoroughly. UI testing will be primarily manual.

## 9. Documentation

*   **`README.md`:** Overall project description, goals, how to set up the development environment, how to run the application, and contribution guidelines (if any).
*   **Code Comments:** Explain complex logic, assumptions, and design choices within the code.
*   **Docstrings:** For public functions and classes.
*   **Module-Specific Info:** Brief descriptions within each module's `ui.py` or a small `README.md` inside the module folder if it grows complex.
*   **This Plan:** `DETAILED_IMPLEMENTATION_PLAN.MD` serves as the primary planning document.

## 10. Ethical Considerations & Disclaimers

*   **In-App Text:** Clearly state that this is an educational simulation, not financial advice.
*   **LLM Limitations:** Explain that LLMs can be unpredictable, biased, or generate incorrect information.
*   **Data Privacy:** All user inputs (like API keys) are handled client-side or in session state and not stored persistently by the application.
*   **Transparency:** Be clear about how LLMs are used to drive agent decisions.

This detailed plan should provide a solid framework for the 100-hour development effort. Flexibility will be key, and some features might need to be simplified or deferred based on progress. Regular self-assessment against the timeline will be important.
