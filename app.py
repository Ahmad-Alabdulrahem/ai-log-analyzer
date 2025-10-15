import os
import re
import spacy
from flask import Flask, render_template, request
from dotenv import load_dotenv
import google.generativeai as genai

# --- Load environment variables ---
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB upload limit

# --- spaCy Setup ---
try:
    nlp = spacy.load("en_core_web_sm")
    nlp.max_length = 2_000_000
    print("✅ spaCy loaded successfully.")
except Exception as e:
    print("❌ spaCy failed to load:", e)

# --- Gemini Setup ---
API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "models/gemini-2.5-flash"

if API_KEY:
    genai.configure(api_key=API_KEY)
    print(f"✅ Gemini API key loaded (starts with): {API_KEY[:8]}...")
else:
    print("⚠️ No Gemini API key found in .env!")

@app.route("/", methods=["GET", "POST"])
def index():
    result_local = ""
    result_gemini = ""
    error = ""

    if request.method == "POST":
        uploaded_file = request.files.get("logfile")
        if not uploaded_file or not uploaded_file.filename:
            error = "Ingen fil valdes eller kunde inte läsas."
            return render_template("index.html", error=error)

        try:
            log_text = uploaded_file.read().decode("utf-8", errors="ignore")
            lines = log_text.splitlines()

            # --- Local regex analysis ---
            error_pattern = re.compile(
                r"(Exception|Error|Fail|Crash|ANR|NullPointerException|OutOfMemoryError|RuntimeException)",
                re.IGNORECASE,
            )

            error_lines = []
            for i, line in enumerate(lines):
                if error_pattern.search(line):
                    context = "\n".join(lines[max(0, i - 2):min(len(lines), i + 3)])
                    error_lines.append(context)

            error_types = re.findall(error_pattern, log_text)
            error_summary = {}
            for e in error_types:
                key = e.strip().title()
                error_summary[key] = error_summary.get(key, 0) + 1

            result_local = (
                f"📄 Filen analyserades framgångsrikt!\n\n"
                f"• Totalt antal rader: {len(lines)}\n"
                f"• Totalt antal tecken: {len(log_text)}\n"
                f"• Antal upptäckta fel: {len(error_types)}\n\n"
            )

            if error_summary:
                result_local += "--- Vanligaste felen ---\n"
                for key, count in sorted(error_summary.items(), key=lambda x: -x[1])[:10]:
                    result_local += f"• {key}: {count} gånger\n"

            if error_lines:
                result_local += (
                    "\n--- Exempel på felrader (med kontext) ---\n"
                    + "\n\n".join(error_lines[:5])
                )
            else:
                result_local += "\n✅ Inga uppenbara fel hittades i loggen."

            # --- Gemini AI Analysis ---
            if API_KEY:
                try:
                    print("🚀 Running Gemini analysis...")
                    model = genai.GenerativeModel(GEMINI_MODEL)
                    prompt = (
                        "Analysera följande Android-logg och skriv en kort, tydlig sammanfattning på svenska. "
                        "Beskriv de mest sannolika felen, deras orsaker och möjliga lösningar:\n\n"
                        + log_text[:8000]
                    )
                    response = model.generate_content(prompt)
                    if hasattr(response, "text"):
                        result_gemini = response.text
                        print("✅ Gemini analysis complete!")
                    else:
                        result_gemini = "⚠️ Gemini gav inget svar."
                        print("⚠️ Gemini returned no text.")
                except Exception as e:
                    print("❌ Gemini error:", e)
                    result_gemini = f"Gemini-analysen misslyckades: {str(e)}"
            else:
                print("⚠️ Ingen API-nyckel — hoppar över Gemini.")
                result_gemini = "Ingen API-nyckel hittades. Gemini-analysen kunde inte köras."

        except Exception as e:
            error = f"Ett fel uppstod under analysen: {str(e)}"
            print("❌ General analysis error:", e)

    return render_template("index.html", result_local=result_local, result_gemini=result_gemini, error=error)


if __name__ == "__main__":
    print("🚀 Flask server started on http://127.0.0.1:5000/")
    app.run(debug=True)

