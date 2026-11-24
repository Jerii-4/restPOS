# Restaurant Management System (Streamlit)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The application stores menu, table and sales information in `data/*.json`.
Generated TXT bills are saved in the `bills/` folder.

Keep the `data/` and `bills/` folders on persistent storage when deploying.
