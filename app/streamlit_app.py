# Path shim (works in Streamlit Cloud and locally)
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

# ===== Appearance: Light/Dark toggle (CSS) =====
with st.sidebar.expander("Appearance", expanded=False):
    dark_mode = st.checkbox("Dark mode", value=False)

LIGHT_CSS = """
<style>
.block-container { padding-top: 1rem; padding-bottom: 2rem; }
[data-testid="stMetric"] {
  background: #fff; border: 1px solid #ececf4; border-radius: 16px;
  padding: 12px 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
section[data-testid="stSidebar"] .stSidebarContent { padding-top: .75rem; }
div[data-testid="stCaptionContainer"] { color: #666; font-size: 0.85rem; }
.stButton>button { border-radius: 999px !important; padding: 0.5rem 0.9rem; }
.stTextInput>div>div>input, .stNumberInput input,
.stSelectbox > div > div, .stSlider > div { border-radius: 10px !important; }
h3 { margin-top: 0.5rem; }
</style>
"""

DARK_CSS = """
<style>
html, body, .block-container { background: #0f1115 !important; color: #e7e7ea !important; }
[data-testid="stMetric"] {
  background: #151821; border: 1px solid #23283b; border-radius: 16px;
  padding: 12px 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.35);
}
section[data-testid="stSidebar"] .stSidebarContent { background:#0c0e12; }
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color:#e7e7ea; }
div[data-testid="stCaptionContainer"] { color: #a0a4b8; }
.stButton>button {
  border-radius: 999px !important; padding:.5rem .9rem;
  background:#1c2030; color:#e7e7ea; border:1px solid #2a3150;
}
.stTextInput>div>div>input, .stNumberInput input { background:#151821; color:#e7e7ea; }
.stSelectbox > div > div, .stSlider > div { background:#151821; color:#e7e7ea; border-radius:10px !important; }
</style>
"""
st.markdown(DARK_CSS if dark_mode else LIGHT_CSS, unsafe_allow_html=True)

# --- Strong input theming: readable in both light & dark ---
if dark_mode:
    st.markdown("""
    <style>
    /* text inputs, number inputs, date/time, select combobox */
    input[type="text"], input[type="number"], input[type="search"],
    .stTextInput input, .stNumberInput input,
    .stDateInput input, .stTimeInput input,
    .stSelectbox [role="combobox"], .stSelectbox input {
      color: #e7e7ea !important;
      background: #151821 !important;
      border-color: #2a3150 !important;
    }
    /* dropdown & menu items */
    .stSelectbox > div > div { color:#e7e7ea !important; background:#151821 !important; }
    .stSelectbox ul[role="listbox"] li { color:#e7e7ea !important; background:#0f1115 !important; }
    /* slider value bubble & labels */
    .stSlider label, .stSlider span { color:#e7e7ea !important; }
    /* placeholders */
    input::placeholder { color:#a0a4b8 !important; opacity:1; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    input[type="text"], input[type="number"], input[type="search"],
    .stTextInput input, .stNumberInput input,
    .stDateInput input, .stTimeInput input,
    .stSelectbox [role="combobox"], .stSelectbox input {
      color: #222 !important;
      background: #ffffff !important;
      border-color: #e2e2e9 !important;
    }
    .stSelectbox > div > div { color:#222 !important; background:#ffffff !important; }
    .stSelectbox ul[role="listbox"] li { color:#222 !important; background:#ffffff !important; }
    .stSlider label, .stSlider span { color:#222 !important; }
    input::placeholder { color:#666 !important; opacity:1; }
    </style>
    """, unsafe_allow_html=True)


# --- fix input text visibility ---
st.markdown("""
<style>
/* Light mode input text */
[data-baseweb="input"] input,
.stNumberInput input,
.stTextInput input,
.stSelectbox div[data-baseweb="select"] > div {
  color: #222 !important;
}

/* Dark mode input text */
html[data-theme="dark"] [data-baseweb="input"] input,
html[data-theme="dark"] .stNumberInput input,
html[data-theme="dark"] .stTextInput input,
html[data-theme="dark"] .stSelectbox div[data-baseweb="select"] > div {
  color: #e7e7ea !important;
}
</style>
""", unsafe_allow_html=True)


# ---------- Sidebar: Gauge ----------
st.sidebar.header("Gauge")
units = st.sidebar.radio("Units", ["imperial (in)", "metric (cm)"], horizontal=True)
if units == "imperial (in)":
    spi = st.sidebar.number_input("Stitches per inch (e.g., dc)",
                                  min_value=0.1, max_value=20.0, value=4.5, step=0.1)
    rpi = st.sidebar.number_input("Rows per inch",
                                  min_value=0.1, max_value=40.0, value=3.5, step=0.1)
else:
    sts_per_10cm = st.sidebar.number_input("Stitches per 10 cm",
                                           min_value=1.0, max_value=80.0, value=18.0, step=0.5)
    rows_per_10cm = st.sidebar.number_input("Rows per 10 cm",
                                            min_value=1.0, max_value=120.0, value=28.0, step=0.5)
    spi = sts_per_10cm / 3.937  # 10 cm = 3.937 in
    rpi = rows_per_10cm / 3.937

g = Gauge(sts_per_in=spi, rows_per_in=rpi)
st.sidebar.caption(f"≈ {g.sts_per_in:.2f} sts/in • {g.rows_per_in:.2f} rows/in")

# ---------- Sidebar: Hook converter ----------
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
    mm_in = st.sidebar.number_input("mm", min_value=1.0, max_value=25.0, value=5.0, step=0.25)
    closest_us, closest_mm = min(HOOK_SIZES, key=lambda p: abs(p[1] - mm_in))
    st.sidebar.write(f"Closest US: **{closest_us}** (≈ {closest_mm} mm)")

# ---------- Beanie resizer ----------
st.subheader("🧢 Beanie resizer")
c1, c2, c3, c4 = st.columns(4)
with c1:
    head_circ = st.number_input("Head circumference (in)", min_value=12.0, max_value=28.0,
                                value=22.0, step=0.5)
with c2:
    ease = st.slider("Ease (≤1 is snug)", min_value=0.85, max_value=1.05, value=0.95, step=0.01)
with c3:
    multiple = st.selectbox("Multiple (rib/pattern)", [1, 2, 3, 4, 6, 8], index=1)
with c4:
    default_height = round(beanie_height_from_circumference(head_circ), 2)
    beanie_h = st.number_input("Beanie height (in)", min_value=5.0, max_value=14.0,
                               value=default_height, step=0.25)

cast_on = cast_on_for_circumference(head_circ, g.sts_per_in, ease=ease, multiple=multiple)
rows = rows_for_height(beanie_h, g.rows_per_in)

k1, k2, k3 = st.columns(3)
k1.metric("Cast on (sts around)", f"{cast_on}")
k2.metric("Work to", f"{rows} rows")
k3.metric("Est. crown inc rounds (DC)", f"{crown_increase_rounds(head_circ, g.sts_per_in)}")
st.caption("Tip: set the multiple to match your stitch pattern (e.g., 2 for rib, 4 for shells).")

# ---------- Rectangle / wrap yardage ----------
st.subheader("🧣 Rectangle / wrap yardage")
colw, colh, cols = st.columns(3)
with colw:
    width_in = st.number_input("Width (in)", min_value=2.0, max_value=120.0, value=18.0, step=0.5)
with colh:
    height_in = st.number_input("Height (in)", min_value=2.0, max_value=120.0, value=60.0, step=0.5)
with cols:
    stitch_type = st.selectbox("Stitch type", ["sc", "hdc", "dc", "tr", "granny"], index=2)
area = width_in * height_in
yardage = estimate_yardage(area, g.sts_per_in, stitch_type=stitch_type)
k4, k5 = st.columns(2)
k4.metric("Area", f"{area:.1f} in²")
k5.metric("Estimated yardage", f"{yardage:.0f} yd")
st.caption("Rule-of-thumb estimator; actual usage varies by fiber, tension, and stitch pattern.")

# ---------- Granny square blanket ----------
st.subheader("🧩 Granny square blanket")
g1, g2, g3, g4 = st.columns(4)
with g1:
    square_in = st.number_input("Square size (in)", min_value=2.0, max_value=16.0,
                                value=6.0, step=0.5)
with g2:
    blanket_w = st.number_input("Blanket width (in)", min_value=12.0, max_value=120.0,
                                value=36.0, step=1.0)
with g3:
    blanket_h = st.number_input("Blanket height (in)", min_value=12.0, max_value=120.0,
                                value=48.0, step=1.0)
with g4:
    sq_yard = st.number_input("Yardage per square (est.)", min_value=5.0, max_value=200.0,
                              value=22.0, step=1.0)

squares_w = math.ceil(blanket_w / square_in)
squares_h = math.ceil(blanket_h / square_in)
total_squares = squares_w * squares_h
total_yard = total_squares * sq_yard

h1, h2, h3 = st.columns(3)
h1.metric("Squares (W × H)", f"{squares_w} × {squares_h}")
h2.metric("Total squares", f"{total_squares}")
h3.metric("Total yardage", f"{total_yard:.0f} yd")
st.caption("Get yardage per square from a test motif (weigh it; convert grams → yards using the ball label).")

# ---------- Presets ----------
st.subheader("💾 Presets")
preset_name = st.text_input("Preset name", "DC Adult Beanie")
cA, cB = st.columns(2)
STATE = "app/.state.json"
store = {}
if os.path.exists(STATE):
    try:
        store = json.load(open(STATE))
    except Exception:
        store = {}

if cA.button("Save preset"):
    store[preset_name] = {
        "gauge": {"spi": g.sts_per_in, "rpi": g.rows_per_in},
        "beanie": {"circ": head_circ, "ease": ease, "mult": multiple, "height": beanie_h},
        "rect": {"w": width_in, "h": height_in, "st": stitch_type},
        "granny": {"sq": square_in, "bw": blanket_w, "bh": blanket_h, "sy": sq_yard}
    }
    try:
        tmp = STATE + ".tmp"
        json.dump(store, open(tmp, "w"), indent=2)
        os.replace(tmp, STATE)
        st.success("Saved.")
    except Exception:
        st.warning("Could not save preset (read-only environment).")

choices = ["(none)"] + list(store.keys())
sel = cB.selectbox("Load preset", choices)
if sel != "(none)":
    st.info(f"Loaded **{sel}** — adjust values above if needed.")

# ===== Milestones & iCal (Timezone aware) =====
st.subheader("🗓️ Milestones & iCal")

plan_mode = st.selectbox("Plan milestones for", ["Beanie (rows)", "Blanket (granny squares)"], index=0)

tz_options = [
    "America/Chicago", "America/New_York", "America/Los_Angeles",
    "Europe/London", "Europe/Paris", "UTC"
]
tzid = st.selectbox("Calendar timezone (TZID)", tz_options, index=0)

col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    start_date = st.date_input("Start date", value=date.today())
with col_b:
    weeks = st.number_input("Duration (weeks)", min_value=1, max_value=52, value=4, step=1)
with col_c:
    sessions_per_week = st.number_input("Sessions per week", min_value=1, max_value=14, value=3, step=1)
with col_d:
    session_hour = st.number_input("Session hour (24h)", min_value=6, max_value=22, value=19, step=1)

total_sessions = int(weeks * sessions_per_week)
if plan_mode == "Beanie (rows)":
    total_work = max(int(rows), 0); work_label = "rows"; title_prefix = "Crochet Beanie"
else:
    total_work = max(int(total_squares), 0); work_label = "squares"; title_prefix = "Granny Blanket"

if total_sessions <= 0:
    st.warning("Please set at least 1 session.")
else:
    per_session = max(1, math.ceil(total_work / total_sessions)) if total_work > 0 else 1
    if sessions_per_week == 1: weekdays = [2]
    elif sessions_per_week == 2: weekdays = [1, 4]
    elif sessions_per_week == 3: weekdays = [0, 3, 5]
    elif sessions_per_week == 4: weekdays = [0, 2, 4, 6]
    else:
        step = max(1, 7 // int(sessions_per_week))
        weekdays = list(range(0, 7, step))[:int(sessions_per_week)]

    session_dates = []
    cur = start_date
    for w in range(int(weeks)):
        anchor = cur - timedelta(days=cur.weekday())
        for wd in weekdays:
            dt = anchor + timedelta(days=wd + w * 7)
            if dt >= start_date:
                session_dates.append(dt)
    session_dates = session_dates[:total_sessions]

    preview, remaining = [], total_work
    for i, d in enumerate(session_dates, start=1):
        qty = min(per_session, max(remaining, 0)) if total_work > 0 else per_session
        remaining -= qty
        preview.append(f"{i:02d}. {d.isoformat()} — {qty} {work_label}")
    st.write("**Plan preview**")
    st.code("\n".join(preview) if preview else "No sessions generated.", language="text")

    def vtimezone_for(tz: str) -> str:
        if tz == "America/Chicago":
            return "\n".join([
                "BEGIN:VTIMEZONE","TZID:America/Chicago","X-LIC-LOCATION:America/Chicago",
                "BEGIN:DAYLIGHT","TZOFFSETFROM:-0600","TZOFFSETTO:-0500","TZNAME:CDT",
                "DTSTART:19700308T020000","RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU","END:DAYLIGHT",
                "BEGIN:STANDARD","TZOFFSETFROM:-0500","TZOFFSETTO:-0600","TZNAME:CST",
                "DTSTART:19701101T020000","RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU","END:STANDARD",
                "END:VTIMEZONE"
            ])
        if tz == "America/New_York":
            return "\n".join([
                "BEGIN:VTIMEZONE","TZID:America/New_York","X-LIC-LOCATION:America/New_York",
                "BEGIN:DAYLIGHT","TZOFFSETFROM:-0500","TZOFFSETTO:-0400","TZNAME:EDT",
                "DTSTART:19700308T020000","RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU","END:DAYLIGHT",
                "BEGIN:STANDARD","TZOFFSETFROM:-0400","TZOFFSETTO:-0500","TZNAME:EST",
                "DTSTART:19701101T020000","RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU","END:STANDARD",
                "END:VTIMEZONE"
            ])
        if tz == "America/Los_Angeles":
            return "\n".join([
                "BEGIN:VTIMEZONE","TZID:America/Los_Angeles","X-LIC-LOCATION:America/Los_Angeles",
                "BEGIN:DAYLIGHT","TZOFFSETFROM:-0800","TZOFFSETTO:-0700","TZNAME:PDT",
                "DTSTART:19700308T020000","RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU","END:DAYLIGHT",
                "BEGIN:STANDARD","TZOFFSETFROM:-0700","TZOFFSETTO:-0800","TZNAME:PST",
                "DTSTART:19701101T020000","RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU","END:STANDARD",
                "END:VTIMEZONE"
            ])
        if tz in ("Europe/London", "Europe/Paris"):
            return "\n".join([
                "BEGIN:VTIMEZONE",f"TZID:{tz}",f"X-LIC-LOCATION:{tz}",
                "BEGIN:DAYLIGHT","TZOFFSETFROM:+0000","TZOFFSETTO:+0100","TZNAME:Summer",
                "DTSTART:19700329T010000","RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU","END:DAYLIGHT",
                "BEGIN:STANDARD","TZOFFSETFROM:+0100","TZOFFSETTO:+0000","TZNAME:Standard",
                "DTSTART:19701025T020000","RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU","END:STANDARD",
                "END:VTIMEZONE"
            ])
        if tz == "UTC":
            return "\n".join([
                "BEGIN:VTIMEZONE","TZID:UTC","X-LIC-LOCATION:UTC",
                "BEGIN:STANDARD","TZOFFSETFROM:+0000","TZOFFSETTO:+0000","TZNAME:UTC",
                "DTSTART:19700101T000000","END:STANDARD","END:VTIMEZONE"
            ])
        return ""

    def _ics_datetime(dt: datetime) -> str:
        return dt.strftime("%Y%m%dT%H%M%S")

    def build_ics() -> str:
        now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        cal = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Crochet Gauge Guru//Milestones//EN"]
        vtz = vtimezone_for(tzid)
        if vtz: cal.append(vtz)
        remaining_local = total_work
        for i, d in enumerate(session_dates, start=1):
            qty = min(per_session, max(remaining_local, 0)) if total_work > 0 else per_session
            remaining_local -= qty
            start_dt = datetime(d.year, d.month, d.day, int(session_hour), 0, 0)
            end_dt = start_dt + timedelta(hours=1)
            uid = f"cgg-{plan_mode.replace(' ','-').lower()}-{i}-{d.isoformat()}@local"
            title = f"{title_prefix} — Session {i}"
            desc = f"Goal: {qty} {work_label}. Generated by Crochet Gauge Guru."
            cal.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now}",
                f"DTSTART;TZID={tzid}:{_ics_datetime(start_dt)}",
                f"DTEND;TZID={tzid}:{_ics_datetime(end_dt)}",
                f"SUMMARY:{title}",
                f"DESCRIPTION:{desc}",
                "END:VEVENT"
            ])
        cal.append("END:VCALENDAR")
        return "\n".join(cal)

    ics_text = build_ics()
    st.download_button(
        "📅 Download iCal (.ics)",
        data=ics_text,
        file_name=f"crochet_{'beanie' if plan_mode.startswith('Beanie') else 'blanket'}_milestones.ics",
        mime="text/calendar"
    )
    st.caption("Tip: import the .ics into Google, Apple, or Outlook calendars.")
