"""Pantalla de ingreso y registro."""

from __future__ import annotations

import re

import flet as ft

from database.db import ErrorIntegridad, Repositorio
from database.models import Usuario
from services.auth import crear_hash, verificar
from views import componentes as base

# correo válido: nombre@dominio.ext (la extensión solo con letras)
EMAIL_RE = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$"
)


def mostrar(page: ft.Page, repo: Repositorio, al_entrar) -> None:
    page.controls.clear()
    page.title = "OBRAx_v2 · Ingresar"
    page.padding = 0
    registro = {"activo": False}

    nombre = ft.TextField(label="Nombre", width=320, visible=False)
    email = ft.TextField(label="Correo", width=320)
    password = ft.TextField(
        label="Contraseña", password=True, can_reveal_password=True, width=320
    )
    confirmar = ft.TextField(
        label="Confirmar contraseña",
        password=True,
        can_reveal_password=True,
        width=320,
        visible=False,
    )
    mensaje = ft.Text("", color=ft.Colors.RED_700)
    titulo = ft.Text("Ingresar", size=22, weight=base.NEGRITA)

    def error(texto: str) -> None:
        mensaje.value = texto
        page.update()

    def alternar(e=None) -> None:
        registro["activo"] = not registro["activo"]
        r = registro["activo"]
        titulo.value = "Crear cuenta" if r else "Ingresar"
        boton.content = "Registrarme" if r else "Ingresar"
        cambio.content = (
            "¿Ya tienes cuenta? Ingresa" if r else "¿No tienes cuenta? Regístrate"
        )
        nombre.visible = confirmar.visible = r
        mensaje.value = ""
        page.update()

    def enviar(e) -> None:
        correo = (email.value or "").strip().lower()
        clave = password.value or ""

        # el correo se valida siempre, al ingresar y al registrarse
        if not EMAIL_RE.match(correo):
            error("Escribe un correo válido, por ejemplo nombre@dominio.com.")
            return

        permiso = repo.autorizado_por_email(correo)

        if not registro["activo"]:  # --- ingresar ---
            u = repo.usuario_por_email(correo)
            if u is None or not verificar(clave, u.password_hash, u.salt):
                error("Correo o contraseña incorrectos.")
                return
            if permiso is None:
                error("Tu acceso fue retirado. Pide al gerente que te autorice.")
                return
            u.rol = permiso.rol  # el rol sale siempre de la lista del gerente
            al_entrar(u)
            return

        # --- registrar ---
        nom = (nombre.value or "").strip()
        primero = not repo.hay_usuarios()  # el primer usuario queda como gerente

        if permiso is None and not primero:
            error("Ese correo no está autorizado. Pide al gerente que lo agregue.")
        elif repo.usuario_por_email(correo):
            error("Ese correo ya está registrado.")
        elif not nom:
            error("Escribe tu nombre.")
        elif any(c.isdigit() for c in nom):
            error("El nombre no puede tener números.")
        elif len(clave) < 6:
            error("La contraseña debe tener al menos 6 caracteres.")
        elif clave != (confirmar.value or ""):
            error("Las contraseñas no coinciden.")
        else:
            if primero:
                repo.autorizar(correo, "Gerente")
                rol_final = "Gerente"
            else:
                rol_final = permiso.rol
            h, salt = crear_hash(clave)
            u = Usuario(nom, correo, h, salt, rol_final)
            try:
                repo.guardar(u)
            except ErrorIntegridad:
                error("Ese correo ya está registrado.")
                return
            al_entrar(u)

    password.on_submit = enviar
    boton = ft.Button("Ingresar", on_click=enviar, width=320)
    cambio = ft.TextButton("¿No tienes cuenta? Regístrate", on_click=alternar)

    tarjeta = ft.Container(
        padding=30,
        border_radius=16,
        border=ft.Border.all(1, ft.Colors.GREY_400),
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("OBRA", size=28, weight=base.NEGRITA),
                        ft.Text("x", size=28, weight=base.NEGRITA, color=base.AMARILLO),
                        ft.Text("_v2", size=28, weight=base.NEGRITA),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=0,
                ),
                titulo,
                nombre,
                email,
                password,
                confirmar,
                mensaje,
                boton,
                cambio,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            tight=True,
        ),
    )
    page.add(ft.Container(content=tarjeta, alignment=ft.Alignment(0, 0), expand=True))
