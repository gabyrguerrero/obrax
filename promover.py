import sys

from database.db import Repositorio

correo, rol = sys.argv[1].lower(), sys.argv[2]  # rol: Gerente o Residente
Repositorio().autorizar(correo, rol)
print("listo")
