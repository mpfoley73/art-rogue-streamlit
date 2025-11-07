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

# Future imports for type hinting and compatibility
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
from utils import fx_search, fx_search_result, CMA_LABEL, MET_LABEL
from chat import get_system_prompt


def main() -> None:
    st.set_page_config(
        page_title="ArtRogue",
        page_icon=":man_artist:",
        layout="wide"
    )

    # Configure OpenAI API key using this priority order:
    # 1. Load .env file (for local development)
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    # 2. Check Streamlit secrets (preferred for production)
    # These can be set in .streamlit/secrets.toml locally or in Streamlit Cloud UI
    secret_key = None
    try:
        # Use .get() for safe access in both Streamlit and non-Streamlit contexts
        secret_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        secret_key = None

    # 3. Get final key, preferring Streamlit secrets over environment variables
    # Environment variables could come from .env (step 1) or system environment
    env_key = os.environ.get("OPENAI_API_KEY")
    final_key = secret_key or env_key
    if final_key:
        os.environ.setdefault("OPENAI_API_KEY", final_key)
    st.title("ArtRogue — The Unsnobby Museum Companion")

    col1, col2 = st.columns([3, 1])

    # Left column is search, right column is chat.
    with col2:
        museum = st.selectbox(
            "Museum", options=[CMA_LABEL, MET_LABEL], index=0)
        st.markdown("---")
        st.subheader("ArtRogue Chat")
        # Initialize chat history in session state as list of messages
        # Each message is a dict: {"role": "user"|"assistant"|"system", "content": str}
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        # Display existing messages
        chat_box = st.container()
        with chat_box:
            for msg in st.session_state["chat_history"]:
                role = msg.get("role")
                content = msg.get("content")
                if role == "user":
                    st.markdown(f"**You:** {content}")
                elif role == "assistant":
                    st.markdown(f"**ArtRogue:** {content}")
                else:
                    st.markdown(f"**{role}:** {content}")

        # Input for follow-up questions
        followup = st.text_input(
            "Your message to ArtRogue", key="followup_input")
        if st.button("Send") and followup:
            # Append user message
            st.session_state["chat_history"].append(
                {"role": "user", "content": followup})
            # Stream assistant response and append progressively
            assistant_msg = ""
            placeholder = st.empty()
            messages = [{"role": "system", "content": get_system_prompt()}]
            # Build messages from history (system + chat)
            for m in st.session_state["chat_history"]:
                messages.append({"role": m["role"], "content": m["content"]})
            for chunk in __import__("chat").stream_messages(messages):
                assistant_msg += chunk
                placeholder.markdown(f"**ArtRogue:** {assistant_msg}")
            # final append
            st.session_state["chat_history"].append(
                {"role": "assistant", "content": assistant_msg})

    with col1:
        q = st.text_input(
            "Search artworks / artist / keyword", value="van gogh")
        c1, c2, c3 = st.columns([1, 1, 1])
        if c1.button("Search"):
            results = fx_search(museum, q)
            st.session_state["results"] = results
        if c2.button("Surprise Me"):
            results = fx_search(museum, "*")
            st.session_state["results"] = results
        if c3.button("What's New?"):
            results = fx_search(museum, "*", highlight=True)
            st.session_state["results"] = results

    results = st.session_state.get("results", [])

    if not results:
        st.info("No results yet. Try a search or click 'Surprise Me'.")
        return

    # Display results as cards
    cols = st.columns(4)
    for i, art in enumerate(results):
        display = fx_search_result(museum, art)
        with cols[i % 4]:
            if display["img_url"]:
                st.image(display["img_url"], use_column_width=True)
            st.markdown(f"**{display['title']}**")
            st.caption(f"{display['artist']} — {display['creation_date']}")
            if st.button("View", key=f"view_{i}"):
                st.session_state["selected"] = (museum, art)

    selected = st.session_state.get("selected")
    if selected:
        museum_label, art = selected
        display = fx_search_result(museum_label, art)
        st.markdown("---")
        st.header(display["title"])
        st.image(display["img_url"], width=800)
        st.write(f"**Artist:** {display['artist']}")
        st.write(f"**Date:** {display['creation_date']}")
        # Offer quick chat about this artwork
        st.markdown("---")
        st.subheader("Chat about this artwork")
        if st.button("Summarize artwork in Januszczak style"):
            # Start a new conversation for this artwork summary
            sys_msg = {"role": "system", "content": get_system_prompt()}
            user_msg = {
                "role": "user", "content": "I am looking at an image of a work of art. What should I understand about it? No need to see the image. Here is the metadata: " + str(art)}
            st.session_state["chat_history"] = [sys_msg, user_msg]
            assistant_msg = ""
            placeholder = st.empty()
            for chunk in __import__("chat").stream_messages(st.session_state["chat_history"]):
                assistant_msg += chunk
                placeholder.markdown(f"**ArtRogue:** {assistant_msg}")
            st.session_state["chat_history"].append(
                {"role": "assistant", "content": assistant_msg})


if __name__ == "__main__":
    main()
