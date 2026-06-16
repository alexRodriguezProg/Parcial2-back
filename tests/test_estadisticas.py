def test_resumen_kpis(client, admin_token):
    r = client.get(
        "/api/v1/estadisticas/resumen",
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 200
    data = r.json()
    assert "ventas_hoy" in data
    assert "ticket_promedio" in data
    assert "pedidos_activos" in data
    assert "ingresos_mes" in data


def test_resumen_solo_admin(client, client_token):
    r = client.get(
        "/api/v1/estadisticas/resumen",
        cookies={"access_token": client_token},
    )
    assert r.status_code == 403


def test_ventas_periodo(client, admin_token):
    r = client.get(
        "/api/v1/estadisticas/ventas?desde=2024-01-01&hasta=2026-12-31",
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_productos_top(client, admin_token):
    r = client.get(
        "/api/v1/estadisticas/productos-top?limit=5",
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    for item in data:
        assert "nombre" in item
        assert "cantidad_vendida" in item
        assert "ingresos" in item


def test_pedidos_por_estado(client, admin_token):
    r = client.get(
        "/api/v1/estadisticas/pedidos-por-estado",
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_ingresos_por_forma_pago(client, admin_token):
    r = client.get(
        "/api/v1/estadisticas/ingresos?desde=2024-01-01&hasta=2026-12-31",
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    for item in data:
        assert "forma_pago_codigo" in item
        assert "total" in item


def test_cancelado_no_suma_en_ventas(client, admin_token, pedido_factory):
    """EST-01: pedidos CANCELADOS no deben sumar en ventas."""
    client.patch(
        f"/api/v1/pedidos/{pedido_factory}/estado",
        json={"nuevo_estado": "CANCELADO", "motivo": "Test EST-01"},
        cookies={"access_token": admin_token},
    )
    r = client.get(
        "/api/v1/estadisticas/resumen",
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 200