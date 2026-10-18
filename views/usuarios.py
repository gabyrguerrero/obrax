"""Vista del gerente: correos autorizados para ingresar."""

from __future__ import annotations

import flet as ft

from database.models import Autorizado
from views import componentes as base
from views.login import EMAIL_RE


def construir(app) -> ft.Column:
    repo = app.repo
    correo = base.campo("Correo a autorizar", ancho=320)
    rol = ft.Dropdown(
        label="Rol",
        value="Residente",
        width=180,
        options=[
            ft.DropdownOption(key="Residente", text="Residente"),
            ft.DropdownOption(key="Gerente", text="Gerente"),
        ],
    )

    def agregar(e) -> None:
        c = (correo.value or "").strip().lower()
        if not EMAIL_RE.match(c):
            app.avisar("Escribe un correo válido, por ejemplo nombre@dominio.com.")
            return
        if c == app.usuario.email and rol.value != "Gerente":
            app.avisar("No puedes quitarte tu propio rol de gerente.")
            return
        repo.autorizar(c, rol.value)
        app.avisar(f"{c} autorizado como {rol.value}.")
        app.refrescar()

    def quitar(email: str) -> None:
        if email == app.usuario.email:
            app.avisar("No puedes quitarte tu propio acceso.")
            return
        repo.desautorizar(email)
        app.avisar(f"Se retiró el acceso a {email}.")
        app.refrescar()

    filas = []
    for a in sorted(repo.listar(Autorizado), key=lambda x: x.email):
        registrado = repo.usuario_por_email(a.email) is not None
        filas.append(
            [
                a.email,
                a.rol,
                "Registrado" if registrado else "Pendiente",
                base.accion_icono(
                    ft.Icons.DELETE, "Quitar acceso", lambda e, m=a.email: quitar(m)
                ),
            ]
        )

    return base.pagina(
        base.titulo("Usuarios autorizados"),
        ft.Text("Solo los correos de esta lista pueden registrarse e ingresar."),
        base.tarjeta(
            base.subtitulo("Autorizar un correo"),
            ft.Row(
                [correo, rol, base.boton("Autorizar", agregar, ft.Icons.ADD)],
                wrap=True,
            ),
        ),
        base.tarjeta(
            base.subtitulo("Correos con acceso"),
            base.tabla(["Correo", "Rol", "Estado", ""], filas),
        ),
    )
