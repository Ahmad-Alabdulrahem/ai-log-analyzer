import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

def analyze_with_gemini(log_text: str) -> str:
    """
    Analyze Android log files using Google Gemini 2.5 models.
    Uses Gemini 2.5 Flash by default, with fallback to Pro.
    """
    if not API_KEY:
        raise RuntimeError("No GEMINI_API_KEY found in .env file.")

    genai.configure(api_key=API_KEY)

    models_to_try = [
        "models/gemini-2.5-flash",  # Fast and reliable
        "models/gemini-2.5-pro"     # More detailed fallback
    ]

    last_error = None
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            prompt = f"""
            You are an AI assistant helping Android developers analyze crash logs.
            Identify common error types, summarize the cause in 3–5 bullet points,
            and give a clear, developer-friendly explanation.

            Log content:
            {log_text}
            """
            response = model.generate_content(prompt)
            return response.text.strip() if hasattr(response, "text") else str(response)
        except Exception as e:
            last_error = e

    return f"Gemini analysis failed with all tested models. Last error: {last_error}"
