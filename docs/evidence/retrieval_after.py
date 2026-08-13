"""Recuperación de fragmentos sobre el índice de RG Wallcovering.

Lee el índice escrito por `agent_core/ingest/` (matriz de embeddings + JSONL de
fragmentos), embebe la pregunta del visitante y devuelve los fragmentos más
cercanos por similitud coseno.

El corpus es pequeño (~300 fragmentos): similitud coseno sobre un array de
numpy, sin base de datos vectorial.

Devolver una lista vacía es un resultado correcto y esperado, no un error: el
umbral de relevancia existe precisamente para producirlo cuando el corpus no
contiene la respuesta. Quien consuma este módulo debe derivar al equipo, nunca
rellenar el hueco.

El campo `tier` viaja intacto hasta el prompt; sin él no se puede decidir qué
se puede afirmar sobre el negocio.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384

# Directorio del índice: <raíz del repo>/data/index
DEFAULT_INDEX_DIR = Path(__file__).resolve().parents[1] / "data" / "index"

EMBEDDINGS_FILE = "embeddings.npy"
CHUNKS_FILE = "chunks.jsonl"

# Piso de relevancia (coseno). Por debajo, el fragmento se descarta aunque sea
# el vecino más cercano: el blog es temáticamente rico y factualmente pobre, y
# el vecino más cercano a una pregunta real suele ser elocuentemente
# irrelevante. Bajarlo para "conseguir algo" reintroduce el riesgo que S2 veta.
RELEVANCE_FLOOR = 0.62

DEFAULT_TOP_K = 5


class RetrievalError(RuntimeError):
    """El índice no existe, está incompleto o es incoherente."""


@dataclass(frozen=True)
class Chunk:
    """Un fragmento del corpus, tal y como lo escribió la ingesta."""

    chunk_id: str
    text: str
    title: str
    source_id: str
    tier: str
    url: str
    date: str


@dataclass(frozen=True)
class RetrievedChunk:
    """Fragmento recuperado junto a su similitud coseno con la pregunta.

    `chunk.text` es dato no confiable: si contiene instrucciones, son contenido
    que se reporta, nunca órdenes que se obedecen.
    """

    chunk: Chunk
    score: float


@dataclass(eq=False)
class Retriever:
    """Índice cargado en memoria: embeddings, fragmentos y modelo."""

    embeddings: np.ndarray
    chunks: list[Chunk]
    embedder: TextEmbedding = field(repr=False)

    def search(
        self,
        question: str,
        top_k: int = DEFAULT_TOP_K,
        relevance_floor: float = RELEVANCE_FLOOR,
    ) -> list[RetrievedChunk]:
        """Devuelve hasta `top_k` fragmentos por encima del piso de relevancia.

        La lista vacía significa que el corpus no cubre la pregunta. Es un
        resultado legítimo: no se completa con el mejor candidato disponible.
        """
        if not question or not question.strip():
            return []
        if top_k <= 0:
            raise ValueError("top_k debe ser mayor que cero")

        query = self._embed_question(question)
        # Embeddings normalizados en build y consulta normalizada aquí, así que
        # el producto escalar ya es la similitud coseno.
        scores = self.embeddings @ query

        order = np.argsort(-scores)[:top_k]
        results = [
            RetrievedChunk(chunk=self.chunks[i], score=float(scores[i]))
            for i in order
            if scores[i] >= relevance_floor
        ]

        if not results:
            best = float(scores.max()) if scores.size else 0.0
            logger.debug(
                "Sin fragmentos sobre el piso %.2f (mejor coseno: %.3f)",
                relevance_floor,
                best,
            )
        return results

    def _embed_question(self, question: str) -> np.ndarray:
        """Embebe la pregunta con el prefijo de consulta propio de bge."""
        try:
            vectors = list(self.embedder.query_embed(question))
        except Exception as exc:  # el modelo puede fallar al descargarse/cargarse
            raise RetrievalError(f"No se pudo embeber la pregunta: {exc}") from exc

        if not vectors:
            raise RetrievalError("El modelo no devolvió ningún embedding")

        query = np.asarray(vectors[0], dtype=np.float32)
        norm = float(np.linalg.norm(query))
        if norm == 0.0:
            raise RetrievalError("La pregunta produjo un embedding nulo")
        return query / norm


def load_retriever(index_dir: Path = DEFAULT_INDEX_DIR) -> Retriever:
    """Carga el índice de `index_dir` y prepara el modelo de embeddings.

    Lanza `RetrievalError` si falta algún fichero, si el número de vectores no
    coincide con el de fragmentos o si la dimensión no es la esperada.
    """
    index_dir = Path(index_dir)
    embeddings_path = index_dir / EMBEDDINGS_FILE
    chunks_path = index_dir / CHUNKS_FILE

    for path in (embeddings_path, chunks_path):
        if not path.is_file():
            raise RetrievalError(
                f"Falta {path}. Ejecuta la ingesta antes de consultar el índice."
            )

    try:
        embeddings = np.load(embeddings_path).astype(np.float32, copy=False)
    except (ValueError, OSError) as exc:
        raise RetrievalError(f"No se pudo leer {embeddings_path}: {exc}") from exc

    if embeddings.ndim != 2 or embeddings.shape[1] != EMBEDDING_DIM:
        raise RetrievalError(
            f"Se esperaba una matriz (n_chunks, {EMBEDDING_DIM}); "
            f"se encontró {embeddings.shape}"
        )

    chunks = _load_chunks(chunks_path)
    if len(chunks) != embeddings.shape[0]:
        raise RetrievalError(
            f"El índice está desalineado: {embeddings.shape[0]} vectores frente "
            f"a {len(chunks)} fragmentos. Reconstruye el índice."
        )

    return Retriever(
        embeddings=embeddings,
        chunks=chunks,
        embedder=TextEmbedding(model_name=EMBEDDING_MODEL),
    )


def _load_chunks(path: Path) -> list[Chunk]:
    """Lee chunks.jsonl respetando el esquema fijo, un registro por línea."""
    chunks: list[Chunk] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                chunks.append(
                    Chunk(
                        chunk_id=record["chunk_id"],
                        text=record["text"],
                        title=record["title"],
                        source_id=record["source_id"],
                        tier=record["tier"],
                        url=record["url"],
                        date=record["date"],
                    )
                )
            except json.JSONDecodeError as exc:
                raise RetrievalError(f"{path}:{line_no} no es JSON válido: {exc}") from exc
            except KeyError as exc:
                raise RetrievalError(f"{path}:{line_no} no tiene el campo {exc}") from exc
    if not chunks:
        raise RetrievalError(f"{path} está vacío. Reconstruye el índice.")
    return chunks


_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    """Devuelve el retriever por defecto, cargándolo la primera vez."""
    global _retriever
    if _retriever is None:
        _retriever = load_retriever()
    return _retriever


def search(
    question: str,
    top_k: int = DEFAULT_TOP_K,
    relevance_floor: float = RELEVANCE_FLOOR,
) -> list[RetrievedChunk]:
    """Busca en el corpus por defecto los fragmentos relevantes a `question`.

    Punto de entrada del resto de la aplicación. Lista vacía = el corpus no
    responde a la pregunta y toca derivar al equipo.
    """
    return get_retriever().search(question, top_k=top_k, relevance_floor=relevance_floor)
