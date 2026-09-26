# ShopBot Frontend (Vue 3 + Vite)

A responsive e-commerce chatbot UI. Browse products on the left, chat with the Gemini-powered assistant on the right, and see the cart update immediately.

## Requirements

- Node.js 20.19+ or 22.12+ (tested with Node 24 LTS; see `.nvmrc`). Vite 8 does not run on Node 18. If `npm run dev` reports that Node is too old, check `node --version`: Ubuntu's `nodejs` package installs Node 18 at `/usr/bin/node`. Node 24 is in `~/.local/node`, so open a new terminal or run `source ~/.bashrc`.
- The FastAPI backend running on `http://localhost:8000`. See the root `README.md` (`python seed_products.py`, then `python main.py`).

## Setup and run

```bash
cd demo-chatbot/frontend
cp .env.example .env        # optional; defaults match .env.example
npm install
npm run dev                 # http://localhost:5173
```

Other scripts:

```bash
npm test          # unit tests (Vitest): API client + cart store
npm run build     # production build in dist/
npm run preview   # serve the build on http://localhost:4173
```

## Configuration (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend base URL |
| `VITE_DEFAULT_USER_ID` | `user123` | Sent with every chat/cart request |
| `VITE_DEFAULT_STORE_ID` | `STORE_1` | Store for chat, products and cart |
| `VITE_DEFAULT_SESSION_ID` | `SESSION_1` | Sent with every chat request |
| `VITE_API_TIMEOUT_MS` | `60000` | Request timeout |
| `VITE_PRODUCTS_PAGE_SIZE` | `12` | Products per page |
| `VITE_MAX_QUANTITY_PER_ITEM` | `10` | Client-side cap (the backend enforces it too) |

The user/store/session context is defined once in `src/config.js` (`chatContext`). The user only types the query.

## Structure

```
src/
├── config.js                 # env-driven config + chatContext
├── services/api.js           # the only module that calls the backend
├── stores/cart.js            # Pinia cart store (single source of cart state)
├── composables/useChat.js    # chat state, history, cart sync
├── composables/useProducts.js# debounced search + pagination
├── utils/format.js           # price/category formatting
├── views/ChatbotView.vue     # page layout
└── components/
    ├── ChatWindow.vue  ChatMessage.vue
    ├── ProductList.vue ProductCard.vue ProductImage.vue
    ├── CartSummary.vue QuantityControl.vue
    ├── SearchBar.vue   Pagination.vue
tests/                        # Vitest unit tests
```

## Backend API used

| Call | Purpose |
|---|---|
| `POST /api/chat` `{query, user_id, store_id, session_id}` | Natural-language request (Gemini planner + semantic search) |
| `GET /api/products?store_id&q&page&page_size` | Product browsing: keyword search over name, brand and category, paginated |
| `GET /api/cart?user_id&store_id` | Current cart (loaded on page start) |
| `PUT /api/cart/items/{product_id}` `{user_id, store_id, quantity}` | Set the absolute quantity; 0 removes the item |

## How the cart stays correct

- **The backend is the source of truth.** The chatbot and the +/− buttons change the same backend cart. Every chat reply's `cart_state` and every cart API response replaces the local cart (`syncFromServer`).
- **One line per product.** Lines are keyed by `product_id`. Asking the assistant for the same product again increases its quantity (for example Fanta ×2) rather than adding a second line. The store also merges any duplicate lines defensively.
- **+/− buttons.**
  - The quantity updates instantly on screen.
  - Changes are sent to the backend one at a time, as absolute quantities, so rapid clicks can't race.
  - When the last change completes, the cart is reconciled with the server.
  - Quantities never go below 0. Pressing − at quantity 1 removes the item.
  - + is disabled at the stock limit or the per-item limit.
  - If the backend rejects a change (for example, not enough stock), the real cart is reloaded and the reason is shown.
- **Page refresh.** The cart is reloaded from the backend, and chat history is restored from `sessionStorage`. The backend keeps carts in memory, so they reset when the backend restarts.

## Error handling

Network failures, timeouts, HTTP 4xx/5xx and malformed responses become short, friendly messages in the chat or cart. Technical details go to the browser console only. Send is disabled while a request is pending, so duplicate requests can't be sent.

## Responsive layout

- **Desktop (≥1024px):** products 60% | cart and chat 40%. The right column stays in view while you scroll the products.
- **Tablet and mobile:** Products → Cart → Chat, stacked. A floating chat button jumps to the chat and hides once the chat is visible. The chat input stays at the bottom of the chat panel, inside the viewport.
- **Phones:** 2-column product grid and compact "Page x of y" pagination. There's no horizontal scrolling at any width.
