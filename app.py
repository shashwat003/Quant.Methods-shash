# Quant Methods for Finance — one-file Streamlit app
# --------------------------------------------------
# How to run (Windows, PowerShell):
#   python -m venv .venv
#   .\.venv\Scripts\activate
#   pip install -r requirements.txt
#   setx AZURE_OPENAI_ENDPOINT "https://testaisentiment.openai.azure.com/"
#   setx AZURE_OPENAI_API_KEY "cb1c33772b3c4edab77db69ae18c9a43"
#   setx AZURE_OPENAI_API_VERSION "2024-02-15-preview"
#   setx AZURE_OPENAI_DEPLOYMENT "aipocexploration"
#   streamlit run app.py
#
# On Streamlit Cloud: put the AZURE_* values in "Settings → Secrets".

import os
import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Optional: SciPy/SymPy if available
try:
    from scipy import stats
except Exception:
    stats = None

try:
    import sympy as sp
except Exception:
    sp = None

# -------------------- Azure OpenAI (no hardcoded secrets) --------------------
OPENAI_OK = False
deployment = None
client = None
try:
    from openai import AzureOpenAI
    endpoint    = os.getenv("AZURE_OPENAI_ENDPOINT")    or "https://testaisentiment.openai.azure.com/"
    api_key     = os.getenv("AZURE_OPENAI_API_KEY")     or "cb1c33772b3c4edab77db69ae18c9a43"
    api_version = os.getenv("AZURE_OPENAI_API_VERSION") or "2024-02-15-preview"
    deployment  = os.getenv("AZURE_OPENAI_DEPLOYMENT")  or st.secrets.get("aipocexploration")

    if endpoint and api_key and deployment:
        client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_version)
        OPENAI_OK = True
except Exception:
    OPENAI_OK = False

def gpt_tutor(messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
    if not OPENAI_OK:
        return "(Azure OpenAI not configured. Add AZURE_* settings to use the tutor.)"
    try:
        resp = client.chat.completions.create(
            model=model or deployment, temperature=0.2, messages=messages
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"(Tutor error: {e})"

# ----------------------------- Streamlit config ------------------------------
st.set_page_config(page_title="Quant Methods for Finance", page_icon="📈", layout="wide")
st.title("📈 Quant Methods for Finance")
st.caption("Basics → Intermediate → Advanced, with interactive labs and an optional GPT tutor.")

# ------------------------------ Helper functions -----------------------------
def ear_to_periodic(ear: float, m: int) -> float:
    return (1 + ear) ** (1 / m) - 1

def annuity_payment(P: float, i: float, n: int) -> float:
    if i == 0: return P / n
    return P * (i * (1 + i) ** n) / ((1 + i) ** n - 1)

def annuity_pv(A: float, i: float, n: int) -> float:
    if i == 0: return A * n
    return A * (1 - (1 + i) ** (-n)) / i

def annuity_fv(A: float, i: float, n: int) -> float:
    if i == 0: return A * n
    return A * ((1 + i) ** n - 1) / i

def perpetuity_pv(C: float, r: float) -> float:
    return float("inf") if r <= 0 else C / r

def bond_price(face: float, coupon_rate: float, y: float, n_years: int, m: int = 2) -> float:
    c = face * coupon_rate / m
    i = y / m
    N = n_years * m
    pv_c = sum(c / (1 + i) ** t for t in range(1, N + 1))
    pv_f = face / (1 + i) ** N
    return pv_c + pv_f

def amortization_schedule(P: float, i: float, n: int) -> pd.DataFrame:
    A = annuity_payment(P, i, n)
    rows, bal = [], P
    for t in range(1, n + 1):
        interest = bal * i
        principal = A - interest
        bal = max(0.0, bal - principal)
        rows.append(dict(Period=t, Payment=A, Interest=interest, Principal=principal, Balance=bal))
    return pd.DataFrame(rows)

def t_test_greater(sample: np.ndarray, mu0: float) -> Tuple[float, int]:
    n = len(sample)
    m = float(np.mean(sample))
    s = float(np.std(sample, ddof=1))
    t = (m - mu0) / (s / math.sqrt(n))
    return t, n - 1

def ols(y: np.ndarray, X: np.ndarray):
    if X.ndim == 1: X = X.reshape(-1, 1)
    X = np.column_stack([np.ones(len(X)), X])
    beta = np.linalg.inv(X.T @ X) @ (X.T @ y)
    yhat = X @ beta
    resid = y - yhat
    n, k = X.shape
    s2 = (resid @ resid) / (n - k)
    covb = s2 * np.linalg.inv(X.T @ X)
    stderr = np.sqrt(np.diag(covb))
    R2 = 1 - (resid @ resid) / np.sum((y - np.mean(y)) ** 2)
    return dict(beta=beta, stderr=stderr, R2=R2)

# ------------------------------- Navigation tabs -----------------------------
tabs = st.tabs(["🏠 Home", "📚 Learn", "🧮 TVM Lab", "📉 Regression Lab", "📝 Exam Mode", "🤖 GPT Tutor"])

# ------------------------------- Home ---------------------------------------
with tabs[0]:
    st.subheader("Welcome")
    st.write(
        "Use **Learn** to read the plain-English explanations, then try the **Labs**, and finally test yourself in **Exam Mode**."
    )
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Calculus", "Rates & Taylor")
    col2.metric("Algebra/TVM", "Annuities & Bonds")
    col3.metric("Prob & Stats", "t-tests & CLT")
    col4.metric("Linear Algebra", "Systems & PD")

# ------------------------------- Learn --------------------------------------
with tabs[1]:
    st.subheader("Learn (Basic → Intermediate → Advanced)")
    topic = st.selectbox("Topic", ["Calculus", "Algebra / TVM", "Probability & Statistics", "Linear Algebra"])
    level = st.radio("Level", ["Basic", "Intermediate", "Advanced"], horizontal=True)

    explanations: Dict[str, Dict[str, str]] = {
        "Calculus|Basic": dict(
            explain="Derivatives measure instantaneous change (like speed). Integrals accumulate small pieces (like area).",
            example="Example: If V(t)=100(1.02)^t, then V'(t)=100(1.02)^t ln(1.02).",
        ),
        "Calculus|Intermediate": dict(
            explain="Optimization: set derivative to 0, check curvature. Taylor approx gives quick re-pricing around a rate.",
            example="PV(r)≈PV(r0)+PV'(r0)(r−r0) with PV'(r0)=−∑ t·CF_t/(1+r0)^{t+1}.",
        ),
        "Calculus|Advanced": dict(
            explain="Continuous compounding: e^{rt}. Simple ODE dS/dt=rS → S(t)=S0 e^{rt}.",
            example="Duration links price sensitivity to small yield moves.",
        ),
        "Algebra / TVM|Basic": dict(
            explain="Geometric series → annuity formulas. Logs turn products into sums (log-returns).",
            example="PV of level A for n periods at rate i is A[1−(1+i)^{-n}]/i.",
        ),
        "Algebra / TVM|Intermediate": dict(
            explain="APR vs EAR and amortization schedules.",
            example="Payment = P * [ i(1+i)^n / ((1+i)^n − 1) ].",
        ),
        "Algebra / TVM|Advanced": dict(
            explain="Perpetuity PV=C/r; growing perpetuity PV=C1/(r−g); deferred streams discount back.",
            example="Deferred perpetuity starting in k years: (C/r)/(1+r)^{k-1}.",
        ),
        "Probability & Statistics|Basic": dict(
            explain="Expectation = average; variance = spread. We estimate, test, and build simple regressions.",
            example="Uniform[a,b]: E=(a+b)/2, Var=(b−a)^2/12.",
        ),
        "Probability & Statistics|Intermediate": dict(
            explain="Normal/CLT, confidence intervals, one-sample t-tests.",
            example="t=(m−m0)/(s/√n) and compare to t_{n−1,α}.",
        ),
        "Probability & Statistics|Advanced": dict(
            explain="OLS: R=α+βMKT+ε; test β=1 or α=0; interpret R² & SEs.",
            example="Run OLS on excess returns; use t-tests for β significance.",
        ),
        "Linear Algebra|Basic": dict(
            explain="Vectors/matrices solve systems: Ax=b.",
            example="x=A^{-1}b when A is invertible.",
        ),
        "Linear Algebra|Intermediate": dict(
            explain="Determinant, rank, eigenvalues; covariance matrices are PSD.",
            example="Var(port)=w'Σw; Σ should be PSD.",
        ),
        "Linear Algebra|Advanced": dict(
            explain="Positive-definiteness via eigenvalues >0 or Cholesky; PCA reduces dimension.",
            example="Σ=QΛQ' → uncorrelated PCs ordered by variance.",
        ),
    }
    box = explanations.get(f"{topic}|{level}")
    st.write(f"**{level} — {topic}**")
    st.write(box["explain"])
    st.info(box["example"])

# ------------------------------- TVM Lab ------------------------------------
with tabs[2]:
    st.subheader("Time Value of Money Lab")
    sub = st.tabs(["Loan Payment & Schedule", "Savings (FV)", "Bond Pricing", "Perpetuity/Deferred"])
    # Loan
    with sub[0]:
        P   = st.number_input("Loan Principal (P)", value=250000.0, step=1000.0)
        apr = st.number_input("APR (annual, %)", value=6.0, step=0.1)/100
        m   = st.number_input("Payments per year m", value=12, step=1, min_value=1)
        years = st.number_input("Years", value=30, step=1, min_value=1)
        use_ear = st.checkbox("Treat APR as EAR (convert)", value=False)
        i = ear_to_periodic(apr, int(m)) if use_ear else apr/int(m)
        N = int(m)*int(years)
        A = annuity_payment(P, i, N)
        st.metric("Payment per period", f"{A:,.2f}")
        df = amortization_schedule(P, i, N)
        st.dataframe(df.head(12))
        st.download_button("Download full schedule (CSV)", df.to_csv(index=False).encode(), "amortization.csv")
        fig, ax = plt.subplots()
        ax.plot(df["Period"], df["Balance"])
        ax.set_xlabel("Period"); ax.set_ylabel("Balance"); ax.set_title("Outstanding Balance")
        st.pyplot(fig)
    # Savings
    with sub[1]:
        A = st.number_input("Contribution per period (A)", value=500.0, step=10.0)
        i = st.number_input("Periodic rate i", value=0.004, format="%f")
        n = st.number_input("# periods n", value=120, step=1)
        st.metric("Future Value", f"{annuity_fv(A, i, int(n)):,.2f}")
    # Bond
    with sub[2]:
        face = st.number_input("Face value", value=1000.0)
        coupon = st.number_input("Annual coupon rate (%)", value=5.0)/100
        y = st.number_input("Yield to maturity (%)", value=6.0)/100
        yrs = st.number_input("Years to maturity", value=5, step=1)
        m   = st.number_input("Coupons per year", value=2, step=1, min_value=1)
        st.metric("Bond Price", f"{bond_price(face, coupon, y, int(yrs), int(m)):,.2f}")
    # Perpetuity
    with sub[3]:
        C = st.number_input("Cash flow (C)", value=50.0)
        r = st.number_input("Discount rate (r)", value=0.05)
        k = st.number_input("Deferral (years until first payment)", value=1, step=1, min_value=1)
        pv_now = perpetuity_pv(C, r) / (1 + r) ** (int(k) - 1)
        st.metric("PV Today", f"{pv_now:,.2f}")

# --------------------------- Regression Lab (OLS) ----------------------------
with tabs[3]:
    st.subheader("Regression Lab (CAPM-style OLS)")
    sample = "x,y\n0.010,0.076\n0.076,0.125\n-0.111,-0.044\n0.005,-0.012\n0.229,0.304\n0.028,0.100"
    raw = st.text_area("Paste CSV with columns x (market excess) and y (asset excess):", value=sample, height=160)
    from io import StringIO
    try:
        df = pd.read_csv(StringIO(raw))
        st.dataframe(df)
        if st.button("Run OLS"):
            res = ols(df["y"].values, df["x"].values)
            b0, b1 = res["beta"]
            se0, se1 = res["stderr"]
            st.write(f"Model: y = {b0:.4f} + {b1:.4f} x")
            st.write(f"StdErr: se(alpha)={se0:.4f}, se(beta)={se1:.4f}")
            st.write(f"R² = {res['R2']:.4f}")
            # Plot
            fig, ax = plt.subplots()
            xs = np.linspace(df["x"].min(), df["x"].max(), 100)
            ax.scatter(df["x"], df["y"])
            ax.plot(xs, b0 + b1*xs)
            ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_title("OLS fit")
            st.pyplot(fig)
    except Exception as e:
        st.warning(f"Could not parse CSV: {e}")

# ------------------------------- Exam Mode -----------------------------------
with tabs[4]:
    st.subheader("Exam Mode — 5 quick questions")
    if "exam_qs" not in st.session_state:
        qs = []
        # Bond reprice
        qs.append({"q": "Price a 4-yr bond (F=1000, c=5%) at y=6% and y=8%. What’s the % change?",
                   "a": "Compute price at 6% and 8% with bond_price, then %Δ."})
        # Perpetuity
        qs.append({"q": "PV of a perpetuity C=50 at r=10%, first payment in 1 year?", "a": "PV=C/r=500."})
        # Uniform
        qs.append({"q": "Uniform[0,10]: E[X]? Var[X]?", "a": "E=5, Var=100/12≈8.333."})
        # t-test
        qs.append({"q": "One-sample right-tailed t: n=8, m=0.0025, s=0.035, H0: μ=0.01.",
                   "a": "t=(0.0025−0.01)/(0.035/√8)."})
        # Solve system
        qs.append({"q": "Solve: 2y+x+2z=10; x−z+y=12; 2z+x−2y=6.", "a": "Use elimination or inverse."})
        st.session_state.exam_qs = qs

    for i, q in enumerate(st.session_state.exam_qs, 1):
        with st.expander(f"Q{i}"):
            st.write(q["q"])
            if st.button("Reveal", key=f"rev_{i}"):
                st.info(q["a"])

# ------------------------------- GPT Tutor -----------------------------------
with tabs[5]:
    st.subheader("GPT Tutor")
    st.caption("Ask for step-by-step help. (Requires Azure OpenAI secrets.)")
    if not OPENAI_OK:
        st.warning("Azure OpenAI not detected. Set AZURE_* values to enable.")
    else:
        if "chat" not in st.session_state:
            st.session_state.chat = [
                {"role": "system", "content": "You are a friendly quant tutor. Use minimal jargon and small numeric examples."}
            ]
        for m in st.session_state.chat:
            if m["role"] == "assistant": st.chat_message("assistant").write(m["content"])
            if m["role"] == "user": st.chat_message("user").write(m["content"])
        prompt = st.chat_input("Ask about TVM, derivatives, CLT, OLS, matrices…")
        if prompt:
            st.session_state.chat.append({"role": "user", "content": prompt})
            reply = gpt_tutor(st.session_state.chat)
            st.session_state.chat.append({"role": "assistant", "content": reply})
            st.chat_message("assistant").write(reply)
