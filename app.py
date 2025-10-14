from flask import Flask, render_template, request
from utils.log_reader import load_logfile
from regex_analysis import analyze_with_regex_and_spacy
from analyze import analyze_with_gemini

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result_local = None
    result_gemini = None
    error = None
    if request.method == "POST":
        file = request.files.get("logfile")
        if not file:
            error = "No file selected."
        else:
            text = load_logfile(file)
            result_local = analyze_with_regex_and_spacy(text)
            try:
                result_gemini = analyze_with_gemini(text)
            except Exception as e:
                result_gemini = "Gemini analysis unavailable."
                error = str(e)
    return render_template("index.html", result_local=result_local, result_gemini=result_gemini, error=error)

if __name__ == "__main__":
    app.run(debug=True)
