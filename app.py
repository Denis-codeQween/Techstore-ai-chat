import os
import json
import base64
import time
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

# 1. Загрузка конфигурации
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ Error: GEMINI_API_KEY not found in .env file!")
    st.stop()

# 2. Инициализация клиента Gemini с увеличенным таймаутом
client = genai.Client(
    api_key=API_KEY,
    http_options={'timeout': 120000}
)

# 3. Загрузка базы знаний
@st.cache_data
def load_knowledge_base(filepath="knowledge_base.json"):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

kb = load_knowledge_base()

# 4. Системный промпт (Zero-Hallucination Guardrails)
SYSTEM_INSTRUCTION = f"""
You are the official Customer Support AI Agent for TechStore.
Your primary objective is to provide 100% accurate information based ONLY on the provided Knowledge Base below.

STRICT ZERO-HALLUCINATION GUARDRAILS:
1. You MUST answer user queries using ONLY the rules and details present in the KNOWLEDGE BASE.
2. If the user's question cannot be answered using the provided context, respond politely with standard support contact info.
3. Always cite the specific policy ID (e.g., [POL-008]) when providing information.

KNOWLEDGE BASE CONTEXT:
{json.dumps(kb, ensure_ascii=False)}
"""

# Настройка страницы
st.set_page_config(
    page_title="TechStore Chat - AI Assistant",
    page_icon="🟠",
    layout="centered"
)

# --- ЗАГРУЗКА ИКОНКИ В BASE64 ДЛЯ ЧИСТОГО HTML ---
def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded_string}"
    except Exception:
        return ""

icon_b64 = get_image_base64("image_7.png")

try:
    assistant_icon = Image.open("image_7.png")
except Exception:
    assistant_icon = "🤖"

# --- КАСТОМНЫЙ CSS СТИЛЬ ---
st.markdown("""
<style>
    /* Скрытие дефолтных элементов Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ограничение ширины основного контейнера */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 500px !important;
        margin: 0 auto !important;
    }
    
    /* Выравнивание ширины поля ввода точно под шапку */
    [data-testid="stChatInput"] {
        max-width: 500px !important;
        margin: 0 auto !important;
        left: 0 !important;
        right: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Инициализация истории чата
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- ЕДИНЫЙ ВИДЖЕТ ШАПКИ И ПРИВЕТСТВИЯ ---
if len(st.session_state.messages) == 0:
    icon_html = f'<img src="{icon_b64}" style="width: 65px; height: 65px; border-radius: 12px; object-fit: cover; flex-shrink: 0;">' if icon_b64 else '<div style="font-size: 40px;">🤖</div>'
    
    widget_html = f"""
    <div style="max-width: 500px; margin: 0 auto 20px auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <!-- Шапка: Премиум SaaS Стиль с живым индикатором -->
        <div style="background: linear-gradient(135deg, #181824 0%, #222232 100%); color: white; padding: 22px 16px; border-radius: 16px 16px 0 0; text-align: center; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2); border-bottom: 2px solid #FF6B00;">
            <div style="font-weight: 700; font-size: 20px; letter-spacing: 0.4px; display: flex; align-items: center; justify-content: center; gap: 8px;">
                💬 TechStore AI Chat
            </div>
            <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(255, 107, 0, 0.15); color: #FF9F43; font-size: 10px; font-weight: 700; margin-top: 10px; padding: 5px 12px; border-radius: 20px; letter-spacing: 1.2px; text-transform: uppercase; border: 1px solid rgba(255, 107, 0, 0.3);">
                <span style="width: 6px; height: 6px; background-color: #2ecc71; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px #2ecc71;"></span>
                ZERO-HALLUCINATION ACTIVE
            </div>
        </div>
        <!-- Карточка приветствия с пиксельной иконкой слева -->
        <div style="background: #F8F9FA; border-radius: 0 0 16px 16px; padding: 20px; border: 1px solid #E9ECEF; border-top: none; display: flex; align-items: center; gap: 16px;">
            {icon_html}
            <div>
                <div style="font-weight: 600; font-size: 15px; color: #212529; margin-bottom: 4px;">
                    Hello! 👋
                </div>
                <div style="font-size: 13px; color: #6C757D; line-height: 1.4;">
                    I am the TechStore virtual assistant. I can answer questions about orders, store policies, and returns. How can I help you today?
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(widget_html, unsafe_allow_html=True)
else:
    # Компактная шапка при активном чате
    header_html = """
    <div style="max-width: 500px; margin: 0 auto 15px auto; font-family: sans-serif;">
        <div style="background: linear-gradient(135deg, #181824 0%, #222232 100%); color: white; padding: 12px; border-radius: 12px; text-align: center; font-weight: 700; font-size: 16px; letter-spacing: 0.5px; border-bottom: 2px solid #FF6B00;">
            💬 TechStore AI Chat
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

# Вывод истории сообщений
for message in st.session_state.messages:
    avatar_to_use = assistant_icon if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar_to_use):
        st.markdown(message["content"])

# Функция запроса с автоповтором (модель gemini-3.8-flash)
def ask_agent_with_retries(query, retries=3):
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=query,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.0
                )
            )
            return response.text
        except Exception as e:
            err_msg = str(e)
            if "503" in err_msg or "429" in err_msg or "504" in err_msg or "timeout" in err_msg.lower() or "deadline" in err_msg.lower():
                if attempt < retries - 1:
                    time.sleep((attempt + 1) * 2)
                    continue
            return f"❌ API Error: {e}"
    return "⚠️ Google servers are busy or the request timed out. Please try again in a few seconds."

# Обработка ввода нового сообщения
if user_prompt := st.chat_input("Type your question about store policies..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant", avatar=assistant_icon):
        with st.spinner("Analyzing knowledge base..."):
            agent_reply = ask_agent_with_retries(user_prompt)
            st.markdown(agent_reply)
            
    st.session_state.messages.append({"role": "assistant", "content": agent_reply})