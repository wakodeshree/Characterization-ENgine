import streamlit as st
import pandas as pd
import numpy as np
import easyocr
from PIL import Image
import re

# --- 1. THE UNIVERSAL CHEMICAL LIBRARIES ---
# Comprehensive Functional Group & Chemical Shift Data
GLOBAL_DB = {
    "IR": [
        (3200, 3650, "Alcohol/Phenol O-H", "Broad peak indicates intermolecular hydrogen bonding"),
        (2400, 3400, "Carboxylic Acid O-H", "Very broad peak overlapping C-H region"),
        (3100, 3500, "Amine/Amide N-H", "Sharp peak(s) characteristic of N-H stretching"),
        (2850, 2970, "Alkane C-H", "Standard sp3 hybridized C-H stretching"),
        (2240, 2260, "Nitrile C≡N", "Sharp, medium intensity peak"),
        (1650, 1850, "Carbonyl C=O", "Strong, sharp peak; exact position depends on conjugation"),
        (1475, 1600, "Aromatic C=C", "Multiple sharp peaks indicating aromatic ring presence"),
        (1350, 1550, "Nitro NO2", "Two strong peaks (symmetric and asymmetric stretching)"),
        (1000, 1300, "C-O Stretch", "Strong peak characteristic of ethers, esters, or alcohols")
    ],
    "H-NMR": [
        (10.0, 13.0, "Amide / Carboxylic Acid NH/OH", "Highly deshielded exchangeable protons"),
        (9.0, 10.5, "Aldehyde CHO / Deshielded Ar-H", "Proton ortho to strong electron-withdrawing groups"),
        (6.5, 8.5, "Aromatic Protons", "Signals within the benzenoid resonance region"),
        (4.5, 6.5, "Vinylic / Benzylic Protons", "Protons attached to or adjacent to double bonds"),
        (2.0, 4.5, "Protons adj. to Heteroatoms", "Deshielding caused by O, N, S, or Halogens"),
        (0.5, 2.0, "Aliphatic (CH2/CH3)", "Standard saturated hydrocarbon environment")
    ],
    "13C-NMR": [
        (160, 220, "Carbonyl (C=O)", "Highly deshielded quaternary or aldehyde/ketone carbons"),
        (100, 160, "Aromatic / Alkene Carbons", "sp2 hybridized carbon environments"),
        (50, 90, "C-O / C-N / Aliphatic Methine", "Deshielding from electronegative heteroatoms"),
        (10, 50, "Aliphatic (CH2/CH3)", "Standard sp3 hybridized carbon chain")
    ]
}

# --- 2. THE UI DASHBOARD ---
st.set_page_config(page_title="Universal Lab Analyst", layout="wide", page_icon="🧪")
st.title("🔬 Universal Spectral Interpretation Engine")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Analysis Control")
    mode = st.selectbox("Select Spectrum Type", ["IR", "H-NMR", "13C-NMR", "Mass Spec"])
    st.divider()
    st.info("Guardian Mode: Axis labels are filtered to ensure high peak-detection accuracy.")

# --- 3. PROCESSING ENGINE ---
up = st.file_uploader(f"Upload {mode} Graph", type=['png', 'jpg', 'jpeg'])

if up:
    img = Image.open(up)
    st.image(img, use_container_width=True)
    
    if st.button(f"🔍 Run Full Interpretation"):
        with st.spinner("Machine Scanning..."):
            reader = easyocr.Reader(['en'])
            # rotation_info catches vertical peak labels common in modern NMR software
            ocr_res = reader.readtext(np.array(img), rotation_info=[90, 270])
            
            # Extract and clean numbers, filtering out axis markers
            found_vals = []
            axis_filters = [12.0, 11.0, 10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0, 4000, 3000, 2000, 1000]
            
            for (bbox, text, prob) in ocr_res:
                clean = "".join(re.findall(r'[0-9.]+', text.replace("I","1").replace("l","1")))
                try:
                    v = float(clean)
                    if mode in ["H-NMR", "IR"] and v in axis_filters: continue
                    found_vals.append(v)
                except: continue

            # Remove duplicates and sort descending
            found_vals = sorted(list(set(found_vals)), reverse=True)

            # --- 4. DATA MATCHING ---
            interpretation = []
            
            if mode == "Mass Spec":
                for v in found_vals:
                    if v > 10: # Ignore noise
                        interpretation.append({
                            "Observed m/z": v,
                            "Literature Range": "m/z scan",
                            "Interpretation": "Potential Molecular Ion or Fragment",
                            "Significance": "Indicates parent mass or structural cleavage"
                        })
            else:
                lib = GLOBAL_DB[mode]
                for v in found_vals:
                    matches = [item for item in lib if item[0] <= v <= item[1]]
                    if matches:
                        for m in matches:
                            interpretation.append({
                                "Exact Value": v,
                                "Literature Range": f"{m[0]} – {m[1]}",
                                "Interpretation": m[2],
                                "Significance": m[3]
                            })
                    else:
                        interpretation.append({
                            "Exact Value": v,
                            "Literature Range": "Fingerprint / Trace",
                            "Interpretation": "Unknown Environment",
                            "Significance": "Possible impurity or structural backbone signal"
                        })

            # --- 5. DISPLAY TABLE ---
            if interpretation:
                st.subheader(f"✅ Interpretation Results: {mode}")
                df = pd.DataFrame(interpretation).drop_duplicates()
                st.table(df)
                
                # Professional Conclusion
                st.success("Analysis Complete: Numerical data has been cross-referenced with standard chemical shift and wavenumber databases.")
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Research Report", csv, "characterization_report.csv", "text/csv")
            else:
                st.error("No valid peaks detected. Please ensure the graph has clear numerical labels.")
