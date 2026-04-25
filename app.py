import streamlit as st
import os
from veritas_engine import VeritasGatedEngine

st.set_page_config(page_title="VERITAS X FASE", page_icon="⚖️", layout="wide")

# Initialize Engine
veritas = VeritasGatedEngine()

st.title("⚖️ HEALY VECTOR LABS: SYSTEM AUDIT")

# UI TABS
tab1, tab2 = st.tabs(["🚀 ACTIVE DASHBOARD", "📚 AUDIT METHODOLOGY"])

with tab1:
    ticker = st.text_input("Enter Ticker Symbol", value="NVDA").upper()
    if st.button("RUN SYSTEM ALIGNMENT AUDIT"):
        with st.spinner(f"Auditing Ground Truth for {ticker}..."):
            signals = veritas.fetch_insider_signals(ticker)
            st.subheader(f"Signal Data: {signals.get('company_name', ticker)}")
            st.write(signals) # The "Receipt" for your screenshot
            
            multiplier = veritas.calculate_truth_multiplier(signals)
            st.metric("TRUTH MULTIPLIER", f"{multiplier}x")
            
            # Contextual Feedback
            if multiplier == 0.1:
                st.error("⚠️ SIGNAL: DELUSION. Insiders are not backing this move.")
            elif multiplier < 3.0:
                st.info("ℹ️ SIGNAL: STABLE. Structural integrity confirmed via Institutional Floor.")
            else:
                st.success("🎯 SIGNAL: HIGH CONVICTION. Insider alignment detected.")

with tab2:
    st.header("The Veritas Methodology")
    st.markdown("---")
    
    st.subheader("What is the Truth Multiplier?")
    st.write("""
    The Truth Multiplier is a proprietary 'Conviction Coefficient' developed by Healy Vector Labs. 
    It audits the gap between market sentiment and the actual capital movement of corporate insiders.
    """)
    
    st.markdown("""
    ### **The Three Pillars of Truth**
    1. **The Base (1.0):** Every audited asset starts at a baseline of 1.0.
    2. **The Fortress (Institutional Hold):** We weight institutional ownership at **1.5x**. If 'Big Money' owns the building, the floor is reinforced.
    3. **The Kinetic (Insider Volume):** Every 50 Million shares of insider buying adds **+1.0x** to the multiplier.
    """)
    
    st.info("### **The Formula**")
    st.latex(r"Multiplier = 1.0 + \frac{InsiderVolume}{50,000,000} + (Institutional\% \times 1.5)")

    st.markdown("""
    ### **Understanding the Scale**
    * **0.1x | Delusion:** Gate locked. No insider buying.
    * **1.0x - 3.0x | Stable:** High institutional 'Fortress' state.
    * **3.1x - 6.0x | Conviction:** Aggressive insider alignment with big money.
    * **6.1x+ | Kinetic Alpha:** Rare, total capital handshake.
    """)

st.divider()
st.caption("Healy Vector Labs © 2026 | Built for High-Frequency Frame Control.")
