"""El bucle de conversación.

No sabe nada de HTTP, Streamlit ni WordPress: cualquier frontend consume
`run_turn()`. Ver docs/03_spec.md §2.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import anthropic

from . import prompts, retrieval, tools
from .config import settings

log = logging.getLogger(__name__)

_cliente: anthropic.Anthropic | None = None


def cliente() -> anthropic.Anthropic:
    """Cliente perezoso: importar el módulo no debe fallar sin API key."""
    global _cliente
    if _cliente is None:
        _cliente = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
    return _cliente


@dataclass
class Fuente:
    """Una fuente citada en la respuesta, para que el frontend la muestre."""

    titulo: str
    url: str
    tier: str
    score: float


@dataclass
class Turno:
    """Resultado de un turno de conversación."""

    respuesta: str
    fuentes: list[Fuente] = field(default_factory=list)
    #: True si el turno no se apoyó en ningún pasaje recuperado. Es la señal
    #: que usa el evaluador: respuesta sin fuentes = respuesta sin fundamento.
    derivado: bool = True
    lead: dict[str, Any] | None = None
    historial: list[dict[str, str]] = field(default_factory=list)
    tokens_entrada: int = 0
    tokens_salida: int = 0
    segundos: float = 0.0
    rechazado: bool = False


MENSAJE_RECHAZO = (
    "I'm sorry — I can't help with that one. If you'd like to reach the team "
    "directly you can write to info@rgwallcovering.com or call "
    "+1 (401) 722-9255."
)

MENSAJE_ERROR = (
    "Sorry, something went wrong on our side. Please try again in a moment, "
    "or reach us directly at info@rgwallcovering.com / +1 (401) 722-9255."
)


def run_turn(
    mensaje: str,
    historial: list[dict[str, str]] | None = None,
    conversation_id: str = "",
) -> Turno:
    """Procesa un mensaje del visitante y devuelve la respuesta del asistente.

    `historial` es una lista de {"role": "user"|"assistant", "content": str}.
    Solo texto: los bloques de herramienta se resuelven dentro del turno y no
    salen de aquí, lo que mantiene el contrato de la API trivial de consumir
    desde JavaScript.
    """
    historial = list(historial or [])
    arranque = time.monotonic()

    mensajes: list[dict[str, Any]] = [
        {"role": m["role"], "content": m["content"]} for m in historial
    ]

    # Recuperación determinista: el mensaje entra con sus pasajes ya buscados,
    # en lugar de depender de que el modelo decida buscar. Medido en la fase 6
    # (docs/evidence/measured_improvement.md): con la decisión en manos del
    # modelo, la misma pregunta se fundamentaba en una corrida y no en la
    # siguiente. La herramienta sigue existiendo para refinar, y refina mejor
    # —el agente formula consultas que recuperan por encima del texto crudo.
    pasajes: list[retrieval.Recuperado] = list(retrieval.buscar(mensaje))
    if pasajes:
        mensajes.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "<retrieved_passages>\n"
                            + tools.formatear_pasajes(pasajes)
                            + "\n</retrieved_passages>"
                        ),
                    },
                    {"type": "text", "text": mensaje},
                ],
            }
        )
    else:
        mensajes.append({"role": "user", "content": mensaje})

    lead: dict[str, Any] | None = None
    tokens_entrada = tokens_salida = 0
    respuesta = None

    for _ in range(settings.max_tool_iterations):
        try:
            respuesta = cliente().messages.create(
                model=settings.model,
                max_tokens=settings.max_tokens,
                system=prompts.bloque_sistema(),
                output_config={"effort": settings.effort},
                tools=tools.TOOLS,
                messages=mensajes,
            )
        except anthropic.APIError:
            log.exception("Fallo al llamar a la API")
            return _turno(
                MENSAJE_ERROR, mensaje, historial, arranque,
                tokens_entrada, tokens_salida,
            )

        tokens_entrada += respuesta.usage.input_tokens
        tokens_salida += respuesta.usage.output_tokens

        if respuesta.stop_reason == "refusal":
            resultado = _turno(
                MENSAJE_RECHAZO, mensaje, historial, arranque,
                tokens_entrada, tokens_salida,
            )
            resultado.rechazado = True
            return resultado

        if respuesta.stop_reason != "tool_use":
            break

        mensajes.append({"role": "assistant", "content": respuesta.content})

        resultados = []
        for bloque in respuesta.content:
            if bloque.type != "tool_use":
                continue
            texto, nuevo_lead, nuevos_pasajes = tools.ejecutar(
                bloque.name, dict(bloque.input), conversation_id
            )
            if nuevo_lead:
                lead = nuevo_lead
            pasajes.extend(nuevos_pasajes)
            resultados.append(
                {
                    "type": "tool_result",
                    "tool_use_id": bloque.id,
                    "content": texto,
                }
            )

        mensajes.append({"role": "user", "content": resultados})
    else:
        # Se agotaron las iteraciones sin que el modelo cerrara el turno.
        log.warning("Tope de iteraciones alcanzado (conversación %s)", conversation_id)

    texto = ""
    if respuesta is not None:
        texto = "".join(b.text for b in respuesta.content if b.type == "text").strip()

    if not texto:
        texto = MENSAJE_ERROR

    resultado = _turno(
        texto, mensaje, historial, arranque, tokens_entrada, tokens_salida
    )
    resultado.lead = lead
    resultado.fuentes = _fuentes_unicas(pasajes)
    resultado.derivado = not pasajes
    return resultado


def _fuentes_unicas(pasajes: list[retrieval.Recuperado]) -> list[Fuente]:
    """Colapsa los pasajes a una fuente por documento, la de mayor score."""
    mejores: dict[str, Fuente] = {}
    for p in pasajes:
        f = p.fragmento
        clave = f.url or f.title
        actual = mejores.get(clave)
        if actual is None or p.score > actual.score:
            mejores[clave] = Fuente(
                titulo=f.title, url=f.url, tier=f.tier, score=p.score
            )
    return sorted(mejores.values(), key=lambda f: f.score, reverse=True)


def _turno(
    texto: str,
    mensaje: str,
    historial: list[dict[str, str]],
    arranque: float,
    tokens_entrada: int,
    tokens_salida: int,
) -> Turno:
    return Turno(
        respuesta=texto,
        historial=historial
        + [
            {"role": "user", "content": mensaje},
            {"role": "assistant", "content": texto},
        ],
        tokens_entrada=tokens_entrada,
        tokens_salida=tokens_salida,
        segundos=round(time.monotonic() - arranque, 2),
    )
