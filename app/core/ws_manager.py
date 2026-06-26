import json
from datetime import datetime, timezone
from typing import Dict, Set
from fastapi import WebSocket


class WSManager:
    """
    Singleton que gestiona el pool de conexiones WebSocket.
    Canales:
      - pedido_{id}  → cliente dueño del pedido
      - admin        → roles ADMIN y PEDIDOS
    """

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}

    def _canal_pedido(self, pedido_id: int) -> str:
        return f"pedido_{pedido_id}"

    async def connect(self, ws: WebSocket, canal: str) -> None:
        """Acepta una conexión WebSocket y la agrega al canal."""
        await ws.accept()
        if canal not in self._connections:
            self._connections[canal] = set()
        self._connections[canal].add(ws)

    def disconnect(self, ws: WebSocket, canal: str) -> None:
        """Desconecta un WebSocket y lo saca del canal."""
        if canal in self._connections:
            self._connections[canal].discard(ws)
            if not self._connections[canal]:
                del self._connections[canal]

    async def _broadcast(self, canal: str, payload: dict) -> None:
        if canal not in self._connections:
            return
        muertos: Set[WebSocket] = set()
        mensaje = json.dumps(payload, default=str)
        for ws in list(self._connections[canal]):
            try:
                await ws.send_text(mensaje)
            except Exception:
                muertos.add(ws)
        for ws in muertos:
            self.disconnect(ws, canal)

    async def broadcast_pedido(self, pedido_id: int, evento: dict) -> None:
        """Notifica al cliente dueño del pedido Y al canal admin. Post-commit (RN-06)."""
        await self._broadcast(self._canal_pedido(pedido_id), evento)
        await self._broadcast("admin", evento)

    async def broadcast_to_admin(self, evento: dict) -> None:
        """Broadcast un evento a todos los admin conectados."""
        await self._broadcast("admin", evento)

    @staticmethod
    def build_evento(
        event: str,
        pedido_id: int,
        estado_nuevo: str,
        estado_anterior: str | None = None,
        usuario_id: int | None = None,
        motivo: str | None = None,
    ) -> dict:
        """Construye un payload de evento para broadcast."""
        return {
            "event":           event,
            "pedido_id":       pedido_id,
            "estado_anterior": estado_anterior,
            "estado_nuevo":    estado_nuevo,
            "usuario_id":      usuario_id,
            "motivo":          motivo,
            "timestamp":       datetime.now(timezone.utc).isoformat(),
        }


# Singleton global
ws_manager = WSManager()