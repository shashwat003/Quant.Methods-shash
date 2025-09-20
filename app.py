# app.py — Bank of Shash • Customer Support (Streamlit)
import os
import time
import streamlit as st

# ---------- Config ----------
st.set_page_config(
    page_title="Bank of Shash • Customer Support",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Azure OpenAI Settings (HARDCODED) ----------
AZURE_OPENAI_ENDPOINT    = "https://testaisentiment.openai.azure.com/"
AZURE_OPENAI_API_KEY     = "cb1c33772b3c4edab77db69ae18c9a43"
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
AZURE_OPENAI_DEPLOYMENT  = "aipocexploration"

# ---------- Styling ----------
PRIMARY = "#0f766e"
ACCENT  = "#0891b2"
LIGHTBG = "#f8fafc"

st.markdown(
    f"""
    <style>
      .main {{
        padding-top: 1.25rem;
        background: linear-gradient(180deg, {LIGHTBG} 0%, #ffffff 35%);
      }}
      .bcard {{
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 8px 24px rgba(15, 118, 110, 0.06);
      }}
      .btn-primary {{
        background: {PRIMARY};
        color: white !important;
        padding: 0.75rem 1.15rem;
        border-radius: 999px;
        text-decoration: none !important;
        font-weight: 600;
        border: 0;
      }}
      .btn-primary:hover {{ background: {ACCENT}; }}
      .subtle {{ color:#475569; font-size:0.95rem; }}
      .tag {{
        display:inline-block; background:#ecfeff; color:#164e63;
        padding:4px 10px; border-radius:999px; font-size:0.8rem; border:1px solid #cffafe;
      }}
      .header-title {{
        font-size: 2.0rem; font-weight: 800; color: #0b3b38; letter-spacing: -0.02em;
      }}
      .hero {{
        background: radial-gradient(1200px 500px at 18% 0%, #ecfeff 0%, transparent 60%);
        border-radius: 18px; padding: 1.25rem 1.5rem; border:1px solid #e5e7eb;
      }}
      .callout {{ background:#f0fdf4; border:1px solid #bbf7d0; color:#065f46;
                 padding:10px 14px; border-radius:12px; font-size:0.95rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Azure OpenAI Client ----------
OPENAI_OK = True
client = None
try:
    from openai import AzureOpenAI
    client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )
except Exception:
    OPENAI_OK = False

def ask_gpt(messages, temperature: float = 0.2, max_tokens: int = 700) -> str:
    """Minimal Azure Chat Completions helper."""
    if not OPENAI_OK or not AZURE_OPENAI_DEPLOYMENT:
        return "(Azure OpenAI not configured properly)"
    try:
        resp = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"(Error calling Azure OpenAI: {e})"

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    default_prompt = (
        "You are the Bank of Shash virtual assistant. Be concise, friendly, and professional. "
        "Before discussing accounts, perform identity checks (never ask for full card or PIN). "
        "Follow compliance, summarize actions, and offer a handoff to phone support at +35345933308 when needed."
    )
    sys_prompt = st.text_area("System Prompt", value=default_prompt, height=180)
    st.session_state["system_prompt"] = sys_prompt

    st.markdown("---")
    st.markdown("**Contact**")
    st.markdown('<a class="btn-primary" href="tel:+35345933308">📞 Call +35345933308</a>', unsafe_allow_html=True)
    st.caption("Available 24/7")

# ---------- Header / Hero ----------
c1, c2 = st.columns([1.6, 1])
with c1:
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown('<div class="header-title">Bank of Shash • Customer Support</div>', unsafe_allow_html=True)
    st.write("Get help instantly via secure chat or call our Retell AI voice agent.")
    st.markdown(
        """
        <div class="bcard" style="margin-top:8px;">
          <div style="display:flex; gap:14px; align-items:center; flex-wrap:wrap;">
            <a class="btn-primary" href="tel:+35345933308">📞 Call +35345933308</a>
            <span class="tag">Retell AI Voice Agent</span>
            <span class="tag">24/7</span>
          </div>
          <div class="subtle" style="margin-top:8px;">Prefer typing? Use the secure chat on the right.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown(
        """
        <div class="bcard">
          <div class="subtle"><b>Status:</b> All systems operational</div>
          <div style="margin-top:10px;" class="subtle">Your security is our priority. We never ask for full PINs or passwords.</div>
          <div style="margin-top:10px;" class="callout">ℹ️ Tip: For card loss, say “lost card” or call +35345933308 for immediate action.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------- Main Layout ----------
left, right = st.columns([0.52, 0.48])

with left:
    st.markdown("### 🧭 Quick Actions")
    if st.button("Report Lost Card", use_container_width=True):
        st.session_state.setdefault("messages", [])
        st.session_state.messages.append({"role": "user", "content": "I lost my card. Please block it and send a replacement."})
        st.rerun()
    if st.button("Dispute a Charge", use_container_width=True):
        st.session_state.setdefault("messages", [])
        st.session_state.messages.append({"role": "user", "content": "I want to dispute a card transaction from yesterday."})
        st.rerun()
    if st.button("Talk to a Human", use_container_width=True):
        st.session_state.setdefault("messages", [])
        st.session_state.messages.append({"role":"assistant",
                                          "content":"Sure—I'll connect you. You can also call our automated agent at +35345933308."})
        st.rerun()

    st.markdown("#### How it works")
    st.markdown(
        """
        <div class="bcard">
          <b>Voice</b>: Our Retell AI agent handles inbound calls at <b>+35345933308</b>.<br/>
          <b>Chat</b>: This chat uses Azure OpenAI with the same system prompt to keep tone/policies aligned.
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown("### 💬 Secure Chat")
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": st.session_state.get("system_prompt", "")},
            {"role": "assistant", "content": "Hi! I'm your Bank of Shash assistant. How can I help today?"}
        ]

    for msg in st.session_state.messages[1:]:
        with st.chat_message("assistant" if msg["role"]=="assistant" else "user"):
            st.write(msg["content"])

    user_text = st.chat_input("Type your message…")
    if user_text:
        st.session_state.messages.append({"role":"user", "content":user_text})
        with st.chat_message("user"):
            st.write(user_text)

        reply = ask_gpt(st.session_state.messages)
        st.session_state.messages.append({"role":"assistant","content":reply})
        with st.chat_message("assistant"):
            st.write(reply)

st.markdown("---")
st.caption("© Bank of Shash — Secure support. Never share full PINs or passwords in chat.")
