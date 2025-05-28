# 🤖 Botify — Shopify WhatsApp Chatbot (MCP + LLaMA + Supabase + Flask)

Botify is an AI-powered WhatsApp chatbot for Shopify stores. Built with **Flask**, **Supabase PostgreSQL**, and **Groq's LLaMA 3**, it handles customer inquiries about product details, stock, variants, orders, delivery, and more — all with context-awareness and multilingual support.

---

## 🌐 Live Stack Architecture

```plaintext
┌────────────┐        ┌─────────────┐         ┌────────────────┐
│ WhatsApp   │──────▶│ Flask API   │◀────────│ Shopify Admin  │
│ User Chat  │       │ (botify.py) │         │ (Product/Order)│
└────────────┘       │             │         └────────────────┘
     ▲               │             │                ▲
     │               │             │                │
     │               │             ▼                │
     │           ┌─────────────┐   ┌────────────┐   │
     └──────────▶│ llama_client│◀──│ Groq LLaMA │◀──┘
                 └─────────────┘   └────────────┘
                        ▲
                        │
                ┌───────────────┐
                │ PostgreSQL DB │◀─ Supabase (Conversation Memory)
                └───────────────┘
```

---

## ⚙️ Features

- 🔄 **Multilingual**: French and English support using `langdetect`
- 🧠 **Contextual Understanding**: Saves message history with PostgreSQL (Supabase) for full conversations
- 🛍️ **Product Intelligence**: Extracts variants, price, and stock in real-time from Shopify
- 📦 **Order Tracking**: Fetches order status via order ID or customer email
- 🧩 **MCP Architecture**: Uses Model Context Protocol for structured prompting
- 🔐 **Environment-Driven**: Clean secrets management using `.env` file

---

## 🏗️ Installation

```bash
git clone https://github.com/your-username/botify-shopify-chatbot.git
cd botify-shopify-chatbot
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

## 📁 Project Structure

```
botify-shopify-chatbot/
│
├── botify.py               # Main Flask app
├── models.py               # SQLAlchemy ORM models
├── context_protocol.py     # MCP context builder
├── prompt_protocol.py      # MCP language-aware instructions
├── llama_client.py         # LLaMA client (via Groq)
├── requirements.txt
└── .env                    # Environment variables (GROQ_KEY, etc.)
```

---

## 🔐 Environment Variables (.env)

```env
SHOPIFY_ACCESS_TOKEN=your_token
SHOP=gabsistore.myshopify.com
GROQ_API_KEY=your_groq_api_key
PHONE_NUMBER_ID=your_whatsapp_phone_id
META_TOKEN=your_meta_whatsapp_token
VERIFY_TOKEN=webhook_verify_token
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

---

## 🧪 Testing with Postman

- `POST /webhook`: Simulate WhatsApp messages via JSON payload.
- `GET /health`: Check DB connectivity.
- `GET /`: Root check.

---

## 🏁 Deployment

You can deploy this project using:
- 🌍 **Render.com** for Flask API
- 🐘 **Supabase** for PostgreSQL (hosted memory)
- 🟢 **WhatsApp Meta Cloud API** for integration

---

## 🧠 Powered by Model Context Protocol (MCP)

This project leverages **MCP** to ensure:
- Modular context injection (user history + product info)
- Language-aware system instructions
- Prompt integrity and reasoning traceability

---

## 📝 License

MIT © 2025 — Aymen Gabsi
