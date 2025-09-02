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
    st.header("Restaurant Finder")
    st.sidebar.header("Enter Your Preferences")
    location = st.sidebar.text_input("Enter your location (latitude,longitude)", "53.349805,-6.26031")  # Default: Dublin
    cuisine = st.sidebar.selectbox("Preferred cuisine", ["Italian", "Indian", "Chinese", "Mexican", "Other"])
    budget = st.sidebar.number_input("Enter your budget (in euros)", min_value=0.0, step=0.5)
    radius = st.sidebar.slider("Search radius (meters)", 500, 50000, 50000)  # Radius default set to 50 km

    if st.sidebar.button("Find Restaurants"):
        with st.spinner("Finding the best restaurants for you..."):
            restaurants = get_nearby_restaurants(location, cuisine, radius)
            if not restaurants:
                st.error("No restaurants found. Try increasing the radius or changing the cuisine.")
            else:
                restaurant_list = [
                    {"name": r["name"], "rating": r.get("rating", "N/A"), "price_level": r.get("price_level", "N/A"), "address": r.get("vicinity", "N/A")}
                    for r in restaurants
                ]
                recommendation = get_chatgpt_recommendation(restaurant_list, budget)
                st.success("Here is our recommendation:")
                st.write(recommendation)

                st.subheader("Nearby Restaurants")
                for r in restaurant_list:
                    st.write(f"**{r['name']}**")
                    st.write(f"- Rating: {r['rating']}")
                    st.write(f"- Price Level: {r['price_level']}")
                    st.write(f"- Address: {r['address']}")
                    st.write("---")
