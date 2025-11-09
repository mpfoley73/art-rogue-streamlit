"""Streamlit port of the ArtRogue Shiny app.

This module defines the Streamlit UI and wires the user interactions to
the helper modules in this package. The app layout uses two columns: the
left column for search/results and the right column for the chat UI.

High-level responsibilities:
- Manage Streamlit `st.session_state` for search results and chat history
- Render artwork cards and a selected-artwork view
- Start and continue conversations by building a `messages` list and
    delegating streaming to `chat.stream_messages`.
"""

from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI
from museum_api import fx_search, fx_search_result, CMA_LABEL, MET_LABEL
from chat import get_system_prompt

# Best practice: Wrap the app in a main() to avoid global state issues.


def main() -> None:

    # Set OpenAI API key from Streamlit secrets, .env, or environment var.
    # 1. Load .env file (for local development)
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    # 2. Check Streamlit secrets (preferred for production).
    # Set secrets locally in .streamlit/secrets.toml or in Streamlit Cloud UI.
    secret_key = None
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        secret_key = None

    # 3. Set key, preferring Streamlit secrets over environment variable.
    # Environment variables could come from .env (step 1) or system environment
    env_key = os.environ.get("OPENAI_API_KEY")
    openai_api_key = secret_key or env_key
    if openai_api_key:
        os.environ.setdefault("OPENAI_API_KEY", openai_api_key)

    # Configure Streamlit page
    st.set_page_config(
        page_title="ArtRogue",
        page_icon=":man_artist:",
        layout="wide"
    )

    st.title("ArtRogue")

    # Settings and search in a sidebar
    # with statements are commonly used for context creation. Without it, you'd
    # have to enter st.sidebar.whatever() for each element.
    with st.sidebar:

        museum = st.selectbox(
            "Museum",
            options=[CMA_LABEL, MET_LABEL],
            index=0,
            width=300
        )
        st.markdown("---")
        q = st.text_input("Search", value="van gogh")
        if st.button("Search"):
            results = fx_search(museum, q)
            st.session_state["results"] = results
        st.markdown("---")
        c1, c2 = st.columns([1, 1])
        if c1.button("Surprise Me"):
            results = fx_search(museum, "*")
            st.session_state["results"] = results
        if c2.button("What's New?"):
            results = fx_search(museum, "*", highlight=True)
            st.session_state["results"] = results

    # Main content area with two columns. Left col for search results,
    # right for chat interface.
    col1, col2 = st.columns([0.6, 0.4], gap="medium")

    # Left column for search results
    with col1:

        # `selected` is set when user clicks "View" on a painting card.
        selected = st.session_state.get("selected")

        # `results` is set when user clicks button to generate search results.
        results = st.session_state.get("results", [])

        # Add a "Back to Results" button when a painting is selected.
        # Clicking the button sets `selected` back to none so the displayed
        # image disappears and the results grid reappears.
        if selected and st.button("← Back to Results"):
            st.session_state["selected"] = None
            st.rerun()

        # Show either the selected painting or the search results
        if selected:
            # Display selected artwork
            museum_label, art = selected
            display = fx_search_result(museum_label, art)
            st.header(display["title"])
            st.image(display["img_url"], width=800)
            st.write(f"**Artist:** {display['artist']}")
            st.write(f"**Date:** {display['creation_date']}")
        else:
            # Display search results
            if not results:
                st.info("No results yet. Try a search.")
            else:
                result_cols = st.columns(3)
                for i, art in enumerate(results):
                    display = fx_search_result(museum, art)
                    with result_cols[i % 3]:
                        if display["img_url"]:
                            st.image(display["img_url"],
                                     use_container_width=True)
                        st.markdown(f"**{display['title']}**")
                        st.caption(
                            f"{display['artist']} — {display['creation_date']}")
                        if st.button("View", key=f"view_{i}"):
                            st.session_state["selected"] = (museum, art)
                            st.rerun()

    # Right column for chat interface
    with col2:
        st.subheader("ArtRogue Chat")

        if "messages" not in st.session_state:
            st.session_state["messages"] = [
                {"role": "assistant", "content": "How can I help you?"}]

        # Create a container for the chat messages
        chat_container = st.container(height=600)

        # Create a container for the chat input at the bottom
        input_container = st.container()

        # Handle chat input first (at the bottom)
        with input_container:
            if selected:
                # if st.button("Summarize artwork in Januszczak style"):
                sys_msg = {"role": "system",
                           "content": get_system_prompt()}
                user_msg = {
                    "role": "user",
                    "content": "I am looking at an image of a work of art. What should I understand about it? No need to see the image. Here is the metadata: " + str(art)
                }
                st.session_state.messages = [sys_msg, user_msg]
                client = OpenAI(api_key=openai_api_key)
                response = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=st.session_state.messages
                )
                msg = response.choices[0].message.content
                st.session_state.messages.append(
                    {"role": "assistant", "content": msg})
            # Chat input
            if prompt := st.chat_input():
                client = OpenAI(api_key=openai_api_key)
                st.session_state.messages.append(
                    {"role": "user", "content": prompt})
                response = client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=st.session_state.messages
                )
                msg = response.choices[0].message.content
                st.session_state.messages.append(
                    {"role": "assistant", "content": msg})

        # Display chat messages in the container above the input
        with chat_container:
            for msg in st.session_state.messages:
                st.chat_message(msg["role"]).write(msg["content"])


if __name__ == "__main__":
    main()
