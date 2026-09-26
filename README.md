# Shopping Assistant API

An AI-powered shopping assistant built with FastAPI, LangGraph, **Google Gemini** and a **local Chroma vector database**. A Gemini planner turns natural language into structured intent. Semantic search finds products, deterministic Python tools filter and select them, and a validated cart operation completes the request.

Google Gemini is the only LLM and embedding provider. No OpenAI or other provider is used.

## Architecture

```
POST /api/chat
  → Planner Agent ── Gemini (GEMINI_MODEL, structured JSON output)
  → intent + constraints (action, search_query, category, max_price, …)
  → Product Agent
      → semantic search: Gemini embeddings (GEMINI_EMBEDDING_MODEL) → Chroma, restricted to store_id
      → relevance cut-off (SEARCH_MAX_DISTANCE / SEARCH_RELEVANCE_MARGIN)
      → deterministic filters: category, price, available == true, stock > 0
      → selection policy (CHEAPEST_MATCH / FIRST_MATCH / ASK_CONFIRMATION)
  → Cart Agent: get cart → validate → add → refresh/verify
  → Response Agent (deterministic message built from the verified state)
  → API response
```

The LLM only understands the request. Search, filtering, price comparison and cart mutation are all done in Python.

## Project Structure

```
demo-chatbot/
├── app/
│   ├── agent/                  # LangGraph workflow and agents
│   │   ├── graph.py            # Workflow definition and routing
│   │   ├── planner.py          # Gemini intent extraction
│   │   ├── product_agent.py    # Semantic search, filtering, selection
│   │   ├── cart_agent.py       # Cart validation and mutation
│   │   ├── response_agent.py   # User-facing response
│   │   └── state.py            # Shared state
│   ├── api/routes/agent.py     # /api/chat, /api/health, /api/config
│   ├── services/
│   │   ├── gemini_client.py    # Only module that talks to Gemini (google-genai SDK)
│   │   ├── vector_store.py     # Chroma product index + Gemini embeddings
│   │   ├── product_service.py  # Product search/lookup on top of the index
│   │   ├── product_images.py   # Product image URL resolution
│   │   └── cart_service.py     # In-memory demo cart
│   ├── tools/                  # Deterministic business-rule functions
│   ├── schemas/                # Pydantic models
│   ├── prompts/                # Prompt templates
│   └── config.py               # Settings from environment / .env
├── data/
│   ├── products/               # Catalog: every *.json here is seeded
│   │   ├── products.json           # 17 hand-written demo products
│   │   └── generated_products.json # 1,000 generated products (generate_catalog.py)
│   └── vector_db/              # Persisted Chroma index (generated, git-ignored)
├── static/product-images/      # SVG product images (generate_product_images.py)
├── frontend/                   # Vue.js chat UI
├── tests/                      # pytest suite
├── generate_catalog.py         # Generates the 1,000-product sample catalog
├── generate_product_images.py  # Generates per-brand product images
├── seed_products.py            # Builds/updates the vector index
├── check_gemini.py             # Gemini configuration diagnostic
└── main.py                     # FastAPI entry point
```

## Setup

1. **Install dependencies** (Python 3.12):
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Gemini:** copy `.env.example` to `.env` and set your key:
   ```env
   GEMINI_API_KEY=your-key
   GEMINI_MODEL=gemini-3.5-flash-lite
   GEMINI_EMBEDDING_MODEL=gemini-embedding-001
   VECTOR_DB_PATH=data/vector_db
   ```
   Model availability varies by API key. To list the models your key can use and check that the configured ones work, run:
   ```bash
   python check_gemini.py
   ```

3. **(Optional) Regenerate sample data and images.** Both are already committed. The generator is deterministic, so re-running it gives the same output:
   ```bash
   python generate_catalog.py          # 1,000 products at ₹10/20/30/35/40/50/80/90/100
   python generate_product_images.py   # static/product-images/<category>/<brand>.svg
   ```

4. **Seed the product vector database:**
   ```bash
   python seed_products.py
   ```
   This loads every catalog file in `data/products/`, embeds each product (name, description, category and brand) with Gemini, and upserts it into the Chroma index at `VECTOR_DB_PATH`. The seed is safe to re-run:
   - unchanged products are skipped
   - changed products are re-embedded
   - products removed from the catalog are deleted
   - the index is rebuilt automatically if the embedding model or dimensions change

   If the Gemini configuration is invalid, the seed exits with a clear error.

   **Free-tier quota.** The Gemini free tier allows 100 embedded texts per minute and 1,000 per day for `gemini-embedding-001`, and the catalog has 1,017 products.
   - The seed paces itself (`SEED_EMBEDDINGS_PER_MINUTE=90`) and waits out rate-limit errors.
   - It saves progress after each batch. If it stops at the daily limit, run it again after the quota resets and it only embeds the missing products.
   - Chat requests also use one embedding per new search query. Repeated queries are cached in memory.

5. **Start the server:**
   ```bash
   python main.py
   # or
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - Health (includes product index readiness): http://localhost:8000/api/health

## API Usage

**POST** `/api/chat`

```bash
curl -X 'POST' \
'http://localhost:8000/api/chat' \
-H 'accept: */*' \
-H 'Content-Type: application/json' \
-d '{
  "query": "Add cold drink which have less price 100 RS",
  "user_id": "user123",
  "store_id": "STORE_1"
}'
```

Actual response:

```json
{
  "response": "Fanta 750ml priced at ₹40 has been added to your cart.\n\nCart (1 item):\n  - Fanta 750ml x1 — ₹40\n\nTotal: ₹40",
  "success": true,
  "intent": {
    "action": "ADD_TO_CART",
    "search_query": "cold drink",
    "category": "cold_drink",
    "max_price": 100.0,
    "min_price": null,
    "quantity": 1,
    "product_name": null,
    "selection_strategy": null
  },
  "cart_state": {
    "cart_id": "CART_user123_STORE_1",
    "user_id": "user123",
    "store_id": "STORE_1",
    "items": [
      { "product_id": "PROD_005", "name": "Fanta 750ml", "quantity": 1, "price": 40.0, "total_price": 40.0 }
    ],
    "total_items": 1,
    "total_price": 40.0
  },
  "error": null
}
```

This response was produced with the original 17-product catalog. With the 1,000-product catalog, the default `SELECTION_POLICY=CHEAPEST_MATCH` picks the cheapest valid STORE_1 cold drink, which is now a ₹10 product. The response also includes `image_url` on each cart item. Products that are unavailable, out of stock, over ₹100, in another store, or in another category (for example beer) are never selected.

Carts are held in memory and reset when the server restarts. The cart keeps one line per product, so sending the same request again increases that product's quantity (×2) instead of adding a duplicate line.

### Product and cart endpoints (used by the frontend)

| Endpoint | Purpose |
|---|---|
| `GET /api/products?store_id=STORE_1&q=fanta&page=1&page_size=12` | Browse the catalog: keyword search over name, brand and category, paginated. Uses no Gemini calls. |
| `GET /api/cart?user_id=user123&store_id=STORE_1` | The user's cart (the same cart the chatbot updates) |
| `PUT /api/cart/items/{product_id}` with body `{"user_id", "store_id", "quantity"}` | Set the absolute quantity; 0 removes the item. Returns 400 with a reason if the stock, per-item limit or store rule is violated. |

CORS allows the Vite dev and preview origins by default (`CORS_ORIGINS`).

### Sample Catalog

There are 1,017 products across three stores (`STORE_1`, `STORE_2`, `STORE_3`):
- cold drinks
- energy drinks
- fruit drinks
- water
- beer, from brands such as Kingfisher, Budweiser, Heineken, Tuborg, Carlsberg, Corona, Bira 91 and Hoegaarden
- wine, from brands such as Sula, Grover Zampa, Fratelli, York, Jacob's Creek and Big Banyan
- snacks

Prices use the demo price points ₹10, 20, 30, 35, 40, 50, 80, 90 and 100. About 5% of products are unavailable and about 7% are out of stock, so the filters get exercised. Beer and wine are labelled as alcoholic (21+). The planner only uses those categories when alcohol is asked for, so "cold drink" never returns beer.

Every product and cart item has an `image_url`: a generated SVG illustration for its category and brand, served from `/static/product-images/`. The frontend shows it in the cart.

### Example Queries

- "Add cold drink which have less price 100 RS"
- "Put a soda in my cart" (synonyms: soft drink, soda, carbonated drink)
- "Add an energy drink under 100"
- "Add 2 mango drinks"
- "Show me cold drinks below 100 and let me choose" (lists the 5 most relevant options)
- "Add a Kingfisher beer under 100"
- "Add a red wine"

### Errors

Errors are returned as `success: false` with a client-safe `error` message. Raw SDK errors and stack traces are logged on the server and never returned. Handled cases:
- invalid Gemini API key
- unsupported or unavailable model
- Gemini unavailable or timing out
- rate limits (transient failures are retried with exponential backoff)
- vector DB not seeded or built with a different embedding model
- no matching product
- out-of-stock products
- unknown store
- invalid price constraint
- cart update failures

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | — | Google AI Studio API key (required) |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Planner model (must support `generateContent`) |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-001` | Product and query embeddings |
| `GEMINI_EMBEDDING_DIMENSIONS` | `768` | Embedding size |
| `GEMINI_TIMEOUT_SECONDS` / `GEMINI_MAX_RETRIES` | `30` / `2` | Request timeout, retries for transient errors |
| `VECTOR_DB_PATH` | `data/vector_db` | Chroma persistence directory |
| `PRODUCT_CATALOG_PATH` | `data/products` | Catalog JSON file or directory |
| `SEED_EMBEDDINGS_PER_MINUTE` | `90` | Seed pacing for the embedding quota (0 = off) |
| `PUBLIC_BASE_URL` | `http://localhost:8000` | Base of product `image_url`s |
| `SEARCH_TOP_K` | `100` | Candidates fetched from the index |
| `SEARCH_MAX_DISTANCE` / `SEARCH_RELEVANCE_MARGIN` | `0.41` / `0.04` | Relevance cut-off (calibrated for `gemini-embedding-001`) |
| `SELECTION_POLICY` | `CHEAPEST_MATCH` | `CHEAPEST_MATCH`, `FIRST_MATCH`, `ASK_CONFIRMATION` |
| `MAX_CART_ITEMS` / `MAX_QUANTITY_PER_ITEM` | `50` / `10` | Cart limits |

## Tests

```bash
pytest                                            # offline suite (fake Gemini, temp Chroma index)
RUN_LIVE_TESTS=1 pytest tests/test_live_gemini.py # real Gemini API + seeded index
```

The offline suite covers:
- Gemini configuration, initialization and error translation
- seeding and idempotency
- embeddings and the vector store
- semantic search with synonyms
- price, store and availability filtering
- planner intent
- add-to-cart
- the `/api/chat` end-to-end flow, including no-match and Gemini-failure cases

## Frontend

A Vue 3 + Vite shopping UI is in `frontend/`: product browsing with search and pagination, a live cart with +/− buttons, and the chat assistant.

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173 (needs the backend on :8000)
```

See `frontend/README.md`.

## Production Considerations

1. **No hallucinated products**: only indexed products can be selected.
2. **Validation first**: the cart is checked (duplicates, stock, limits, store) before mutation.
3. **State verification**: the cart is refreshed after mutation, and responses are built from the verified state.
4. **Deterministic business logic**: price, stock and selection are handled in Python, not by the LLM.
5. **Isolated provider integration**: all Gemini calls live in `app/services/gemini_client.py`.

## Limitations / Future Enhancements

- Carts are in memory and reset on restart. Connect a real cart API/DB for persistence.
- Product images are generated illustrations, not real product photos.
- There is no age verification before adding beer or wine to the cart.
- The relevance thresholds are calibrated for the sample catalog and `gemini-embedding-001`. Re-check them if you change the embedding model or the catalog substantially.
- Add authentication, conversation memory, observability and an evaluation dataset.
