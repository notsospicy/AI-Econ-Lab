import streamlit as st

st.set_page_config(layout="wide")

st.title("AI Econ Lab")

st.markdown("""
Welcome to the AI Econ Lab!

This platform allows for interactive experimentation with economic principles using Large Language Models.
Select a module from the sidebar to begin.
""")

# Import the marketplace module UI
from modules.marketplace import ui as marketplace_ui

# --- Module Navigation (Simple for MVP) ---
# For MVP, we only have one module. In the future, this could be a selectbox or a more complex router.
# For now, we'll always render the marketplace module.

# Placeholder for future module selection
# module_options = {
#     "Marketplace": marketplace_ui.render_marketplace_module,
#     # "Negotiators & Game Theory": None, # Placeholder for Module 2
# }

# selected_module_name = st.sidebar.radio(
#     "Select Module:",
#     list(module_options.keys()),
#     key="main_module_selector"
# )

if __name__ == "__main__":
    # Directly render the marketplace module for the MVP
    marketplace_ui.render_marketplace_module()

    # Footer or common elements can go here
    st.sidebar.markdown("---")
    st.sidebar.info(
        "AI Econ Lab MVP | "
        "[GitHub](https://github.com/your-repo/AI-Econ-Lab)" # Replace with actual repo
    )