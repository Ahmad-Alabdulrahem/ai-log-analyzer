# AI Log Analyzer (Flask + regex + spaCy + Gemini optional)

This is a ready-to-run Python web app for **Windows / Visual Studio 2022**.
It lets you upload Android log files, runs **regex + spaCy** analysis locally,
and (optionally) calls **Google Gemini** to produce a concise AI summary.

## Quick Start (Windows, Visual Studio)
1) Open **Visual Studio 2022** → *Open a local folder* → select this folder.
2) Create a virtual environment (recommended Python 3.11 or 3.12 for best spaCy compatibility).
   - If you only have Python 3.13, it may still work; if spaCy fails to install,
     create an additional 3.11 environment from the Visual Studio *Python Environments* window.
3) In the VS Terminal (PowerShell), run:
   ```powershell
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```
   If that model fails on Python 3.13, try a 3.11 or 3.12 environment.
4) Copy `.env.example` to `.env` and paste your **regenerated** Gemini key:
   ```
   GEMINI_API_KEY=your_new_key_here
   ```
   > If you don't want to use Gemini, you can skip the API key; the app will still run with regex+spaCy.
5) Run the app (press ▶️ in Visual Studio or run `python app.py`).
6) Open http://127.0.0.1:5000 and upload a `.log` or `.txt` file.

## What it does
- **Regex detection** of common Android error types (NullPointerException, OutOfMemoryError, NetworkOnMainThreadException)
- **spaCy entity extraction** (file names, APIs, etc.). If spaCy isn't available, the app degrades gracefully.
- **Gemini summary (optional)**: If `GEMINI_API_KEY` is present, the app asks Gemini to summarize the log.

## Offline / Privacy
- Regex + spaCy run fully **offline**.
- Gemini requires **internet** and sends your text to Google via API. Omit the key if you must stay offline.

## Files
- `app.py` – Flask app
- `regex_analysis.py` – local analysis (regex + spaCy)
- `analyze.py` – Gemini integration (optional)
- `utils/log_reader.py` – file loader
- `templates/index.html` – simple UI
- `requirements.txt` – dependencies
- `.env.example` – template for your API key

## Notes for Python 3.13
- Some spaCy wheels may lag behind for brand-new Python releases.
  If `pip install spacy` or `python -m spacy download en_core_web_sm` fails,
  create a **Python 3.11** environment in Visual Studio and use that for this project.
  Gemini and Flask work fine on 3.13; this note is only about spaCy compatibility.
