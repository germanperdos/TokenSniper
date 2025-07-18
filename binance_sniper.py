import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton

# 🔐 Данные бота и канала
TOKEN = "8095404561:AAFVTgtiLbWoI_YbrNV_9TlSzI1rqgfFqeY"
CHAT_ID = -1002744594411  # числовой ID канала

# 🔑 Ключ OpenRouter
OPENROUTER_API_KEY = "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"

def generate_summary(title, url):
    prompt = f"""
Ты — крипто-бот. Твоя задача — составить короткую выжимку для Telegram:

🔹 Где — биржа (например, Binance)  
🔹 Что — монета (например, FLOKI)  
🔹 Когда — дата и время начала торгов (в МСК)  
🔹 Краткое описание монеты (если есть)  

Формат ответа:

🔔 Binance добавляет монету ABC  
🕒 22 июля, 15:00 МСК  
🪙 ABC — это монета для Web3 и DeFi

Заголовок: {title}  
Ссылка на новость: {url}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://t.me/TokenSniperNews",
        "Content-Type": "application/json"
    }

    data = {
        "model": "meta-llama/llama-3-70b-instruct",
        "messages": [
            {"role": "system", "content": "Ты помощник крипто-бота"},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        print("❌ Ошибка OpenRouter:", response.text)
        return f"🔔 {title}\n⚠️ GPT недоступен"

def send_to_telegram(title, url, summary):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📰 Читать новость полностью", url=url)]
    ])

    # Определяем стиль действия
    lower_title = title.lower()
    if "лист" in lower_title or "will list" in lower_title or "add" in lower_title:
        action = "<b>🟢 добавляет</b>"
    elif "делист" in lower_title or "remove" in lower_title or "delist" in lower_title:
        action = "<b>❌ удаляет</b>"
    else:
        action = "<b>ℹ️ обновляет</b>"

    # Определяем биржу (например: Binance)
    exchange = title.split()[0].strip()

    message = f"""
🔔 <b>{exchange}</b> {action} монету  
{summary}

🔗 Подпишись: @TokenSniperNews
""".strip()

    Bot(token=TOKEN).send_message(
        chat_id=CHAT_ID,
        text=message,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

def fetch_binance_announcements(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    time.sleep(3)

    elements = driver.find_elements("xpath", "//a[contains(@href, '/en/support/announcement/')]")
    announcements = []

    for el in elements:
        href = el.get_attribute("href")
        title = el.text.strip()
        if title and ("Will List" in title or "Delist" in title or "Delisting" in title):
            announcements.append((title, href))

    driver.quit()
    return announcements

if __name__ == "__main__":
    urls = {
        "Листинги": "https://www.binance.com/en/support/announcement/c-48",
        "Делистинги": "https://www.binance.com/en/support/announcement/c-59"
    }

    for name, url in urls.items():
        print(f"\n🔍 Чекаем: {name}")
        data = fetch_binance_announcements(url)
        for title, link in data:
            print(f"{title} → {link}")
            try:
                summary = generate_summary(title, link)
            except Exception as e:
                print("❌ GPT-ошибка:", e)
                summary = f"🔔 {title}\n⚠️ GPT недоступен"
            
            send_to_telegram(title, link, summary)
