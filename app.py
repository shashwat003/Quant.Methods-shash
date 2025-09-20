# app.py — Bank of Shash • Business Support (Streamlit, dark professional UI)
import os
import time
import streamlit as st

# =========================
# PAGE & THEME CONFIG
# =========================
st.set_page_config(
    page_title="Bank of Shash • Business Banking Support",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---- Color palette (professional dark) ----
BG_DARK     = "#0b1220"  # page background (deep navy)
PANEL_DARK  = "#0f172a"  # card bg (slate-900)
BORDER      = "#1e293b"  # card border (slate-800)
TEXT_MAIN   = "#e5e7eb"  # text (slate-200)
TEXT_SOFT   = "#94a3b8"  # muted text (slate-400)
PRIMARY     = "#22d3ee"  # cyan-400
PRIMARY_D   = "#06b6d4"  # cyan-500
ACCENT      = "#7c3aed"  # violet-600
GOOD        = "#22c55e"  # green-500
BAD         = "#ef4444"  # red-500
PILL_BG     = "#0b3b38"  # deep teal for little pills

# =========================
# HARD-CODED AZURE OPENAI
# =========================
AZURE_OPENAI_ENDPOINT    = "https://testaisentiment.openai.azure.com/"
AZURE_OPENAI_API_KEY     = "cb1c33772b3c4edab77db69ae18c9a43"
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
AZURE_OPENAI_DEPLOYMENT  = "aipocexploration"

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
      .stButton>button {{
        background: linear-gradient(180deg, {PRIMARY} 0%, {PRIMARY_D} 100%);
        color: #001016;
        font-weight: 700;
        border: 0;
        border-radius: 12px;
        padding: 0.6rem 1rem;
        box-shadow: 0 6px 20px rgba(34,211,238,0.18);
      }}
      .pill {{
        display:inline-flex; align-items:center; gap:8px;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 0.85rem;
        background: #0b3b38;
        color: {PRIMARY};
        border: 1px solid #0e4b48;
      }}
      .card {{
        background: {PANEL_DARK};
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 18px;
        box-shadow: 0 12px 40px rgba(2,6,23,0.45);
      }}
      .headline {{
        font-size: 1.95rem; font-weight: 800; letter-spacing:-0.02em;
      }}
      .soft {{
        color: {TEXT_SOFT};
      }}
      .kpi {{ font-size: 2.0rem; font-weight: 800; }}
      .good {{ color: {GOOD}; }}
      .bad {{ color: {BAD}; }}
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
      /* chat message colors (dark mode friendly) */
      .stChatMessage .stMarkdown p {{ color: {TEXT_MAIN}; }}
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
        return ("(Model not configured. Please hard-code AZURE settings at the top "
                "or provide valid credentials.)")
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
top_l, top_r = st.columns([0.75, 0.25])
with top_l:
    st.markdown(
        f"""
        <div style="display:flex; gap:14px; align-items:center;">
          <div class="headline">Business Banking Support</div>
          <span class="pill">● Live Data</span>
          <span class="soft">Senior Business Support</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with top_r:
    st.markdown(
        '<div style="text-align:right;"><a href="tel:+35345933308" class="pill">📞 Call +35345933308</a></div>',
        unsafe_allow_html=True,
    )

# =========================
# MOVING UPDATE (Ticker)
# =========================
st.markdown(
    """
    <div class="ticker-wrap">
      <div class="ticker">
        🌱 We have introduced <b>Green Mortgage</b> with preferential rates for energy-efficient homes —
        <a href="https://bankofshash.example/green-mortgage" target="_blank">click here to learn more</a>
        or call <a href="tel:+35345933308">+35345933308</a> to talk to our agent.
        &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
        🌍 Financing a renovation? Ask our agent about **Home Energy Upgrade** bundles.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================
# CUSTOMER HEADER CARD
# =========================
st.markdown(
    f"""
    <div class="card" style="padding:22px; margin-bottom:14px;">
      <div style="display:flex; align-items:center; gap:16px; flex-wrap:wrap;">
        <div style="width:44px; height:44px; background:{ACCENT}; border-radius:12px;"></div>
        <div>
          <div style="font-weight:800; font-size:1.25rem;">Lighthouse Financial Services</div>
          <div class="soft">Business ID: BIZ-789123 • Private Limited Company • Active Call: 00:04:32</div>
        </div>
        <div style="margin-left:auto; display:flex; gap:8px; align-items:center;">
          <span class="pill" title="Tier">premium Business</span>
          <span class="pill" style="color:{GOOD}">active</span>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================
# BODY LAYOUT
# =========================
left, right = st.columns([0.55, 0.45])

# --- LEFT: Social / Insights style block ---
with left:
    st.markdown(
        f"""
        <div class="card">
          <div style="display:flex; align-items:center; justify-content:space-between;">
            <div style="font-weight:800; font-size:1.15rem;">Business Social Media Intelligence</div>
            <div class="soft">● Live monitoring</div>
          </div>
          <div class="soft" style="margin-top:4px;">Corporate online presence analysis</div>

          <div style="margin-top:16px; display:grid; gap:14px;">
            <div style="display:flex; gap:12px;">
              <div style="width:26px; height:26px; border-radius:6px; background:#3b82f6;"></div>
              <div>
                <div><b>LinkedIn Business</b> <span class="soft">· 2 hours ago</span></div>
                <div class="soft">Posted about expanding AI services to healthcare sector. Received 127 likes, 23 comments.</div>
                <div class="soft">127 likes · 23 comments</div>
              </div>
            </div>

            <div style="display:flex; gap:12px;">
              <div style="width:26px; height:26px; border-radius:6px; background:#000;"></div>
              <div>
                <div><b>Twitter Business</b> <span class="soft">· 5 hours ago</span></div>
                <div class="soft">Announced partnership with TechCorp for advanced AI solutions. #AI #Innovation</div>
                <div class="soft">89 likes · 45 retweets</div>
              </div>
            </div>

            <div style="display:flex; gap:12px;">
              <div style="width:26px; height:26px; border-radius:6px; background:#8b5cf6;"></div>
              <div>
                <div><b>Website Analytics</b> <span class="soft">· Last 24h</span></div>
                <div style="display:flex; gap:22px; margin-top:6px;">
                  <div><div class="kpi">2.4K</div><div class="soft">Visits</div></div>
                  <div><div class="kpi">18</div><div class="soft">Leads</div></div>
                  <div><div class="kpi">7</div><div class="soft">Demos</div></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- RIGHT: Chat + Products teaser ---
with right:
    # Products panel
    st.markdown(
        f"""
        <div class="card" style="margin-bottom:14px;">
          <div style="display:flex; align-items:center; justify-content:space-between;">
            <div style="font-weight:800; font-size:1.15rem;">Business Banking Products</div>
            <div class="soft">$0 <span class="soft">Total Portfolio</span></div>
          </div>
          <div class="soft">Commercial accounts & services</div>

          <div style="margin-top:10px;">
            <div class="soft" style="font-weight:700;">Recent Transactions</div>
            <div style="margin-top:6px; display:grid; gap:6px;">
              <div style="display:flex; justify-content:space-between;">
                <span>TechCorp Invoice Payment</span><span class="bad">-$125,000</span>
              </div>
              <div style="display:flex; justify-content:space-between;">
                <span>Client Deposit - MedCorp</span><span class="good">+$89,500</span>
              </div>
              <div style="display:flex; justify-content:space-between;">
                <span>Office Rent Payment</span><span class="bad">-$15,000</span>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Chat panel
    st.markdown(
        f"""
        <div class="card">
          <div style="display:flex; align-items:center; justify-content:space-between;">
            <div style="font-weight:800; font-size:1.15rem;">💬 Secure Chat</div>
            <a href="tel:+35345933308" class="pill">Or Call +35345933308</a>
          </div>
          <div class="soft">This assistant follows your Retell AI prompt and can hand off to phone support.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Chat engine (below the styled header)
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system",
             "content": ("You are the Bank of Shash virtual assistant. Be concise, friendly, and professional. "
                         "Verify identity before account-specific help. Never ask for full card/PIN. "
                         "Offer phone handoff at +35345933308 when appropriate.")},
            {"role": "assistant", "content": "Hi! I'm your Bank of Shash assistant. How can I help today?"}
        ]

    # render chat history (skip system in visible UI)
    for m in st.session_state.messages[1:]:
        with st.chat_message("assistant" if m["role"] == "assistant" else "user"):
            st.write(m["content"])

    user_text = st.chat_input("Type your message…")
    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.write(user_text)

        # generate reply
        try:
            reply = ask_gpt(st.session_state.messages)
            if reply.startswith("(Model not configured") or reply.startswith("(Error"):
                # graceful fallback messages
                if "lost" in user_text.lower() and "card" in user_text.lower():
                    reply = ("I’m sorry to hear that. I can help you block your card now after verification, "
                             "or you can call our automated agent at +35345933308 for immediate action.")
                else:
                    reply = ("I can help here, or you can reach the phone agent at +35345933308. "
                             "For account-specific help I’ll need to verify your identity.")
        except Exception as e:
            reply = f"Something went wrong. Please try again or call +35345933308. ({e})"

        st.session_state.messages.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.write(reply)

# =========================
# FOOTER
# =========================
st.markdown("<hr style='border-color:#1f2937;'>", unsafe_allow_html=True)
st.caption("© Bank of Shash — Secure support. Never share full PINs or passwords in chat.  •  Voice agent: +35345933308")
