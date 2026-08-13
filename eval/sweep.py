"""Barrido del piso de relevancia, solo sobre la recuperación.

    python -m eval.sweep

No llama al modelo. El piso solo decide qué pasajes entran en el contexto, y
eso es determinista: para cada pregunta del set se calcula, en cada valor del
piso, cuántos pasajes pasarían y cuáles. Con eso se ve la curva completa por
cero coste, y la corrida cara de `eval.run` se gasta una vez, en el valor que
este barrido señale.

Los scores de este corpus caen todos entre 0.51 y 0.76 —`bge-small` comprime
el coseno en una banda estrecha— así que el paso es 0.02. Con 0.1 se salta por
encima de la decisión entera.

**Lo que este barrido mide, y lo que no.** Busca con el texto crudo del
visitante. El agente no busca eso: formula su propia consulta, y suele
recuperar bastante mejor —"how long have you been doing this?" en crudo se
queda seco a 0.56, mientras que en la corrida real ese caso recuperó seis
pasajes con el mejor a 0.791—. Así que estas cifras son el **peor caso**, útil
para ver la forma de la curva y qué documentos esperan justo debajo del piso,
no para predecir el resultado de una corrida. Las consultas reales del agente
se registran ahora en `run.py` (campo `consultas` de cada turno).
"""

from pathlib import Path

import yaml

from agent_core import retrieval
from agent_core.config import settings

EVAL_DIR = Path(__file__).resolve().parent
PISOS = [round(0.50 + 0.02 * i, 2) for i in range(11)]  # 0.50 … 0.70


def preguntas() -> list[tuple[str, str]]:
    """(id, texto) de cada turno del visitante que el agente buscaría.

    Se incluyen todos los turnos: en las conversaciones de calificación el
    turno que decide es a menudo el segundo, no el primero.
    """
    casos = yaml.safe_load((EVAL_DIR / "questions.yaml").read_text(encoding="utf-8"))
    return [
        (f"{c['id']}.{n}", turno)
        for c in casos
        for n, turno in enumerate(c["turnos"], start=1)
    ]


def main() -> None:
    consultas = preguntas()
    print(f"{len(consultas)} consultas · piso actual {settings.relevance_floor}\n")

    # Se recupera una sola vez con el piso más bajo y se filtra después: el
    # coseno no depende del piso, así que repetir la búsqueda once veces sería
    # calcular lo mismo once veces.
    recuperado = {
        clave: retrieval.buscar(texto, piso=min(PISOS)) for clave, texto in consultas
    }

    print(f"{'piso':>6} {'sin pasajes':>12} {'pasajes/consulta':>18} {'nuevos':>8}")
    previo: set[str] | None = None
    filas = []
    for piso in PISOS:
        pasan = {
            clave: [r for r in res if r.score >= piso] for clave, res in recuperado.items()
        }
        vacias = {clave for clave, res in pasan.items() if not res}
        total = sum(len(res) for res in pasan.values())
        nuevas = len(vacias - previo) if previo is not None else 0
        filas.append((piso, vacias, total))
        print(
            f"{piso:>6} {len(vacias):>12} {total / len(consultas):>18.1f} {nuevas:>8}"
        )
        previo = vacias

    print("\nConsultas que dejan de recuperar nada, y a qué piso:")
    visto: set[str] = set()
    for piso, vacias, _ in filas:
        aparecen = sorted(vacias - visto)
        if aparecen:
            print(f"  {piso}: {', '.join(aparecen)}")
        visto |= vacias


if __name__ == "__main__":
    main()
