import sys

sys.path.insert(0, "C:/Users/ferna/Videos/PARCIAL-IA")

from backend.application.ga_controller import GAController
from backend.application.game_loop import _construir_estado

ctrl = GAController()

# 1. factor_velocidad existe
assert hasattr(ctrl, "factor_velocidad"), "FALLO: factor_velocidad missing"
assert ctrl.factor_velocidad == 1
print("OK - factor_velocidad =", ctrl.factor_velocidad)

# 2. Estado tiene cromosomas y umbral_distancia
estado = _construir_estado(ctrl)
assert "cromosomas" in estado, "FALLO: cromosomas no en estado"
assert "umbral_distancia" in estado["avatares"][0], (
    "FALLO: umbral_distancia no en avatar"
)
assert len(estado["cromosomas"]) == 30
print("OK - cromosomas:", estado["cromosomas"][0])
print("OK - avatar[0]:", estado["avatares"][0])

# 3. Cambiar velocidad
ctrl.factor_velocidad = 5
assert ctrl.factor_velocidad == 5
print("OK - factor_velocidad cambiado a 5")

print("\nTODAS LAS VERIFICACIONES OK")
