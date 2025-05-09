# AI Econ Lab

**Vision:** To be a premier interactive educational platform that empowers technically-minded individuals, particularly programmers, to deeply understand complex economic, entrepreneurial, and behavioral principles through hands-on experimentation with and critical analysis of Large Language Models (LLMs).

**MVP Focus:** Deliver a fully functional and polished version of **Module 1: The Multi-Agent LLM Marketplace**.

This project is built using Python and Streamlit.

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
│   └── helpers.py           # General utility functions (e.g., state management wrappers) (Phase 1)
├── tests/                   # Unit tests (Phase 1 onwards)
│   ├── core/
│   └── modules/
├── requirements.txt         # Python dependencies
├── .gitignore
├── README.md                # This file
├── PLAN.md                  # Original high-level vision
└── DETAILED_IMPLEMENTATION_PLAN.MD # Detailed MVP plan
```

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
3.  Open your web browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`).
4.  You will be prompted for your Google AI Studio API key in the sidebar if you haven't entered it previously in the session.

## Development Phases (MVP)

This project follows the phases outlined in `DETAILED_IMPLEMENTATION_PLAN.MD`.

*   **Phase 0: Setup & Foundational Elements (Complete)**
*   **Phase 1:** Core Simulation Logic & Rule-Based Agents
*   **Phase 2:** Marketplace Module - "Market Genesis" with LLM Agents
*   **Phase 3:** "LLM Behavior Variant" Lab & Comparative Analysis
*   **Phase 4:** Testing, Documentation, Polish & Ethical Considerations

## Contributing

(Details to be added later if applicable)

## License

(To be determined)
