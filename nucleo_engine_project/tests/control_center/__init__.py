"""Bootstrap de imports para los tests del Control Center (§13).

pytest importa este paquete bajo el nombre ``control_center`` (tests/ no es
paquete: el basedir de colección es ``tests/``), que colisiona con el paquete
del MOTOR del mismo nombre. Solución contenida aquí (sin archivos extra):
1. se añade el ROOT del motor a ``sys.path`` (para ``dark_director``,
   ``jazz_engine``, ``forge``…), y
2. se extiende ``__path__`` de ESTE paquete con ``<motor>/control_center/``,
   de modo que ``from control_center import esquema_plan`` resuelva los
   submódulos REALES del motor desde el contexto de colección de pytest.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_MOTOR_CC = ROOT / "control_center"
if _MOTOR_CC.is_dir() and str(_MOTOR_CC) not in __path__:
    __path__.append(str(_MOTOR_CC))
