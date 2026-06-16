def test_crear_pedido_ok(client, client_token, producto_factory):
    r = client.post(
        "/api/v1/pedidos/",
        json={
            "items": [{"producto_id": producto_factory, "cantidad": 2, "personalizacion": None}],
            "forma_pago_codigo": "EFECTIVO",
        },
        cookies={"access_token": client_token},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["estado_codigo"] == "PENDIENTE"
    assert data["total"] > 0
    assert len(data["detalles"]) == 1
    assert len(data["historial"]) == 1
    assert data["historial"][0]["estado_desde"] is None  # RN-02


def test_crear_pedido_sin_auth(client, producto_factory):
    r = client.post(
        "/api/v1/pedidos/",
        json={
            "items": [{"producto_id": producto_factory, "cantidad": 1, "personalizacion": None}],
            "forma_pago_codigo": "EFECTIVO",
        },
    )
    assert r.status_code == 401


def test_crear_pedido_stock_insuficiente(client, client_token, producto_factory):
    r = client.post(
        "/api/v1/pedidos/",
        json={
            "items": [{"producto_id": producto_factory, "cantidad": 9999, "personalizacion": None}],
            "forma_pago_codigo": "EFECTIVO",
        },
        cookies={"access_token": client_token},
    )
    assert r.status_code == 400
    assert "Stock insuficiente" in r.json()["detail"]


def test_crear_pedido_producto_inexistente(client, client_token):
    r = client.post(
        "/api/v1/pedidos/",
        json={
            "items": [{"producto_id": 99999, "cantidad": 1, "personalizacion": None}],
            "forma_pago_codigo": "EFECTIVO",
        },
        cookies={"access_token": client_token},
    )
    assert r.status_code == 404


def test_avanzar_estado_valido(client, admin_token, pedido_factory):
    r = client.patch(
        f"/api/v1/pedidos/{pedido_factory}/estado",
        json={"nuevo_estado": "CONFIRMADO", "motivo": None},
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 200
    assert r.json()["estado_codigo"] == "CONFIRMADO"


def test_avanzar_estado_invalido(client, admin_token, pedido_factory):
    """No se puede ir de PENDIENTE a ENTREGADO directamente."""
    r = client.patch(
        f"/api/v1/pedidos/{pedido_factory}/estado",
        json={"nuevo_estado": "ENTREGADO", "motivo": None},
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 422


def test_avanzar_estado_terminal(client, admin_token, pedido_factory):
    """RN-01: estado terminal no admite transiciones."""
    client.patch(
        f"/api/v1/pedidos/{pedido_factory}/estado",
        json={"nuevo_estado": "CANCELADO", "motivo": "Test cancelación"},
        cookies={"access_token": admin_token},
    )
    r = client.patch(
        f"/api/v1/pedidos/{pedido_factory}/estado",
        json={"nuevo_estado": "PENDIENTE", "motivo": None},
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 422


def test_cancelar_sin_motivo(client, admin_token, pedido_factory):
    """RN-05: motivo obligatorio al cancelar."""
    r = client.patch(
        f"/api/v1/pedidos/{pedido_factory}/estado",
        json={"nuevo_estado": "CANCELADO", "motivo": None},
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 422


def test_historial_append_only(client, admin_token, pedido_factory):
    """RN-03: cada transición agrega un registro al historial."""
    client.patch(
        f"/api/v1/pedidos/{pedido_factory}/estado",
        json={"nuevo_estado": "CONFIRMADO", "motivo": None},
        cookies={"access_token": admin_token},
    )
    r = client.get(
        f"/api/v1/pedidos/{pedido_factory}",
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 200
    historial = r.json()["historial"]
    assert len(historial) == 2
    assert historial[0]["estado_desde"] is None
    assert historial[1]["estado_desde"] == "PENDIENTE"
    assert historial[1]["estado_hacia"] == "CONFIRMADO"


def test_cliente_no_ve_pedido_ajeno(client, client_token, pedido_factory):
    """CLIENT solo accede a sus propios pedidos."""
    client.post("/api/v1/auth/register", json={
        "nombre": "Otro", "apellido": "Cliente",
        "email": "otro@test.com", "password": "Otro1234!",
    })
    r2 = client.post("/api/v1/auth/login", json={
        "email": "otro@test.com", "password": "Otro1234!",
    })
    otro_token = r2.json()["access_token"]
    r = client.get(
        f"/api/v1/pedidos/{pedido_factory}",
        cookies={"access_token": otro_token},
    )
    assert r.status_code == 403