******** CHATBOAT***************
FASTAPI SETUP IMPLEMENTATION API WITH SEAGGER
CREATE .env file also

Haan. Aapke use case ke liye simple chain se zyada LangGraph-based planner + specialized agents + deterministic tools architecture suitable hai.

Aapka example:

“Add cold drink which has less price than 100 RS.”

Iska production flow ideally:

User
 │
 ▼
FastAPI
 │
 ▼
Planner / Intent Agent
 │
 ├── Understand:
 │     category = cold drink
 │     max_price = ₹100
 │     action = ADD_TO_CART
 │
 ▼
Product Discovery Agent
 │
 ▼
Semantic/Product Search Tool
 │
 ▼
Candidate Products
 │
 ▼
Python Filter Tool
 │     price < ₹100
 │
 ▼
Product Selection Agent
 │
 ▼
Selected Product
 │
 ▼
Cart Validation Tool
 │
 ├── Already in cart?
 ├── Available?
 ├── Correct store?
 └── Quantity?
 │
 ▼
Cart Action Tool
 │
 ▼
Add Product API
 │
 ▼
Cart State Refresh
 │
 ▼
Response Agent
 │
 ▼
"Pepsi 500ml ₹45 has been added to your cart."
सबसे important production principle

LLM को price calculation, inventory validation या cart mutation खुद नहीं करनी चाहिए।

LLM:

Understand → Plan → Select tool → Explain

Python/API:

Search → Filter → Validate → Calculate → Add to cart

इस separation से hallucination और unsafe cart changes काफी कम होते हैं।

1. Recommended Production Architecture

मैं आपके case में LangGraph + Planner + specialized workers + deterministic tools रखूंगा।

                         ┌────────────────────┐
                         │       User         │
                         └─────────┬──────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │      FastAPI       │
                         └─────────┬──────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │      LangGraph State        │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │       Planner Agent         │
                    │                             │
                    │ Understand user request     │
                    │ Create execution plan       │
                    └──────────────┬──────────────┘
                                   │
                  ┌────────────────┼────────────────┐
                  │                │                │
                  ▼                ▼                ▼
          Product Agent       Cart Agent       User Agent
                  │                │
                  ▼                ▼
          Product Tools       Cart Tools
                  │                │
                  ▼                ▼
          Product Search       Cart API
                  │
                  ▼
          Python Filter
                  │
                  ▼
          Product Selection
                  │
                  └────────┬───────┘
                           ▼
                    Validation Agent
                           │
                           ▼
                     Cart Action
                           │
                           ▼
                      Cart API
                           │
                           ▼
                    Updated Cart
                           │
                           ▼
                    Response Agent
                           │
                           ▼
                         User
2. Example request

User:

Add cold drink which have less price 100 RS

Planner को ideally यह structured plan बनाना चाहिए:

{
  "intent": "ADD_PRODUCT_TO_CART",
  "category": "cold_drink",
  "max_price": 100,
  "currency": "INR",
  "quantity": 1
}

लेकिन मैं planner को directly product select करने नहीं दूंगा।

Planner सिर्फ intent + constraints + required workflow निकालेगा।

3. LangGraph State

सबसे important चीज़ है आपका shared state.

Example:

from typing import TypedDict, Any


class AgentState(TypedDict, total=False):

    user_query: str

    user_id: str
    store_id: str

    intent: dict

    plan: dict

    search_query: str

    candidate_products: list

    filtered_products: list

    selected_product: dict

    cart: dict

    validation_result: dict

    action_result: dict

    final_response: str

    error: str

Graph के सभी nodes इसी state को read/update करेंगे।

4. Why State is important?

Suppose:

Planner
 ↓
Product Search
 ↓
Filter
 ↓
Cart Validation
 ↓
Add Cart

हर agent को पूरा conversation दोबारा देने की जरूरत नहीं।

State:

{
    user_query,
    intent,
    candidate_products,
    selected_product,
    cart,
    validation_result
}

एक shared context की तरह काम करेगा।

5. Planner Agent

Planner का काम:

User क्या चाहता है और उसके लिए कौन-कौन से steps चाहिए?

User:

Add cold drink which have less price 100 RS

Planner:

{
  "goal": "add_product_to_cart",
  "constraints": {
    "category": "cold_drink",
    "max_price": 100
  },
  "quantity": 1,
  "requires": [
    "product_search",
    "price_filter",
    "cart_validation",
    "add_to_cart"
  ]
}
6. Planner को over-smart मत बनाओ

Production में एक common mistake है:

LLM को पूरा control दे दिया

मैं ऐसा नहीं करूंगा।

Planner को limited structured output दो:

class ShoppingIntent(BaseModel):
    action: Literal[
        "SEARCH_PRODUCT",
        "ADD_TO_CART",
        "REMOVE_FROM_CART",
        "UPDATE_CART",
        "VIEW_CART"
    ]

    category: str | None = None
    max_price: float | None = None
    min_price: float | None = None
    quantity: int = 1

इससे LLM का output controlled रहेगा।

7. Product Discovery Agent

Planner के बाद:

Product Discovery Agent

इसका काम:

"cold drink"

को product search system तक भेजना।

आपका semantic search system internally कुछ भी हो सकता है:

Vector DB
ElasticSearch
OpenSearch
Database
Hybrid Search

Agent को implementation जानने की जरूरत नहीं।

Tool:

search_products(
    query="cold drink",
    store_id="123"
)

Return:

[
    {
        "id": "P1",
        "name": "Pepsi 500ml",
        "price": 45
    },
    {
        "id": "P2",
        "name": "Coca Cola 750ml",
        "price": 110
    },
    {
        "id": "P3",
        "name": "Sprite 500ml",
        "price": 50
    }
]
8. अब LLM नहीं — Python filtering

User ने कहा:

less price than 100

यह deterministic constraint है।

इसलिए:

def filter_by_price(products, max_price):
    return [
        product
        for product in products
        if product["price"] < max_price
    ]

Result:

[
    {
        "id": "P1",
        "name": "Pepsi 500ml",
        "price": 45
    },
    {
        "id": "P3",
        "name": "Sprite 500ml",
        "price": 50
    }
]

यहाँ LLM से comparison करवाने की जरूरत नहीं है।

9. अब ambiguity आती है

अब दो products हैं:

Pepsi  ₹45
Sprite ₹50

User ने यह नहीं बताया:

Which one?

यहाँ आपका system automatically Pepsi choose करे या clarification मांगे — यह business policy है।

Production में मैं इसे explicit policy बनाऊंगा:

If multiple valid products:
    ask user to choose

Response:

I found two cold drinks under ₹100:

1. Pepsi 500ml — ₹45
2. Sprite 500ml — ₹50

Which one would you like me to add?

यह safest behavior है।

10. अगर business rule कहता है cheapest product

अगर product requirement है:

"which has less price"

तो इसका अर्थ cheapest matching product भी लिया जा सकता है।

Python:

def select_cheapest(products):
    return min(
        products,
        key=lambda product: product["price"]
    )

Result:

{
    "id": "P1",
    "name": "Pepsi 500ml",
    "price": 45
}

अब:

Selected Product
Pepsi 500ml
₹45
11. Cart Agent

अब सीधे add मत करो।

पहले cart inspect करो।

Tool:

get_cart(user_id)

Result:

{
    "cart_id": "C123",
    "items": [
        {
            "product_id": "P1",
            "name": "Pepsi 500ml",
            "quantity": 1
        }
    ]
}

Agent/tool देखेगा:

Is P1 already in cart?

हाँ।

अब business policy decide करेगी:

increase quantity?
or
ask user?
12. Cart validation

मैं इसे deterministic Python function रखूंगा:

def validate_cart_addition(cart, product_id, quantity):

    for item in cart["items"]:

        if item["product_id"] == product_id:

            return {
                "valid": False,
                "reason": "already_in_cart"
            }

    return {
        "valid": True
    }

लेकिन production में और validations होंगे:

Product exists
Product active
Product available
Inventory available
Correct store
Price valid
Promotion valid
Quantity allowed
Age restriction
Membership restriction
EBT restriction
13. Add-to-cart Tool

Actual mutation हमेशा API/tool करेगा:

def add_to_cart(
    cart_id: str,
    product_id: str,
    quantity: int
):
    ...

LLM सिर्फ tool call request generate करेगा।

Example:

{
    "tool": "add_to_cart",
    "arguments": {
        "cart_id": "C123",
        "product_id": "P1",
        "quantity": 1
    }
}

Backend actual API call करेगा।

14. Add करने के बाद Cart Refresh

यह बहुत important है।

गलत:

add_to_cart()
↓
assume success
↓
tell user

Better:

add_to_cart()
      ↓
API success
      ↓
get_cart()
      ↓
verify item exists
      ↓
final response

इससे system actual state पर answer देता है।

15. Complete LangGraph

आपका graph roughly:

START
  │
  ▼
planner
  │
  ▼
route_intent
  │
  ├───────────────┐
  │               │
  ▼               ▼
product_flow    cart_flow
  │
  ▼
product_search
  │
  ▼
deterministic_filter
  │
  ▼
product_selection
  │
  ▼
cart_validation
  │
  ▼
add_to_cart
  │
  ▼
verify_cart
  │
  ▼
response
  │
  ▼
 END
16. LangGraph क्यों?

आपके use case में LangGraph useful है क्योंकि workflow में:

conditional routing
state
loops
human approval
tool calls
retry
validation
error handling

सब हो सकते हैं।

Example:

Search
 ↓
No products?
 ↓
Broaden search
 ↓
Search again

या:

Multiple products?
 ↓
Ask user
 ↓
Wait
 ↓
Continue graph

यह simple chain से ज्यादा natural है।

17. Multiple Agents कैसे रखूँगा?

मैं बहुत ज्यादा agents नहीं बनाऊंगा।

Recommended:
1. Planner Agent

2. Product Agent

3. Cart Agent

4. Response Agent

और बाकी functionality:

Tools

के रूप में।

18. Why not 10 agents?

यह architecture avoid करें:

Price Agent
Promotion Agent
EBT Agent
Inventory Agent
Search Agent
Cart Agent
Drink Agent
Discount Agent
Tax Agent
Response Agent

यह unnecessarily complex हो जाएगा।

Better:

Planner
   ↓
Specialized Agent
   ↓
Tools

Tools:

search_products
filter_products
get_product
get_cart
validate_cart
add_to_cart
remove_from_cart
update_cart
get_promotions
check_ebt
19. Tool design सबसे important है

Tool descriptions अच्छे होने चाहिए।

Example:

@tool
def search_products(
    query: str,
    store_id: str
):
    """
    Search products available in a specific store.

    Use this tool when the user wants to find
    products based on natural-language criteria.

    Returns candidate products only.
    Price and business-rule filtering must be
    performed separately.
    """

LLM tool का purpose समझ सकेगा।

20. Tool categories

मैं tools को 4 categories में रखूंगा।

Product tools
search_products
get_product
check_inventory
Cart tools
get_cart
add_to_cart
remove_from_cart
update_cart
clear_cart
Business tools
get_promotions
check_ebt_eligibility
get_membership_benefits
calculate_cart
User tools
get_user_profile
get_subscription
get_delivery_address
21. आपके complete example का execution

User:

Add cold drink which have less price 100 RS
Step 1

FastAPI:

{
    "query": "Add cold drink which have less price 100 RS"
}
Step 2

Planner:

{
    "action": "ADD_TO_CART",
    "category": "cold drink",
    "max_price": 100,
    "quantity": 1
}
Step 3

Product search:

search_products(
    query="cold drink",
    store_id="STORE_1"
)
Step 4

Products:

Pepsi ₹45
Sprite ₹50
Coke ₹110
Mountain Dew ₹60
Step 5

Python:

price < 100

Result:

Pepsi ₹45
Sprite ₹50
Mountain Dew ₹60
Step 6

Selection policy:

CHEAPEST_MATCH

Result:

Pepsi ₹45
Step 7

Cart:

Check Pepsi already exists?
Step 8

If not:

add_to_cart(Pepsi, quantity=1)
Step 9

Refresh cart:

get_cart()
Step 10

Final response:

Pepsi 500ml priced at ₹45 has been added to your cart.
22. अगर product नहीं मिले
User
 ↓
Search
 ↓
0 products

Agent को hallucinate नहीं करना चाहिए।

Response:

I couldn't find a cold drink under ₹100 in your selected store.
23. अगर तीन products मिले

अगर user ने कहा:

Add cold drink below ₹100

और 3 मिले।

अगर policy:

ask_confirmation

तो:

I found 3 cold drinks under ₹100:

1. Pepsi 500ml — ₹45
2. Sprite 500ml — ₹50
3. Mountain Dew 500ml — ₹60

Which one would you like me to add?
24. अगर user कहता है "cheapest one"

अब same graph continue हो सकता है:

User:
cheapest one

Planner:

{
    "selection_strategy": "CHEAPEST"
}

Python:

min(products, key=lambda x: x["price"])

Then add.

25. LLM कौन सा use करें?

आपके use case में मैं एक ही model हर काम के लिए use नहीं करूंगा।

Production architecture में model selection task-wise रख सकता है।

Planner / complex reasoning

OpenAI GPT-5.6-class model अच्छा fit है।

आपका planner:

natural language
        ↓
constraints
        ↓
structured plan

जैसा complex reasoning करेगा।

Simple classification / extraction

Smaller/cheaper model use किया जा सकता है अगर evaluation में accuracy sufficient हो।

Final response

Smaller model भी पर्याप्त हो सकता है।

26. लेकिन अभी PoC में

आप initially:

GPT-5.6

से पूरा flow test करो।

पहले accuracy establish करो।

फिर measure करो:

Planner accuracy
Tool selection accuracy
Product selection accuracy
Cart validation accuracy
Latency
Cost

उसके बाद smaller model पर optimize करो।

पहले cost optimize मत करो; पहले behavior establish करो।

27. LangGraph + LangChain architecture

Production code structure मैं ऐसा रखूंगा:

app/
│
├── api/
│   └── routes/
│       └── agent.py
│
├── agent/
│   ├── graph.py
│   ├── state.py
│   ├── planner.py
│   ├── product_agent.py
│   ├── cart_agent.py
│   └── response_agent.py
│
├── tools/
│   ├── product_tools.py
│   ├── cart_tools.py
│   ├── promotion_tools.py
│   └── user_tools.py
│
├── services/
│   ├── product_service.py
│   ├── cart_service.py
│   └── promotion_service.py
│
├── schemas/
│   ├── intent.py
│   ├── product.py
│   ├── cart.py
│   └── response.py
│
├── prompts/
│   ├── planner.py
│   ├── product.py
│   └── response.py
│
└── tests/
    ├── test_planner.py
    ├── test_product_agent.py
    ├── test_cart_agent.py
    └── test_end_to_end.py
28. आपके पहले वाले learning roadmap को production roadmap बनाओ

आपका existing:

1. LLM basics
2. Structured Output
3. Tool Calling
4. LangChain Runnables / LCEL
5. Agent
6. State management
7. Cart as structured state
8. Deterministic Python functions
9. Product Search / RAG
10. Agent + Tools + APIs
11. Evaluation / testing

मैं इसमें LangGraph और production safety जोड़कर इसे ऐसे करूँगा:

01. LLM Fundamentals
        ↓
02. Prompt Engineering
        ↓
03. Structured Output / Pydantic
        ↓
04. Tool Calling
        ↓
05. LangChain Runnables / LCEL
        ↓
06. LangGraph Fundamentals
        ↓
07. Graph State
        ↓
08. Planner Node
        ↓
09. Product Agent
        ↓
10. Cart Agent
        ↓
11. Deterministic Python Business Rules
        ↓
12. Product Search / Semantic Search
        ↓
13. Vector DB / RAG where required
        ↓
14. API Tools / FastAPI
        ↓
15. Human-in-the-loop
        ↓
16. Validation & Guardrails
        ↓
17. Retry / Error Handling
        ↓
18. Observability / Tracing
        ↓
19. Evaluation
        ↓
20. Production Optimization
29. सबसे important Production Rules

आपके shopping agent में मैं ये rules mandatory रखूंगा:

Rule 1 — Never hallucinate products

अगर API ने product नहीं दिया:

Don't invent product.
Rule 2 — Never trust LLM for price calculation

Use Python/API.

Rule 3 — Never mutate cart without validation
get cart
 ↓
validate
 ↓
action
Rule 4 — After mutation verify state
add
 ↓
refresh cart
 ↓
verify
Rule 5 — Ambiguous request → clarification
"Add a drink"

अगर 50 drinks हैं:

Which drink?
Rule 6 — Tool permissions

Agent को सिर्फ allowed tools मिलें।

Rule 7 — Idempotency

Repeated request से accidental duplicate additions नहीं होने चाहिए।

Rule 8 — API failures
timeout
401
404
500
inventory changed

इनका proper handling होना चाहिए।

30. Evaluation — यह आपके R&D का सबसे important हिस्सा होगा

आप 50–100 test queries बनाओ:

Add cold drink under ₹100

Find me a cheap cold drink and add it

Can you add a soda below 100 rupees?

Put the cheapest cold drink in my cart

I want a drink for less than ₹100

Add something cold under 100

Find me a Pepsi under ₹100

Add the cheapest eligible drink

Can you put a cold beverage below 100 in my cart?

फिर expected output define करो:

intent correct?
category correct?
max_price correct?
search called?
filter correct?
selected product correct?
cart checked?
add API called?
final answer correct?

आपका evaluation table:

Test	Intent	Search	Filter	Selection	Cart Check	Add	Result
Query 1	✅	✅	✅	✅	✅	✅	Pass
Query 2	✅	✅	✅	✅	✅	✅	Pass
Query 3	✅	✅	❌	—	—	—	Fail

यहीं से पता चलेगा कि आपका Agent actually production-ready है या सिर्फ demo में काम कर रहा है।

31. मेरा recommended final architecture

आपके exact project के लिए:

                    ┌───────────────┐
                    │     User      │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    FastAPI    │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   LangGraph   │
                    │     State     │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Planner Agent │
                    └───────┬───────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
        ┌────────────────┐    ┌────────────────┐
        │ Product Agent  │    │   Cart Agent   │
        └───────┬────────┘    └───────┬────────┘
                │                     │
                ▼                     ▼
        Product Search             Get Cart
                │                     │
                ▼                     ▼
        Candidate Products       Cart Structure
                │
                ▼
       Deterministic Python
            Filtering
                │
                ▼
       Product Selection
                │
                └──────────┐
                           ▼
                  Cart Validation
                           │
                           ▼
                    Add Cart Tool
                           │
                           ▼
                    Verify Cart
                           │
                           ▼
                  Response Agent
                           │
                           ▼
                         User
Technology stack
FastAPI
   +
LangGraph
   +
LangChain
   +
OpenAI GPT-5.6-class model
   +
Pydantic
   +
Your Product Search API
   +
Your Cart API
   +
PostgreSQL / Redis for application state as appropriate
   +
LangSmith / equivalent observability
   +
pytest + evaluation dataset



