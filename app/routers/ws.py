from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.ws_manager import ws_manager
from app.core.security import decode_token
from app.models import RolCodigo
from app.repositories import UsuarioRepository
from app.repositories.unit_of_work import UnitOfWork

router = APIRouter(tags=["websocket"])


def _autenticar_ws(token: str):
    payload = decode_token(token)
    usuario_id = int(payload.get("sub", 0))
    with UnitOfWork() as uow:
        repo = UsuarioRepository(uow.session)
        usuario = repo.get_with_roles(usuario_id)
    if not usuario or not usuario.activo:
        return None
    return usuario


@router.websocket("/ws/pedidos/{pedido_id}")
async def ws_pedido(
    websocket: WebSocket,
    pedido_id: int,
    token: str = Query(...),
):
    
    try:
        usuario = _autenticar_ws(token)
    except Exception:
        await websocket.close(code=4001)
        return

    if not usuario:
        await websocket.close(code=4001)
        return

    canal = f"pedido_{pedido_id}"
    await ws_manager.connect(websocket, canal)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, canal)


@router.websocket("/ws/admin/pedidos")
async def ws_admin_pedidos(
    websocket: WebSocket,
    token: str = Query(...),
):
    
    try:
        usuario = _autenticar_ws(token)
    except Exception:
        await websocket.close(code=4001)
        return

    if not usuario:
        await websocket.close(code=4001)
        return

    user_roles = {r.codigo for r in usuario.roles}
    if not {RolCodigo.ADMIN, RolCodigo.PEDIDOS}.intersection(user_roles):
        await websocket.close(code=4003)
        return

    canal = "admin"
    await ws_manager.connect(websocket, canal)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, canal)