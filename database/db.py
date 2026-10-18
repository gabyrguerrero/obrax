"""Persistencia en SQLite. Las tablas se generan a partir de las dataclasses."""

from __future__ import annotations

import sqlite3
import typing
from dataclasses import fields
from datetime import date
from pathlib import Path

from .models import Actividad, Autorizado, Capitulo, Obra, Reporte, Trabajador, Usuario

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
FOTOS, INFORMES = DATOS / "fotos", DATOS / "informes"
SQL = {str: "TEXT", float: "REAL", int: "INTEGER", bool: "INTEGER", date: "TEXT"}


class Repositorio:

    def __init__(self, ruta: Path | str | None = None):
        for carpeta in (DATOS, FOTOS, INFORMES):
            carpeta.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(ruta or DATOS / "obrax.db")
        self.con.row_factory = sqlite3.Row
        for cls in (Obra, Capitulo, Actividad, Trabajador, Usuario, Autorizado):
            self._crear_tabla(cls)
        # si la base ya existía sin usuario_id, agrega la columna
        cols = [c["name"] for c in self.con.execute("PRAGMA table_info(obra)")]
        if "usuario_id" not in cols:
            self.con.execute("ALTER TABLE obra ADD COLUMN usuario_id TEXT DEFAULT ''")
        self.con.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_usuario_email ON usuario(email)"
        )
        # las cuentas que ya existían quedan autorizadas con su rol actual
        self.con.execute(
            "INSERT OR IGNORE INTO autorizado (email, rol, id) "
            "SELECT email, rol, email FROM usuario"
        )
        self.con.execute(
            "CREATE TABLE IF NOT EXISTS reporte (id TEXT PRIMARY KEY, obra_id TEXT, fecha TEXT,"
            " condiciones TEXT, observaciones TEXT, novedades TEXT, datos TEXT)"
        )
        self.con.commit()

    # --- CRUD genérico para dataclasses planas ---
    @staticmethod
    def _tabla(cls) -> str:
        return cls.__name__.lower()

    def _crear_tabla(self, cls) -> None:
        tipos = typing.get_type_hints(cls)
        cols = ", ".join(
            f"{f.name} {SQL[tipos[f.name]]}"
            + (" PRIMARY KEY" if f.name == "id" else "")
            for f in fields(cls)
        )
        self.con.execute(f"CREATE TABLE IF NOT EXISTS {self._tabla(cls)} ({cols})")

    def guardar(self, obj) -> None:
        nombres = [f.name for f in fields(obj)]
        valores = [self._a_sql(getattr(obj, n)) for n in nombres]
        cambios = ", ".join(f"{n}=excluded.{n}" for n in nombres if n != "id")
        self.con.execute(
            f"INSERT INTO {self._tabla(type(obj))} ({', '.join(nombres)}) "
            f"VALUES ({', '.join('?' * len(nombres))}) ON CONFLICT(id) DO UPDATE SET {cambios}",
            valores,
        )
        self.con.commit()

    def listar(self, cls, **filtros):
        sql = f"SELECT * FROM {self._tabla(cls)}"
        if filtros:
            sql += " WHERE " + " AND ".join(f"{k}=?" for k in filtros)
        return [
            self._de_fila(cls, r) for r in self.con.execute(sql, list(filtros.values()))
        ]

    def eliminar(self, cls, id: str) -> None:
        self.con.execute(f"DELETE FROM {self._tabla(cls)} WHERE id=?", (id,))
        self.con.commit()

    @staticmethod
    def _a_sql(v):
        return (
            v.isoformat()
            if isinstance(v, date)
            else int(v) if isinstance(v, bool) else v
        )

    @staticmethod
    def _de_fila(cls, fila):
        tipos, kw = typing.get_type_hints(cls), {}
        for f in fields(cls):
            v, t = fila[f.name], tipos[f.name]
            kw[f.name] = (
                date.fromisoformat(v) if t is date else bool(v) if t is bool else v
            )
        return cls(**kw)

    # --- usuarios y correos autorizados ---
    def usuario_por_email(self, email: str) -> Usuario | None:
        r = self.listar(Usuario, email=email)
        return r[0] if r else None

    def hay_usuarios(self) -> bool:
        return self.con.execute("SELECT 1 FROM usuario LIMIT 1").fetchone() is not None

    def autorizado_por_email(self, email: str) -> Autorizado | None:
        r = self.listar(Autorizado, email=email.strip().lower())
        return r[0] if r else None

    def autorizar(self, email: str, rol: str) -> None:
        """Autoriza un correo (o cambia su rol). Si ya tiene cuenta, la actualiza."""
        email = email.strip().lower()
        self.guardar(Autorizado(email, rol))
        u = self.usuario_por_email(email)
        if u is not None:
            u.rol = rol
            self.guardar(u)

    def desautorizar(self, email: str) -> None:
        self.eliminar(Autorizado, email.strip().lower())

    # --- borrados en cascada ---
    def eliminar_actividad(self, id: str) -> None:
        ids, i = [id], 0
        while i < len(ids):
            ids += [a.id for a in self.listar(Actividad, padre_id=ids[i])]
            i += 1
        self.con.executemany("DELETE FROM actividad WHERE id=?", [(x,) for x in ids])
        self.con.commit()

    def eliminar_capitulo(self, id: str) -> None:
        self.con.execute("DELETE FROM actividad WHERE capitulo_id=?", (id,))
        self.eliminar(Capitulo, id)

    def eliminar_obra(self, id: str) -> None:
        for tabla in ("actividad", "capitulo", "trabajador", "reporte"):
            self.con.execute(f"DELETE FROM {tabla} WHERE obra_id=?", (id,))
        self.eliminar(Obra, id)

    # --- reportes diarios (lista de avances, asistencias y fotos en JSON) ---
    def guardar_reporte(self, r: Reporte) -> None:
        self.con.execute(
            "INSERT INTO reporte VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
            "condiciones=excluded.condiciones, observaciones=excluded.observaciones, "
            "novedades=excluded.novedades, datos=excluded.datos",
            (
                r.id,
                r.obra_id,
                r.fecha.isoformat(),
                r.condiciones,
                r.observaciones,
                r.novedades,
                r.datos_json(),
            ),
        )
        self.con.commit()

    @staticmethod
    def _reporte(f) -> Reporte:
        r = Reporte(
            f["obra_id"],
            date.fromisoformat(f["fecha"]),
            f["condiciones"],
            f["observaciones"],
            f["novedades"],
        )
        r.cargar_datos(f["datos"])
        return r

    def listar_reportes(self, obra_id: str) -> list[Reporte]:
        filas = self.con.execute(
            "SELECT * FROM reporte WHERE obra_id=? ORDER BY fecha", (obra_id,)
        )
        return [self._reporte(f) for f in filas]

    def reporte_de(self, obra_id: str, fecha: date) -> Reporte | None:
        f = self.con.execute(
            "SELECT * FROM reporte WHERE id=?", (f"{obra_id}-{fecha.isoformat()}",)
        ).fetchone()
        return self._reporte(f) if f else None
