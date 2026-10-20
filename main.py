import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Загружаем переменные окружения (.env)
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("❌ Ошибка: API ключ GEMINI_API_KEY не найден в файле .env!")

# 2. Инициализируем клиент Gemini
client = genai.Client(api_key=API_KEY)

# 3. Загружаем базу знаний из JSON
def load_knowledge_base(filepath="knowledge_base.json"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Ошибка при чтении базы знаний {filepath}: {e}")
        return None

kb = load_knowledge_base()

# 4. Формируем строгий системный промпт (Zero-Hallucination Guardrail)
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

# 5. Функция обработки вопросов с автоповтором и обработкой подвисаний
def ask_agent(user_query: str, retries: int = 3):
    print(f"\n❓ Вопрос пользователя: {user_query}")
    print("⏳ Обработка запроса моделью Gemini...")
    
    for attempt in range(retries):
        try:
            # Выполняем запрос к API
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=user_query,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.0
                )
            )
            print("\n🤖 Ответ агента:")
            print(response.text)
            print("-" * 60)
            return
        except Exception as e:
            err_msg = str(e)
            if "503" in err_msg or "UNAVAILABLE" in err_msg or "429" in err_msg:
                wait_time = (attempt + 1) * 2  # 2 секунды, затем 4 секунды и т.д.
                if attempt < retries - 1:
                    print(f"⚠️ Сервер перегружен. Автоповтор {attempt + 1}/{retries} через {wait_time} сек...")
                    time.sleep(wait_time)
                else:
                    print(f"\n❌ Сервера Google сейчас под высокой нагрузкой (503). Нажмите Enter или попробуйте через минуту.")
            else:
                print(f"❌ Ошибка при запросе к Gemini API: {e}")
                break

# 6. Запуск диалогового режима в консоли
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TechStore Zero-Hallucination AI Support Agent Запущен!")
    print("   Загружено правил в контекст:", kb.get("total_rules", 0) if kb else 0)
    print("   Введите 'exit' или 'quit' для выхода.")
    print("=" * 60)

    # Автоматический тестовый вопрос при запуске
    test_query = "What is the return window for items and do I have to pay for return shipping?"
    ask_agent(test_query)

    # Интерактивный цикл
    while True:
        try:
            user_input = input("\nВведите вопрос агенту > ").strip()
            if user_input.lower() in ["exit", "quit", "выход"]:
                print("Завершение работы агента. До связи!")
                break
            if user_input:
                ask_agent(user_input)
        except KeyboardInterrupt:
            print("\nЗавершение работы.")
            break