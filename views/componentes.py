"""Componentes de interfaz compartidos por todas las vistas."""

from __future__ import annotations

from datetime import date

import flet as ft

from services.calculos import Estado
from services.formato import (
    dinero,
    fmt,
)  # noqa: F401  (las vistas los importan desde aquí)

AMARILLO, ROJO, VERDE, GRIS = "#1F4E79", "#C4410C", "#2A8A56", "#5D6773"
ACENTO_CLARO = "#5B9BD5"
COLOR_ESTADO = {
    Estado.TERMINADA: VERDE,
    Estado.ATRASADA: ROJO,
    Estado.EN_CURSO: GRIS,
    Estado.PENDIENTE: GRIS,
}
NEGRITA = ft.FontWeight.BOLD


def num(texto, defecto: float = 0.0) -> float:
    try:
        return float(str(texto).replace(",", "."))
    except ValueError:
        return defecto


def fecha(texto: str) -> date | None:
    try:
        return date.fromisoformat(texto.strip())
    except ValueError:
        return None


def titulo(t: str) -> ft.Text:
    return ft.Text(t, size=26, weight=NEGRITA)


def subtitulo(t: str) -> ft.Text:
    return ft.Text(t, size=18, weight=NEGRITA)


def campo(label: str, valor="", ancho: int = 200, **kw) -> ft.TextField:
    return ft.TextField(label=label, value=str(valor), width=ancho, **kw)


def boton(texto: str, accion, icono=None, secundario: bool = False):
    clase = ft.OutlinedButton if secundario else ft.Button
    return clase(content=texto, icon=icono, on_click=accion)


def accion_icono(icono, ayuda: str, accion) -> ft.IconButton:
    return ft.IconButton(icon=icono, tooltip=ayuda, on_click=accion)


def tarjeta(*controles) -> ft.Card:
    return ft.Card(
        content=ft.Container(padding=14, content=ft.Column(list(controles), tight=True))
    )


def kpi(titulo_: str, valor: str, color: str | None = None) -> ft.Card:
    return ft.Card(
        content=ft.Container(
            width=175,
            padding=12,
            content=ft.Column(
                [
                    ft.Text(titulo_, size=12, color=GRIS),
                    ft.Text(valor, size=24, weight=NEGRITA, color=color),
                ],
                tight=True,
            ),
        )
    )


def estado_texto(e: Estado) -> ft.Text:
    return ft.Text(e.value, color=COLOR_ESTADO[e], weight=NEGRITA)


def avance(real: float, prog: float, ancho: int = 110) -> ft.Row:
    color = ROJO if prog - real > 10 else VERDE
    return ft.Row(
        [
            ft.ProgressBar(value=min(real, 100) / 100, width=ancho, color=color),
            ft.Text(f"{fmt(real)}% (prog. {fmt(prog, 0)}%)", size=12),
        ],
        spacing=8,
    )


def tabla(encabezados: list[str], filas: list[list], numericas=()) -> ft.Row:
    def celda(x):
        return ft.DataCell(x if isinstance(x, ft.Control) else ft.Text(str(x)))

    t = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text(h, weight=NEGRITA), numeric=i in numericas)
            for i, h in enumerate(encabezados)
        ],
        rows=[ft.DataRow(cells=[celda(x) for x in f]) for f in filas],
        column_spacing=16,
    )
    return ft.Row([t], scroll=ft.ScrollMode.AUTO)


def pagina(*controles) -> ft.Column:
    return ft.Column(
        list(controles), spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH
    )


def vacio(app) -> ft.Column:
    controles = [titulo("Aún no hay una obra registrada")]
    if app.rol == "residente":
        controles += [
            ft.Text(
                "Crea la obra y sus actividades, o carga datos de ejemplo para explorar."
            ),
            ft.Row(
                [
                    boton("Crear obra", lambda e: app.ir_a("Crear obra"), ft.Icons.ADD),
                    boton(
                        "Cargar datos de ejemplo",
                        lambda e: app.cargar_demo(),
                        secundario=True,
                    ),
                ]
            ),
        ]
    else:
        controles.append(
            ft.Text("Cuando el residente cree la obra verás aquí el avance.")
        )
    return pagina(*controles)
