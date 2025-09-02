import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from io import StringIO


AZURE_OPENAI_ENDPOINT    =  "https://testaisentiment.openai.azure.com/"
AZURE_OPENAI_API_KEY     =  "cb1c33772b3c4edab77db69ae18c9a43"
AZURE_OPENAI_API_VERSION =  "2024-02-15-preview"
GOOGLE_MAPS_API_KEY = "AIzaSyCRHbWFgUuSIjOm3CgHNKq6Q8RLMKXjlKU"

DEPLOYMENT_NAME = "aipocexploration"  

import requests

# Center of Dublin (used as a default bias if user doesn't choose IP-based)
DUBLIN_CENTRE = (53.349805, -6.26031)

def get_ip_location():
    """
    Approximate coordinates via IP (city-level). Returns (lat, lng) or None.
    """
    try:
        r = requests.get("https://ipapi.co/json/", timeout=10)
        if r.status_code == 200:
            j = r.json()
            lat, lng = j.get("latitude"), j.get("longitude")
            if lat is not None and lng is not None:
                return (float(lat), float(lng))
    except Exception:
        pass
    return None

def find_place_candidates(query: str, bias_latlng=None, radius_m: int = 30000):
    """
    Use Google Places 'Find Place From Text' with location bias to prefer
    results near 'bias_latlng'. Falls back to IP bias if no bias provided.
    Returns a list of {name, address, lat, lng}.
    """
    if not GOOGLE_MAPS_API_KEY:
        return []
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": query,
        "inputtype": "textquery",
        "fields": "name,formatted_address,geometry",
        "key": GOOGLE_MAPS_API_KEY,
    }
    if bias_latlng:
        params["locationbias"] = f"circle:{max(1000, int(radius_m))}@{bias_latlng[0]},{bias_latlng[1]}"
    else:
        params["locationbias"] = "ipbias"

    r = requests.get(url, params=params, timeout=15)
    if r.status_code != 200:
        return []

    out = []
    for c in r.json().get("candidates", []):
        loc = c.get("geometry", {}).get("location")
        if loc:
            out.append({
                "name": c.get("name"),
                "address": c.get("formatted_address"),
                "lat": loc.get("lat"),
                "lng": loc.get("lng"),
            })
    return out

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
    st.subheader("Your own Tutor")
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
# --- Restaurants ---
with tab_food:
    st.subheader("Restaurants near me")
    st.caption("Type a place (e.g., 'Blackrock'), an address, or 'lat,lng'. "
               "Use '📍 Use my current location (IP-based)' to bias results near you.")

    col1, col2 = st.columns([2,1])
    with col1:
        location = st.text_input("Location", value="Dublin, Ireland",
                                 help="Place name, address, or 'lat,lng'. Try 'Blackrock'.")
        cuisine = st.selectbox("Cuisine", ["Any", "Italian", "Indian", "Chinese", "Mexican",
                                           "Thai", "Japanese", "Cafe", "Other"], index=1)
    with col2:
        budget = st.number_input("Budget per person (€)", min_value=0.0, value=20.0, step=1.0)
        radius_km = st.slider("Search radius (km)", 1, 30, 5)

    c1, c2 = st.columns(2)
    with c1:
        go = st.button("🔎 Find Restaurants")
    with c2:
        use_ip = st.button("📍 Use my current location (IP-based)")

    # Determine bias for disambiguation: IP if chosen; otherwise Dublin center
    bias_latlng = None
    if use_ip:
        with st.spinner("Detecting your approximate location…"):
            bias_latlng = get_ip_location()
            if bias_latlng:
                st.success(f"Detected approx location: {bias_latlng[0]:.5f}, {bias_latlng[1]:.5f}")
            else:
                st.error("Couldn't detect location from IP. Using Dublin as default.")
                bias_latlng = DUBLIN_CENTRE
    else:
        bias_latlng = DUBLIN_CENTRE

    if go or use_ip:
        if not GOOGLE_MAPS_API_KEY:
            st.error("Google Maps API key not set. Add GOOGLE_MAPS_API_KEY via Streamlit Secrets.")
        else:
            # 1) Accept direct 'lat,lng'
            lat_lng = None
            if "," in location:
                try:
                    p1, p2 = location.split(",", 1)
                    lat_lng = (float(p1.strip()), float(p2.strip()))
                except Exception:
                    lat_lng = None

            # 2) Otherwise resolve free-text via Places with location bias
            candidates = []
            if lat_lng is None:
                candidates = find_place_candidates(location, bias_latlng=bias_latlng, radius_m=int(radius_km*1000))

                # If the query was ambiguous (e.g., multiple Blackrocks), let user choose
                if len(candidates) > 1:
                    st.info("Multiple places found. Please choose the correct one:")
                    labels = [f"{c['name']} — {c['address']}" for c in candidates]
                    choice = st.selectbox("Which location do you mean?", labels)
                    idx = labels.index(choice) if choice in labels else 0
                    lat_lng = (candidates[idx]["lat"], candidates[idx]["lng"])
                elif len(candidates) == 1:
                    lat_lng = (candidates[0]["lat"], candidates[0]["lng"])
                else:
                    # Final fallback: append ', Ireland'
                    fallback = find_place_candidates(location + ", Ireland",
                                                     bias_latlng=bias_latlng,
                                                     radius_m=int(radius_km*1000))
                    if fallback:
                        c = fallback[0]
                        lat_lng = (c["lat"], c["lng"])

            if not lat_lng:
                st.error("Could not resolve location. Try a clearer place name, a full address, or 'lat,lng'.")
            else:
                lat, lng = lat_lng
                radius_m = int(radius_km * 1000)
                query = "" if cuisine == "Any" else cuisine
                results = nearby_restaurants(lat, lng, query, radius_m=radius_m)
                results = filter_by_budget(results, budget)

                if not results:
                    st.warning("No results. Try increasing the radius or changing cuisine.")
                else:
                    st.success(f"Found {len(results)} place(s).")
                    rec = recommend_with_gpt(results, budget, cuisine if cuisine != "Any" else "general")
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

