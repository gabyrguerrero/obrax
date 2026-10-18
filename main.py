"""OBRAx · Gestión y control de obra.   Ejecuta:  python main.py"""

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
    ft.run(main)
