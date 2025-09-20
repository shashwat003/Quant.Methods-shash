# app.py — Bank of Shash • Customer Support
# Clean chat layout (no mixed ordering), verification FSM, readable buttons, rich banking content.
# FIX: DOB comparison now normalizes both sides (removes st/nd/rd/th etc.) so 3/11/2000 == 3rd November 2000.

import re
import streamlit as st

# ────────────────────────────────────────────────────────────────────────────────
# PAGE / CONSTANTS
# ────────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Bank of Shash • Customer Support", page_icon="🏦",
                   layout="wide", initial_sidebar_state="collapsed")
PHONE_NUMBER = "+35345933308"

# Hard-coded Azure OpenAI (optional; safe fallback if unset)
AZURE_OPENAI_ENDPOINT    = "https://testaisentiment.openai.azure.com/"
AZURE_OPENAI_API_KEY     = "cb1c33772b3c4edab77db69ae18c9a43"
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
AZURE_OPENAI_DEPLOYMENT  = "aipocexploration"

# Demo customers
CUSTOMERS = {
    "john cena":  {"name":"John Cena","last4":"1234","dob":"3rd november 2000","balance":2000.0,"lost_stolen_active":True},
    "sagar karnik":{"name":"Sagar Karnik","last4":"5678","dob":"3rd december 2005","balance":2500.0,"lost_stolen_active":True},
}

# ────────────────────────────────────────────────────────────────────────────────
# THEME / STYLES (high contrast, readable buttons)
# ────────────────────────────────────────────────────────────────────────────────
BG, PANEL, BORDER, TEXT, MUTED = "#0b1220", "#111827", "#22314a", "#eef2f7", "#9fb0c7"
PRIMARY, PRIMARY2, ACCENT, GOOD, WARN, DANGER = "#22d3ee", "#0fb5cf", "#7c3aed", "#22c55e", "#f59e0b", "#ef4444"
st.markdown(f"""
<style>
  html, body, .block-container {{ background:{BG}; color:{TEXT}; }}
  .card {{ background:{PANEL}; border:1px solid {BORDER}; border-radius:16px; padding:18px; box-shadow:0 10px 30px rgba(3,12,24,.45); }}
  .headline {{ font-size:2rem; font-weight:800; letter-spacing:-.02em; }}
  .soft {{ color:{MUTED}; }}
  .pill {{ display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border-radius:999px; font-size:.85rem;
          background:rgba(34,211,238,.12); color:{PRIMARY}; border:1px solid rgba(34,211,238,.28); }}
  .stButton>button {{ background:#1f2937; color:{TEXT}; border:1px solid {BORDER}; border-radius:10px; font-weight:700; padding:.6rem 1rem; }}
  .stButton>button:hover {{ background:linear-gradient(180deg,{PRIMARY} 0%, {PRIMARY2} 100%); color:#001016; border:0;
                            box-shadow:0 6px 18px rgba(34,211,238,.18); }}
  .ticker-wrap {{ width:100%; overflow:hidden; background:#0d3b37; border:1px solid #115e56; border-radius:14px; padding:8px 0; margin:10px 0 16px 0; }}
  .ticker {{ display:inline-block; white-space:nowrap; animation:scroll-left 18s linear infinite; font-weight:600; }}
  .ticker a {{ color:{PRIMARY}; text-decoration:none; }}
  @keyframes scroll-left {{ 0% {{transform:translateX(100%);}} 100% {{transform:translateX(-100%);}} }}
  /* Chat container keeps bubbles inside and input at bottom */
  .chat-wrap {{ background:{PANEL}; border:1px solid {BORDER}; border-radius:16px; padding:0; }}
  div[data-testid="stChatMessage"] {{ margin-left:0 !important; margin-right:0 !important; }}
  div[data-testid="stChatInput"] textarea {{ background:#0c1423 !important; color:{TEXT} !important; border:2px solid {BORDER} !important; }}
  .stChatMessage .stMarkdown p {{ color:{TEXT}; }}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────────────────
# OPTIONAL LLM
# ────────────────────────────────────────────────────────────────────────────────
OPENAI_OK=True
client=None
try:
    from openai import AzureOpenAI
    client=AzureOpenAI(azure_endpoint=AZURE_OPENAI_ENDPOINT, api_key=AZURE_OPENAI_API_KEY,
                       api_version=AZURE_OPENAI_API_VERSION)
except Exception:
    OPENAI_OK=False

def ask_gpt(messages, temperature=0.2, max_tokens=700):
    if not OPENAI_OK or not AZURE_OPENAI_DEPLOYMENT:
        return "(Model not configured.)"
    try:
        r=client.chat.completions.create(model=AZURE_OPENAI_DEPLOYMENT,
                                         messages=messages, temperature=temperature, max_tokens=max_tokens)
        return r.choices[0].message.content
    except Exception as e:
        return f"(Error calling Azure OpenAI: {e})"

# ────────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT (your Retell agent prompt, mirrored)
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
"""

# ────────────────────────────────────────────────────────────────────────────────
# PARSING & VERIFICATION (with flexible DOB + numeric-only account & last4 support)
# ────────────────────────────────────────────────────────────────────────────────
MONTHS = {
    "1":"january","01":"january","jan":"january","january":"january",
    "2":"february","02":"february","feb":"february","february":"february",
    "3":"march","03":"march","mar":"march","march":"march",
    "4":"april","04":"april","apr":"april","april":"april",
    "5":"may","05":"may","may":"may",
    "6":"june","06":"june","jun":"june","june":"june",
    "7":"july","07":"july","jul":"july","july":"july",
    "8":"august","08":"august","aug":"august","august":"august",
    "9":"september","09":"september","sep":"september","sept":"september","september":"september",
    "10":"october","oct":"october","october":"october",
    "11":"november","nov":"november","november":"november",
    "12":"december","dec":"december","december":"december",
}
def norm(s:str)->str: return re.sub(r"\s+"," ",s.strip().lower())

def human_dob(s:str)->str:
    s = s.strip()
    m = re.match(r"^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})$", s)  # 03/11/2000 or 3-11-2000
    if m:
        d, mo, y = m.groups()
        month = MONTHS.get(mo.lstrip("0") or mo, MONTHS.get(mo, None))
        return f"{int(d)} {month} {y}".lower() if month else s.lower()
    m2 = re.match(r"^(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})$", s, flags=re.I)
    if m2:
        d, mo, y = m2.groups()
        return f"{int(d)} {MONTHS.get(mo.lower(), mo.lower())} {y}".lower()
    return s.lower()

# NEW: normalize both sides for DOB equality (remove st/nd/rd/th, collapse spaces, lowercase)
def clean_dob_text(s: str) -> str:
    x = human_dob(s)  # ensures "3/11/2000" -> "3 november 2000"
    x = re.sub(r"\b(\d{1,2})(?:st|nd|rd|th)\b", r"\1", x)  # remove ordinals if still present
    x = re.sub(r"\s+", " ", x.strip().lower())
    return x

NAME_P  = r"(john\s*cena|sagar\s*karnik)"
LAST4_P = r"(?:last\s*4\s*digits|last\s*four|\*\*\*\*|ending\s*in|last4)\D*(\d{4})"
ACCT_P  = r"(?:account\s*number|acct\s*no\.?|a/c|account)\D*(\d{3,})"
DOB_ANY = r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}|(?:\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4}))"

def parse_identity(text:str, expect_acct:bool=False, expect_last4:bool=False):
    """
    When expect_acct=True, accept a digits-only message as account number.
    When expect_last4=True, accept a 4-digit-only message as last-4.
    """
    t = text.strip()
    tl = t.lower()

    name = re.search(NAME_P, tl)
    last4 = re.search(LAST4_P, tl)
    if expect_last4 and not last4:
        last4 = re.match(r"^\s*(\d{4})\s*$", t)  # accept plain 4 digits
    acct = re.search(ACCT_P, tl)
    if expect_acct and not acct:
        acct = re.match(r"^\s*(\d{5,})\s*$", t)  # accept plain digits for account

    dobm = re.search(DOB_ANY, t, flags=re.I)

    return (" ".join(name.group(1).split()) if name else None,
            last4.group(1) if last4 else None,
            human_dob(dobm.group(1)) if dobm else None,
            acct.group(1) if acct else None)

def verify(name,last4,dob):
    if not name or not last4 or not dob:
        missing=[]
        if not name: missing.append("full name")
        if not last4: missing.append("last 4 digits")
        if not dob: missing.append("date of birth")
        return False,"For security, please provide your "+", ".join(missing)+".",None
    rec = CUSTOMERS.get(name)
    if not rec:
        return False,"I couldn’t find that customer. Please re-enter your full name exactly as on the account.",None
    issues=[]
    if last4 != rec["last4"]: issues.append("last 4 digits")
    # UPDATED: compare normalized DOBs (handles 3/11/2000 vs 3rd November 2000)
    if clean_dob_text(dob) != clean_dob_text(rec["dob"]): issues.append("date of birth")
    if issues:
        return False,f"Hmm, the {', '.join(issues)} don’t match our records. Could you check and try again?",None
    return True,f"Thanks {rec['name']}, you’re verified.",rec

# ────────────────────────────────────────────────────────────────────────────────
# STATE (FSM) + INIT
# ────────────────────────────────────────────────────────────────────────────────
def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages=[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"assistant","content":"Hello! This is Sam from Bank of Shash. How can I assist you today?"}
        ]
    if "verif" not in st.session_state:
        st.session_state.verif={"step":"await_name","name":None,"acct":None,"last4":None,"dob":None,
                                "tries":0,"ok":False,"record":None}
init_state()

# ────────────────────────────────────────────────────────────────────────────────
# HEADER + TICKER
# ────────────────────────────────────────────────────────────────────────────────
hl, hr = st.columns([0.75,0.25])
with hl:
    st.markdown(f"""
      <div style="display:flex;gap:14px;align-items:center;">
        <div style="width:46px;height:46px;background:{ACCENT};border-radius:12px;"></div>
        <div class="headline">Bank of Shash — Customer Support</div>
        <span class="pill">● Live</span>
      </div>""", unsafe_allow_html=True)
with hr:
    st.markdown(f'<div style="text-align:right;"><a class="pill" href="tel:{PHONE_NUMBER}">📞 {PHONE_NUMBER}</a></div>',
                unsafe_allow_html=True)

st.markdown(f"""
<div class="ticker-wrap"><div class="ticker">
🌱 We have introduced <b>Green Mortgage</b> with preferential rates for energy-efficient homes —
<a href="#" onclick="return false;">click here to learn more</a> or call <a href="tel:{PHONE_NUMBER}">{PHONE_NUMBER}</a>.
&nbsp;&nbsp;|&nbsp;&nbsp; 💡 Ask in chat: “Tell me about Green Mortgage eligibility.”
</div></div>""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────────────────
# LEFT: ACTIONS + RICH CONTENT
# ────────────────────────────────────────────────────────────────────────────────
left, right = st.columns([0.52,0.48])

with left:
    st.markdown('<div class="card"><div style="font-weight:800;font-size:1.15rem;">Help Center</div><div class="soft" style="margin-top:4px;">Choose a quick action or ask in chat.</div></div>', unsafe_allow_html=True)
    a,b,c = st.columns(3)
    with a:
        if st.button("Report Lost/Stolen", use_container_width=True):
            st.session_state.messages.append({"role":"user","content":"I lost my card."}); st.rerun()
    with b:
        if st.button("Check Balance", use_container_width=True):
            st.session_state.messages.append({"role":"user","content":"What's my account balance?"}); st.rerun()
    with c:
        if st.button("Green Mortgage", use_container_width=True):
            st.session_state.messages.append({"role":"user","content":"Tell me about Green Mortgage eligibility and rates."}); st.rerun()

    # Products
    st.markdown(f"""
    <div class="card" style="margin-top:14px;">
      <div style="font-weight:800;font-size:1.15rem;">Personal Banking Products</div>
      <div class="soft">Explore our most popular services.</div>
      <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:12px;">
        <div style="background:#0d1526;border:1px solid {BORDER};border-radius:14px;padding:12px;">
          <div style="font-weight:700;">Current Account</div><div class="soft">No monthly fees with minimum balance. Instant notifications.</div>
        </div>
        <div style="background:#0d1526;border:1px solid {BORDER};border-radius:14px;padding:12px;">
          <div style="font-weight:700;">Savings Plus</div><div class="soft">Competitive variable rate, flexible withdrawals.</div>
        </div>
        <div style="background:#0d1526;border:1px solid {BORDER};border-radius:14px;padding:12px;">
          <div style="font-weight:700;">Visa Credit Card</div><div class="soft">0% FX fees for first 90 days on online purchases.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Loans & Mortgages
    st.markdown(f"""
    <div class="card" style="margin-top:14px;">
      <div style="font-weight:800;font-size:1.15rem;">Loans & Mortgages</div>
      <div class="soft">Financing built for you.</div>
      <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:12px;">
        <div style="background:#0e1b2a;border:1px solid {BORDER};border-radius:14px;padding:12px;">
          <div style="font-weight:700;">Green Mortgage</div><div class="soft">Preferential rates for energy-efficient homes (BER A/B).</div>
        </div>
        <div style="background:#0e1b2a;border:1px solid {BORDER};border-radius:14px;padding:12px;">
          <div style="font-weight:700;">Car Loan</div><div class="soft">Fixed low rates, decision in minutes.</div>
        </div>
        <div style="background:#0e1b2a;border:1px solid {BORDER};border-radius:14px;padding:12px;">
          <div style="font-weight:700;">Student Loan</div><div class="soft">Flexible repayments while you study.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Digital + Security
    st.markdown(f"""
    <div class="card" style="margin-top:14px;">
      <div style="font-weight:800;font-size:1.15rem;">Digital Banking</div>
      <ul class="soft" style="margin-top:8px;">
        <li>Biometric login & virtual cards</li>
        <li>Instant transfers & bill payments</li>
        <li>Spending insights and budgeting</li>
      </ul>
      <hr style="border-color:{BORDER};">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div style="font-weight:800;">Security Center</div>
        <div class="pill">● Systems Operational</div>
      </div>
      <div class="soft" style="margin-top:6px;">Never share full card numbers, passwords or OTPs. We’ll never ask for them.</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Frequently Used Forms"):
        st.markdown("- **Dispute a Card Transaction** — PDF form")
        st.markdown("- **Address Change** — Online form")
        st.markdown("- **Close/Reopen Account** — Online form")

    with st.expander("FAQs"):
        st.markdown("- **How do I freeze my card?** Use chat to confirm identity or call our agent. We can freeze instantly.")
        st.markdown("- **What are branch hours?** 9 AM – 5 PM GMT.")
        st.markdown("- **Green Mortgage?** Preferential rates for energy-efficient homes (BER A/B).")

# ────────────────────────────────────────────────────────────────────────────────
# RIGHT: CHAT (clean rerun pattern)
# ────────────────────────────────────────────────────────────────────────────────
with right:
    st.markdown(f"""
    <div class="card" style="margin-bottom:10px;">
      <div style="display:flex;align-items:center;justify-content:space-between;">
        <div style="font-weight:800;font-size:1.15rem;">💬 Secure Chat</div>
        <a class="pill" href="tel:{PHONE_NUMBER}">Or call {PHONE_NUMBER}</a>
      </div>
      <div class="soft">Do not share full card numbers or passwords. Answers in GMT. Branch hours: 9 AM – 5 PM GMT.</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)

    # Render history (skip system)
    for m in st.session_state.messages[1:]:
        with st.chat_message("assistant" if m["role"]=="assistant" else "user"):
            st.write(m["content"])

    user_text = st.chat_input("Type your message…")

    if user_text:
        st.session_state.messages.append({"role":"user","content":user_text})

        v = st.session_state.verif
        # parse with awareness of current step, so digits-only works for account and last-4
        name, last4, dob, acct = parse_identity(
            user_text,
            expect_acct=(v["step"]=="await_acct"),
            expect_last4=(v["step"]=="await_last4"),
        )
        if name: v["name"]=name
        if acct: v["acct"]=acct
        if last4: v["last4"]=last4
        if dob: v["dob"]=dob

        reply = None
        # FSM verification — NEVER call the model during verification
        if not v["ok"]:
            step = v["step"]
            if step == "await_name":
                if v["name"]:
                    v["step"]="await_acct"; reply=f"Thank you, {v['name'].title()}. Can you provide your account number?"
                else:
                    reply="For security, please share your full name as on the account."
            elif step == "await_acct":
                if v["acct"]:
                    v["step"]="await_last4"; reply="Thanks. Please provide the last 4 digits of your debit card."
                else:
                    reply="Please share your account number."
            elif step == "await_last4":
                if v["last4"]:
                    # validate last-4 immediately against the named customer (if we have a name)
                    if v["name"] in CUSTOMERS and v["last4"] != CUSTOMERS[v["name"]]["last4"]:
                        v["last4"] = None
                        v["tries"] += 1
                        reply = ("Hmm, the last 4 digits don’t match our records. Could you check and try again?"
                                 if v["tries"] < 2 else
                                 "I’m sorry, I can’t verify your account right now. Please contact Bank of Shash support staff for further help.")
                    else:
                        v["step"]="await_dob"; reply="Got it. Finally, please provide your date of birth."
                else:
                    reply="Please provide the last 4 digits of your debit card."
            elif step == "await_dob":
                # At DOB stage, last-4 already validated
                if v["dob"] and v["last4"] and v["name"]:
                    ok, msg, rec = verify(v["name"], v["last4"], v["dob"])
                    if ok:
                        v["ok"]=True; v["record"]=rec; v["step"]="verified"; reply=f"{msg} How can I help you today?"
                    else:
                        # If DOB wrong, keep asking DOB; if name wrong (rare), restart at name
                        if "date of birth" in msg:
                            reply = "That date of birth doesn’t match our records. Please check and enter it again."
                        else:
                            v["step"] = "await_name"
                            reply = "I couldn’t find that customer. Please enter your full name exactly as on the account."
                else:
                    reply="Please provide your date of birth."

        # After verification, handle intents locally
        if v["ok"] and reply is None:
            rec = v["record"]; low = user_text.lower()
            if "balance" in low:
                reply = f"Your balance is €{CUSTOMERS[rec['name'].lower()]['balance']:.0f}."
            elif "lost" in low or "stolen" in low or ("block" in low and "card" in low):
                if rec["name"] == "John Cena":
                    reply = ("I’m really sorry to hear about your card. That can be stressful — let’s take care of this together.\n\n"
                             "Looking at your recent activity… I see your last transaction was on Camden Street, at O’Brian’s Pub.\n"
                             f"While we’re checking if it was left behind, I’ve secured your account. Your card ending {rec['last4']} is now blocked and a replacement has been ordered.")
                else:
                    reply = ("I’m really sorry to hear about this — fraud concerns are serious. Let’s work through this together. "
                             "I’ll block your card, monitor unusual activity, and order a replacement if needed. Your funds are protected.")
            elif "mortgage" in low:
                reply = ("Our Green Mortgage offers preferential rates for energy-efficient homes. "
                         f"I can book you with an advisor, or you can call us at {PHONE_NUMBER}.")
            elif "appointment" in low or "book" in low:
                reply = ("Happy to help with an appointment. Please share your first name, email, and account type. "
                         "I’ll check availability and confirm or offer two alternative slots.")

        # General Q&A only when non-sensitive or verified
        if reply is None:
            sensitive = any(k in user_text.lower() for k in ["balance","card","lost","stolen","fraud","account"])
            if (not sensitive) or v["ok"]:
                out = ask_gpt(st.session_state.messages)
                reply = out if not out.startswith("(") else f"I can help here, or you can call {PHONE_NUMBER}."
            else:
                reply = "For security, please complete verification first."

        st.session_state.messages.append({"role":"assistant","content":reply})
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("<hr style='border-color:#1f2937;'>", unsafe_allow_html=True)
st.caption(f"© Bank of Shash — Secure support. Never share full PINs or passwords in chat. • Voice agent: {PHONE_NUMBER}")
