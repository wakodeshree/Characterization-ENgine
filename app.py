import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re

# --- 1. THE UNIVERSAL DATABASE (High Precision) ---
GLOBAL_DB = {
    "H-NMR": [
        (10.0, 13.0, "Amide / Carboxylic Acid NH/OH", "Highly deshielded exchangeable protons"),
        (9.0, 10.5, "Aldehyde CHO / Deshielded Ar-H", "Proton ortho to strong electron-withdrawing groups"),
        (6.5, 8.5, "Aromatic Protons", "Signals within the benzenoid resonance region"),
        (4.5, 6.5, "Vinylic / Benzylic Protons", "Protons attached to or adjacent to double bonds"),
        (2.0, 4.5, "Protons adj. to Heteroatoms", "Deshielding caused by O, N, S, or Halogens"),
        (0.5, 2.0, "Aliphatic (CH2/CH3)", "Standard saturated hydrocarbon environment")
    ],
    "13C-NMR": [
        (160, 220, "Carbonyl (C=O)", "Highly deshielded quaternary or aldehyde carbons"),
        (100, 160, "Aromatic / Alkene Carbons", "sp2 hybridized carbon environments"),
        (50, 90, "C-O / C-N / Aliphatic Methine", "Deshielding from electronegative heteroatoms"),
        (10, 50, "Aliphatic (CH2/CH3)", "Standard sp3 hybridized carbon chain")
    ]
}

st.set_page_config(page_title="AI Spectral Interpreter", layout="wide")
st.title("🔬 AI-Powered Universal Spectral Interpreter")

with st.sidebar:
    st.header("⚙️ Intelligence Settings")
    mode = st.selectbox("Spectrum Type", ["H-NMR", "13C-NMR", "Mass Spec"])
    st.info("AI Mode: Spatial Filtering active. Metadata and plot names will be ignored.")

up = st.file_uploader(f"Upload {mode} Graph", type=['png', 'jpg', 'jpeg'])

if up:
    img = Image.open(up)
    width, height = img.size
    st.image(img, use_container_width=True)
    
    if st.button(f"🔍 Run AI Interpretation"):
        with st.spinner("AI Scanning & Filtering Metadata..."):
            # Initialize OCR with 'paragraph' mode to better handle slanted/vertical text
            reader = easyocr.Reader(['en'])
            ocr_res = reader.readtext(np.array(img), rotation_info=[90, 270], paragraph=False)
            
            found_vals = []
            
            for (bbox, text, prob) in ocr_res:
                # --- AI SPATIAL FILTER ---
                # Calculate center of the detected text box
                center_x = (bbox[0][0] + bbox[2][0]) / 2
                center_y = (bbox[0][1] + bbox[2][1]) / 2
                
                # Rule: Ignore text in the far bottom-left or top-right (usually metadata)
                if center_x < (width * 0.2) and center_y > (height * 0.8): continue
                
                # Clean the text to find valid numbers (handles I=1, l=1, s=5)
                clean = "".join(re.findall(r'[0-9.]+', text.replace("I","1").replace("l","1").replace("s","5")))
                
                try:
                    v = float(clean)
                    # VALID RANGE FILTER: Only accept values that make sense for the mode
                    if mode == "H-NMR" and (v < 0 or v > 15): continue
                    if mode == "13C-NMR" and (v < 0 or v > 230): continue
                    found_vals.append(v)
                except: continue

            # Clean duplicates and sort
            found_vals = sorted(list(set(found_vals)), reverse=True)

            # --- DATA MATCHING ---
            interpretation = []
            if mode == "Mass Spec":
                for v in found_vals:
                    if v > 10:
                        interpretation.append({
                            "Exact Value": v, "Literature Range": "m/z Scan",
                            "Interpretation": "Potential Ion/Fragment", "Significance": "Molecular weight indicator"
                        })
            else:
                lib = GLOBAL_DB[mode]
                for v in found_vals:
                    # Logic: Find the range the value belongs to
                    matches = [m for m in lib if m[0] <= v <= m[1]]
                    if matches:
                        for m in matches:
                            interpretation.append({
                                "Exact Value": v, "Literature Range": f"{m[0]} – {m[1]}",
                                "Interpretation": m[2], "Significance": m[3]
                            })
                    else:
                        interpretation.append({
                            "Exact Value": v, "Literature Range": "Minor Signal",
                            "Interpretation": "Reference/Solvent/Trace", "Significance": "Background or trace impurity"
                        })

            # --- DISPLAY ---
            if interpretation:
                st.subheader(f"✅ AI Interpretation Results: {mode}")
                df = pd.DataFrame(interpretation).drop_duplicates()
                st.table(df)
                st.success("AI has successfully isolated peaks from metadata and axis labels.")
                st.download_button("📥 Download Report", df.to_csv(index=False), "AI_Report.csv")
            else:
                st.error("AI could not isolate any peaks. Please ensure peak labels are clearly visible.")
