from datetime import date
from fastapi import APIRouter, Query
from app.services.estadistica_service import EstadisticaService
from app.core.dependencies import AdminUser

router = APIRouter(prefix="/api/v1/estadisticas", tags=["estadisticas"])
service = EstadisticaService()


@router.get("/resumen")
def get_resumen(_: AdminUser = None): # type: ignore
    """KPIs: ventas hoy, ticket promedio, pedidos activos, ingresos del mes."""
    return service.get_resumen_kpis()


@router.get("/ventas")
def get_ventas(
    desde:      date = Query(...),
    hasta:      date = Query(...),
    agrupacion: str  = Query(default="day", pattern="^(day|week|month)$"),
    _: AdminUser = None, # type: ignore
):
    """Ventas por período agrupadas por day | week | month."""
    return service.get_ventas_periodo(desde, hasta, agrupacion)


@router.get("/productos-top")
def get_productos_top(
    limit: int = Query(default=10, ge=1, le=50),
    _: AdminUser = None, # type: ignore
):
    """Top productos por ingresos (usa subtotal_snap — EST-02)."""
    return service.get_productos_top(limit)


@router.get("/pedidos-por-estado")
def get_pedidos_por_estado(_: AdminUser = None): # type: ignore
    """Cantidad de pedidos agrupados por estado actual."""
    return service.get_pedidos_por_estado()


@router.get("/ingresos")
def get_ingresos(
    desde: date = Query(...),
    hasta: date = Query(...),
    _: AdminUser = None,  # type: ignore
):
    """Ingresos por forma de pago (solo pagos approved — EST-03)."""
    return service.get_ingresos_por_forma_pago(desde, hasta)