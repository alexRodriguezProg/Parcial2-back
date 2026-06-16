from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, status

MAX_INTENTOS    = 5
VENTANA_MINUTOS = 15

_intentos: dict[str, list[datetime]] = defaultdict(list)


def _limpiar_viejos(ip: str) -> None:
    corte = datetime.utcnow() - timedelta(minutes=VENTANA_MINUTOS)
    _intentos[ip] = [t for t in _intentos[ip] if t > corte]


def verificar_rate_limit(request: Request) -> None:
    ip = request.client.host  # type: ignore
    _limpiar_viejos(ip)
    if len(_intentos[ip]) >= MAX_INTENTOS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos fallidos. Intentá de nuevo en {VENTANA_MINUTOS} minutos.",
            headers={"Retry-After": str(VENTANA_MINUTOS * 60)},
        )


def registrar_intento_fallido(request: Request) -> None:
    ip = request.client.host # type: ignore
    _intentos[ip].append(datetime.utcnow())


def limpiar_intentos(request: Request) -> None:
    ip = request.client.host # type: ignore
    _intentos[ip] = []