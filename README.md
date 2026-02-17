# Google Dependency Audit (Streamlit)

A Streamlit questionnaire that scores **how centralized your digital life is around a single Google account** across:

- Identity Centralization
- Archive Concentration
- Workflow Reliance
- Resilience / Redundancy

It produces a composite **Lock‑In Index** and a results page with practical mitigation guidance (including a “Selective Backup Strategy”).

<p align="center">
  <img src="assets/hero.png" alt="Google Dependency Audit hero" width="800">
</p>

## Quick start (local)

```bash
# 1) Create & activate a virtual environment (recommended)
python -m venv .venv
.\.venv\Scripts\activate

# 2) Install deps
pip install -r requirements.txt

# 3) Run the app
streamlit run app.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501).

## Deploy (Streamlit Community Cloud)

1. Push this repo to GitHub.
2. Go to Streamlit Community Cloud and create a new app.
3. Select:
   - **Repository:** your fork
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Deploy.

## What’s included

- `app.py` — the Streamlit app
- `requirements.txt` — Streamlit dependency list
- `assets/hero.png` — project image used in the README
- `docs/Reducing-Your-Digital-Dependency-On-Google-Services.pdf` — the companion blueprint (optional)

## Companion blueprint

If you want to include the written guide that pairs with this app, it’s in:

- `docs/Reducing-Your-Digital-Dependency-On-Google-Services.pdf`

(This is the same “Selective Backup Strategy Blueprint” referenced in the UI.)

## Roadmap ideas

- Export results as JSON/Markdown
- Add a “Top risks” summary section derived from answers
- Optional “Takeout size (GB)” weighting in the composite score
- Add unit tests for scoring logic

## License

MIT (see `LICENSE`).
