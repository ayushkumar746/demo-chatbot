# CHATBOT E-COMMERCE FRONTEND — VUE.JS

Build a complete, polished, responsive Vue.js frontend for my existing chatbot/e-commerce demo application.

IMPORTANT:
- All frontend code MUST be inside:

demo-chatbot/frontend/

- Do not modify the backend unless absolutely necessary for API compatibility.
- Use Vue.js for the frontend.
- The backend API already exists at:

http://localhost:8000/api/chat

- The frontend must communicate with the backend using the existing API.
- The UI must be production-quality, responsive, modern, clean, and attractive.
- The application must work on desktop, tablet, and mobile.
- Do not create a fake/mock chatbot response. Use the real backend API.

---

# 1. FRONTEND APPLICATION

Create/complete the Vue.js application inside:

demo-chatbot/frontend/

Recommended structure:

frontend/
├── src/
│   ├── components/
│   │   ├── ChatWindow.vue
│   │   ├── ChatMessage.vue
│   │   ├── ProductList.vue
│   │   ├── ProductCard.vue
│   │   ├── CartSummary.vue
│   │   ├── QuantityControl.vue
│   │   ├── SearchBar.vue
│   │   └── Pagination.vue
│   │
│   ├── views/
│   │   └── ChatbotView.vue
│   │
│   ├── services/
│   │   └── api.js
│   │
│   ├── stores/
│   │   └── cart.js
│   │
│   ├── composables/
│   │   └── useChat.js
│   │
│   ├── assets/
│   ├── App.vue
│   └── main.js
│
├── public/
├── package.json
├── vite.config.js
└── README.md

You may adjust the structure if a better Vue architecture already exists.

---

# 2. TECHNOLOGY

Use:

- Vue 3
- Vite
- JavaScript or TypeScript based on the existing frontend setup
- Vue Router if needed
- Pinia for cart/application state if appropriate
- Axios or native fetch for API calls
- Modern CSS
- Responsive design

Avoid unnecessary dependencies.

First inspect the existing `frontend` folder and reuse existing code where possible.

---

# 3. MAIN PAGE DESIGN

Create a professional chatbot shopping interface.

Desktop layout:

┌───────────────────────────────────────────────────────────┐
│                       CHATBOT                             │
├───────────────────────────────┬───────────────────────────┤
│                               │                           │
│       PRODUCT LIST            │       CHAT WINDOW         │
│                               │                           │
│  Search Products              │  Assistant messages      │
│                               │  User messages            │
│  ┌─────────┐ ┌─────────┐     │                           │
│  │ Product │ │ Product │     │                           │
│  │ Image   │ │ Image   │     │                           │
│  │ Name    │ │ Name    │     │                           │
│  │ ₹40     │ │ ₹50     │     │                           │
│  │  - 1 +  │ │  - 1 +  │     │                           │
│  └─────────┘ └─────────┘     │  Type your request...     │
│                               │  [ Send ]                 │
│  Pagination                   │                           │
└───────────────────────────────┴───────────────────────────┘

Desktop:
- Left side = product browsing
- Right side = chatbot

Mobile:
- Stack the product list and chat naturally.
- Chat should remain easy to use.
- Product cards should become one-column or responsive grid.
- Chat input should remain accessible.

---

# 4. CHAT WINDOW

Create an attractive chat interface on the RIGHT side of the page.

The user should see:

- Chat header
- Assistant avatar/icon
- Conversation messages
- User messages
- Assistant messages
- Loading indicator
- Error messages
- Chat input
- Send button

The user should type ONLY the natural-language query.

Example:

"Add cold drink which have less price 100 RS"

The user must NOT need to enter:

- user_id
- store_id
- session_id

Those values must be maintained automatically by the frontend.

---

# 5. DEFAULT API PARAMETERS

Every API request must automatically include:

```json
{
  "user_id": "user123",
  "store_id": "STORE_1",
  "session_id": "SESSION_1"
}

The user should only enter:

{
  "query": "Add cold drink which have less price 100 RS"
}

The frontend should construct the complete API payload:

{
  "query": "Add cold drink which have less price 100 RS",
  "user_id": "user123",
  "store_id": "STORE_1",
  "session_id": "SESSION_1"
}

Keep these values centralized in frontend configuration/state so they can easily be changed later.

Do not hardcode them in multiple components.

Prefer something like:

const chatContext = {
  user_id: "user123",
  store_id: "STORE_1",
  session_id: "SESSION_1"
};
6. CHAT API

Use:

POST

http://localhost:8000/api/chat

Headers:

accept: */*
Content-Type: application/json

Request:

{
  "query": "Add cold drink which have less price 100 RS",
  "user_id": "user123",
  "store_id": "STORE_1",
  "session_id": "SESSION_1"
}

Do NOT use the curl command from the browser.

Implement this using Axios or fetch.

7. API RESPONSE

The backend returns data similar to:

{
  "response": "Fanta 750ml priced at ₹40 has been added to your cart.\n\nCart (1 item):\n  - Fanta 750ml x1 — ₹40\n\nTotal: ₹40",

  "success": true,

  "intent": {
    "action": "ADD_TO_CART",
    "search_query": "cold drink",
    "category": "cold_drink",
    "max_price": 100,
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
      {
        "product_id": "PROD_005",
        "name": "Fanta 750ml",
        "quantity": 1,
        "price": 40,
        "total_price": 40
      }
    ],

    "total_items": 1,
    "total_price": 40
  },

  "error": null
}

The frontend must properly parse this response.

8. CART SYNCHRONIZATION

This is very important.

When the chatbot returns:

"success": true

and provides:

"cart_state"

the frontend cart MUST immediately synchronize with that response.

For example:

User enters:

"Add cold drink which have less price 100 RS"

Backend returns:

Fanta 750ml
₹40
quantity: 1

Frontend must immediately show:

Cart
Fanta 750ml
₹40
Qty: 1

without requiring a page refresh.

9. DUPLICATE PRODUCT RULE

VERY IMPORTANT:

If a product is already in the cart, do NOT create another duplicate cart item.

Example:

First request:

Add Fanta

Cart:

Fanta x1

Second request:

Add Fanta

Do NOT create:

Fanta x1
Fanta x1

Instead:

Fanta x2

Use:

product_id

as the unique product identifier.

The cart should contain one line item per product.

If the backend already handles duplicate prevention, the frontend must still correctly display the returned cart_state.

10. PRODUCT LIST — LEFT SIDE

The LEFT side should display standard e-commerce products.

Create an attractive product browsing section.

Each product card should display:

Product image
Product name
Product price
Optional brand
Optional category
Quantity
Minus button
Quantity number
Plus button

Example:

┌─────────────────────┐
│ │
│ PRODUCT IMAGE │
│ │
├─────────────────────┤
│ Fanta 750ml │
│ ₹40 │
│ │
│ [ − ] 1 [ + ] │
└─────────────────────┘

Use attractive hover effects.

11. PRODUCT IMAGES

Use proper product image handling.

If the backend/sample product data contains image URLs, use those.

If images are not available, create a clean fallback product-image component rather than broken <img> elements.

Fallback should look professional.

Do not use broken image icons.

12. PRODUCT SEARCH

Add a search bar above the product list.

Example:

🔍 Search products...

Search should allow users to search:

product name
brand
category

Implement debouncing if search is connected to an API.

If the existing backend does not provide a product listing/search API, first inspect the project and create the frontend using a clean service abstraction so a product API can be connected without rewriting the UI.

Do not hardcode the entire product list into UI components.

13. PAGINATION

Product list must support pagination.

Display:

← Previous   1  2  3  4  5   Next →

Make pagination responsive.

On mobile, simplify pagination if necessary.

14. CART DISPLAY

The interface should clearly show the current cart.

Display:

Cart

Fanta 750ml
₹40 × 1

Coca Cola 750ml
₹45 × 2

----------------
3 Items
Total: ₹130

The cart should update immediately when:

chatbot adds a product
plus button is clicked
minus button is clicked
quantity changes

Do not allow quantity to go below 0.

If quantity reaches 0, remove the item from the cart.

15. PLUS / MINUS BUTTONS

Create attractive quantity controls:

[ − ]  1  [ + ]

Requirements:

Plus increases quantity.
Minus decreases quantity.
Quantity cannot become negative.
Clicking minus at quantity 1 should remove the item or reduce it according to the application's cart behavior.
Prevent accidental duplicate items.
Buttons must work on mobile/touch devices.
16. CHAT → CART INTEGRATION

This is the most important feature.

Example:

User types:

Add cold drink which have less price 100 RS

Frontend sends:

{
  "query": "Add cold drink which have less price 100 RS",
  "user_id": "user123",
  "store_id": "STORE_1",
  "session_id": "SESSION_1"
}

Backend returns:

{
  "success": true,
  "cart_state": {
    "items": [
      {
        "product_id": "PROD_005",
        "name": "Fanta 750ml",
        "quantity": 1,
        "price": 40
      }
    ],
    "total_price": 40
  }
}

Frontend must:

Add/update Fanta in cart.
Update quantity.
Update total.
Update item count.
Display the assistant response.
Keep the chat conversation visible.

No page refresh.

17. LOADING STATE

While API is processing:

Show something like:

Assistant is thinking...
● ● ●

Disable Send temporarily to prevent duplicate requests.

Do not allow multiple identical API calls while one request is still pending.

After response:

Enable Send again.
Scroll chat to latest message.
18. ERROR HANDLING

If API returns:

{
  "success": false,
  "error": "..."
}

show a clean error message in the chat.

Do NOT display raw technical stack traces to the user.

Example:

Sorry, I couldn't complete that request.
Please try again.

Log technical details to the browser console during development.

Handle:

network failure
backend unavailable
timeout
HTTP 4xx
HTTP 5xx
malformed response
19. CHAT HISTORY

Maintain chat messages during the current session.

Example:

User:
Add cold drink which have less price 100 RS

Assistant:
Fanta 750ml priced at ₹40 has been added to your cart.

User:
Add another one

Assistant:
Fanta 750ml quantity updated to 2.

Do not reload the page after every message.

20. RESPONSIVE DESIGN

The application MUST work correctly on:

Desktop
Laptop
Tablet
Mobile

Desktop:

Products 60% | Chat 40%

Tablet:

Products
Chat

Mobile:

Products
Cart
Chat

The chat input must never be hidden below the viewport.

Avoid horizontal scrolling.

21. UI / UX DESIGN

Create a modern e-commerce AI assistant design.

Use:

clean typography
rounded cards
subtle shadows
good spacing
attractive buttons
professional icons
smooth hover states
subtle animations
loading animation
sticky chat input
responsive layout

Do NOT overuse animations.

The interface should feel like a real production e-commerce application, not a basic demo.

Use accessible:

buttons
labels
keyboard navigation
focus states
color contrast
22. FRONTEND CONFIGURATION

Create:

.env

or:

.env.example

Use:

VITE_API_BASE_URL=http://localhost:8000
VITE_DEFAULT_USER_ID=user123
VITE_DEFAULT_STORE_ID=STORE_1
VITE_DEFAULT_SESSION_ID=SESSION_1

Do not hardcode API URLs throughout the application.

API service should use:

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
23. CORS

If the Vue frontend runs on a different port, for example:

http://localhost:5173

and FastAPI runs on:

http://localhost:8000

make sure the backend CORS configuration allows the frontend origin.

Only modify backend CORS if required for the frontend to work.

Do not make CORS unnecessarily permissive in production.

24. DEPENDENCIES

Inspect the current frontend/package.json first.

Install only the dependencies actually required.

At minimum, use:

Vue 3
Vite

Use Pinia if appropriate for cart state.

Use Axios if preferred for API calls.

Do not install unnecessary UI frameworks just for basic components.

25. RUN THE FRONTEND

Make sure the frontend can be started from:

cd demo-chatbot/frontend

Install:

npm install

Run:

npm run dev

Expected development URL:

http://localhost:5173

Verify that the frontend can communicate with:

http://localhost:8000/api/chat
26. TEST THE COMPLETE FLOW

After implementation, actually run the frontend and test:

Test 1

Input:

Add cold drink which have less price 100 RS

Verify:

API called
correct payload sent
assistant response displayed
product added to cart
cart count updated
cart total updated
Test 2

Send the same request again.

Verify:

Fanta x2

NOT:

Fanta x1
Fanta x1
Test 3

Click:

+

Verify quantity increases.

Test 4

Click:

-

Verify quantity decreases.

Test 5

Search products.

Verify search results.

Test 6

Navigate pagination.

Verify product pages change correctly.

Test 7

Refresh page.

Handle cart/session state according to the existing application architecture.

27. IMPORTANT IMPLEMENTATION RULES

Before writing code:

Inspect the existing frontend directory.
Determine whether Vue/Vite is already configured.
Reuse existing components where possible.
Do not unnecessarily rewrite working code.
Inspect the backend API contract.
Use the actual /api/chat response structure.
Keep API communication in a dedicated service.
Keep cart state centralized.
Keep chat state separate from UI components.
Keep user/store/session context centralized.

Do not create fake API responses.

Do not hardcode product results in the chat.

Do not duplicate products in the cart.

28. FINAL DELIVERABLE

Everything related to the Vue frontend must be inside:

demo-chatbot/frontend/

At the end:

Install all required frontend dependencies.
Start the Vue application.
Verify the application opens successfully.
Verify /api/chat integration.
Test the exact user prompt.
Verify cart synchronization.
Verify duplicate prevention.
Verify product search.
Verify pagination.
Verify responsive layout.
Fix all frontend errors found during testing.

Finally provide a concise report containing:

Files created/modified
Dependencies installed
How to start frontend
Frontend URL
Backend URL
API integration details
Cart synchronization approach
Duplicate-product handling
Search implementation
Pagination implementation
Responsive behavior
Any remaining issues

The final result should be a polished, responsive Vue.js e-commerce chatbot UI where the user can simply type:

"Add cold drink which have less price 100 RS"

and the real backend API is called automatically, the product is added to the cart, and the updated cart is immediately reflected in the UI.