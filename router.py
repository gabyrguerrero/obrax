"""Router: barra superior, menú lateral y cambio entre las vistas."""

from __future__ import annotations

from datetime import date

import flet as ft

from services.calculos import Control
from database.demo import cargar_demo
from database.models import Actividad, Capitulo, Obra, Reporte, Trabajador
from database.db import Repositorio
from views import componentes as base
from views import (
    crear_obra,
    informes,
    panel_gerencial,
    programacion,
    reporte_diario,
    usuarios,
)

# (nombre, icono, vista, roles que la ven)
AMBOS = ("residente", "gerente")
SECCIONES = [
    ("Panel gerencial", ft.Icons.DASHBOARD, panel_gerencial, AMBOS),
    ("Crear obra", ft.Icons.CONSTRUCTION, crear_obra, ("residente",)),
    ("Programación", ft.Icons.TIMELINE, programacion, AMBOS),
    ("Reporte diario", ft.Icons.EDIT_NOTE, reporte_diario, ("residente",)),
    ("Informes", ft.Icons.ASSESSMENT, informes, AMBOS),
    ("Usuarios", ft.Icons.GROUP, usuarios, ("gerente",)),
]


class Router:
    def __init__(
        self, page: ft.Page, usuario, cerrar_sesion, repo: Repositorio | None = None
    ):
        self.page, self.repo = page, repo or Repositorio()
        self.usuario, self.cerrar_sesion = usuario, cerrar_sesion
        self.indice = 0
        self.obra_id: str | None = None
        self.borrador: Reporte | None = None  # reporte del día que se está llenando
        self.filtro_bitacora, self.inf_tipo, self.inf_fecha = "", "diario", date.today()
        self.picker = ft.FilePicker()
        page.services.append(self.picker)
        page.title = "OBRAx_v2 · Gestión y control de obra"
        page.padding = 0
        page.theme = ft.Theme(color_scheme_seed=base.AMARILLO)

        self.selector_obra = ft.Dropdown(
            width=240,
            hint_text="Sin obras",
            on_select=self.cambiar_obra,
            filled=True,
            fill_color="white",
            bgcolor="white",
            color="black",
            border_color="white",
        )
        # el rol solo se muestra: no hay forma de cambiarlo desde la interfaz
        etiqueta_rol = ft.Container(
            content=ft.Text(
                f"Rol: {usuario.rol}", color="white", size=12, weight=base.NEGRITA
            ),
            bgcolor="#3A4049",
            padding=8,
            border_radius=12,
        )
        barra = ft.Container(
            bgcolor="#2A2F37",
            padding=10,
            content=ft.Row(
                [
                    ft.Text("OBRA", size=26, weight=base.NEGRITA, color="white"),
                    ft.Text("x", size=26, weight=base.NEGRITA, color=base.ACENTO_CLARO),
                    ft.Container(expand=True),
                    self.selector_obra,
                    etiqueta_rol,
                    ft.Text(usuario.nombre, color="#C3CAD2"),
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT,
                        icon_color="white",
                        tooltip="Cerrar sesión",
                        on_click=lambda e: self.cerrar_sesion(),
                    ),
                ]
            ),
        )
        self.riel = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=96,
            destinations=self.destinos(),
            on_change=lambda e: self.ir(e.control.selected_index),
        )
        self.cuerpo = ft.Container(expand=True, padding=16)
        page.add(
            ft.Column(
                [
                    barra,
                    ft.Row(
                        [self.riel, ft.VerticalDivider(width=1), self.cuerpo],
                        expand=True,
                    ),
                ],
                expand=True,
                spacing=0,
            )
        )
        self.refrescar()

    # --- rol (solo lectura: sale siempre del usuario que inició sesión) ---
    @property
    def rol(self) -> str:
        return self.usuario.rol.lower()

    def obras_visibles(self) -> list[Obra]:
        """El gerente ve todas las obras; el residente, solo las suyas."""
        if self.rol == "gerente":
            return self.repo.listar(Obra)
        return self.repo.listar(Obra, usuario_id=self.usuario.id)

    # --- datos ---
    @property
    def obra(self) -> Obra | None:
        obras = self.obras_visibles()
        if not obras:
            return None
        for o in obras:
            if o.id == self.obra_id:
                return o
        self.obra_id = obras[0].id  # si no hay una elegida, la primera
        return obras[0]

    def control(self) -> Control | None:
        o = self.obra
        if o is None:
            return None
        r = self.repo
        return Control(
            o,
            r.listar(Capitulo, obra_id=o.id),
            r.listar(Actividad, obra_id=o.id),
            r.listar(Trabajador, obra_id=o.id),
            r.listar_reportes(o.id),
        )

    def cargar_borrador(self, fecha: date) -> Reporte:
        return self.repo.reporte_de(self.obra.id, fecha) or Reporte(self.obra.id, fecha)

    def cambiar_obra(self, e) -> None:
        self.obra_id = e.control.value
        self.borrador = None  # el reporte en curso era de la otra obra
        self.filtro_bitacora, self.inf_fecha = "", date.today()
        self.refrescar()

    def actualizar_selector_obra(self) -> None:
        obras = self.repo.listar(Obra, usuario_id=self.usuario.id)
        self.selector_obra.options = [
            ft.DropdownOption(key=o.id, text=o.nombre or "(sin nombre)") for o in obras
        ]
        self.selector_obra.value = self.obra_id if obras else None

    def cargar_demo(self) -> None:
        obra = cargar_demo(self.repo, self.usuario.id)
        self.obra_id = obra.id
        self.ir_a("Panel gerencial")

    def secciones(self):
        return [s for s in SECCIONES if self.rol in s[3]]

    def destinos(self):
        return [
            ft.NavigationRailDestination(icon=icono, label=nombre)
            for nombre, icono, _, _ in self.secciones()
        ]

    def ir(self, indice: int) -> None:
        self.indice = indice
        self.refrescar()

    def ir_a(self, nombre: str) -> None:
        nombres = [s[0] for s in self.secciones()]
        self.ir(nombres.index(nombre) if nombre in nombres else 0)

    def refrescar(self) -> None:
        self.obra  # fija obra_id si todavía no hay una elegida
        self.actualizar_selector_obra()
        self.riel.selected_index = self.indice
        vista = self.secciones()[self.indice][2]
        self.cuerpo.content = ft.Column(
            [vista.construir(self)], scroll=ft.ScrollMode.AUTO, expand=True
        )
        self.page.update()

    def avisar(self, texto: str) -> None:
        self.page.show_dialog(ft.SnackBar(content=ft.Text(texto)))
