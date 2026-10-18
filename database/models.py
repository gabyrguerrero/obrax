"""Modelos de datos de OBRAx (dataclasses)."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date

HORAS_MES = 240  # base para calcular el valor de la hora


def nuevo_id() -> str:
    return uuid.uuid4().hex[:8]


@dataclass
class Obra:
    nombre: str = ""
    cliente: str = ""
    ubicacion: str = ""
    inicio: date = field(default_factory=date.today)
    fin: date = field(default_factory=date.today)
    recargo_extra: float = 25.0  # % de recargo sobre la hora extra
    cierre: str = ""  # "", "solicitado" o "aprobado"
    id: str = field(default_factory=nuevo_id)


@dataclass
class Usuario:
    nombre: str
    email: str
    password_hash: str
    salt: str
    rol: str = "Residente"  # "Residente" o "Gerente"
    id: str = field(default_factory=nuevo_id)


@dataclass
class Capitulo:
    obra_id: str
    nombre: str
    id: str = field(default_factory=nuevo_id)


@dataclass
class Actividad:
    """Actividad o subactividad (si tiene padre_id)."""

    obra_id: str
    capitulo_id: str
    nombre: str
    unidad: str
    cantidad: float  # cantidad programada
    inicio: date
    fin: date
    padre_id: str = ""
    cerrada: bool = False
    id: str = field(default_factory=nuevo_id)


@dataclass
class Trabajador:
    obra_id: str
    nombre: str
    cargo: str
    salario: float  # mensual
    costo_laboral: float = 52.0  # % sobre el salario (prestaciones, etc.)
    id: str = field(default_factory=nuevo_id)

    @property
    def valor_hora(self) -> float:
        return self.salario * (1 + self.costo_laboral / 100) / HORAS_MES


@dataclass
class Avance:
    actividad_id: str
    cantidad: float


@dataclass
class Asistencia:
    trabajador_id: str
    horas: float = 8.0
    horas_extra: float = 0.0
    actividades: list[str] = field(default_factory=list)


@dataclass
class Foto:
    actividad_id: str
    ruta: str


@dataclass
class Reporte:
    """Reporte diario único de la obra."""

    obra_id: str
    fecha: date
    condiciones: str = "Soleado"
    observaciones: str = ""
    novedades: str = ""
    avances: list[Avance] = field(default_factory=list)
    asistencias: list[Asistencia] = field(default_factory=list)
    fotos: list[Foto] = field(default_factory=list)

    @property
    def id(self) -> str:
        return f"{self.obra_id}-{self.fecha.isoformat()}"

    def datos_json(self) -> str:
        return json.dumps(
            {
                "avances": [asdict(x) for x in self.avances],
                "asistencias": [asdict(x) for x in self.asistencias],
                "fotos": [asdict(x) for x in self.fotos],
            }
        )

    def cargar_datos(self, texto: str) -> None:
        d = json.loads(texto or "{}")
        self.avances = [Avance(**x) for x in d.get("avances", [])]
        self.asistencias = [Asistencia(**x) for x in d.get("asistencias", [])]
        self.fotos = [Foto(**x) for x in d.get("fotos", [])]


@dataclass
class Autorizado:
    """Correo que el gerente autoriza a ingresar. El id es el propio correo."""

    email: str
    rol: str = "Residente"  # "Residente" o "Gerente"
    id: str = ""

    def __post_init__(self) -> None:
        self.id = self.email
