# Path shim (works in Streamlit Cloud, Codespaces, and locally)
import sys, os
APP_DIR = os.path.dirname(__file__)
if APP_DIR not in sys.path: sys.path.insert(0, APP_DIR)
REPO_ROOT = os.path.abspath(os.path.join(APP_DIR, ".."))
if REPO_ROOT not in sys.path: sys.path.insert(0, REPO_ROOT)

import streamlit as st
import math, json
from datetime import date, timedelta, datetime
from app.calc.crochet import (
    Gauge, cast_on_for_circumference, rows_for_height,
    estimate_yardage, beanie_height_from_circumference, crown_increase_rounds
)

st.set_page_config(page_title="🪡 Crochet Gauge Guru", layout="wide")
st.title("🪡 Crochet Gauge Guru — calculators & pattern resizer")

# ---- FORCE DARK MODE: Fully themed Streamlit UI (fixes white boxes + hides toolbar) ----
DARK_CSS = """
<style>
/* --- Global background + text --- */
html, body, [class^="stApp"] {
  background-color: #0f1115 !important;
  color: #e7e7ea !important;
}

/* --- Metrics, cards, sidebar --- */
[data-testid="stMetric"], .stAlert, .stExpander {
  background: #151821 !important;
  border: 1px solid #23283b !important;
  border-radius: 16px !important;
  color: #e7e7ea !important;
}
section[data-testid="stSidebar"] .stSidebarContent {
  background: #0c0e12 !important;
  color: #e7e7ea !important;
}

/* --- Input boxes (text, number, date, time, select, multiselect) --- */
input:not([type="range"]), textarea, select,
.stTextInput input, .stNumberInput input,
.stDateInput input, .stTimeInput input,
.stSelectbox [role="combobox"], .stSelectbox input,
.stMultiSelect [role="combobox"], .stMultiSelect input {
  background-color: #151821 !important;
  color: #e7e7ea !important;
  border: 1px solid #2a3150 !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}

/* --- Dropdown menus --- */
ul[role="listbox"], .stSelectbox ul, .stMultiSelect ul {
  background-color: #151821 !important;
  color: #e7e7ea !important;
  border: 1px solid #2a3150 !important;
}

/* --- Buttons --- */
.stButton > button {
  background-color: #1c2030 !important;
  color: #e7e7ea !important;
  border: 1px solid #2a3150 !important;
  border-radius: 999px !important;
  padding: 0.5rem 1rem !important;
  font-weight: 500;
  cursor: pointer;
}
.stButton > button:hover {
  background-color: #2b3250 !important;
  border-color: #3a4370 !important;
}

/* --- Sliders --- */
.stSlider > div[data-baseweb="slider"] { color: #e7e7ea !important; }
.stSlider [role="slider"] { background-color: #7b5cff !important; }

/* --- Labels & captions --- */
label, .stMarkdown, .stCaption, .stSlider label, .stSlider span {
  color: #e7e7ea !important;
}

/* --- Placeholders --- */
input::placeholder, textarea::placeholder {
  color: #a0a4b8 !important;
  opacity: 1 !important;
}

/* --- Headings --- */
h1, h2, h3, h4, h5, h6 { color: #ffffff !important; }

/* --- Dividers --- */
hr, .stDivider { border-color: #2a3150 !important; }

/* --- Metric cards fix --- */
.stMetric, div[data-testid="stMetric"], div[data-testid="stMetric"] * {
  background-color: #151821 !important;
  color: #e7e7ea !important;
}
div[data-testid="stMetric"] {
  border: 1px solid #23283b !important;
  border-radius: 16px !important;
  padding: 12px 16px !important;
  box-shadow: none !important;
}

/* --- Hide the built-in Streamlit settings/appearance menu --- */
[data-testid="stToolbar"] [title="Settings"],
[data-testid="stToolbarActions"],
[data-testid="stToolbar"] button[title="View app"],
[data-testid="stToolbar"] div[title="View app"],
button[title="Open command palette"],
[data-testid="stToolbar"] [title="Run"] {
  display: none !important;
}
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

# ---- Sidebar: Gauge ----
st.sidebar.header("Gauge")
spi = st.sidebar.number_input("Stitches per inch (e.g., dc)", 0.1, 20.0, 4.5, 0.1)
rpi = st.sidebar.number_input("Rows per inch", 0.1, 40.0, 3.5, 0.1)
g = Gauge(sts_per_in=spi, rows_per_in=rpi)
st.sidebar.caption(f"≈ {g.sts_per_in:.2f} sts/in • {g.rows_per_in:.2f} rows/in")

# ---- Sidebar: Hook converter ----
HOOK_SIZES = [
    ("B-1", 2.25), ("C-2", 2.75), ("D-3", 3.25), ("E-4", 3.5),
    ("F-5", 3.75), ("G-6", 4.0), ("7", 4.5), ("H-8", 5.0),
    ("I-9", 5.5), ("J-10", 6.0), ("K-10.5", 6.5), ("L-11", 8.0),
    ("M/N-13", 9.0), ("N/P-15", 10.0), ("P/Q", 15.0), ("Q", 16.0),
]
st.sidebar.header("Hook size")
mode = st.sidebar.radio("Convert", ["US → mm", "mm → closest US"], horizontal=True)
if mode == "US → mm":
    us = st.sidebar.selectbox("US size", [u for u, _ in HOOK_SIZES], index=7)
    mm = dict(HOOK_SIZES)[us]
    st.sidebar.write(f"**≈ {mm} mm**")
else:
    mm_in = st.sidebar.number_input("mm", 1.0, 25.0, 5.0, 0.25)
    closest_us, closest_mm = min(HOOK_SIZES, key=lambda p: abs(p[1] - mm_in))
    st.sidebar.write(f"Closest US: **{closest_us}** (≈ {closest_mm} mm)")

# ---- Beanie resizer ----
st.subheader("🧢 Beanie resizer")
c1, c2, c3, c4 = st.columns(4)
with c1:
    head_circ = st.number_input("Head circumference (in)", 12.0, 28.0, 22.0, 0.5)
with c2:
    ease = st.slider("Ease (≤1 is snug)", 0.85, 1.05, 0.95, 0.01)
with c3:
    multiple = st.selectbox("Multiple (rib/pattern)", [1, 2, 3, 4, 6, 8], 1)
with c4:
    beanie_h = st.number_input("Beanie height (in)", 5.0, 14.0,
                               round(beanie_height_from_circumference(22.0), 2), 0.25)

cast_on = cast_on_for_circumference(head_circ, g.sts_per_in, ease=ease, multiple=multiple)
rows = rows_for_height(beanie_h, g.rows_per_in)
st.metric("Cast on (sts around)", f"{cast_on}")
st.metric("Work to", f"{rows} rows")
st.metric("Est. crown inc rounds (DC)", f"{crown_increase_rounds(head_circ, g.sts_per_in)}")

# ---- Rectangle yardage ----
st.subheader("🧣 Rectangle / wrap yardage")
width_in = st.number_input("Width (in)", 2.0, 120.0, 18.0, 0.5)
height_in = st.number_input("Height (in)", 2.0, 120.0, 60.0, 0.5)
stitch_type = st.selectbox("Stitch type", ["sc", "hdc", "dc", "tr", "granny"], 2)
area = width_in * height_in
yardage = estimate_yardage(area, g.sts_per_in, stitch_type=stitch_type)
st.metric("Area", f"{area:.1f} in²")
st.metric("Estimated yardage", f"{yardage:.0f} yd")

# ---- Granny square blanket ----
st.subheader("🧩 Granny square blanket")
square_in = st.number_input("Square size (in)", 2.0, 16.0, 6.0, 0.5)
blanket_w = st.number_input("Blanket width (in)", 12.0, 120.0, 36.0, 1.0)
blanket_h = st.number_input("Blanket height (in)", 12.0, 120.0, 48.0, 1.0)
sq_yard = st.number_input("Yardage per square (est.)", 5.0, 200.0, 22.0, 1.0)

squares_w = math.ceil(blanket_w / square_in)
squares_h = math.ceil(blanket_h / square_in)
total_squares = squares_w * squares_h
total_yard = total_squares * sq_yard
st.metric("Squares (W × H)", f"{squares_w} × {squares_h}")
st.metric("Total squares", f"{total_squares}")
st.metric("Total yardage", f"{total_yard:.0f} yd")
