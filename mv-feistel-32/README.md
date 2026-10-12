# MV Feistel 32

A small Flask app for a 32-bit multivariate Feistel cipher using polynomial systems stored in the app data folder.

## Run the app

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app/app.py
```

Then open:

```text
http://127.0.0.1:5000/
```

## Files to share

If you want to send the app to someone else, include:

- the full project folder
- the app/data directory with the polynomial JSON files
- the requirements file

The app reads its polynomial systems from the data folder, so those files must remain with the app.
