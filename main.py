import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Load environment variables (.env)
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("❌ Error: GEMINI_API_KEY not found in the .env file!")

# 2. Initialize Gemini client
client = genai.Client(api_key=API_KEY)

# 3. Load knowledge base from JSON
def load_knowledge_base(filepath="knowledge_base.json"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error reading knowledge base {filepath}: {e}")
        return None

kb = load_knowledge_base()

# 4. Formulate strict system prompt (Zero-Hallucination Guardrail)
SYSTEM_INSTRUCTION = f"""
You are the official Customer Support AI Agent for TechStore Global Enterprise.
Your primary objective is to provide 100% accurate information based ONLY on the provided Knowledge Base below.

STRICT ZERO-HALLUCINATION GUARDRAILS:
1. You MUST answer user queries using ONLY the rules and details present in the KNOWLEDGE BASE.
2. If the user's question cannot be answered using the provided context, you MUST respond exactly with:
   "I'm sorry, but I don't have information about that in my official knowledge base. Please contact our support team at support@techstore-global.com or call +1-800-555-0199 for further assistance."
3. Never invent facts, procedures, prices, fees, or timelines that are not explicitly stated in the context.
4. Always cite the specific policy ID (e.g., [POL-008]) when providing information from a policy.

KNOWLEDGE BASE CONTEXT:
{json.dumps(kb, indent=2, ensure_ascii=False)}
"""

# 5. Question processing function with retries and timeout handling
def ask_agent(user_query: str, retries: int = 3):
    print(f"\n❓ User Question: {user_query}")
    print("⏳ Processing query with Gemini model...")
    
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=user_query,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.0
                )
            )
            print("\n🤖 Agent Response:")
            print(response.text)
            print("-" * 60)
            return
        except Exception as e:
            err_msg = str(e)
            if "503" in err_msg or "UNAVAILABLE" in err_msg or "429" in err_msg:
                wait_time = (attempt + 1) * 2  # 2 seconds, then 4 seconds, etc.
                if attempt < retries - 1:
                    print(f"⚠️ Server overloaded. Retrying {attempt + 1}/{retries} in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"\n❌ Google servers are currently under high load (503). Press Enter or try again in a minute.")
            else:
                print(f"❌ Error querying Gemini API: {e}")
                break

# 6. Run console interactive mode
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TechStore Zero-Hallucination AI Support Agent Started!")
    print("   Rules loaded into context:", kb.get("total_rules", 0) if kb else 0)
    print("   Type 'exit' or 'quit' to exit.")
    print("=" * 60)

    # Automatic test question on startup
    test_query = "What is the return window for items and do I have to pay for return shipping?"
    ask_agent(test_query)

    # Interactive loop
    while True:
        try:
            user_input = input("\nEnter question for agent > ").strip()
            if user_input.lower() in ["exit", "quit", "выход"]:
                print("Shutting down agent. Goodbye!")
                break
            if user_input:
                ask_agent(user_input)
        except KeyboardInterrupt:
            print("\nShutting down.")
            break
