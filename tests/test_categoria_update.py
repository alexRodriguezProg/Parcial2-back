import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.main import app
from app.models import Categoria
from tests.conftest import engine_test


def test_update_categoria_change_name(client: TestClient, admin_token: str):
    # First create a category
    r = client.post(
        "/api/v1/categorias/",
        json={"nombre": "Bebidas"},
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 201, r.text
    cat_id = r.json()["id"]

    # Now update the name
    r = client.put(
        f"/api/v1/categorias/{cat_id}",
        json={"nombre": "Bebidas Frias", "parent_id": None},
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 200, f"Status: {r.status_code}, Body: {r.text}"


def test_update_categoria_change_parent(client: TestClient, admin_token: str):
    # Create a root category
    r = client.post(
        "/api/v1/categorias/",
        json={"nombre": "Comidas"},
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 201, r.text
    parent_id = r.json()["id"]

    # Create a child category
    r = client.post(
        "/api/v1/categorias/",
        json={"nombre": "Pastas", "parent_id": parent_id},
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 201, r.text
    child_id = r.json()["id"]

    # Change child's parent to None (make it root)
    r = client.put(
        f"/api/v1/categorias/{child_id}",
        json={"nombre": "Pastas", "parent_id": None},
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 200, f"Status: {r.status_code}, Body: {r.text}"


def test_update_categoria_only_name(client: TestClient, admin_token: str):
    # Create a category
    r = client.post(
        "/api/v1/categorias/",
        json={"nombre": "Snacks"},
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 201, r.text
    cat_id = r.json()["id"]

    # Update only name (no parent_id in payload at all)
    r = client.put(
        f"/api/v1/categorias/{cat_id}",
        json={"nombre": "Snacks Saludables"},
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 200, f"Status: {r.status_code}, Body: {r.text}"


def test_update_categoria_empty_parent(client: TestClient, admin_token: str):
    """Simulate frontend sending parent_id as null (user selected 'Ninguna')."""
    r = client.post(
        "/api/v1/categorias/",
        json={"nombre": "Categoria Test"},
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 201, r.text
    cat_id = r.json()["id"]

    # Update with parent_id explicitly null (like frontend does)
    r = client.put(
        f"/api/v1/categorias/{cat_id}",
        json={"nombre": "Categoria Test", "parent_id": None},
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 200, f"Status: {r.status_code}, Body: {r.text}"
