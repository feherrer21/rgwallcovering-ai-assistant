"""Ejecuta el set de evaluación y escribe los resultados en bruto.

No puntúa nada: S1 y S4 necesitan criterio humano, así que esto produce la
hoja que se etiqueta a mano y el JSON completo para poder discutir cualquier
fila con la respuesta delante.

    python -m eval.run

Dos cosas se apartan a propósito durante la corrida:

- los leads van a `eval/results/`, no a `data/leads.jsonl`, para no ensuciar
  el registro operativo con personas inventadas;
- el envío por correo se desactiva. La entrega ya está probada de extremo a
  extremo (T4.5.4) y lo que se mide aquí es el comportamiento del asistente,
  no el SMTP. Sin esto, cada corrida son cinco correos.
"""

import csv
import json
import time
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from agent_core import run_turn
from agent_core.config import settings

EVAL_DIR = Path(__file__).resolve().parent
RESULTADOS = EVAL_DIR / "results"


def preparar_aislamiento(marca: str) -> None:
    """Aparta los leads de la corrida y apaga el envío."""
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    settings.leads_file = RESULTADOS / f"leads_{marca}.jsonl"
    settings.smtp_user = ""
    settings.smtp_password = ""


def ejecutar_caso(caso: dict[str, Any]) -> dict[str, Any]:
    """Corre los turnos de un caso y devuelve el registro completo."""
    historial: list[dict[str, str]] = []
    turnos: list[dict[str, Any]] = []
    lead: dict[str, Any] | None = None

    for mensaje in caso["turnos"]:
        turno = run_turn(mensaje, historial=historial, conversation_id=caso["id"])
        historial = turno.historial
        lead = turno.lead or lead
        turnos.append(
            {
                "pregunta": mensaje,
                "respuesta": turno.respuesta,
                "derivado": turno.derivado,
                "rechazado": turno.rechazado,
                "fuentes": [
                    {
                        "titulo": f.titulo,
                        "tier": f.tier,
                        "score": round(f.score, 3),
                        "url": f.url,
                    }
                    for f in turno.fuentes
                ],
                "segundos": turno.segundos,
                "tokens_entrada": turno.tokens_entrada,
                "tokens_salida": turno.tokens_salida,
            }
        )

    ultimo = turnos[-1]
    return {
        "id": caso["id"],
        "categoria": caso["categoria"],
        "esperado": caso["esperado"],
        "prueba": caso["prueba"],
        "turnos": turnos,
        # El derivado que cuenta es el del turno que cierra la conversación.
        "derivado": ultimo["derivado"],
        "lead": lead,
        "segundos": round(sum(t["segundos"] for t in turnos), 2),
        "tokens_entrada": sum(t["tokens_entrada"] for t in turnos),
        "tokens_salida": sum(t["tokens_salida"] for t in turnos),
    }


def escribir_hoja(registros: list[dict[str, Any]], ruta: Path) -> None:
    """Hoja para etiquetar a mano. Las cuatro últimas columnas van vacías."""
    with ruta.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(
            [
                "id", "categoria", "esperado", "pregunta", "respuesta_final",
                "derivado", "fuentes", "lead_id", "S1", "S2", "S3", "S4",
            ]
        )
        for r in registros:
            ultimo = r["turnos"][-1]
            fuentes = " | ".join(
                f"{s['titulo']} [{s['tier']} {s['score']}]" for s in ultimo["fuentes"]
            )
            escritor.writerow(
                [
                    r["id"], r["categoria"], r["esperado"],
                    r["turnos"][0]["pregunta"], ultimo["respuesta"],
                    "sí" if r["derivado"] else "no", fuentes,
                    (r["lead"] or {}).get("lead_id", ""),
                    "", "", "", "",
                ]
            )


def resumir(registros: list[dict[str, Any]]) -> dict[str, Any]:
    """Lo que se puede contar sin criterio humano. El resto se etiqueta."""
    derivados = [r for r in registros if r["derivado"]]
    con_lead = [r for r in registros if r["lead"]]
    calificacion = [r for r in registros if r["categoria"] == "calificacion"]
    return {
        "casos": len(registros),
        "derivados": len(derivados),
        "con_fuentes": len(registros) - len(derivados),
        "leads_capturados": len(con_lead),
        "casos_de_calificacion": len(calificacion),
        "segundos_totales": round(sum(r["segundos"] for r in registros), 1),
        "segundos_por_caso": round(
            sum(r["segundos"] for r in registros) / len(registros), 1
        ),
        "tokens_entrada": sum(r["tokens_entrada"] for r in registros),
        "tokens_salida": sum(r["tokens_salida"] for r in registros),
    }


def main() -> None:
    marca = f"{date.today():%Y%m%d}"
    preparar_aislamiento(marca)

    casos = yaml.safe_load((EVAL_DIR / "questions.yaml").read_text(encoding="utf-8"))
    print(f"{len(casos)} casos · piso {settings.relevance_floor} · {settings.model}")

    arranque = time.monotonic()
    registros = []
    for n, caso in enumerate(casos, start=1):
        registro = ejecutar_caso(caso)
        registros.append(registro)
        print(
            f"[{n:>2}/{len(casos)}] {registro['id']:<6} "
            f"{'deriva' if registro['derivado'] else 'responde':<8} "
            f"{'lead' if registro['lead'] else '    '} "
            f"{registro['segundos']:>5.1f}s"
        )

    resumen = resumir(registros)
    salida = {
        "fecha": str(date.today()),
        "modelo": settings.model,
        "piso_relevancia": settings.relevance_floor,
        "top_k": settings.top_k,
        "resumen": resumen,
        "casos": registros,
    }

    ruta_json = RESULTADOS / f"baseline_{marca}.json"
    ruta_csv = RESULTADOS / f"baseline_{marca}.csv"
    ruta_json.write_text(
        json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    escribir_hoja(registros, ruta_csv)

    print(f"\n{json.dumps(resumen, indent=2, ensure_ascii=False)}")
    print(f"\nreloj: {time.monotonic() - arranque:.0f}s")
    print(f"escrito: {ruta_json.name} y {ruta_csv.name}")


if __name__ == "__main__":
    main()
