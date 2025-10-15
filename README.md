# 🪡 Crochet Gauge Guru
Smart crochet calculators with dark mode + timezone-aware iCal milestone export. Built with **Streamlit**.

## Features
- Gauge inputs (imperial/metric)
- Beanie resizer (cast-on, rows, crown rounds)
- Wrap/rectangle yardage (by stitch type)
- Granny-square blanket helper
- Hook size converter (US ↔ mm)
- Save/load presets (simple JSON)
- **Dark mode toggle**
- **Timezone-aware iCal (.ics) milestone planner**

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
