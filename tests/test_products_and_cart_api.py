"""Tests for the product browsing and cart REST endpoints used by the frontend."""
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from main import app

USER = {"user_id": "ui_user", "store_id": "STORE_1"}


@pytest.fixture
def client():
    return TestClient(app)


def first_available_product(client, **params):
    items = client.get("/api/products", params={"page_size": 50, **params}).json()["items"]
    return next(item for item in items if item["available"] and item["inventory"] >= 3)


def test_products_are_paginated(client, wired_app):
    first = client.get("/api/products", params={"page": 1, "page_size": 12}).json()
    second = client.get("/api/products", params={"page": 2, "page_size": 12}).json()

    assert len(first["items"]) == 12
    assert first["total"] > 12 and first["total_pages"] == -(-first["total"] // 12)
    assert {p["id"] for p in first["items"]}.isdisjoint({p["id"] for p in second["items"]})
    assert {p["store_id"] for p in first["items"]} == {"STORE_1"}


def test_products_search_by_name_brand_and_category(client, wired_app):
    for query, check in [
        ("fanta", lambda p: "fanta" in p["name"].lower()),
        ("kingfisher", lambda p: p["brand"] == "Kingfisher"),
        ("cold drink", lambda p: p["category"] == "cold_drink"),
    ]:
        body = client.get("/api/products", params={"q": query}).json()
        assert body["total"] > 0, query
        assert all(check(product) for product in body["items"]), query


def test_products_include_images(client, wired_app):
    product = client.get("/api/products").json()["items"][0]
    assert product["image_url"].endswith(".svg")


def test_products_unknown_store_and_bad_paging(client, wired_app):
    assert client.get("/api/products", params={"store_id": "STORE_404"}).status_code == 404
    assert client.get("/api/products", params={"page": 0}).status_code == 422
    assert client.get("/api/products", params={"page_size": 500}).status_code == 422


def test_cart_quantity_set_increment_decrement_and_remove(client, wired_app):
    product = first_available_product(client)
    url = f"/api/cart/items/{product['id']}"

    cart = client.put(url, json={**USER, "quantity": 1}).json()["cart"]
    assert [(i["product_id"], i["quantity"]) for i in cart["items"]] == [(product["id"], 1)]

    cart = client.put(url, json={**USER, "quantity": 2}).json()["cart"]
    assert len(cart["items"]) == 1 and cart["items"][0]["quantity"] == 2
    assert cart["total_price"] == 2 * product["price"]

    cart = client.put(url, json={**USER, "quantity": 1}).json()["cart"]
    assert cart["items"][0]["quantity"] == 1

    cart = client.put(url, json={**USER, "quantity": 0}).json()["cart"]
    assert cart["items"] == [] and cart["total_price"] == 0

    assert client.get("/api/cart", params=USER).json()["items"] == []


def test_cart_rejects_negative_and_excess_quantity(client, wired_app):
    product = first_available_product(client)
    url = f"/api/cart/items/{product['id']}"
    assert client.put(url, json={**USER, "quantity": -1}).status_code == 422

    too_many = settings.max_quantity_per_item + 1
    response = client.put(url, json={**USER, "quantity": too_many})
    assert response.status_code == 400
    assert "Maximum quantity" in response.json()["detail"]


def test_cart_rejects_unavailable_product(client, wired_app, catalog):
    unavailable = next(r for r in catalog if r["store_id"] == "STORE_1" and not r["available"])
    response = client.put(f"/api/cart/items/{unavailable['product_id']}", json={**USER, "quantity": 1})
    assert response.status_code == 400


def test_cart_rejects_product_from_other_store(client, wired_app, catalog):
    other = next(r for r in catalog if r["store_id"] == "STORE_2")
    response = client.put(f"/api/cart/items/{other['product_id']}", json={**USER, "quantity": 1})
    assert response.status_code == 400


def test_chat_and_cart_api_share_the_same_cart(client, wired_app):
    chat_cart = client.post("/api/chat", json={
        "query": "Add cold drink which have less price 100 RS", **USER, "session_id": "SESSION_1",
    }).json()["cart_state"]
    assert client.get("/api/cart", params=USER).json() == chat_cart


def test_cors_allows_vite_dev_origin(client):
    response = client.options("/api/chat", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_rejects_unknown_origin(client):
    response = client.options("/api/chat", headers={
        "Origin": "http://evil.example",
        "Access-Control-Request-Method": "POST",
    })
    assert "access-control-allow-origin" not in response.headers
