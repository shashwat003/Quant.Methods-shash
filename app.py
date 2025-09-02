import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from io import StringIO


AZURE_OPENAI_ENDPOINT    =  "https://testaisentiment.openai.azure.com/"
AZURE_OPENAI_API_KEY     =  "cb1c33772b3c4edab77db69ae18c9a43"
AZURE_OPENAI_API_VERSION =  "2024-02-15-preview"


DEPLOYMENT_NAME = "aipocexploration"  

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


def ask_gpt(messages, temperature=0.2, max_tokens=300):
    """
    Minimal helper for Azure Chat Completions.
    `DEPLOYMENT_NAME` is the Azure *deployment name* (not the model id).
    """
    if not OPENAI_OK:
        return "(Azure OpenAI client not configured. Check endpoint/key/version and deployment name.)"
    try:
        resp = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"(Error: {e})"


# ===================================
# Google Places (Restaurants) helpers
# ===================================
# Provide your key via Streamlit Secrets or env var. (Do NOT hardcode real keys.)
GOOGLE_MAPS_API_KEY = "AIzaSyCRHbWFgUuSIjOm3CgHNKq6Q8RLMKXjlKU"

def geocode_address(address: str):
    """
    Convert a free-text address (e.g., 'Dublin, Ireland') to (lat, lng) using
    Google Geocoding API. If it fails, return None.
    """
    if not GOOGLE_MAPS_API_KEY:
        return None
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": GOOGLE_MAPS_API_KEY}
    r = requests.get(url, params=params, timeout=15)
    if r.status_code != 200:
        return None
    data = r.json()
    if data.get("results"):
        loc = data["results"][0]["geometry"]["location"]
        return (loc["lat"], loc["lng"])
    return None


def nearby_restaurants(lat: float, lng: float, cuisine: str, radius_m: int = 5000):
    """
    Use Places Nearby Search to find restaurants around (lat, lng), filtered by cuisine keyword.
    """
    if not GOOGLE_MAPS_API_KEY:
        return []
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius_m,
        "type": "restaurant",
        "keyword": cuisine,
        "key": GOOGLE_MAPS_API_KEY,
    }
    r = requests.get(url, params=params, timeout=15)
    if r.status_code != 200:
        return []
    return r.json().get("results", [])


def price_level_to_text(level):
    # Google price_level: 0 (Free) to 4 (Very Expensive)
    mapping = {0: "Free", 1: "Inexpensive", 2: "Moderate", 3: "Expensive", 4: "Very Expensive"}
    if isinstance(level, int):
        return mapping.get(level, "N/A")
    return "N/A"


def filter_by_budget(restaurants, budget_eur: float):
    """
    Very rough mapping from budget to Google price_level.
    You can tweak the thresholds to your preference.
    """
    if budget_eur <= 0:
        return restaurants
    # heuristic: under 15€ → <=1, 15–30 → <=2, 30–60 → <=3, >60 → allow all
    if budget_eur <= 15:
        max_pl = 1
    elif budget_eur <= 30:
        max_pl = 2
    elif budget_eur <= 60:
        max_pl = 3
    else:
        max_pl = 4
    out = []
    for r in restaurants:
        pl = r.get("price_level")
        if pl is None or pl <= max_pl:
            out.append(r)
    return out


def recommend_with_gpt(restaurants, budget_eur: float, cuisine: str):
    """
    Ask your Azure OpenAI deployment to pick one place and say why.
    """
    short_list = [
        {
            "name": r.get("name"),
            "rating": r.get("rating"),
            "user_ratings_total": r.get("user_ratings_total"),
            "price_level": r.get("price_level"),
            "address": r.get("vicinity"),
        }
        for r in restaurants[:10]  # keep prompt short
    ]
    msg = [
        {"role": "system", "content": "You are a helpful assistant that recommends restaurants succinctly."},
        {"role": "user", "content":
            f"Given these restaurants (JSON): {short_list}\n"
            f"Recommend ONE {cuisine} option within a {budget_eur:.0f} EUR per-person budget. "
            f"Prefer higher rating and more reviews. Reply in 2-3 sentences."}
    ]
    return ask_gpt(msg, max_tokens=180)


# ======================
# Streamlit application
# ======================
st.set_page_config(page_title="Quant Methods for Finance", page_icon="📊", layout="wide")
st.title("📊 Quant Methods for Finance")
st.caption("Interactive tutor + restaurant finder for students")

tab_tutor, tab_food = st.tabs(["Your own Tutor", "🍽️ Find Restaurants"])



# --- GPT Tutor ---
with tab_tutor:
    st.subheader("GPT Tutor")
    if "chat" not in st.session_state:
        st.session_state.chat = [
            {"role": "system", "content": "You are a friendly quant tutor. Use tiny numeric examples and clear steps."}
        ]
    for m in st.session_state.chat[1:]:
        st.chat_message("assistant" if m["role"]=="assistant" else "user").write(m["content"])
    q = st.chat_input("Ask something (TVM, regression, matrices…)…")
    if q:
        st.session_state.chat.append({"role":"user","content":q})
        a = ask_gpt(st.session_state.chat)
        st.session_state.chat.append({"role":"assistant","content":a})
        st.chat_message("assistant").write(a)

# --- Restaurants ---
with tab_food:
    st.subheader("Restaurants near me")
    st.caption("Uses Google Places. Provide a location (address or 'lat,lng'), a cuisine, and a per-person budget.")

    col1, col2 = st.columns([2,1])
    with col1:
        location = st.text_input("Location", value="Dublin, Ireland")
        cuisine = st.selectbox("Cuisine", ["Any", "Italian", "Indian", "Chinese", "Mexican", "Thai", "Japanese", "Cafe", "Other"], index=1)
    with col2:
        budget = st.number_input("Budget per person (€)", min_value=0.0, value=20.0, step=1.0)
        radius_km = st.slider("Search radius (km)", 1, 30, 5)

    go = st.button("🔎 Find Restaurants")
    if go:
        if not GOOGLE_MAPS_API_KEY:
            st.error("Google Maps API key not set. Add GOOGLE_MAPS_API_KEY via Streamlit Secrets.")
        else:
            # Parse location: allow "lat,lng" or free-text address
            lat_lng = None
            if "," in location:
                try:
                    p1, p2 = location.split(",", 1)
                    lat_lng = (float(p1.strip()), float(p2.strip()))
                except Exception:
                    lat_lng = None
            if lat_lng is None:
                lat_lng = geocode_address(location)

            if not lat_lng:
                st.error("Could not resolve location. Try 'lat,lng' or a clearer address.")
            else:
                lat, lng = lat_lng
                radius_m = int(radius_km * 1000)
                query = "" if cuisine=="Any" else cuisine
                results = nearby_restaurants(lat, lng, query, radius_m=radius_m)
                results = filter_by_budget(results, budget)

                if not results:
                    st.warning("No results. Try increasing radius or changing cuisine.")
                else:
                    st.success(f"Found {len(results)} place(s).")
                    # Recommendation via GPT (optional)
                    rec = recommend_with_gpt(results, budget, cuisine if cuisine!="Any" else "general")
                    if rec and not rec.startswith("(Error"):
                        st.info(rec)

                    for r in results[:20]:
                        st.markdown("---")
                        st.markdown(f"**{r.get('name','(no name)')}**")
                        st.write(r.get("vicinity",""))
                        rating = r.get("rating", "N/A")
                        total = r.get("user_ratings_total", "N/A")
                        price_level = price_level_to_text(r.get("price_level"))
                        st.write(f"⭐ {rating} ({total} reviews) · 💲 {price_level}")
   
