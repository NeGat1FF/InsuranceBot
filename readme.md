# Car Insurance Telegram Bot

This is a Telegram bot designed to assist users in purchasing car insurance. It guides users through uploading necessary documents, confirms extracted data, provides a fixed price, and issues a dummy insurance policy using OpenAI.

## Features

- 📄 Document upload and processing (passport and vehicle registration)
- 🧠 AI-powered conversation handling using OpenAI
- 🧾 Dummy insurance policy generation
- ✅ User-friendly step-by-step interaction
- 🛡️ Fixed price confirmation and policy issuance

---

## Tech Stack

- **Python 3.10+**
- **python-telegram-bot**
- **OpenAI API (async)**
- **Mindee API** for document OCR

---

## Setup Instructions

1. **Clone the repository:**

```bash
git clone https://github.com/your-username/car-insurance-bot.git
cd car-insurance-bot
````

2. **Copy a `.env.example` file, rename it to `.env` and provide required environment variables:**

```
BOT_TOKEN = your_telegram_bot_token
MINDEE_API_KEY = your_mindee_api_key 
MINDEE_PASS_MODEL = your_mindee_passport_model_id
MINDEE_VEHICLE_MODEL = your_mindee_vehicle_model_id
OPENAI_API_KEY = your_openai_api_key
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Run the bot:**

```bash
python main.py
```

---

## Conversation Flow

1. `/start` — Bot introduces itself and asks for passport photo
2. User uploads passport → Bot extracts data → asks for confirmation
3. User confirms → Bot asks for vehicle registration photo
4. User uploads it → Bot extracts → asks for confirmation
5. If confirmed → Bot asks to confirm fixed price: 100 USD
6. If agreed → Bot generates a dummy policy and sends it

---

## Notes

* The bot uses OpenAI to generate all conversation responses and confirmations.


