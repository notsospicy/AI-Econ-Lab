# AI Econ Lab

**Vision:** To be a premier interactive educational platform that empowers technically-minded individuals, particularly programmers, to deeply understand complex economic, entrepreneurial, and behavioral principles through hands-on experimentation with and critical analysis of Large Language Models (LLMs).

**MVP Focus:** Deliver a fully functional and polished version of **Module 1: The Multi-Agent LLM Marketplace**.
This module simulates a basic marketplace where autonomous buyer and seller agents interact over multiple rounds to trade a generic good. It demonstrates price discovery dynamics and market efficiency concepts. Users can configure parameters such as the number of buyers and sellers, their initial funds/inventory, and valuation/cost ranges via a Streamlit interface. They can then run the simulation and observe outcomes like price convergence, transaction volumes, and individual agent performance. In this module, LLMs (powered by Google's Gemini API) can be configured to act as buyer or seller agents. These LLM agents make decisions (to bid, ask, or pass) based on their persona, current market state, and interaction history, as guided by dynamic prompt templates.

This project is built using Python and Streamlit.

For those interested in the project's evolution and detailed planning, `PLAN.md` outlines the original high-level vision, while `DETAILED_IMPLEMENTATION_PLAN.md` provides a more granular breakdown of the steps taken to develop the Minimum Viable Product (MVP).
## Project Structure

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
│   ├── prompt_manager.py    # Loads and formats prompts (Phase 1)
│   ├── simulation_engine.py # Core logic for market simulation rounds (Phase 1)
│   └── models.py            # Pydantic models for Agents, Transactions, MarketState
├── modules/
│   ├── __init__.py
│   ├── base_module.py       # Abstract base class or interface for modules (Future)
│   └── marketplace/
│       ├── __init__.py
│       ├── logic.py         # Specific simulation logic for the marketplace module (Phase 1-2)
│       └── ui.py            # Streamlit UI components for the marketplace module (Phase 1-2)
├── ui/
│   ├── __init__.py
│   └── shared_components.py # Reusable Streamlit widgets (Phase 2)
├── utils/
│   ├── __init__.py
├── tests/                   # Unit tests (Phase 1 onwards)
│   ├── core/
│   └── modules/
├── requirements.txt         # Python dependencies
├── .gitignore
├── README.md                # This file
├── PLAN.md                  # Original high-level vision
└── DETAILED_IMPLEMENTATION_PLAN.md # Detailed MVP plan
```
## Key Technologies Used

*   Python
*   Streamlit (for the web UI)
*   Google Gemini API (via `google-generativeai` SDK for LLM capabilities)
*   Pydantic (for data modeling and validation)
*   PyYAML (for prompt configuration loading)
*   Jinja2 (for prompt templating)
*   Pandas (for data processing and display)
*   pytest (for unit and integration testing)

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd AI-Econ-Lab
    ```

2.  **Create and activate a virtual environment:**
    *   On macOS and Linux:
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```
    *   On Windows:
        ```bash
        python -m venv .venv
        .\.venv\Scripts\activate
        ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **API Key for Google AI Studio:**
    This application uses the Google Generative AI API (e.g., Gemini). You will need an API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
    The application will prompt you to enter this key in the sidebar when it first runs or when LLM features are accessed. The key is stored in the Streamlit session state and is not persisted by the application.

## How to Run

1.  Ensure your virtual environment is activated and dependencies are installed.
2.  Run the Streamlit application:
    ```bash
    streamlit run app.py
    ```
    This command will launch the AI Econ Lab application. The Marketplace module, which is the focus of the MVP, will be available as the primary simulation environment.
3.  Open your web browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`).
4.  You will be prompted for your Google AI Studio API key in the sidebar if you haven't entered it previously in the session.

## Development Phases (MVP)

This project follows the phases outlined in `DETAILED_IMPLEMENTATION_PLAN.MD`.

*   **Phase 0: Setup & Foundational Elements (Complete)**
*   **Phase 1:** Core Simulation Logic & Rule-Based Agents (Complete)
*   **Phase 2:** Marketplace Module - "Market Genesis" with LLM Agents (Complete)
*   **Phase 3:** "LLM Behavior Variant" Lab & Comparative Analysis (Planned for future extension)
*   **Phase 4:** Testing, Documentation, Polish & Ethical Considerations (Largely complete for MVP; ongoing refinement)

## Contributing

We welcome contributions to the AI Econ Lab!

To report bugs or suggest new features, please open an issue on GitHub.

If you'd like to contribute code:
1. Fork the repository.
2. Create a new branch for your feature or bug fix (e.g., `git checkout -b feature/your-feature-name` or `bugfix/issue-number`).
3. Make your changes.
4. Ensure your code passes any existing tests, or add new tests if you are introducing new functionality.
5. Submit a pull request with a clear description of your changes and why they are needed.

Please try to follow PEP 8 guidelines for Python code and maintain a clear and readable code style consistent with the existing codebase.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
