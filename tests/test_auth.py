def test_register_ok(client):
    r = client.post("/api/v1/auth/register", json={
        "nombre": "Juan", "apellido": "Perez",
        "email": "juan@test.com", "password": "Segura1234!",
    })
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["usuario"]["email"] == "juan@test.com"


def test_register_email_duplicado(client):
    payload = {
        "nombre": "Ana", "apellido": "Lopez",
        "email": "ana@test.com", "password": "Segura1234!",
    }
    client.post("/api/v1/auth/register", json=payload)
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 409


def test_login_ok(client, admin_token):
    assert admin_token is not None
    assert len(admin_token) > 10


def test_login_credenciales_invalidas(client):
    r = client.post("/api/v1/auth/login", json={
        "email": "noexiste@test.com",
        "password": "wrongpassword",
    })
    assert r.status_code == 401


def test_login_password_incorrecta(client):
    client.post("/api/v1/auth/register", json={
        "nombre": "Pedro", "apellido": "Gil",
        "email": "pedro@test.com", "password": "Correcta1234!",
    })
    r = client.post("/api/v1/auth/login", json={
        "email": "pedro@test.com",
        "password": "Incorrecta999!",
    })
    assert r.status_code == 401


def test_me_autenticado(client, admin_token):
    r = client.get(
        "/api/v1/auth/me",
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 200
    assert r.json()["email"] == "admin@test.com"


def test_me_sin_token(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_logout(client, admin_token):
    r = client.post(
        "/api/v1/auth/logout",
        cookies={"access_token": admin_token},
    )
    assert r.status_code == 200


def test_rate_limit(client):
    """Después de 5 intentos fallidos debe devolver 429."""
    for _ in range(5):
        client.post("/api/v1/auth/login", json={
            "email": "ratelimit@test.com",
            "password": "wrong",
        })
    r = client.post("/api/v1/auth/login", json={
        "email": "ratelimit@test.com",
        "password": "wrong",
    })
    assert r.status_code == 429
    assert "Retry-After" in r.headers