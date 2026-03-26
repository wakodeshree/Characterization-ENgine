import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re

# --- 1. UNIVERSAL CHEMICAL ENVIRONMENT DATABASE ---
CHEMICAL_DB = {
    "H-NMR": [
        (10.0, 13.0, "Amide / Carboxylic Acid", "Deshielded exchangeable proton (NH/OH)"),
        (8.5, 10.5, "Aldehyde / Deshielded Ar-H", "Aromatic proton ortho to electron-withdrawing group"),
        (6.5, 8.5, "Aromatic Region", "Benzenoid resonance signals"),
        (4.0, 6.5, "Vinylic / Benzylic", "Protons on or near double bonds/rings"),
        (2.0, 4.0, "Alpha to Heteroatoms", "Deshielding from O, N, S, or Carbonyls"),
        (0.5, 2.0, "Aliphatic Region", "Saturated hydrocarbon CH2/CH3 signals")
    ],
    "13C-NMR": [
        (160, 220, "Carbonyl Group", "C=O carbons (Amide, Ester, Ketone)"),
        (100, 160, "Aromatic / Alkene", "sp2 hybridized carbon signals"),
        (40, 90, "Heteroatom Linked C", "Carbons attached to O, N, or Halogens"),
        (5, 40, "Aliphatic Carbon", "Standard sp3 carbon chain")
    ]
}

st.set_page_config(page_title="AI Precision Analyst", layout="wide")
st.title("🔬 AI-Precision Spectral Interpreter")

with st.sidebar:
    st.header("⚙️ OCR Intelligence")
    mode = st.selectbox("Spectrum Mode", ["H-NMR", "13C-NMR", "Mass Spec"])
    st.info("Zone-Filtering Active: Ignoring X-axis scale and Plotname metadata.")

up = st.file_uploader(f"Upload {mode} Graph", type=['png', 'jpg', 'jpeg'])

if up:
    img = Image.open(up)
    width, height = img.size
    st.image(img, use_container_width=True)
    
    if st.button("🚀 Run Precision Analysis"):
        with st.spinner("AI Isolating Peak Data from Scale..."):
            reader = easyocr.Reader(['en'])
            # rotation_info is CRITICAL for the vertical blue numbers in your graph
            results = reader.readtext(np.array(img), rotation_info=[90, 270])
            
            extracted_data = []
            
            for (bbox, text, prob) in results:
                # --- GEOMETRIC ZONE FILTERING ---
                # Calculate the vertical position (Y-coordinate)
                # bbox format: [[top-left], [top-right], [bottom-right], [bottom-left]]
                y_pos = (bbox[0][1] + bbox[2][1]) / 2 / height
                
                # RULE 1: Ignore the bottom 15% of the image (This is where the 12, 11, 10 scale is)
                if y_pos > 0.85: continue
                
                # RULE 2: Ignore the very top 10% (Title/Plotname)
                if y_pos < 0.10: continue

                # CLEAN DATA: Extract only numbers and decimals
                clean = "".join(re.findall(r'[0-9.]+', text.replace("I","1").replace("l","1")))
                
                try:
                    val = float(clean)
                    # RULE 3: Range Enforcement
                    if mode == "H-NMR" and (val < 0 or val > 15): continue
                    if mode == "13C-NMR" and (val < 0 or val > 230): continue
                    
                    extracted_data.append(val)
                except: continue

            # Remove duplicates and sort
            final_peaks = sorted(list(set(extracted_data)), reverse=True)

            # --- MATCHING LOGIC ---
            report = []
            if mode == "Mass Spec":
                for p in final_peaks:
                    if p > 10:
                        report.append({"Exact Value": p, "Literature Range": "N/A", "Interpretation": "Ion/Fragment", "Significance": "Mass-to-charge ratio detected"})
            else:
                lib = CHEMICAL_DB[mode]
                for p in final_peaks:
                    # Find matching chemical environment
                    match = [m for m in lib if m[0] <= p <= m[1]]
                    if match:
                        m = match[0]
                        report.append({
                            "Exact Value": p,
                            "Literature Range": f"{m[0]} – {m[1]}",
                            "Interpretation": m[2],
                            "Significance": m[3]
                        })
                    else:
                        report.append({
                            "Exact Value": p,
                            "Literature Range": "Trace",
                            "Interpretation": "Reference/Solvent",
                            "Significance": "Potential trace impurity or reference signal"
                        })

            # --- RENDER TABLE ---
            if report:
                st.subheader(f"✅ Precision Results: {mode}")
                df = pd.DataFrame(report).drop_duplicates()
                st.table(df)
                st.success("Analysis Complete: AI focused exclusively on the data zone above the baseline.")
                st.download_button("📥 Export Report", df.to_csv(index=False), "Lab_Analysis.csv")
            else:
                st.error("AI could not detect labels in the data zone. Ensure peaks are labeled with numerical values.")
