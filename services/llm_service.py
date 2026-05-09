import os
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.llm = None
        self._llm_error = None
        self.conversation_history = []

    def _get_llm(self):
        if self.llm is not None or self._llm_error:
            return self.llm
        if not os.getenv("GROQ_API_KEY"):
            self._llm_error = "GROQ_API_KEY is not configured"
            return None
        try:
            import httpx
            from langchain_groq import ChatGroq

            self.llm = ChatGroq(
                api_key=os.getenv("GROQ_API_KEY"),
                model=os.getenv("GROQ_MODEL", "llama3-8b-8192"),
                temperature=float(os.getenv("GROQ_TEMPERATURE", "0.25")),
                timeout=float(os.getenv("GROQ_TIMEOUT", "25")),
                max_retries=int(os.getenv("GROQ_MAX_RETRIES", "1")),
                http_client=httpx.Client(trust_env=False, timeout=float(os.getenv("GROQ_TIMEOUT", "25"))),
            )
        except Exception as exc:
            self._llm_error = str(exc)
            print(f"[LLMService] Groq client unavailable: {exc}")
        return self.llm

    def invoke(self, prompt: str, fallback: str = "") -> str:
        llm = self._get_llm()
        if llm is None:
            return fallback or "I can answer from the available store data, but the live LLM service is not configured."
        try:
            return llm.invoke(prompt).content
        except Exception as exc:
            print(f"[LLMService] Groq unavailable, using local data fallback: {exc}")
            return fallback or "I can answer from the available store data, but the live LLM service is currently unavailable."

    def _clean_grounded_output(self, response: str) -> str:
        blocked_followups = [
            "would you like",
            "do you want",
            "if you'd like",
            "if you would like",
            "let me know",
            "feel free",
        ]
        lines = []
        for line in response.splitlines():
            compact = line.strip()
            if not compact:
                lines.append(line)
                continue
            normalized = compact.lower()
            if any(phrase in normalized for phrase in blocked_followups):
                continue
            lines.append(line)
        cleaned = "\n".join(lines).strip()
        return cleaned or response.strip()

    def grounded_answer(self, user_message: str, verified_facts: str, role: str, fallback: str = "") -> str:
        """Use Groq to humanise only verified project facts."""
        prompt = f"""You are SmartRetailAI's {role}.

Your job:
- Answer naturally and professionally.
- Use ONLY the verified project facts below.
- Do not add outside knowledge, live web facts, generic claims, or invented numbers.
- Preserve product names, prices, stock, sales growth, offers, and policy rules exactly.
- Treat listed prices as the current catalog price. Never infer an original price, final price, savings amount, or hidden offer.
- If verified facts include product lists, keep the same product names and exact numeric values; do not rename, merge, or replace them.
- For customer product answers, always include current catalog price and stock status when those facts are provided.
- For customer product lists or filters, include each product's name, current catalog price, stock status, and short description when those facts are provided.
- If an offer or discount is mentioned only inside a product description, repeat it exactly as description text and do not calculate the discounted amount.
- If the user asks outside this domain, politely say you can only help within this SmartRetailAI area.
- Keep the response compact: 3-6 clear lines or bullets.
- Sound human, not like a hardcoded mapping.
- Do not add filler such as "if you'd like" or offer extra details unless those details are in the verified facts.
- Do not mention that you were given verified facts or context.

Verified project facts:
{verified_facts}

User question:
{user_message}

Final answer:"""
        response = self.invoke(prompt, fallback=fallback or verified_facts)
        response = self._clean_grounded_output(response)
        self.conversation_history.append({"user": user_message, "assistant": response})
        return response

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
