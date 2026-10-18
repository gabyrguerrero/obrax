"""OBRAx_v2 · Gestión y control de obra.   Ejecuta:  python main.py"""
import os

import flet as ft

from database.db import Repositorio
from router import Router
from views import login


def main(page: ft.Page) -> None:
    repo = Repositorio()

    def entrar(usuario) -> None:
        page.controls.clear()
        Router(page, usuario, cerrar_sesion, repo)

    def cerrar_sesion() -> None:
        page.services.clear()  # el Router agrega un FilePicker cada vez
        login.mostrar(page, repo, entrar)

    login.mostrar(page, repo, entrar)


if __name__ == "__main__":
    puerto = os.environ.get("PORT")
    if puerto:  # en Render: se sirve como sitio web
        ft.run(main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=int(puerto))
    else:  # en tu computador: ventana de escritorio, como siempre
        ft.run(main)
