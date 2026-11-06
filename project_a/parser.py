import os
import json
import warnings

# Suppress deprecation warnings for cleaner console output
warnings.filterwarnings("ignore")

from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"), transport="rest")

SYSTEM_PROMPT = """You extract tax data from user descriptions. Output a valid JSON. 
Allowed keys: 'gross_salary', 'age' (default 30), 'basic', 'da', 'hra_received', 'rent_paid', 'metro' (bool), 'sec_80c', 'sec_80ccd_1b', 'sec_80d_self', 'sec_80d_parents', 'parents_senior' (bool), 'home_loan_interest'. 
RULE 1: Convert all monthly amounts to annual. 
RULE 2: If the user mentions an expense (like rent, home loan, or insurance) but DOES NOT provide the amount, or if the math is impossible (basic > gross), DO NOT GUESS. Instead, return a JSON with a single key: {'clarifying_question': '<your specific question>'}.
RULE 3: If sufficient data is provided, return the extracted numerical/boolean keys."""


def parse_user_query(query: str) -> dict:
    """
    Parses a plain-language tax query using Gemini and returns extracted structured data
    or a clarifying question if essential details are missing/invalid.
    """
    # Candidate models: requested models with reliable fallbacks
    models_to_try = [
        os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        "gemini-1.5-flash",
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-flash-lite-latest",
    ]

    last_error = None
    for model_name in models_to_try:
        if not model_name:
            continue
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=SYSTEM_PROMPT,
                generation_config={"response_mime_type": "application/json"},
            )
            response = model.generate_content(query)
            text_response = response.text.strip()
            return json.loads(text_response)
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise last_error
    return {}


if __name__ == "__main__":
    print("--- Test 1: Complete Hinglish Case ---")
    hinglish_query = "Mera gross 12L hai aur rent 20k per month Bangalore mein"
    print(f"Query: {hinglish_query}")
    hinglish_result = parse_user_query(hinglish_query)
    print("Result:")
    print(json.dumps(hinglish_result, indent=2))

    print("\n--- Test 2: Incomplete Case ---")
    incomplete_query = "I earn 10 LPA and have a home loan"
    print(f"Query: {incomplete_query}")
    incomplete_result = parse_user_query(incomplete_query)
    print("Result:")
    print(json.dumps(incomplete_result, indent=2))
