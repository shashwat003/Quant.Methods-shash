# app.py — Bank of Shash • Customer Support
# Fixes: robust state init (no AttributeError), improved contrast, clearer inputs
# Identity flow: name → account number → last4 → DOB (retry if wrong), matches your call-agent prompt

import re
import streamlit as st

# ------------------------------
# Page config
# ------------------------------
st.set_page_config(
    page_title="Bank of Shash • Customer Support",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PHONE_NUMBER = "+35345933308"

# ------------------------------
# Hard-coded Azure OpenAI (optional)
# ------------------------------
AZURE_OPENAI_ENDPOINT    = "https://testaisentiment.openai.azure.com/"
AZURE_OPENAI_API_KEY     = "cb1c33772b3c4edab77db69ae18c9a43"
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
AZURE_OPENAI_DEPLOYMENT  = "aipocexploration"

# ------------------------------
# Hard-coded customers
# ------------------------------
CUSTOMERS = {
    "john cena": {
        "name": "John Cena",
        "last4": "1234",
        "dob": "3rd november 2000",
        "balance": 2000.00,
        "lost_stolen_active": True,
    },
    "sagar karnik": {
        "name": "Sagar Karnik",
        "last4": "5678",
        "dob": "3rd december 2005",
        "balance": 2500.00,
        "lost_stolen_active": True,  # fraud may/may not; handled in flow
    },
}

# ------------------------------
# Styles (higher contrast)
# ------------------------------
BG_DARK     = "#0b1220"     # page
PANEL_DARK  = "#101827"     # card bg (brighter than before for readability)
BORDER      = "#263246"     # card border
TEXT_MAIN   = "#eef2f7"     # primary text (lighter)
TEXT_SOFT   = "#9fb0c7"     # muted text
PRIMARY     = "#22d3ee"     # cyan
PRIMARY_D   = "#0fb5cf"
ACCENT      = "#7c3aed"     # violet
GOOD        = "#22c55e"
WARN        = "#f59e0b"
DANGER      = "#ef4444"

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
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 12px 34px rgba(3,12,24,0.45);
      }}
      .headline {{
        font-size: 2.0rem; font-weight: 800; letter-spacing:-0.02em;
      }}
      .soft {{ color: {TEXT_SOFT}; }}
      .pill {{
        display:inline-flex; align-items:center; gap:8px;
        padding: 6px 12px; border-radius: 999px; font-size: 0.85rem;
        background: rgba(34,211,238,0.12); color: {PRIMARY};
        border: 1px solid rgba(34,211,238,0.28);
      }}
      .btn {{
        display:inline-block; padding: 10px 14px; border-radius:12px;
        background: linear-gradient(180deg, {PRIMARY} 0%, {PRIMARY_D} 100%);
        color:#001016; text-decoration:none !important; font-weight:700;
        box-shadow: 0 6px 18px rgba(34,211,238,0.18);
      }}
      .btn:active {{ transform: translateY(1px); }}
      .good {{ color: {GOOD}; font-weight:700; }}
      .warn {{ color: {WARN}; font-weight:700; }}
      .danger {{ color: {DANGER}; font-weight:700; }}
      /* Ticker */
      .ticker-wrap {{
        width: 100%; overflow: hidden;
        background: #0d3b37; border: 1px solid #115e56;
        border-radius: 14px; padding: 8px 0; margin: 10px 0 16px 0;
      }}
      .ticker {{ display: inline-block; white-space: nowrap; animation: scroll-left 18s linear infinite; font-weight: 600; }}
      .ticker a {{ color: {PRIMARY}; text-decoration: none; }}
      @keyframes scroll-left {{ 0% {{ transform: translateX(100%); }} 100% {{ transform: translateX(-100%); }} }}
      /* Inputs / chat */
      div[data-baseweb="input"] input, .stTextInput>div>div>input, .stTextArea textarea {{
        background:{BG_DARK}; color:{TEXT_MAIN}; border:1px solid {BORDER};
      }}
      div[data-testid="stChatInput"] textarea {{
        background:{BG_DARK} !important; color:{TEXT_MAIN} !important; border:1px solid {BORDER} !important;
      }}
      .stChatMessage .stMarkdown p {{ color: {TEXT_MAIN}; }}
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------
# LLM client (optional)
# ------------------------------
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
        return "(Model not configured. Update AZURE_* constants at top of file.)"
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

# ------------------------------
# System prompt (your call-agent prompt mirrored)
# ------------------------------
SYSTEM_PROMPT = """🧾 Identity & Purpose
You are Sam, a friendly, professional, and knowledgeable virtual banking assistant for Bank of Shash.
You assist customers with inquiries, account services, card issues (like fraud or stolen cards), and appointment scheduling.
Always answer in GMT timezone. Bank of Shash branch is open 9 AM – 5 PM GMT.

👥 Hard-Coded Customers
John Cena
Last 4 digits of debit card: 1234
Date of birth: 3rd November 2000
Account balance: €2000
Lost/Stolen card flow: Always active

Sagar Karnik
Last 4 digits of debit card: 5678
Date of birth: 3rd December 2005
Account balance: €2500
Fraud queries: May or may not call — handle with standard fraud-protection flow

🔐 Verification Flow
Before disclosing any account info or taking action:
1) Ask for full name.
2) Ask for account number (any number is accepted for flow).
3) Ask for last 4 digits of debit card.
   - If mismatch → say: “Hmm, the digits don’t match our records. Could you check and try again?”
   - Allow retry.
   - If still incorrect → stop politely: “I’m sorry, I can’t verify your account right now. Please contact Bank of Shash support staff for further help.”
4) Ask for date of birth.
Only proceed if verified.

🎤 Introduction
“Hello! This is Sam from Bank of Shash. How can I assist you today?”

📞 Conversation Flow
1) General Inquiry Handling — Answer questions about account services, balances, or branch info. If more help is needed → recommend appointment with advisor.
2) Account Balance Inquiry — If John Cena: “Your balance is €2000.” If Sagar Karnik: “Your balance is €2500.”
3) Card Lost/Stolen Handling (John Cena special)
   - Empathy; verify; mention last known activity (Camden Street / O’Brian’s Pub); secure account.
4) Fraud Handling (Sagar/General) — Empathy; verify; reassure protection.
5) Appointment Booking — Collect first name, email, account type; check availability; confirm/offer two alternatives.

✅ Resolution & Closing
• John: closing + gentle upsell (mortgage/car loan).
• Sagar: closing + gentle upsell (student loan/credit card).
• Failed verification after retry: provide the polite stop message.

📌 Guardrails
• Only banking topics. Never disclose info without full verification. Stay calm, respectful, professional.
"""

# ------------------------------
# Identity parsing & validation
# ------------------------------
NAME_PATTERN  = r"(john\\s*cena|sagar\\s*karnik)"
LAST4_PATTERN = r"(?:last\\s*4\\s*digits|last\\s*four|\\*\\*\\*\\*|ending\\s*in|last4)\\D*(\\d{{4}})"
DOB_PATTERN   = r"(\\d{{1,2}}(?:st|nd|rd|th)?\\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|"
DOB_PATTERN  += r"january|february|march|april|june|july|august|september|october|november|december)\\s+\\d{{4}})"
ACCT_PATTERN  = r"(?:account\\s*number|acct\\s*no\\.?|a/c|account)\\D*(\\d{3,})"

def _norm(s: str) -> str:
    return re.sub(r"\\s+", " ", s.strip().lower())

def parse_identity(text: str):
    t = text.lower()
    name = re.search(NAME_PATTERN, t)
    last4 = re.search(LAST4_PATTERN, t)
    dob = re.search(DOB_PATTERN, t, flags=re.IGNORECASE)
    acct = re.search(ACCT_PATTERN, t)
    return (
        " ".join(name.group(1).split()) if name else None,
        last4.group(1) if last4 else None,
        _norm(dob.group(0)) if dob else None,
        acct.group(1) if acct else None,
    )

def verify(name, last4, dob):
    if not name or not last4 or not dob:
        missing = []
        if not name:  missing.append("full name")
        if not last4: missing.append("last 4 digits")
        if not dob:   missing.append("date of birth (e.g., 3rd November 2000)")
        return False, "For security, please provide your " + ", ".join(missing) + ".", None

    rec = CUSTOMERS.get(name)
    if not rec:
        return False, "I couldn’t find that customer. Please re-enter your full name exactly as on the account.", None

    issues = []
    if last4 != rec["last4"]:
        issues.append("last 4 digits")
    if _norm(dob) != rec["dob"]:
        issues.append("date of birth")

    if issues:
        return False, f"Hmm, the {', '.join(issues)} don’t match our records. Could you check and try again?", None

    return True, f"Thanks {rec['name']}, you’re verified.", rec

# ------------------------------
# Safe state init (prevents AttributeError)
# ------------------------------
def ensure_state():
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": "Hello! This is Sam from Bank of Shash. How can I assist you today?"}
        ]
    if "verif" not in st.session_state:
        st.session_state["verif"] = {"name": None, "acct": None, "last4": None, "dob": None,
                                     "attempts": 0, "ok": False, "record": None}

ensure_state()

# ------------------------------
# Header + Ticker
# ------------------------------
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

st.markdown(
    f"""
    <div class="ticker-wrap">
      <div class="ticker">
        🌱 We have introduced <b>Green Mortgage</b> with preferential rates for energy-efficient homes —
        <a href="#" onclick="return false;">click here to learn more</a>
        or call <a href="tel:{PHONE_NUMBER}">{PHONE_NUMBER}</a> to talk to our agent.
        &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; 💡 Ask in chat: “Tell me about Green Mortgage eligibility.”
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# Layout
# ------------------------------
left, right = st.columns([0.52, 0.48])

with left:
    st.markdown(
        """
        <div class="card">
          <div style="font-weight:800; font-size:1.15rem;">Help Center</div>
          <div class="soft" style="margin-top:4px;">Choose a quick action or ask in chat.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    a, b, c = st.columns(3)
    with a:
        if st.button("Report Lost/Stolen", use_container_width=True):
            st.session_state.messages.append({"role":"user","content":
                "My name is John Cena. Account number 12345678. Last 4 digits 1234. DOB 3rd November 2000. I lost my card."})
            st.rerun()
    with b:
        if st.button("Check Balance", use_container_width=True):
            st.session_state.messages.append({"role":"user","content":
                "My name is Sagar Karnik. Account no 999001. Last four 5678. DOB 3rd December 2005. What is my balance?"})
            st.rerun()
    with c:
        if st.button("Green Mortgage", use_container_width=True):
            st.session_state.messages.append({"role":"user","content":
                "Tell me about Green Mortgage eligibility and rates."})
            st.rerun()

with right:
    st.markdown(
        f"""
        <div class="card" style="margin-bottom:10px;">
          <div style="display:flex; align-items:center; justify-content:space-between;">
            <div style="font-weight:800; font-size:1.15rem;">💬 Secure Chat</div>
            <a class="pill" href="tel:{PHONE_NUMBER}">Or call {PHONE_NUMBER}</a>
          </div>
          <div class="soft">Do not share full card numbers or passwords. Answers in GMT. Branch hours: 9 AM – 5 PM GMT.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # render history (skip system)
    for m in st.session_state.messages[1:]:
        with st.chat_message("assistant" if m["role"]=="assistant" else "user"):
            st.write(m["content"])

    user_text = st.chat_input("Type your message…")
    if user_text:
        st.session_state.messages.append({"role":"user","content":user_text})
        with st.chat_message("user"):
            st.write(user_text)

        # identity capture
        name, last4, dob, acct = parse_identity(user_text)
        v = st.session_state.verif
        if name:  v["name"]  = name
        if acct:  v["acct"]  = acct
        if last4: v["last4"] = last4
        if dob:   v["dob"]   = dob

        reply = None

        # Need verification for account-specific topics
        needs_verif = any(k in user_text.lower() for k in ["balance", "lost", "stolen", "fraud", "card", "account"])
        if not v["ok"] and needs_verif:
            if not v["name"]:
                reply = "For security, please share your full name as on the account."
            elif not v["acct"]:
                reply = "Please share your account number."
            elif not v["last4"]:
                reply = "Please share the last 4 digits of your debit card."
            elif not v["dob"]:
                reply = "Please share your date of birth (e.g., 3rd November 2000)."
            else:
                ok, msg, rec = verify(v["name"], v["last4"], v["dob"])
                if ok:
                    v["ok"] = True
                    v["record"] = rec
                    reply = f"{msg} How can I help you today?"
                else:
                    v["attempts"] += 1
                    if v["attempts"] >= 2:
                        reply = ("I’m sorry, I can’t verify your account right now. "
                                 "Please contact Bank of Shash support staff for further help.")
                    else:
                        reply = msg  # ask to verify again

        # If verified, handle key intents locally
        if v["ok"] and reply is None:
            rec = v["record"]
            low = user_text.lower()
            if "balance" in low:
                reply = f"Your balance is €{CUSTOMERS[rec['name'].lower()]['balance']:.0f}."
            elif "lost" in low or "stolen" in low or ("card" in low and "block" in low):
                if rec["name"] == "John Cena":
                    reply = (
                        "I’m really sorry to hear about your card. That can be stressful — let’s take care of this together.\n\n"
                        "Looking at your recent activity… I see your last transaction was on Camden Street, at O’Brian’s Pub.\n"
                        f"While we’re checking if it was left behind, I’ll secure your account. Your card ending {rec['last4']} is now blocked and a replacement has been ordered."
                    )
                else:
                    reply = (
                        "I’m really sorry to hear about this — fraud concerns are serious. Let’s work through this together. "
                        "I’ll block your card, monitor unusual activity, and order a replacement if needed. Your funds are protected."
                    )
            elif "mortgage" in low:
                reply = ("Our Green Mortgage offers preferential rates for energy-efficient homes. "
                         f"I can book you with an advisor, or you can call us at {PHONE_NUMBER}.")
            elif "appointment" in low or "book" in low:
                reply = ("Happy to help with an appointment. Please share your first name, email, and account type. "
                         "I’ll check availability and confirm or offer two alternative slots.")

        # Model or fallback for general Q&A
        if reply is None:
            model_out = ask_gpt(st.session_state.messages)
            if model_out.startswith("("):
                reply = (f"I can help with banking services here, or you can reach our phone agent at {PHONE_NUMBER}.")
            else:
                reply = model_out

        st.session_state.messages.append({"role":"assistant","content":reply})
        with st.chat_message("assistant"):
            st.write(reply)

# Footer
st.markdown("<hr style='border-color:#1f2937;'>", unsafe_allow_html=True)
st.caption(f"© Bank of Shash — Secure support. Never share full PINs or passwords in chat. • Voice agent: {PHONE_NUMBER}")
