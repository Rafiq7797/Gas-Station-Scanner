import streamlit as st
import json
import google.generativeai as genai
import pandas as pd
from PIL import Image

# Page Configuration
st.set_page_config(page_title="Gas Station Invoice Scanner", page_icon="⛽", layout="centered")

st.title("⛽ Gas Station Auto-Pricing & Margin Calculator")
st.write("Snap or upload a photo of your invoice. The app extracts costs automatically and lets you enter selling prices to compute your exact margin %.")

# Initialize Gemini API (Uses Streamlit secrets or sidebar input)
api_key = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Enter Google Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.8-flash')
else:
    st.warning("Please enter your Google Gemini API Key in the sidebar to start scanning invoices.")

# Image Upload
uploaded_file = st.file_uploader("Take a photo or upload invoice image", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file and api_key:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Invoice", use_column_width=True)
    
    if st.button("🚀 Process Invoice", type="primary"):
        with st.spinner("AI is reading your invoice..."):
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
                
                extracted_data = []
                for item in items:
                    qty = float(item.get("quantity", 1))
                    total = float(item.get("total_cost", 0))
                    unit_cost = (total / qty) if qty > 0 else 0
                    
                    extracted_data.append({
                        "Item / Fuel": item.get("item_name"),
                        "Quantity / Gallons": qty,
                        "Total Cost ($)": round(total, 2),
                        "Unit Cost ($)": round(unit_cost, 3),
                        # Default suggested selling price with a 15% starting margin
                        "Selling Price ($)": round(unit_cost / 0.85, 2) if unit_cost > 0 else 0.0
                    })
                
                st.session_state['invoice_items'] = extracted_data
                st.success("Invoice successfully processed!")
                
            except Exception as e:
                st.error(f"Could not parse the invoice automatically. Error: {e}")

# Interactive Data Table to Enter Selling Price and Calculate Margins
if 'invoice_items' in st.session_state:
    st.subheader("📊 Enter Your Selling Prices & View Margins")
    st.info("💡 You can edit the **Selling Price ($)** column below for each item. The profit and margin % will update automatically!")
    
    df = pd.DataFrame(st.session_state['invoice_items'])
    
    # Editable Table
    edited_df = st.data_editor(
        df,
        column_config={
            "Selling
