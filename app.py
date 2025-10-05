"""Minimal Streamlit port of the ArtRogue Shiny app.

Features:
- Search MET or CMA APIs
- Display a grid of small artwork cards
- Click to view a larger image and metadata

This is intentionally small and educational.
"""
from __future__ import annotations

import streamlit as st
from utils import fx_search, fx_search_result, CMA_LABEL, MET_LABEL


def main() -> None:
    st.set_page_config(page_title="ArtRogue", layout="wide")
    st.title("ArtRogue — The Unsnobby Museum Companion")

    col1, col2 = st.columns([3, 1])

    with col2:
        museum = st.selectbox(
            "Museum", options=[CMA_LABEL, MET_LABEL], index=0)

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


if __name__ == "__main__":
    main()
