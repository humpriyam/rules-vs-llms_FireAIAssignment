import warnings
warnings.filterwarnings("ignore")
import os, time
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"), transport="rest")

candidates = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemma-4-31b-it",
]

for name in candidates:
    try:
        m = genai.GenerativeModel(name)
        t = time.time()
        r = m.generate_content("Reply with the single word: ready")
        print(f"OK    {name:30s} {time.time()-t:.1f}s -> {r.text.strip()}")
    except Exception as e:
        print(f"FAIL  {name:30s} {str(e)[:100]}")
    time.sleep(2)