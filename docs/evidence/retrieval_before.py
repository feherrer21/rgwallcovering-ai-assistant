"""Retrieval half of the RG Wallcovering RAG chatbot.

An offline ingestion script crawls the RG Wallcovering website and blog,
splits the pages into overlapping text chunks, embeds them with
``BAAI/bge-small-en-v1.5`` and writes two files into ``data/index/``:

``embeddings.npy``
    A ``(n_chunks, dim)`` float array of L2-comparable chunk embeddings, one
    row per chunk, in the same order as the JSONL file.

``chunks.jsonl``
    One JSON object per line describing the corresponding chunk: its text
    plus metadata about the page it came from (url, title, ...).

This module loads that index once per process and answers similarity queries
against it.  The rest of the application should only need :func:`search`.

Typical use::

    from agent_core.retrieval import search

    for hit in search("do you install grasscloth wallpaper?", top_k=5):
        print(hit.score, hit.url, hit.text[:120])
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy as np

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

#: Embedding model.  Must match the model used by the ingestion script,
#: otherwise the query vectors live in a different space than the index.
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

#: BGE models are trained with an asymmetric prefix on the query side only.
#: Passages are embedded bare; queries get this instruction prepended.
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

#: Location of the index written by the ingestion script.  Overridable with
#: the ``RG_INDEX_DIR`` environment variable (useful in tests and deploys).
DEFAULT_INDEX_DIR = Path(os.environ.get("RG_INDEX_DIR", "data/index"))

EMBEDDINGS_FILENAME = "embeddings.npy"
CHUNKS_FILENAME = "chunks.jsonl"

#: Number of chunks returned when the caller does not say.
DEFAULT_TOP_K = 5

#: Cosine similarity below which a chunk is considered irrelevant.  BGE-small
#: scores are fairly generous, so this is deliberately a floor against
#: obvious noise rather than a precision knob.
DEFAULT_SCORE_THRESHOLD = 0.30

# Candidate field names in the JSONL records, most specific first.  The
# ingestion format is owned by another script, so we read it defensively.
_TEXT_FIELDS = ("text", "content", "chunk", "chunk_text", "page_content", "body")
_URL_FIELDS = ("url", "source_url", "source", "link", "page_url")
_TITLE_FIELDS = ("title", "page_title", "heading", "name")


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------


class RetrievalError(RuntimeError):
    """Base class for every error raised by this module."""


class IndexNotFoundError(RetrievalError):
    """The index directory or one of its files is missing."""


class IndexCorruptError(RetrievalError):
    """The index files exist but are unusable (bad shape, mismatch, bad JSON)."""


class EmbeddingError(RetrievalError):
    """The embedding model could not be loaded or could not embed the query."""


# --------------------------------------------------------------------------
# Data types
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Chunk:
    """A single ingested chunk of website copy."""

    text: str
    url: Optional[str] = None
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def source_label(self) -> str:
        """Short human-readable label for citations, e.g. in the answer footer."""
        return self.title or self.url or "RG Wallcovering"


@dataclass(frozen=True)
class SearchResult:
    """A chunk together with its similarity to the query."""

    text: str
    score: float
    url: Optional[str] = None
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    index: int = -1

    @property
    def source_label(self) -> str:
        """Short human-readable label for citations."""
        return self.title or self.url or "RG Wallcovering"

    def to_dict(self) -> Dict[str, Any]:
        """JSON-serializable view, for logging or API responses."""
        return {
            "text": self.text,
            "score": self.score,
            "url": self.url,
            "title": self.title,
            "metadata": self.metadata,
            "index": self.index,
        }


# --------------------------------------------------------------------------
# Embedding model (lazily loaded, cached per process)
# --------------------------------------------------------------------------

_model_lock = threading.Lock()
_model = None  # type: ignore[var-annotated]


def _get_model():
    """Return the shared :class:`fastembed.TextEmbedding` instance.

    The model is downloaded on first use (a few tens of MB) and then cached
    on disk by fastembed, so only the first ever call is slow.  Subsequent
    calls in the same process reuse the loaded ONNX session.

    Raises:
        EmbeddingError: if fastembed is not installed or the model cannot
            be loaded (no network on first run, corrupt cache, ...).
    """
    global _model
    if _model is not None:
        return _model

    with _model_lock:
        if _model is not None:  # another thread won the race
            return _model
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:  # pragma: no cover - environment issue
            raise EmbeddingError(
                "fastembed is required for retrieval. Install it with "
                "`pip install fastembed`."
            ) from exc

        try:
            logger.info("Loading embedding model %s", EMBEDDING_MODEL_NAME)
            _model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)
        except Exception as exc:
            raise EmbeddingError(
                f"Could not load embedding model {EMBEDDING_MODEL_NAME!r}: {exc}"
            ) from exc

    return _model


def _embed_query(query: str) -> np.ndarray:
    """Embed a user question and return a unit-length float32 vector.

    Uses fastembed's ``query_embed`` when available so the BGE query
    instruction prefix is applied the way the model expects; falls back to
    prefixing manually.

    Raises:
        EmbeddingError: if the model returns nothing or fails.
    """
    model = _get_model()

    vector: Optional[np.ndarray] = None
    try:
        query_embed = getattr(model, "query_embed", None)
        if callable(query_embed):
            for emb in query_embed(query):
                vector = np.asarray(emb, dtype=np.float32)
                break
        if vector is None:
            for emb in model.embed([BGE_QUERY_PREFIX + query]):
                vector = np.asarray(emb, dtype=np.float32)
                break
    except Exception as exc:
        raise EmbeddingError(f"Failed to embed query: {exc}") from exc

    if vector is None or vector.size == 0:
        raise EmbeddingError("Embedding model returned no vector for the query.")

    return _normalize(vector.reshape(-1))


def _normalize(vectors: np.ndarray) -> np.ndarray:
    """L2-normalize a vector or a stack of row vectors (zero-safe)."""
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim == 1:
        norm = float(np.linalg.norm(vectors))
        return vectors if norm == 0.0 else vectors / norm
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return vectors / norms


# --------------------------------------------------------------------------
# Index loading (lazily loaded, cached per index directory)
# --------------------------------------------------------------------------


class _Index:
    """In-memory copy of one on-disk index: normalized vectors + chunks."""

    __slots__ = ("embeddings", "chunks", "directory")

    def __init__(self, embeddings: np.ndarray, chunks: List[Chunk], directory: Path):
        self.embeddings = embeddings
        self.chunks = chunks
        self.directory = directory

    def __len__(self) -> int:
        return len(self.chunks)


_index_lock = threading.Lock()
_index_cache: Dict[Path, _Index] = {}


def _first_present(record: Dict[str, Any], keys: Sequence[str]) -> Optional[Any]:
    """Return the first non-empty value among ``keys`` in ``record``."""
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return None


def _parse_chunk_record(record: Dict[str, Any], line_no: int) -> Chunk:
    """Turn one JSONL record into a :class:`Chunk`.

    The ingestion script owns this format, so both flat records and records
    that nest page metadata under a ``metadata`` key are accepted.

    Raises:
        IndexCorruptError: if the record has no recognizable text field.
    """
    metadata = record.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {k: v for k, v in record.items() if k not in _TEXT_FIELDS}

    text = _first_present(record, _TEXT_FIELDS)
    if text is None:
        text = _first_present(metadata, _TEXT_FIELDS)
    if not isinstance(text, str) or not text.strip():
        raise IndexCorruptError(
            f"Chunk record on line {line_no} has no usable text field "
            f"(looked for {', '.join(_TEXT_FIELDS)})."
        )

    url = _first_present(record, _URL_FIELDS) or _first_present(metadata, _URL_FIELDS)
    title = _first_present(record, _TITLE_FIELDS) or _first_present(
        metadata, _TITLE_FIELDS
    )

    return Chunk(
        text=text,
        url=str(url) if url is not None else None,
        title=str(title) if title is not None else None,
        metadata=metadata,
    )


def _read_chunks(path: Path) -> List[Chunk]:
    """Read ``chunks.jsonl`` into a list of :class:`Chunk`, skipping blank lines."""
    chunks: List[Chunk] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise IndexCorruptError(
                        f"{path} line {line_no} is not valid JSON: {exc}"
                    ) from exc
                if not isinstance(record, dict):
                    raise IndexCorruptError(
                        f"{path} line {line_no} is not a JSON object."
                    )
                chunks.append(_parse_chunk_record(record, line_no))
    except OSError as exc:
        raise IndexNotFoundError(f"Could not read {path}: {exc}") from exc

    if not chunks:
        raise IndexCorruptError(f"{path} contains no chunks; re-run the ingestion.")
    return chunks


def _load_index(index_dir: Path) -> _Index:
    """Load and validate the index in ``index_dir`` (uncached)."""
    embeddings_path = index_dir / EMBEDDINGS_FILENAME
    chunks_path = index_dir / CHUNKS_FILENAME

    if not index_dir.is_dir():
        raise IndexNotFoundError(
            f"Index directory {index_dir} does not exist. "
            "Run the ingestion script to build the index first."
        )
    for path in (embeddings_path, chunks_path):
        if not path.is_file():
            raise IndexNotFoundError(
                f"Missing index file {path}. Run the ingestion script to rebuild "
                f"{index_dir}."
            )

    try:
        embeddings = np.load(embeddings_path, allow_pickle=False)
    except Exception as exc:
        raise IndexCorruptError(
            f"Could not load embeddings from {embeddings_path}: {exc}"
        ) from exc

    embeddings = np.asarray(embeddings, dtype=np.float32)
    if embeddings.ndim != 2 or embeddings.size == 0:
        raise IndexCorruptError(
            f"Expected a 2-D (n_chunks, dim) array in {embeddings_path}, "
            f"got shape {embeddings.shape}."
        )

    chunks = _read_chunks(chunks_path)
    if len(chunks) != embeddings.shape[0]:
        raise IndexCorruptError(
            f"Index is inconsistent: {embeddings.shape[0]} embeddings in "
            f"{embeddings_path.name} but {len(chunks)} chunks in "
            f"{chunks_path.name}. Re-run the ingestion script."
        )

    logger.info(
        "Loaded index from %s (%d chunks, dim=%d)",
        index_dir,
        len(chunks),
        embeddings.shape[1],
    )
    # Pre-normalize once so each query is a single matrix-vector product.
    return _Index(_normalize(embeddings), chunks, index_dir)


def get_index(index_dir: Optional[os.PathLike | str] = None) -> _Index:
    """Return the cached index for ``index_dir``, loading it on first use.

    Args:
        index_dir: Directory holding ``embeddings.npy`` and ``chunks.jsonl``.
            Defaults to ``data/index`` (or ``$RG_INDEX_DIR``).

    Raises:
        IndexNotFoundError: the directory or a required file is missing.
        IndexCorruptError: the files exist but do not line up.
    """
    path = Path(index_dir) if index_dir is not None else DEFAULT_INDEX_DIR
    path = path.expanduser().resolve()

    cached = _index_cache.get(path)
    if cached is not None:
        return cached

    with _index_lock:
        cached = _index_cache.get(path)
        if cached is None:
            cached = _load_index(path)
            _index_cache[path] = cached
    return cached


def clear_cache() -> None:
    """Drop the cached index (and force a reload on the next search).

    Call this after re-running the ingestion script inside a long-lived
    process; otherwise the stale index stays in memory.
    """
    with _index_lock:
        _index_cache.clear()


def warm_up(index_dir: Optional[os.PathLike | str] = None) -> None:
    """Load the model and index ahead of time.

    Call this at application start-up so the first user question does not pay
    for the model download / index read.
    """
    _get_model()
    get_index(index_dir)


def index_stats(index_dir: Optional[os.PathLike | str] = None) -> Dict[str, Any]:
    """Return a small summary of the loaded index, for health checks and logs."""
    index = get_index(index_dir)
    sources = {chunk.url for chunk in index.chunks if chunk.url}
    return {
        "index_dir": str(index.directory),
        "chunks": len(index.chunks),
        "dimensions": int(index.embeddings.shape[1]),
        "unique_sources": len(sources),
        "model": EMBEDDING_MODEL_NAME,
    }


# --------------------------------------------------------------------------
# Public search API
# --------------------------------------------------------------------------


def search(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    *,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    max_per_source: Optional[int] = None,
    index_dir: Optional[os.PathLike | str] = None,
) -> List[SearchResult]:
    """Find the chunks of RG Wallcovering's site most relevant to ``query``.

    The question is embedded with the same model used at ingestion time and
    compared against every chunk by cosine similarity.  Because both sides
    are unit-normalized, scores fall in ``[-1, 1]`` where higher is better.

    Args:
        query: The user's question. Whitespace-only queries return ``[]``.
        top_k: Maximum number of chunks to return.
        score_threshold: Minimum cosine similarity a chunk must reach.
            Pass ``0.0`` (or a negative value) to disable filtering.
        max_per_source: If set, keep at most this many chunks per source page,
            so one long blog post cannot crowd out the rest of the context.
        index_dir: Override the index location (mainly for tests).

    Returns:
        Up to ``top_k`` :class:`SearchResult` objects, highest score first.
        An empty list means nothing cleared the threshold — the caller should
        treat that as "not covered by the website" rather than as an error.

    Raises:
        TypeError: ``query`` is not a string.
        ValueError: ``top_k`` is not a positive integer.
        IndexNotFoundError / IndexCorruptError: the index is unusable.
        EmbeddingError: the query could not be embedded.
    """
    if not isinstance(query, str):
        raise TypeError(f"query must be a string, got {type(query).__name__}")
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError(f"top_k must be a positive integer, got {top_k!r}")

    query = query.strip()
    if not query:
        logger.debug("Empty query; returning no results.")
        return []

    index = get_index(index_dir)
    query_vector = _embed_query(query)

    if query_vector.shape[0] != index.embeddings.shape[1]:
        raise IndexCorruptError(
            f"Query vector has {query_vector.shape[0]} dimensions but the index "
            f"has {index.embeddings.shape[1]}. The index was probably built with "
            f"a different model than {EMBEDDING_MODEL_NAME}; re-run the ingestion."
        )

    scores = index.embeddings @ query_vector  # cosine similarity, shape (n_chunks,)

    # Take a generous candidate pool so threshold and per-source filtering
    # still have material to work with, then sort just that pool.
    pool_size = min(len(scores), max(top_k * 5, top_k))
    candidate_idx = np.argpartition(-scores, pool_size - 1)[:pool_size]
    candidate_idx = candidate_idx[np.argsort(-scores[candidate_idx], kind="stable")]

    results: List[SearchResult] = []
    per_source: Dict[str, int] = {}
    for i in candidate_idx:
        score = float(scores[i])
        if score < score_threshold:
            break  # candidates are sorted, so everything after this is worse

        chunk = index.chunks[i]
        if max_per_source is not None:
            key = chunk.url or chunk.title or f"__chunk_{i}"
            if per_source.get(key, 0) >= max_per_source:
                continue
            per_source[key] = per_source.get(key, 0) + 1

        results.append(
            SearchResult(
                text=chunk.text,
                score=score,
                url=chunk.url,
                title=chunk.title,
                metadata=chunk.metadata,
                index=int(i),
            )
        )
        if len(results) >= top_k:
            break

    logger.debug(
        "Query %r -> %d result(s), best score %.3f",
        query,
        len(results),
        results[0].score if results else float("nan"),
    )
    return results


def format_context(
    results: Iterable[SearchResult],
    *,
    max_chars: Optional[int] = None,
    include_sources: bool = True,
) -> str:
    """Render search results as a context block for the answering prompt.

    Each chunk becomes a numbered section labelled with its page title and
    URL, so the model can cite where an answer came from.

    Args:
        results: Results from :func:`search`.
        max_chars: Optional budget for the whole block. Chunks are added
            whole, in order, until the next one would not fit.
        include_sources: Whether to print the title/URL header per chunk.

    Returns:
        The formatted context, or an empty string if there is nothing to show.
    """
    blocks: List[str] = []
    total = 0
    for position, result in enumerate(results, start=1):
        header = f"[{position}]"
        if include_sources:
            header = f"{header} {result.source_label}"
            if result.url and result.url != result.source_label:
                header = f"{header} ({result.url})"
        block = f"{header}\n{result.text.strip()}"

        if max_chars is not None:
            added = len(block) + (2 if blocks else 0)
            if total + added > max_chars:
                if not blocks:  # never return nothing at all: truncate the first
                    blocks.append(block[:max_chars].rstrip())
                break
            total += added
        blocks.append(block)

    return "\n\n".join(blocks)


def retrieve_context(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    *,
    max_chars: Optional[int] = None,
    **search_kwargs: Any,
) -> str:
    """Convenience wrapper: search and return a ready-to-prompt context string.

    Returns an empty string when nothing relevant is found, which the caller
    should handle by telling the visitor the site does not cover the topic
    (and, for RG Wallcovering, pointing them at the contact page).
    """
    return format_context(
        search(query, top_k=top_k, **search_kwargs), max_chars=max_chars
    )


__all__ = [
    "Chunk",
    "SearchResult",
    "RetrievalError",
    "IndexNotFoundError",
    "IndexCorruptError",
    "EmbeddingError",
    "EMBEDDING_MODEL_NAME",
    "DEFAULT_INDEX_DIR",
    "DEFAULT_TOP_K",
    "DEFAULT_SCORE_THRESHOLD",
    "search",
    "retrieve_context",
    "format_context",
    "get_index",
    "index_stats",
    "warm_up",
    "clear_cache",
]


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    import argparse

    parser = argparse.ArgumentParser(description="Query the RG Wallcovering index.")
    parser.add_argument("query", nargs="+", help="Question to search for")
    parser.add_argument("-k", "--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--index-dir", default=None)
    parser.add_argument("--threshold", type=float, default=DEFAULT_SCORE_THRESHOLD)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    hits = search(
        " ".join(args.query),
        top_k=args.top_k,
        score_threshold=args.threshold,
        index_dir=args.index_dir,
    )
    if not hits:
        print("No relevant chunks found.")
    for rank, hit in enumerate(hits, start=1):
        print(f"\n--- {rank}. {hit.score:.3f} | {hit.source_label} | {hit.url}")
        print(hit.text[:500])
