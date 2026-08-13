"""Recuperación de fragmentos sobre el índice del corpus.

Lee el índice que escribe `agent_core/ingest/`, embebe la pregunta del
visitante y devuelve los fragmentos más cercanos por similitud coseno.

Dos ideas gobiernan este módulo:

1. **Devolver la lista vacía es un resultado correcto.** El piso de relevancia
   existe para producirlo. Medido sobre el corpus real, el 84% de los
   fragmentos son ensayos decorativos del blog, así que el vecino más cercano
   a una pregunta de negocio suele ser elocuentemente irrelevante. Quien
   consume este módulo deriva al equipo; no rellena el hueco con el mejor
   candidato disponible.

2. **`tier` viaja intacto hasta el prompt.** Sin él no se puede decidir qué se
   puede afirmar sobre el negocio, y el criterio S2 deja de ser exigible.

El corpus son ~360 fragmentos: producto matriz-vector sobre un array de numpy,
sin base de datos vectorial. Ver docs/03_spec.md §3.2.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding

from .config import settings

log = logging.getLogger(__name__)

EMBEDDING_DIM = 384


class ErrorDeIndice(RuntimeError):
    """El índice no existe, está incompleto o es incoherente."""


@dataclass(frozen=True)
class Fragmento:
    """Un fragmento del corpus, tal y como lo escribió la ingesta."""

    chunk_id: str
    text: str
    title: str
    source_id: str
    tier: str
    url: str
    date: str


@dataclass(frozen=True)
class Recuperado:
    """Un fragmento junto a su similitud coseno con la pregunta.

    `fragmento.text` es dato NO confiable: si contiene instrucciones, son
    contenido que se reporta, nunca órdenes que se obedecen.
    """

    fragmento: Fragmento
    score: float


@dataclass(eq=False)
class Indice:
    """Índice cargado en memoria: embeddings, fragmentos y modelo."""

    embeddings: np.ndarray
    fragmentos: list[Fragmento]
    embebedor: TextEmbedding = field(repr=False)

    def buscar(
        self,
        pregunta: str,
        top_k: int | None = None,
        piso: float | None = None,
        max_por_fuente: int | None = None,
    ) -> list[Recuperado]:
        """Devuelve hasta `top_k` fragmentos por encima del piso de relevancia.

        La lista vacía significa que el corpus no cubre la pregunta.
        """
        top_k = top_k if top_k is not None else settings.top_k
        piso = piso if piso is not None else settings.relevance_floor
        max_por_fuente = (
            max_por_fuente if max_por_fuente is not None else settings.max_por_fuente
        )

        if not pregunta or not pregunta.strip():
            return []
        if top_k <= 0:
            raise ValueError("top_k debe ser mayor que cero")

        consulta = self._embeber_pregunta(pregunta)
        # Los embeddings se normalizaron al construir el índice y la consulta
        # se normaliza aquí, así que el producto escalar ya es el coseno.
        scores = self.embeddings @ consulta

        resultados: list[Recuperado] = []
        por_documento: dict[str, int] = {}

        # Se recorre en orden descendente y se corta al primer fragmento por
        # debajo del piso: a partir de ahí todos son peores.
        for i in np.argsort(-scores):
            score = float(scores[i])
            if score < piso:
                break

            fragmento = self.fragmentos[i]
            clave = fragmento.url or fragmento.source_id
            if por_documento.get(clave, 0) >= max_por_fuente:
                continue
            por_documento[clave] = por_documento.get(clave, 0) + 1

            resultados.append(Recuperado(fragmento=fragmento, score=score))
            if len(resultados) >= top_k:
                break

        if not resultados:
            mejor = float(scores.max()) if scores.size else 0.0
            # debug, no warning: no encontrar nada es funcionamiento normal.
            log.debug(
                "Nada sobre el piso %.2f (mejor coseno %.3f) para: %s",
                piso,
                mejor,
                pregunta[:80],
            )
        return resultados

    def _embeber_pregunta(self, pregunta: str) -> np.ndarray:
        """Embebe la pregunta con el prefijo de consulta propio de BGE.

        BGE es asimétrico: los pasajes se embeben tal cual (`embed()`, en la
        ingesta) y solo la consulta lleva prefijo de instrucción
        (`query_embed()`, aquí). Cruzarlo degrada en silencio todas las
        similitudes del sistema.
        """
        try:
            vectores = list(self.embebedor.query_embed(pregunta))
        except Exception as exc:
            raise ErrorDeIndice(f"No se pudo embeber la pregunta: {exc}") from exc

        if not vectores:
            raise ErrorDeIndice("El modelo no devolvió ningún embedding")

        consulta = np.asarray(vectores[0], dtype=np.float32)
        norma = float(np.linalg.norm(consulta))
        if norma == 0.0:
            raise ErrorDeIndice("La pregunta produjo un embedding nulo")
        return consulta / norma


def cargar(directorio: Path | None = None) -> Indice:
    """Carga el índice de disco y prepara el modelo de embeddings."""
    directorio = Path(directorio) if directorio else settings.index_dir
    ruta_emb = directorio / "embeddings.npy"
    ruta_frag = directorio / "chunks.jsonl"

    for ruta in (ruta_emb, ruta_frag):
        if not ruta.is_file():
            raise ErrorDeIndice(
                f"Falta {ruta}. Ejecuta 'python -m agent_core.ingest.build' "
                "antes de consultar el índice."
            )

    try:
        embeddings = np.load(ruta_emb).astype(np.float32, copy=False)
    except (ValueError, OSError) as exc:
        raise ErrorDeIndice(f"No se pudo leer {ruta_emb}: {exc}") from exc

    if embeddings.ndim != 2 or embeddings.shape[1] != EMBEDDING_DIM:
        raise ErrorDeIndice(
            f"Se esperaba una matriz (n, {EMBEDDING_DIM}); se encontró "
            f"{embeddings.shape}"
        )

    fragmentos = _leer_fragmentos(ruta_frag)
    if len(fragmentos) != embeddings.shape[0]:
        raise ErrorDeIndice(
            f"Índice desalineado: {embeddings.shape[0]} vectores frente a "
            f"{len(fragmentos)} fragmentos. Reconstruye el índice."
        )

    return Indice(
        embeddings=embeddings,
        fragmentos=fragmentos,
        embebedor=TextEmbedding(model_name=settings.embedding_model),
    )


def _leer_fragmentos(ruta: Path) -> list[Fragmento]:
    """Lee chunks.jsonl con el esquema fijo declarado en CLAUDE.md."""
    fragmentos: list[Fragmento] = []
    with ruta.open(encoding="utf-8") as f:
        for n, linea in enumerate(f, start=1):
            linea = linea.strip()
            if not linea:
                continue
            try:
                r = json.loads(linea)
                fragmentos.append(
                    Fragmento(
                        chunk_id=r["chunk_id"],
                        text=r["text"],
                        title=r["title"],
                        source_id=r["source_id"],
                        tier=r["tier"],
                        url=r["url"],
                        date=r["date"],
                    )
                )
            except json.JSONDecodeError as exc:
                raise ErrorDeIndice(f"{ruta}:{n} no es JSON válido: {exc}") from exc
            except KeyError as exc:
                raise ErrorDeIndice(f"{ruta}:{n} no tiene el campo {exc}") from exc

    if not fragmentos:
        raise ErrorDeIndice(f"{ruta} está vacío. Reconstruye el índice.")
    return fragmentos


_indice: Indice | None = None


def indice() -> Indice:
    """Devuelve el índice por defecto, cargándolo la primera vez."""
    global _indice
    if _indice is None:
        _indice = cargar()
    return _indice


def precalentar() -> None:
    """Carga índice y modelo por adelantado.

    Sin esto, el primer visitante paga la carga del modelo ONNX dentro de su
    propia petición. Se llama al arrancar el frontend, no en cada turno.
    """
    indice()


def buscar(
    pregunta: str,
    top_k: int | None = None,
    piso: float | None = None,
) -> list[Recuperado]:
    """Punto de entrada del resto de la aplicación.

    Lista vacía = el corpus no responde a la pregunta y toca derivar.
    """
    return indice().buscar(pregunta, top_k=top_k, piso=piso)
