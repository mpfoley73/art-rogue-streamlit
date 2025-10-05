ArtRogue Streamlit
==================

Minimal port of the ArtRogue Shiny app to Streamlit. 

Run locally:

```powershell
# create a virtual env and install
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
streamlit run app.py
```

Files:
- `app.py` — main Streamlit app
- `utils.py` — helpers to query MET and CMA APIs

Chat / OpenAI
---------------

This prototype includes a simple chat panel that uses OpenAI's API to generate text. To use it set an environment variable `OPENAI_API_KEY` with your OpenAI API key before running Streamlit. If the key or SDK aren't available, the chat will show a helpful message instead of streaming.

# Local development with a .env file
#
# You can also store the key in a local `.env` file for convenience while developing. Make sure `.env` is in `.gitignore` (the repo includes one).
# Example `.env`:
#

Architecture
------------

This repository contains a small Streamlit app that mirrors an R/Shiny app called ArtRogue. The core files are:

- `app.py` — Streamlit application: layout, widgets, session state, and wiring between UI and helpers.
- `utils.py` — Small helpers that query the MET and Cleveland Museum of Art APIs and normalize results for the UI.
- `chat.py` — Thin OpenAI integration layer that streams LLM responses. Supports both the new `openai>=1.0` client and older SDKs.
- `requirements.txt` — Python dependencies used to run the app.
- `.streamlit/secrets.toml` & `.env` — Local secret storage (ignored by git when configured correctly).

Data shapes and flow
--------------------

- Search results: `utils.fx_search(api_label, q)` returns a list of artwork dicts returned directly from the museum APIs. Each artwork dict has vendor-specific fields (e.g., `primaryImageSmall` for MET or `images.web.url` for CMA).
- Normalized result: `utils.fx_search_result(api_label, artwork)` returns a dict with `img_url`, `title`, `artist`, and `creation_date` used by the UI.
- Chat messages: a list of message dicts, each `{role: "system"|"user"|"assistant", content: str}`. `chat.stream_messages(messages)` streams the assistant response for that conversation history.

Where to read the code
----------------------
- Start at `app.py` to understand UI layout, session state, and the user flow (search -> select -> chat).
- Inspect `utils.py` when you want to extend or change the museum API behavior.
- Inspect `chat.py` to change the LLM model, streaming behavior, or to add retries / rate-limiting.

# ```ini
# OPENAI_API_KEY=sk-...yourkey...
# ```
#
# The app now loads `.env` automatically (via python-dotenv) and will also prefer `st.secrets` when available.

# art-rogue-streamlit