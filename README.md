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
# art-rogue-streamlit