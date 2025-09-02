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


def nearby_restaurants(location, cuisine, radius=50000):  # Radius set to 50 km
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": location,  # Format: "latitude,longitude"
        "radius": radius,  # Radius in meters
        "type": "restaurant",
        "keyword": cuisine,
        "key": google_api_key,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    else:
        return []

# Function to analyze and recommend using ChatGPT
def get_chatgpt_recommendation(restaurants, budget):
    message_text = [
        {"role": "system", "content": "You are an expert in financial advice and restaurant recommendations."},
        {"role": "user", "content": f"Here is a list of restaurants: {restaurants}. Recommend the best restaurant within a budget of {budget} euros, considering ratings and price level."}
    ]
    try:
        response = openai_client.chat.completions.create(
            model="aipocexploration",  # Use the model you’ve deployed in Azure OpenAI
            messages=message_text,
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

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
   
