# app.py — Bank of Shash • Customer Support (Streamlit, dark professional UI inspired by your reference)
import streamlit as st
import os

# =========================
# PAGE & THEME CONFIG
# =========================
st.set_page_config(
    page_title="Bank of Shash • Customer Support",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---- Color palette (professional dark) ----
BG_DARK     = "#0b1220"   # deep navy
PANEL_DARK  = "#0f172a"   # slate-900
BORDER      = "#1e293b"   # slate-800
TEXT_MAIN   = "#e5e7eb"   # slate-200
TEXT_SOFT   = "#94a3b8"   # slate-400
PRIMARY     = "#22d3ee"   # cyan-400
PRIMARY_D   = "#06b6d4"   # cyan-500
ACCENT      = "#7c3aed"   # violet-600
GOOD        = "#22c55e"   # green-500
WARN        = "#f59e0b"   # amber-500

PHONE_NUMBER = "+35345933308"

# =========================
# HARD-CODED AZURE OPENAI
# =========================
AZURE_OPENAI_ENDPOINT    = "https://testaisentiment.openai.azure.com/"
AZURE_OPENAI_API_KEY     = "cb1c33772b3c4edab77db69ae18c9a43"
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
AZURE_OPENAI_DEPLOYMENT  = "AIzaSyCRHbWFgUuSIjOm3CgHNKq6Q8RLMKXjlKU"

# =========================
# STYLES
# =========================
st.markdown(
    f"""
    <style>
      html, body, .block-container {{
        background: {BG_DARK};
        color: {TEXT_MAIN};
      }}
      .card {{
        background: {PANEL_DARK};
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 12px 40px rgba(2,6,23,0.45);
      }}
      .headline {{
        font-size: 2.0rem; font-weight: 800; letter-spacing:-0.02em;
      }}
      .soft {{ color: {TEXT_SOFT}; }}
      .pill {{
        display:inline-flex; align-items:center; gap:8px;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 0.85rem;
        background: rgba(34,211,238,0.14);
        color: {PRIMARY};
        border: 1px solid rgba(34,211,238,0.28);
      }}
      .btn {{
        display:inline-block; padding: 10px 14px; border-radius:12px;
        background: linear-gradient(180deg, {PRIMARY} 0%, {PRIMARY_D} 100%);
        color:#001016; text-decoration:none !important; font-weight:700;
        box-shadow: 0 6px 20px rgba(34,211,238,0.18);
      }}
      .btn:active {{ transform: translateY(1px); }}
      .good {{ color: {GOOD}; font-weight:700; }}
      .warn {{ color: {WARN}; font-weight:700; }}
      /* marquee banner */
      .ticker-wrap {{
        width: 100%;
        overflow: hidden;
        background: rgba(12, 83, 74, 0.35);
        border: 1px solid #0e4b48;
        border-radius: 14px;
        padding: 8px 0;
        margin: 10px 0 16px 0;
      }}
      .ticker {{
        display: inline-block;
        white-space: nowrap;
        animation: scroll-left 18s linear infinite;
        font-weight: 600;
      }}
      .ticker a {{ color: {PRIMARY}; text-decoration: none; }}
      @keyframes scroll-left {{
        0%   {{ transform: translateX(100%); }}
        100% {{ transform: translateX(-100%); }}
      }}
      /* chat colors */
      .stChatMessage .stMarkdown p {{ color: {TEXT_MAIN}; }}
      .stTextInput>div>div>input {{ background:{PANEL_DARK}; color:{TEXT_MAIN}; border:1px solid {BORDER}; }}
      .stTextArea textarea {{ background:{PANEL_DARK}; color:{TEXT_MAIN}; border:1px solid {BORDER}; }}
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# AZURE OPENAI CLIENT
# =========================
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
    if not OPENAI_OK or not AZURE_OPENAI_DEPLOYMENT:
        return ("(Model not configured. Update AZURE_OPENAI_* constants at top of app.py.)")
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

# =========================
# HEADER
# =========================
hdr_l, hdr_r = st.columns([0.75, 0.25])
with hdr_l:
    st.markdown(
        f"""
        <div style="display:flex; gap:14px; align-items:center;">
          <div style="width:46px; height:46px; background:{ACCENT}; border-radius:12px;"></div>
          <div class="headline">Bank of Shash — Customer Support</div>
          <span class="pill">● Live</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with hdr_r:
    st.markdown(
        f'<div style="text-align:right;"><a class="btn" href="tel:{PHONE_NUMBER}">📞 Call {PHONE_NUMBER}</a></div>',
        unsafe_allow_html=True,
    )

# =========================
# MOVING UPDATE (Ticker)
# =========================
st.markdown(
    f"""
    <div class="ticker-wrap">
      <div class="ticker">
        🌱 We have introduced <b>Green Mortgage</b> with preferential rates for energy-efficient homes —
        <a href="#" onclick="window.alert('A support specialist will contact you shortly.');return false;">click here to learn more</a>
        or call <a href="tel:{PHONE_NUMBER}">{PHONE_NUMBER}</a> to talk to our agent.
        &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
        💡 Ask in chat: “Tell me about Green Mortgage eligibility.”
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================
# CUSTOMER SUPPORT LAYOUT
# =========================
left, right = st.columns([0.52, 0.48])

# --- LEFT: Support options / status ---
with left:
    st.markdown(
        """
        <div class="card">
          <div style="display:flex; align-items:center; justify-content:space-between;">
            <div style="font-weight:800; font-size:1.15rem;">Help Center</div>
            <span class="soft">Secure & 24/7</span>
          </div>
          <div class="soft" style="margin-top:4px;">Choose a quick action or ask in chat.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Report Lost Card", use_container_width=True):
            st.session_state.setdefault("messages", [])
            st.session_state.messages.append({"role":"user","content":
                "I lost my card. Please block it and send a replacement."})
            st.rerun()
    with c2:
        if st.button("Dispute a Charge", use_container_width=True):
            st.session_state.setdefault("messages", [])
            st.session_state.messages.append({"role":"user","content":
                "I need to dispute a card transaction from yesterday."})
            st.rerun()
    with c3:
        if st.button("Mortgage Support", use_container_width=True):
            st.session_state.setdefault("messages", [])
            st.session_state.messages.append({"role":"user","content":
                "Tell me about the new Green Mortgage and eligibility."})
            st.rerun()

    st.markdown(
        f"""
        <div class="card" style="margin-top:14px;">
          <div style="display:flex; align-items:center; justify-content:space-between;">
            <div style="font-weight:800; font-size:1.15rem;">Contact Options</div>
            <a class="btn" href="tel:{PHONE_NUMBER}">📞 Call {PHONE_NUMBER}</a>
          </div>
          <div class="soft" style="margin-top:6px;">
            • Phone agent (Retell AI) available 24/7.<br/>
            • For urgent card blocks, calling is fastest. <span class="good">Typical wait &lt; 1 min</span>.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- RIGHT: Chat assistant ---
with right:
    st.markdown(
        f"""
        <div class="card" style="margin-bottom:10px;">
          <div style="display:flex; align-items:center; justify-content:space-between;">
            <div style="font-weight:800; font-size:1.15rem;">💬 Secure Chat</div>
            <a class="pill" href="tel:{PHONE_NUMBER}">Or call {PHONE_NUMBER}</a>
          </div>
          <div class="soft">Do not share full card numbers or passwords here.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system",
             "content": ("You are the Bank of Shash customer support assistant. "
                         "Be concise, friendly, and compliant. Verify identity before discussing account specifics. "
                         "Never request full card/PIN. Offer a phone handoff at +35345933308 when appropriate.")},
            {"role": "assistant", "content": "Hi! I’m your Bank of Shash assistant. How can I help today?"}
        ]

    for m in st.session_state.messages[1:]:
        with st.chat_message("assistant" if m["role"]=="assistant" else "user"):
            st.write(m["content"])

    user_text = st.chat_input("Type your message…")
    if user_text:
        st.session_state.messages.append({"role":"user","content":user_text})
        with st.chat_message("user"):
            st.write(user_text)

        try:
            reply = ask_gpt(st.session_state.messages)
            if reply.startswith("(Model not configured") or reply.startswith("(Error"):
                # graceful fallback if creds missing
                if "lost" in user_text.lower() and "card" in user_text.lower():
                    reply = ("I can help you block your card now after verification, "
                             f"or you can call our automated agent at {PHONE_NUMBER} for immediate action.")
                else:
                    reply = (f"I can help here, or you can reach our phone agent at {PHONE_NUMBER}. "
                             "For account-specific help I’ll need to verify your identity.")
        except Exception as e:
            reply = f"Something went wrong. Please try again or call {PHONE_NUMBER}. ({e})"

        st.session_state.messages.append({"role":"assistant","content":reply})
        with st.chat_message("assistant"):
            st.write(reply)

# =========================
# FOOTER
# =========================
st.markdown("<hr style='border-color:#1f2937;'>", unsafe_allow_html=True)
st.caption(f"© Bank of Shash — Secure support. Never share full PINs or passwords in chat.  •  Voice agent: {PHONE_NUMBER}")
