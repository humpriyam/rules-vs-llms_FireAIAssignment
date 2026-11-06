import warnings
warnings.filterwarnings("ignore")
import os
from dotenv import load_dotenv
import google.generativeai as genai

print("Loading .env and connecting to Gemini API...")
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"), transport="rest")
model = genai.GenerativeModel("gemini-3.8-flash")

print("Sending prompt...")
response = model.generate_content("Reply with the single word: ready")
print(response.text.strip())
