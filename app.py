import os
import re
import spacy
import requests
from flask import Flask, render_template, request, Request
from dotenv import load_dotenv
import google.generativeai as genai

# -------------------------------
#   FIX FOR LARGE FILE UPLOADS
# -------------------------------
class LargeRequest(Request):
    max_content_length = 500 * 1024 * 1024  # 500 MB upload limit

# --- Load environment variables ---
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
app.request_class = LargeRequest
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB limit

# --- spaCy Setup ---
try:
    nlp = spacy.load("en_core_web_sm")
    nlp.max_length = 2_000_000
    print("✅ spaCy loaded successfully.")
except Exception as e:
    print("❌ spaCy failed to load:", e)
    nlp = None

# --- Gemini Setup ---
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "models/gemini-2.5-flash"

if API_KEY:
    genai.configure(api_key=API_KEY)
    print(f"✅ Gemini API key loaded (starts with): {API_KEY[:8]}...")
else:
    print("⚠️ No Gemini API key found in .env!")

# --- LLaMA / Ollama Setup ---
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
print(f"🦙 Ollama model set to: {OLLAMA_MODEL}")

# ---------------------------------------
#   LOG LEVEL PARSING
# ---------------------------------------
LOG_LEVEL_ORDER = {
    "E": 0,
    "W": 1,
    "I": 2,
    "D": 3,
    "V": 4,
    "X": 5,  
}

LOG_LEVEL_RE_FULL = re.compile(
    r"""
    ^\d{2}-\d{2}\s+
    \d{2}:\d{2}:\d{2}\.\d+\s+
    .*?\s([EWIDV])\s+
    """,
    re.VERBOSE,
)

LOG_LEVEL_RE_SIMPLE = re.compile(
    r"""^\s*([EWIDV])\s+[A-Za-z0-9._$:/-]+""",
    re.VERBOSE,
)

LOG_LEVEL_RE_SLASH = re.compile(
    r"""^\s*([EWIDV])/[A-Za-z0-9._$-]+""",
    re.VERBOSE,
)


def get_log_level(line: str):
    """Returnerar loggnivån (E/W/I/D/V) från en Android-loggrad."""
    if not line:
        return None

    for regex in (LOG_LEVEL_RE_FULL, LOG_LEVEL_RE_SIMPLE, LOG_LEVEL_RE_SLASH):
        m = regex.match(line)
        if m:
            return m.group(1)

    return None


# --------------------------------------------------------
#   SMART CRASHBLOCK RANKING
# --------------------------------------------------------
def extract_ranked_crashblocks(raw_text: str, context=25, max_blocks=30):
    markers = {
        "FATAL EXCEPTION": 3,
        "java.lang.": 3,
        "SIGABRT": 3,
        "signal 6": 3,
        "Abort message": 3,
        "OutOfMemoryError": 3,
        "Process ": 2,
        "has died": 2,
        "ANR in": 2,
        "ANR:": 2,
        "Error": 1,
        "Fail": 1,
        "Crash": 1,
    }

    lines = raw_text.splitlines()
    blocks = []

    for i, line in enumerate(lines):
        score = sum(weight for m, weight in markers.items() if m in line)
        if score > 0:
            start = max(0, i - context)
            end = min(len(lines), i + context)
            blocks.append((score, "\n".join(lines[start:end])))

    if not blocks:
        return raw_text

    blocks.sort(key=lambda x: -x[0])
    selected = blocks[:max_blocks]
    return "\n\n--- CRASH BLOCK ---\n\n".join(block for _, block in selected)


# --------------------------------------------------------
#   FELDETEKTERING + SORTERING
# --------------------------------------------------------
ERROR_PATTERN = re.compile(
    r"(Exception|Error|Fail|Crash|ANR|NullPointerException|OutOfMemoryError|RuntimeException)",
    re.IGNORECASE,
)


def collect_errors(lines):
    """
    Hittar ALLA felrader (med nivå) för statistik och sortering.
    Returnerar:
      - entries: lista av dicts {level, line, index}
      - summary: dict med counts per feltyp
      - has_real_levels: om någon rad har E/W/I/D/V
    """
    entries = []
    error_keywords = []
    has_real_levels = False

    for i, line in enumerate(lines):
        if ERROR_PATTERN.search(line):
            level_char = get_log_level(line)

            if level_char:
                has_real_levels = True
            else:
                # fallback: ingen nivå -> X
                level_char = "X"

            entries.append(
                {
                    "level": level_char,
                    "line": line,
                    "index": i,
                }
            )

            for m in ERROR_PATTERN.findall(line):
                error_keywords.append(m)

    summary = {e.title(): error_keywords.count(e) for e in set(error_keywords)}
    return entries, summary, has_real_levels


def sort_and_filter_errors(entries, selected_levels, has_real_levels):
    """
    Sorterar efter loggnivå och tar hänsyn till:
      - om riktiga nivåer (E/W/I/D/V) finns
      - vilka nivåer som användaren valt i UI
    Regler:
      - Om has_real_levels = True -> X tas bort helt.
      - Om has_real_levels = False -> ignorera valda nivåer, visa alla (X).
    """
    if has_real_levels:
        # ta bort X
        filtered = [e for e in entries if e["level"] != "X"]
        # använd checkbox-filtrering
        selected_set = set(selected_levels)
        filtered = [e for e in filtered if e["level"] in selected_set]
    else:
        # inga E/W/I/D/V: visa alla (X), strunta i checkboxar
        filtered = entries

    entries_sorted = sorted(
        filtered,
        key=lambda e: (LOG_LEVEL_ORDER.get(e["level"], 99), e["index"])
    )
    return entries_sorted


# -----------------------------
#     GEMINI ANALYSIS
# -----------------------------
def run_gemini_full_log_analysis(error_text: str) -> str:
    if not API_KEY:
        return "Ingen Gemini API-nyckel hittades."

    model = genai.GenerativeModel(GEMINI_MODEL)
    prompt = (
        "Du får utdrag ur en Android-loggfil som innehåller felrader och krascher.\n"
        "Beskriv kortfattat vilka problemen är, varför de händer och ge enkla "
        "förslag på lösning. Skriv på svenska.\n\n"
        f"{error_text}"
    )

    try:
        result = model.generate_content(prompt)
        return result.text
    except Exception as e:
        return f"Gemini misslyckades: {e}"


# -----------------------------
#     LLaMA ANALYSIS
# -----------------------------
def run_llama_full_log_analysis(error_text: str) -> str:
    prompt = (
        "Du får utdrag ur en Android-loggfil som innehåller felrader och krascher.\n"
        "Beskriv kortfattat vilka problemen är, varför de händer och ge enkla "
        "förslag på lösning. Skriv på svenska.\n\n"
        f"{error_text}"
    )

    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=180,
        )
    except Exception as e:
        return f"LLaMA (Ollama) misslyckades: {e}"

    if not resp.ok:
        return f"Ollama svarade med fel {resp.status_code}: {resp.text}"

    data = resp.json()
    return data.get("response", "Inget svar från LLaMA.")


# ---------------------------------------------------
#                    MAIN ROUTE
# ---------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    result_local = ""
    result_ai = ""
    raw_log_text = ""
    error = ""

    # standard: visa alla nivåer i UI
    selected_levels = ["E", "W", "I", "D", "V"]

    # popup-data
    show_x_popup = False
    x_entries_text = ""

    if request.method == "POST":
        model_choice = request.form.get("model_choice", "llama")
        selected_levels = request.form.getlist("levels") or selected_levels
        uploaded_file = request.files.get("logfile")

        if not uploaded_file:
            error = "Ingen fil valdes."
            return render_template(
                "index.html",
                error=error,
                selected_levels=selected_levels,
                show_x_popup=False,
                x_entries_text="",
            )

        try:
            raw_log_text = uploaded_file.read().decode("utf-8", errors="ignore")

            # Smart crashblock-filtrering
            filtered_text = extract_ranked_crashblocks(raw_log_text)
            lines = filtered_text.splitlines()

            # Hitta felrader
            all_entries, error_summary, has_real_levels = collect_errors(lines)
            total_errors = len(all_entries)

            # Sortera & filtrera
            visible_entries = sort_and_filter_errors(
                all_entries, selected_levels, has_real_levels
            )
            visible_count = len(visible_entries)

            # Popup-logik: visa X-fel endast om inga riktiga nivåer finns
            if not has_real_levels:
                x_only = [e for e in all_entries if e["level"] == "X"]
                if x_only:
                    show_x_popup = True
                    x_entries_text = "\n".join(e["line"] for e in x_only)

            # Lokal analys – alltid utifrån visible_entries
            result_local = (
                f"Totalt antal rader (efter smart filtrering): {len(lines)}\n"
                f"Antal visade felrader: {visible_count}\n\n"
            )

            if error_summary:
                result_local += "--- Vanligaste feltyper ---\n"
                for key, count in sorted(error_summary.items(), key=lambda x: -x[1]):
                    result_local += f"{key}: {count} gånger\n"

            if visible_entries:
                result_local += "\n--- Felrader sorterade ---\n\n"
                for e in visible_entries:
                    result_local += f"[{e['level']}] {e['line']}\n"

            # AI-input = samma felrader som syns lokalt
            if visible_entries:
                ai_input = "\n".join(
                    f"[{e['level']}] {e['line']}" for e in visible_entries
                )
            else:
                ai_input = filtered_text

            MAX_AI_INPUT = 15000
            if len(ai_input) > MAX_AI_INPUT:
                ai_input = ai_input[:MAX_AI_INPUT]

            if model_choice == "llama":
                print("🦙 Kör LLaMA...")
                result_ai = "=== LLaMA (lokal via Ollama) ===\n\n"
                result_ai += run_llama_full_log_analysis(ai_input)
            elif model_choice == "gemini":
                print("✨ Kör Gemini...")
                result_ai = "=== Gemini (moln) ===\n\n"
                result_ai += run_gemini_full_log_analysis(ai_input)

        except Exception as e:
            error = str(e)
            print("❌ Fel under analys:", e)

    return render_template(
        "index.html",
        result_local=result_local,
        result_gemini=result_ai,
        raw_log_text=raw_log_text,
        error=error,
        selected_levels=selected_levels,
        show_x_popup=show_x_popup,
        x_entries_text=x_entries_text,
    )


if __name__ == "__main__":
    print("🚀 Flask server körs på http://127.0.0.1:5000/")
    app.run(debug=True)
