# Setup Instructions

```bash
pip install -r requirements.txt
cp .env.example .env          # then set GEMINI_API_KEY (never commit .env)
python check_gemini.py        # verify the key and configured Gemini models
python seed_products.py       # build the local product vector database
python main.py                # start the API on http://localhost:8000
```

See [README.md](README.md) for configuration, the API example and tests.
