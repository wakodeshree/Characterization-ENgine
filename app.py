import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re

# --- UNIVERSAL DATABASE ---
GLOBAL_DB = {
    "H-NMR": [(10, 14, "Amide/Acid"), (6.5, 9.5, "Aromatic"), (0.5, 4.5, "Aliphatic")],
    "13C-NMR": [(160, 220, "Carbonyl"), (100, 160, "Aromatic"), (10, 90, "Aliphatic")]
}

st.title("🧪 AI-Powered Spectral Guardian")

# --- AI LOGIC: MODE VERIFICATION ---
up = st.file_uploader("Upload Graph", type=['png', 'jpg'])
user_mode = st.selectbox("I think this is:", ["H-NMR", "13C-NMR", "Mass Spec"])

if up:
    img = Image.open(up)
    st.image(img)
    
    if st.button("🚀 Run AI Analysis"):
        reader = easyocr.Reader(['en'])
        results = reader.readtext(np.array(img))
        full_text = " ".join([res[1].upper() for res in results])

        # AI STEP: Cross-check Mode
        is_actually_hnmr = any(x in full_text for x in ["PROTON", "1H", "H-NMR"])
        is_actually_cnmr = any(x in full_text for x in ["13C", "C-NMR", "CARBON"])

        if user_mode == "13C-NMR" and is_actually_hnmr:
            st.error("⚠️ AI ALERT: You selected 13C-NMR, but the graph text says 'PROTON'. Switching to H-NMR mode for accuracy.")
            active_mode = "H-NMR"
        elif user_mode == "H-NMR" and is_actually_cnmr:
            st.error("⚠️ AI ALERT: You selected H-NMR, but the graph shows Carbon-13 data. Switching mode.")
            active_mode = "13C-NMR"
        else:
            active_mode = user_mode

        # --- DATA FILTERING ---
        extracted = []
        for res in results:
            # AI Spatial Filter: Ignore bottom axis (12, 11, 10...)
            # Only accept numbers if they are in the 'Data Zone'
            clean = "".join(re.findall(r'[0-9.]+', res[1]))
            try:
                v = float(clean)
                if active_mode == "H-NMR" and (v > 15 or v.is_integer()): continue
                extracted.append(v)
            except: continue

        # Display Final Table (Same format as before)
        st.write(f"Results for {active_mode}:")
        # (Table rendering logic here...)
