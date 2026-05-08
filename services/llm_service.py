import os
from dotenv import load_dotenv

load_dotenv()

try:
    from langchain_groq import ChatGroq
except Exception:
    ChatGroq = None

class LLMService:
    def __init__(self):
        self.llm = None
        if ChatGroq is not None and os.getenv("GROQ_API_KEY"):
            self.llm = ChatGroq(
                api_key=os.getenv("GROQ_API_KEY"),
                model_name=os.getenv("GROQ_MODEL", "llama3-8b-8192"),
                temperature=0.7
            )
        self.conversation_history = []

    def invoke(self, prompt: str, fallback: str = "") -> str:
        if self.llm is None:
            return fallback or "I can answer from the available store data, but the live LLM service is not configured."
        try:
            return self.llm.invoke(prompt).content
        except Exception as exc:
            print(f"[LLMService] Groq unavailable, using local data fallback: {exc}")
            return fallback or "I can answer from the available store data, but the live LLM service is currently unavailable."

    def chat(self, user_message: str, context: str = "") -> str:
        """Generate a response using the LLM with context and conversation history."""
        convo_lines = []
        for msg in self.conversation_history[-5:]:
            convo_lines.append(f"User: {msg.get('user', '')}\\nAssistant: {msg.get('assistant', '')}")
        convo_text = chr(10).join(convo_lines)

        prompt = f"""You are a warm, human-sounding SmartRetailAI assistant. Use the provided store data first, and do not invent product, order, price, stock, policy, or analytics facts.

Instructions:
1. Answer naturally, like a helpful person, not like a database dump.
2. If the user asks about return policies, exchange rules, discounts, orders, or products, answer from the context.
3. Keep answers concise, usually 3-5 short lines.
4. If data is missing, say what you can confirm and ask one useful follow-up.
5. If the user asks about a specific product, use the exact live MongoDB product record from context. Do not replace it with policy, sales, or generic discount text.
6. For product answers, output a simple 3-5 line summary strictly following this format:
**Name:** [Exact Name]
**Category:** [Exact Category]
**Price:** [Exact Price from context, do not change it]
**Stock:** [Exact Stock from context]
**Description:** [Exact Description from context]
7. NEVER make up or change prices, stock, or descriptions. Use the exact data provided in the context.

Context from store policies, products, or orders (use this to help answer):
{context}

Conversation history:
{convo_text}

Current user question: {user_message}

Respond in a friendly, humanised way using only the context above."""

        response = self.invoke(prompt, fallback=self._fallback_response(user_message, context))
        self.conversation_history.append({"user": user_message, "assistant": response})
        return response

    def _fallback_response(self, user_message: str, context: str = "") -> str:
        if not context.strip():
            return "I can help with products, orders, returns, refunds, shipping, and store policies. Please ask a specific question."

        lines = [line.strip() for line in context.splitlines() if line.strip()]
        if any(line.startswith("Catalog product record") for line in lines):
            fields = [
                line for line in lines
                if line.startswith(("Name:", "Category:", "Price:", "Stock:", "Description:"))
            ]
            return "\n".join(fields[:5])
        useful_lines = [line for line in lines if not line.lower().startswith(("products found", "context"))]
        if useful_lines:
            return "\n".join(useful_lines[:4])
        return "Here is what I found from the store data:\n" + "\n".join(lines[:3])
