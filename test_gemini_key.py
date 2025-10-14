import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env file (must be in same folder as this script)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ No API key found in .env file.")
else:
    print("✅ API key found. Testing Gemini connection...")

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")

        response = model.generate_content("Hello! Just testing the connection.")
        print("\n✅ Gemini connection successful!")
        print("Response preview:\n")
        print(response.text[:300])  # print only first part of response
    except Exception as e:
        print("\n❌ Gemini test failed.")
        print("Error message:\n", e)
