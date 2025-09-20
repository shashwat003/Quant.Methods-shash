# app.py — Bank of Shash • Customer Support (polished UI, chat layout fixed, readable buttons, richer content)
# - Robust identity flow (name → account no. → last4 → DOB; retry if wrong)
# - Dark professional theme with higher contrast + readable buttons
# - Green Mortgage moving banner
# - Rich banking content sections (Products, Digital Services, Security, FAQs, Service Status)

import re
import streamlit as st

# ────────────────────────────────────────────────────────────────────────────────
# Page config / constants
# ────────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bank of Shash • Customer Support",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PHONE_NUMBER = "+35345933308"

# Hard-coded Azure OpenAI (optional; leave placeholders if not using)
AZURE_OPENAI_ENDPOINT    = "https://testaisentiment.openai.azure.com/"
AZURE_OPENAI_API_KEY     = "cb1c33772b3c4edab77db69ae18c9a43"
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
AZURE_OPENAI_DEPLOYMENT  = "aipocexploration"

# Hard-coded customers
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

# ────────────────────────────────────────────────────────────────────────────────
# Styles (tuned for readability) + chat container fixes
# ────────────────────────────────────────────────────────────────────────────────
BG      = "#0b1220"   # page
PANEL   = "#111827"   # card bg (lighter than before)
BORDER  = "#22314a"   # border
TEXT    = "#eef2f7"   # primary text
MUTED   = "#9fb0c7"   # secondary text
PRIMARY = "#22d3ee"   # cyan
PRIMARY2= "#0fb5cf"
ACCENT  = "#7c3aed"   # violet
GOOD    = "#22c55e"
WARN    = "#f59e0b"
DANGER  = "#ef4444"

st.markdown(
    f"""
    <style>
      html, body, .block-container {{
        background:{BG}; color:{TEXT};
      }}
      .card {{
        background:{PANEL}; border:1px solid {BORDER};
        border-radius:16px; padding:18px; box-shadow:0 10px 30px rgba(3,12,24,.45);
      }}
      .headline {{ font-size:2rem; font-weight:800; letter-spacing:-.02em; }}
      .soft {{ color:{MUTED}; }}
      .pill {{
        display:inline-flex; align-items:center; gap:8px; padding:6px 12px;
        border-radius:999px; font-size:.85rem; background:rgba(34,211,238,.12);
        color:{PRIMARY}; border:1px solid rgba(34,211,238,.28);
      }}
      /* Make ALL streamlit buttons readable */
      .stButton>button {{
        background:#1f2937; color:{TEXT}; border:1px solid {BORDER};
        border-radius:10px; font-weight:700; padding:.6rem 1rem;
      }}
      .stButton>button:hover {{
        background:linear-gradient(180deg,{PRIMARY} 0%, {PRIMARY2} 100%); color:#001016; border:0;
        box-shadow:0 6px 18px rgba(34,211,238,.18);
      }}
      /* Ticker */
      .ticker-wrap {{
        width:100%; overflow:hidden; background:#0d3b37; border:1px solid #115e56;
        border-radius:14px; padding:8px 0; margin:10px 0 16px 0;
      }}
      .ticker {{ display:inline-block; white-space:nowrap; animation:scroll-left 18s linear infinite; font-weight:600; }}
      .ticker a {{ color:{PRIMARY}; text-decoration:none; }}
      @keyframes scroll-left {{ 0% {{transform:translateX(100%);}} 100% {{transform:translateX(-100%);}} }}
      /* Inputs & chat bubbles */
      /* Chat area container to prevent messages escaping card bounds */
      .chat-wrap {{
        background:{PANEL}; border:1px solid {BORDER}; border-radius:16px; padding:0;
      }}
      div[data-testid="stChatMessage"] {{
        margin-left:0 !important; margin-right:0 !important;  /* align bubbles with container */
      }}
      /* Chat input field contrast */
      div[data-testid="stChatInput"] textarea {{
        background:#0c1423 !important; color:{TEXT} !important; border:1px solid {BORDER} !important;
      }}
      .stChatMessage .stMarkdown p {{ color:{TEXT}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────────────────────────────────────────
# LLM client (optional)
# ────────────────────────────────────────────────────────────────────────────────
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

# ────────────────────────────────────────────────────────────────────────────────
# System prompt (your call-agent prompt mirrored for chat)
# ────────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """🧾 Identity & Purpose
You are Sam, a friendly, professional, and knowledgeable virtual banking assistant for Bank of Shash.
You assist customers with inquiries, account services, card issues (like fraud or stolen cards), and appointment scheduling.
Always answer in GMT timezone. Bank of Shash branch is open 9 AM – 5 PM GMT.

👥 Hard-Coded Customers
John Cena — Last 4: 1234 — DOB: 3rd November 2000 — Balance: €2000 — Lost/Stolen flow: always active
Sagar Karnik — Last 4: 5678 — DOB: 3rd December 2005 — Balance: €2500 — Fraud: standard flow

🔐 Verification Flow
Ask for: full name → account number (any number accepted for flow) → last 4 digits → date of birth.
If mismatch say: “Hmm, the digits don’t match our records. Could you check and try again?” Allow retry once.
If still incorrect: “I’m sorry, I can’t verify your account right now. Please contact Bank of Shash support staff for further help.”
Only proceed if verified.

🎤 Introduction
“Hello! This is Sam from Bank of Shash. How can I assist you today?”

📞 Conversation Flow
1) General info & branch hours; suggest advisor appointment if needed.
2) Balance: John = €2000, Sagar = €2500.
3) Lost/Stolen (John special): empathy; mention Camden Street / O’Brian’s Pub last activity; secure account.
4) Fraud (Sagar/general): empathy; verify; reassure funds protected; block/monitor/replace.
5) Appointment: collect first name, email, account type; check availability; confirm or suggest alternatives.

✅ Closing & Upsell
John → upsell mortgage or car loan.  Sagar → upsell student loan or credit card.

📌 Guardrails
Banking topics only. Never disclose info without full verification. Stay calm, respectful, professional.
"""

# ────────────────────────────────────────────────────────────────────────────────
# Identity parsing & validation
# ────────────────────────────────────────────────────────────────────────────────
NAME_P   = r"(john\\s*cena|sagar\\s*karnik)"
LAST4_P  = r"(?:last\\s*4\\s*digits|last\\s*four|\\*\\*\\*\\*|ending\\s*in|last4)\\D*(\\d{{4}})"
DOB_P1   = r"(\\d{{1,2}}(?:st|nd|rd|th)?\\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|"
DOB_P1  += r"january|february|march|april|june|july|august|september|october|november|december)\\s+\\d{{4}})"
ACCT_P   = r"(?:account\\s*number|acct\\s*no\\.?|a/c|account)\\D*(\\d{3,})"

def _norm(s: str) -> str:
    return re.sub(r"\\s+", " ", s.strip().lower())

def parse_identity(text: str):
    t = text.lower()
    name = re.search(NAME_P, t)
    last4 = re.search(LAST4_P, t)
    dob = re.search(DOB_P1, t, flags=re.IGNORECASE)
    acct = re.search(ACCT_P, t)
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

# ────────────────────────────────────────────────────────────────────────────────
# Safe state init (prevents AttributeError) + helpers
# ────────────────────────────────────────────────────────────────────────────────
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

# ────────────────────────────────────────────────────────────────────────────────
# Header + Ticker
# ────────────────────────────────────────────────────────────────────────────────
hl, hr = st.columns([0.75, 0.25])
with hl:
    st.markdown(
        f"""
        <div style="display:flex; gap:14px; align-items:center;">
          <div style="width:46px; height:46px; background:{ACCENT}; border-radius:12px;"></div>
          <div class="headline">Bank of Shash — Customer Support</div>
          <span class="pill">● Live</span>
        </div>
        """, unsafe_allow_html=True
    )
with hr:
    st.markdown(f'<div style="text-align:right;"><a class="btn" href="tel:{PHONE_NUMBER}">📞 Call {PHONE_NUMBER}</a></div>',
                unsafe_allow_html=True)

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
    """, unsafe_allow_html=True
)

# ────────────────────────────────────────────────────────────────────────────────
# Main layout
# ────────────────────────────────────────────────────────────────────────────────
left, right = st.columns([0.52, 0.48])

# LEFT: Help Center + Rich Banking Content
with left:
    st.markdown(
        """
        <div class="card">
          <div style="font-weight:800; font-size:1.15rem;">Help Center</div>
          <div class="soft" style="margin-top:4px;">Choose a quick action or ask in chat.</div>
        </div>
        """, unsafe_allow_html=True
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

    # Products grid
    st.markdown(
        f"""
        <div class="card" style="margin-top:14px;">
          <div style="font-weight:800; font-size:1.15rem;">Personal Banking Products</div>
          <div class="soft">Explore our most popular services.</div>
          <div style="display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; margin-top:12px;">
            <div style="background:#0d1526; border:1px solid {BORDER}; border-radius:14px; padding:12px;">
              <div style="font-weight:700;">Current Account</div>
              <div class="soft">No monthly fees with minimum balance. Instant notifications.</div>
            </div>
            <div style="background:#0d1526; border:1px solid {BORDER}; border-radius:14px; padding:12px;">
              <div style="font-weight:700;">Savings Plus</div>
              <div class="soft">Competitive variable rate, flexible withdrawals.</div>
            </div>
            <div style="background:#0d1526; border:1px solid {BORDER}; border-radius:14px; padding:12px;">
              <div style="font-weight:700;">Visa Credit Card</div>
              <div class="soft">0% FX fees on online purchases for first 90 days.</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True
    )

    # Digital services
    st.markdown(
        f"""
        <div class="card" style="margin-top:14px;">
          <div style="font-weight:800; font-size:1.15rem;">Digital Banking</div>
          <div class="soft">Everything you need, right from your phone.</div>
          <ul class="soft" style="margin-top:8px;">
            <li>Mobile app with biometric login</li>
            <li>Virtual cards for secure online payments</li>
            <li>Instant transfers & bill payments</li>
            <li>Spending insights and budgeting</li>
          </ul>
        </div>
        """, unsafe_allow_html=True
    )

    # Security + status
    st.markdown(
        f"""
        <div class="card" style="margin-top:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-weight:800; font-size:1.15rem;">Security Center</div>
            <div class="pill">● Systems Operational</div>
          </div>
          <div class="soft" style="margin-top:6px;">Never share full card numbers, passwords or OTPs. We’ll never ask for them.</div>
        </div>
        """, unsafe_allow_html=True
    )

    # FAQs
    with st.expander("Frequently Asked Questions"):
        st.markdown("- **How do I freeze my card?** Use chat to confirm identity or call our agent. We can freeze instantly.")
        st.markdown("- **What are branch hours?** 9 AM – 5 PM GMT.")
        st.markdown("- **Green Mortgage?** Preferential rates for energy-efficient homes (BER A/B).")

# RIGHT: Chat (wrapped in its own container to keep bubbles inside)
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
        """, unsafe_allow_html=True
    )

    # Chat container fixes overflow/spacing
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    # Render history (skip system)
    for m in st.session_state.messages[1:]:
        with st.chat_message("assistant" if m["role"]=="assistant" else "user"):
            st.write(m["content"])

    user_text = st.chat_input("Type your message…")
    if user_text:
        st.session_state.messages.append({"role":"user","content":user_text})
        with st.chat_message("user"):
            st.write(user_text)

        # Identity capture
        name, last4, dob, acct = parse_identity(user_text)
        v = st.session_state.verif
        if name:  v["name"]  = name
        if acct:  v["acct"]  = acct
        if last4: v["last4"] = last4
        if dob:   v["dob"]   = dob

        reply = None

        # Require verification for sensitive intents
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
                        f"While we’re checking if it was left behind, I’ve secured your account. Your card ending {rec['last4']} is now blocked and a replacement has been ordered."
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

        # Model or fallback
        if reply is None:
            model_out = ask_gpt(st.session_state.messages)
            if model_out.startswith("("):
                reply = (f"I can help with banking services here, or you can reach our phone agent at {PHONE_NUMBER}.")
            else:
                reply = model_out

        st.session_state.messages.append({"role":"assistant","content":reply})
        with st.chat_message("assistant"):
            st.write(reply)

    st.markdown('</div>', unsafe_allow_html=True)  # close chat-wrap

# Footer
st.markdown("<hr style='border-color:#1f2937;'>", unsafe_allow_html=True)
st.caption(f"© Bank of Shash — Secure support. Never share full PINs or passwords in chat. • Voice agent: {PHONE_NUMBER}")
