import getpass
import sys

from database.db import Repositorio
from services.auth import crear_hash

if len(sys.argv) < 2:
    sys.exit("Uso: python restablecer.py correo@ejemplo.com")

correo = sys.argv[1].strip().lower()
repo = Repositorio()
u = repo.usuario_por_email(correo)
if u is None:
    sys.exit("No existe una cuenta con ese correo.")
nueva = getpass.getpass("Nueva contraseña (mínimo 6 caracteres): ")
if len(nueva) < 6:
    sys.exit("Muy corta: usa al menos 6 caracteres.")
u.password_hash, u.salt = crear_hash(nueva)
repo.guardar(u)
print("Contraseña actualizada.")
