import streamlit as st
import json
import google.generativeai as genai
from PIL import Image

# Page Configuration
st.set_page_config(page_title="Gas Station Invoice Scanner", page_icon="⛽", layout="centered")

st.title("⛽ Gas Station Auto-Pricing Scanner")
st.write("Snap or upload a photo of your invoice. The app will extract line items, calculate unit costs, and apply your target margin automatically.")

# Sidebar Settings for Margins
st.sidebar.header("Pricing Settings")
default_margin = st.sidebar.slider("Target Profit Margin (%)", min_value=1.0, max_value=50.0, value=15.0, step=0.5)
target_margin = default_margin / 100.0

# Initialize Gemini API (Uses Streamlit secrets or allows direct entry)
api_key = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Enter Google Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # Using Gemini Flash for fast multimodal extraction
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    st.warning("Please enter your Google Gemini API Key in the sidebar to start scanning invoices.")

# Image Upload (Supports phone cameras directly)
uploaded_file = st.file_uploader("Take a photo or upload invoice image", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file and api_key:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Invoice", use_column_width=True)
    
    if st.button("🚀 Process Invoice & Calculate Prices", type="primary"):
        with st.spinner("AI is reading your invoice and computing margins..."):
            try:
                prompt = """
                Analyze this invoice image for a gas station. Extract all line items.
                Return ONLY a valid JSON array (no markdown code blocks, just raw JSON text) with objects containing:
                - "item_name": string (e.g., "Regular Unleaded", "Diesel", "Red Bull 12oz")
                - "quantity": number (total gallons or unit count purchased)
                - "total_cost": number (total dollar amount paid for this line item)
                """
                
                response = model.generate_content([prompt, image])
                
                # Clean up response text to ensure pure JSON loading
                raw_text = response.text.replace("```json", "").replace("```", "").strip()
                items = json.loads(raw_text)
                
                processed_data = []
                for item in items:
                    qty = float(item.get("quantity", 1))
                    total = float(item.get("total_cost", 0))
                    
                    # Core Gas Station Math Formulas
                    unit_cost = (total / qty) if qty > 0 else 0
                    # Margin-based pricing: Price = Cost / (1 - Margin%)
                    selling_price = unit_cost / (1 - target_margin) if target_margin < 1 else unit_cost
                    profit_per_unit = selling_price - unit_cost
                    
                    processed_data.append({
                        "Item / Fuel": item.get("item_name"),
                        "Quantity / Gallons": qty,
                        "Total Cost ($)": round(total, 2),
                        "Unit Cost ($)": round(unit_cost, 3),
                        "Selling Price ($)": round(selling_price, 3),
                        "Profit / Unit ($)": round(profit_per_unit, 3)
                    })
                
                st.success("Invoice successfully processed!")
                st.subheader("📊 Calculated Pricing Breakdown")
                st.table(processed_data)
                
            except Exception as e:
                st.error(f"Could not parse the invoice automatically. Error: {e}")
