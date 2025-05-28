# botify.py — Shopify WhatsApp Chatbot with MCP Refactor, Variants, Multilingual Replies, PostgreSQL + LLaMA

from flask import Flask, request
import requests
import os
from dotenv import load_dotenv
from flask_cors import CORS
from models import Session, Message
from datetime import datetime
from sqlalchemy import text
from langdetect import detect
from prompt_protocol import get_protocol
from context_protocol import assemble_context
from llama_client import call_llama_mcp

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOP = "gabsistore.myshopify.com"
META_TOKEN = os.getenv("META_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "🟢 Botify WhatsApp Chatbot Running"

@app.route('/health')
def health():
    try:
        session = Session()
        session.execute(text("SELECT 1"))
        session.close()
        return "✅ Database connected"
    except Exception as e:
        return f"❌ DB error: {e}", 500

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Token de vérification invalide", 403

    if request.method == 'POST':
        data = request.json
        entry = data['entry'][0]['changes'][0]['value']
        if 'messages' in entry:
            message = entry['messages'][0]
            phone_number = message['from']
            text = message['text']['body']

            reply = handle_message(text, phone_number)
            send_whatsapp_message(phone_number, reply)

        return 'OK', 200

def send_whatsapp_message(phone, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "text": {"body": text}
    }
    res = requests.post(url, headers=headers, json=payload)
    print("📤 WhatsApp API response:", res.status_code, res.text)

def save_to_supabase(user_id, role, message):
    session = Session()
    msg = Message(user_id=user_id, role=role, message=message)
    session.add(msg)
    session.commit()
    session.close()

def detect_language(text):
    try:
        return detect(text)
    except:
        return 'en'

def classify_intent_and_entities(user_message):
    prompt = f"""
Given this customer message, identify the intent and extract any relevant entities.

Format:
intent: one of [product_info, order_status, delivery_policy, return_policy, generic]
product_name: <if applicable>
order_id: <if applicable>
email: <if applicable>
info: one of [price, variants, stock, stock_by_variant, color, size]

Message: "{user_message}"
"""
    messages = [
        {"role": "system", "content": "You extract intent and relevant data from customer messages."},
        {"role": "user", "content": prompt}
    ]
    content = call_llama_mcp("Extract structured entities from customer messages.", [], user_message)
    result = {"intent": "generic", "product_name": None, "order_id": None, "email": None, "info": None}
    for line in content.splitlines():
        if line.startswith("intent:"): result["intent"] = line.split(":", 1)[1].strip()
        if line.startswith("product_name:"): result["product_name"] = line.split(":", 1)[1].strip()
        if line.startswith("order_id:"): result["order_id"] = line.split(":", 1)[1].strip()
        if line.startswith("email:"): result["email"] = line.split(":", 1)[1].strip()
        if line.startswith("info:"): result["info"] = line.split(":", 1)[1].strip()
    return result

def get_product_details(product_name):
    url = f"https://{SHOP}/admin/api/2024-04/products.json?title={product_name}"
    res = requests.get(url, headers={"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}, verify=False)
    data = res.json()
    return data['products'][0] if data['products'] else None

def extract_requested_info(product, info_type):
    variants = product.get('variants', [])
    title = product.get('title', 'N/A')
    description = product.get('body_html', 'N/A')
    option_names = [o['name'] for o in product.get('options', []) if o['name'].lower() != 'title']

    if not variants:
        return "Aucune information de stock disponible."

    if len(variants) == 1 and not option_names:
        v = variants[0]
        price = v.get('price', 'N/A')
        stock = v.get('inventory_quantity', 0)
        return f"""📦 *Produit:* {title}
🧾 *Description:* {description.strip()}
💰 *Prix:* ${price}
📦 *Stock:* {stock} en stock"""

    option_info = "\n".join([f"- Option {i+1}: {name}" for i, name in enumerate(option_names)])
    variant_details = []
    for v in variants:
        option_values = [v.get(f"option{i+1}", '') for i in range(len(option_names))]
        details = [f"{option_names[i]}: {option_values[i]}" for i in range(len(option_values)) if option_values[i]]
        price = v.get('price', 'N/A')
        stock = v.get('inventory_quantity', 0)
        line = f"- {' | '.join(details)} | Price: ${price} | Stock: {stock}"
        variant_details.append(line)

    info_block = f"""📦 *Produit:* {title}
🧾 *Description:* {description.strip()}
🧩 *Variant Attributes:*
{option_info}
🔢 *Variant Details:*
{chr(10).join(variant_details)}"""
    return info_block.strip()

def get_order_info(order_id=None, email=None):
    if order_id:
        url = f"https://{SHOP}/admin/api/2024-04/orders.json?name={order_id}"
    elif email:
        url = f"https://{SHOP}/admin/api/2024-04/orders.json?email={email}"
    else:
        return None
    res = requests.get(url, headers={"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}, verify=False)
    orders = res.json().get('orders', [])
    return orders[0] if orders else None

def generate_mcp_response(user_id, product_info=None, user_input=None):
    lang = detect_language(user_input or "")
    instruction = get_protocol(lang)
    context_messages = assemble_context(user_id, product_info)
    return call_llama_mcp(instruction, context_messages, user_input)

def handle_message(user_text, phone_number):
    save_to_supabase(phone_number, "user", user_text)
    analysis = classify_intent_and_entities(user_text)
    intent = analysis["intent"]
    reply_text = "Je n'ai pas bien compris votre demande."

    if intent == "product_info" and analysis["product_name"]:
        product = get_product_details(analysis["product_name"])
        if product:
            info = extract_requested_info(product, analysis.get("info", "price"))
            reply_text = generate_mcp_response(phone_number, info, user_text)
        else:
            reply_text = "Je suis désolé, je n’ai pas trouvé ce produit dans notre boutique."

    elif intent == "order_status" and (analysis["order_id"] or analysis["email"]):
        order = get_order_info(order_id=analysis["order_id"], email=analysis["email"])
        if order:
            reply_text = generate_mcp_response(phone_number, f"Order status: {order['fulfillment_status']}", user_text)
        else:
            reply_text = "Je n’ai pas trouvé de commande associée."

    elif intent == "delivery_policy":
        reply_text = "La livraison prend entre 3 et 5 jours ouvrés."

    elif intent == "return_policy":
        reply_text = "Les retours sont acceptés sous 30 jours. Les articles doivent être non utilisés et dans leur emballage d'origine."

    else:
        reply_text = generate_mcp_response(phone_number, None, user_text)

    save_to_supabase(phone_number, "assistant", reply_text)
    return reply_text

if __name__ == '__main__':
    app.run(debug=True)
