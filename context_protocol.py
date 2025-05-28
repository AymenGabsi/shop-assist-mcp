# context_protocol.py
from models import Session, Message


def get_conversation_history(user_id, limit=10):
    session = Session()
    msgs = (
        session.query(Message)
        .filter_by(user_id=user_id)
        .order_by(Message.timestamp.desc())
        .limit(limit)
        .all()
    )
    session.close()
    return [{"role": m.role, "content": m.message} for m in reversed(msgs)]


def assemble_context(user_id, product_data=None):
    context_messages = []
    if product_data:
        context_messages.append(
            {
                "role": "system",
                "content": f"""PRODUCT DATA:\n{product_data.strip()}\n\nInstruction: Use only the provided product data to answer. Extract specific variant attributes like color, size, material from the variant list if asked. Do not claim missing data if it is present.""",
            }
        )

    context_messages += get_conversation_history(user_id)
    return context_messages
