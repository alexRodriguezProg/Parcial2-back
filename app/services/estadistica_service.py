from datetime import date
from sqlmodel import text
from app.repositories.unit_of_work import UnitOfWork


class EstadisticaService:

    def get_resumen_kpis(self) -> dict:
        """Devuelve KPIs: ventas hoy, ticket promedio, pedidos activos, ingresos del mes."""
        with UnitOfWork() as uow:
            session = uow.session
            hoy = date.today()
            mes_actual = f"{hoy.year}-{hoy.month:02d}"

            ventas_hoy = session.exec(text("""
                SELECT COALESCE(SUM(p.total), 0)
                FROM pedido p
                WHERE p.estado_codigo NOT IN ('CANCELADO', 'PENDIENTE')
                  AND DATE(p.created_at) = :hoy
            """).bindparams(hoy=hoy)).scalar() or 0

            ticket_promedio = session.exec(text("""
                SELECT COALESCE(AVG(p.total), 0)
                FROM pedido p
                WHERE p.estado_codigo NOT IN ('CANCELADO', 'PENDIENTE')
            """)).scalar() or 0

            pedidos_activos = session.exec(text("""
                SELECT COUNT(*)
                FROM pedido
                WHERE estado_codigo IN ('PENDIENTE', 'CONFIRMADO', 'EN_PREP')
                  AND deleted_at IS NULL
            """)).scalar() or 0

            ingresos_mes = session.exec(text("""
                SELECT COALESCE(SUM(p.total), 0)
                FROM pedido p
                WHERE p.estado_codigo NOT IN ('CANCELADO', 'PENDIENTE')
                  AND to_char(p.created_at, 'YYYY-MM') = :mes_actual
            """).bindparams(mes_actual=mes_actual)).scalar() or 0

            return {
                "ventas_hoy":      round(float(ventas_hoy), 2),
                "ticket_promedio": round(float(ticket_promedio), 2),
                "pedidos_activos": int(pedidos_activos),
                "ingresos_mes":    round(float(ingresos_mes), 2),
            }

    def get_ventas_periodo(self, desde: date, hasta: date, agrupacion: str = "day") -> list:
        """Devuelve ventas agrupadas por período."""
        if agrupacion not in {"day", "week", "month"}:
            agrupacion = "day"

        with UnitOfWork() as uow:
            rows = uow.session.exec(text("""
                SELECT
                    DATE(p.created_at)        AS periodo,
                    COUNT(p.id)               AS cantidad_pedidos,
                    COALESCE(SUM(p.total), 0) AS total_ventas
                FROM pedido p
                WHERE p.estado_codigo NOT IN ('CANCELADO', 'PENDIENTE')
                  AND DATE(p.created_at) BETWEEN :desde AND :hasta
                GROUP BY DATE(p.created_at)
                ORDER BY DATE(p.created_at) ASC
            """).bindparams(desde=str(desde), hasta=str(hasta))).all()

            return [
                {
                    "periodo":          str(r[0]),
                    "cantidad_pedidos": int(r[1]),
                    "total_ventas":     round(float(r[2]), 2),
                }
                for r in rows
            ]

    def get_productos_top(self, limit: int = 10) -> list:
        """Devuelve el top de productos por ingresos."""
        with UnitOfWork() as uow:
            rows = uow.session.exec(text("""
                SELECT
                    dp.nombre_snapshot                 AS nombre,
                    SUM(dp.cantidad)                   AS cantidad_vendida,
                    COALESCE(SUM(dp.subtotal_snap), 0) AS ingresos
                FROM detalle_pedido dp
                JOIN pedido p ON p.id = dp.pedido_id
                WHERE p.estado_codigo != 'CANCELADO'
                GROUP BY dp.nombre_snapshot
                ORDER BY ingresos DESC
                LIMIT :limit
            """).bindparams(limit=limit)).all()

            return [
                {
                    "nombre":           r[0],
                    "cantidad_vendida": int(r[1]),
                    "ingresos":         round(float(r[2]), 2),
                }
                for r in rows
            ]

    def get_pedidos_por_estado(self) -> list:
        """Devuelve la cantidad de pedidos agrupados por estado."""
        with UnitOfWork() as uow:
            rows = uow.session.exec(text("""
                SELECT estado_codigo, COUNT(*) AS cantidad
                FROM pedido
                WHERE deleted_at IS NULL
                GROUP BY estado_codigo
                ORDER BY estado_codigo
            """)).all()

            return [
                {"estado_codigo": r[0], "cantidad": int(r[1])}
                for r in rows
            ]

    def get_ingresos_por_forma_pago(self, desde: date, hasta: date) -> list:
        """Devuelve ingresos agrupados por forma de pago en un período."""
        with UnitOfWork() as uow:
            rows = uow.session.exec(text("""
                SELECT
                    p.forma_pago_codigo,
                    COUNT(p.id)               AS cantidad,
                    COALESCE(SUM(p.total), 0) AS total
                FROM pedido p
                WHERE p.estado_codigo NOT IN ('CANCELADO', 'PENDIENTE')
                  AND DATE(p.created_at) BETWEEN :desde AND :hasta
                GROUP BY p.forma_pago_codigo
                ORDER BY total DESC
            """).bindparams(desde=str(desde), hasta=str(hasta))).all()

            return [
                {
                    "forma_pago_codigo": r[0],
                    "cantidad":          int(r[1]),
                    "total":             round(float(r[2]), 2),
                }
                for r in rows
            ]