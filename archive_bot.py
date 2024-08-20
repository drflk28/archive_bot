import telebot
import requests
from transformers import pipeline
from html import unescape

# Инициализация бота с токеном
TELEGRAM_TOKEN = "7543703235:AAE5JNvmCqUgUgQNjIhjB7vfLlNtmPrOcYU"
HUGGINGFACE_TOKEN = "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"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# URL для API Archive.org
ARCHIVE_API_URL = "https://archive.org/advancedsearch.php"

def search_archive(query):
    params = {
        "q": f'subject:"{query}"',
        "fl[]": "identifier,title,description,added",
        "rows": 3,  # Количество возвращаемых результатов
        "page": 1,
        "output": "json"
    }

    try:
        response = requests.get(ARCHIVE_API_URL, params=params)
        print(f"Request URL: {response.url}")
        print(f"Response Status Code: {response.status_code}")

        if response.status_code == 200:
            results = response.json()
            docs = results.get('response', {}).get('docs', [])
            if docs:
                # Логируем данные о найденных статьях
                for doc in docs:
                    print(f"Fetched document: {doc}")
                return docs
        else:
            print(f"Error fetching data: {response.status_code} - {response.text}")

    except requests.RequestException as e:
        print(f"RequestException occurred: {e}")

    return []

def safe_summary(description):
    if len(description) > 2000:
        description = description[:2000] + "..."
    return description

def get_summary(description):
    if not description.strip() or len(description) < 10:
        return "No detailed description available."

    summarizer = pipeline("summarization", model="facebook/bart-large-cnn", token=HUGGINGFACE_TOKEN)
    summary = summarizer(description, max_length=150, min_length=30, do_sample=False)

    if summary and len(summary) > 0:
        return summary[0]['summary_text']

    return "Summary generation failed or the description is too short."

@bot.message_handler(content_types=['text'])
def get_response(message):
    print(f"Received message: {message.text}")

    docs = search_archive(message.text)

    if docs:
        # Выбираем первый документ для обработки
        doc = docs[0]
        identifier = doc.get("identifier")
        title = doc.get("title", "No Title")
        description = doc.get("description", "No Description")
        safe_description = safe_summary(description)

        # Декодируем HTML сущности
        decoded_description = unescape(safe_description)

        # Логируем описание и его длину
        print(f"Description: {decoded_description}")
        print(f"Description length: {len(decoded_description)}")

        summary = get_summary(decoded_description)

        response = f"*Title*: {title}\n\n*Summary*: {summary}\n\n*Link*: https://archive.org/details/{identifier}"
    else:
        response = "No articles found for your query."

    print(f"Sending response: {response}")

    try:
        bot.send_message(message.chat.id, response, parse_mode='Markdown')
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Failed to send message: {e}")

# Запуск бота
bot.polling(none_stop=True, interval=0)
