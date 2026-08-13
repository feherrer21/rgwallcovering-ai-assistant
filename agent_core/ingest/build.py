"""Construye el índice del corpus. Se ejecuta a mano:

    python -m agent_core.ingest.build [--refrescar]

Produce data/index/embeddings.npy y data/index/chunks.jsonl.
Ver docs/03_spec.md §3.1.
"""

import argparse
import json
import logging
from pathlib import Path

import numpy as np

from ..config import settings
from . import chunk as troceo
from . import extract, fetch
from .sources import FUENTES, Fuente

log = logging.getLogger(__name__)


def _fragmentos_de_fuente(
    fuente: Fuente, refrescar: bool
) -> list[dict]:
    """Devuelve los registros de fragmento de una fuente."""
    documentos: list[tuple[str, str, str]] = []  # (titulo, texto, url)

    if fuente.kind == "local":
        ruta = Path(fuente.ref)
        if not ruta.exists():
            log.warning("Falta el documento local %s", ruta)
            return []
        titulo, cuerpo = extract.extraer_markdown(
            ruta.read_text(encoding="utf-8")
        )
        documentos.append((titulo or fuente.titulo, cuerpo, ""))

    elif fuente.kind == "page":
        html = fetch.obtener(fuente.ref, refrescar)
        if html:
            titulo, texto = extract.extraer(html)
            documentos.append((titulo or fuente.titulo, texto, fuente.ref))

    elif fuente.kind == "index":
        html = fetch.obtener(fuente.ref, refrescar)
        if html:
            enlaces = fetch.descubrir_enlaces(html)
            log.info("  %s: %d enlaces descubiertos", fuente.id, len(enlaces))
            for url in enlaces:
                pagina = fetch.obtener(url, refrescar)
                if not pagina:
                    continue
                titulo, texto = extract.extraer(pagina)
                if len(texto) < 200:
                    log.debug("  descartado por vacío: %s", url)
                    continue
                documentos.append((titulo, texto, url))

    registros: list[dict] = []
    for titulo, texto, url in documentos:
        for i, fragmento in enumerate(troceo.trocear(texto, titulo)):
            registros.append(
                {
                    "chunk_id": f"{fuente.id}-{len(registros):04d}",
                    "text": fragmento,
                    "title": titulo,
                    "source_id": fuente.id,
                    "tier": fuente.tier,
                    "url": url,
                    "date": "",
                }
            )
    return registros


def construir(refrescar: bool = False) -> dict[str, int]:
    """Construye el índice completo y devuelve el recuento por fuente."""
    todos: list[dict] = []
    recuento: dict[str, int] = {}

    for fuente in FUENTES:
        log.info("Procesando %s (nivel %s)", fuente.id, fuente.tier)
        registros = _fragmentos_de_fuente(fuente, refrescar)
        recuento[fuente.id] = len(registros)
        todos.extend(registros)

    if not todos:
        raise RuntimeError(
            "No se generó ningún fragmento. Revisa la conectividad y las "
            "rutas de los documentos locales."
        )

    log.info("Embebiendo %d fragmentos...", len(todos))
    from fastembed import TextEmbedding

    modelo = TextEmbedding(model_name=settings.embedding_model)

    # IMPORTANTE: embed() plano, no query_embed().
    # BGE es asimétrico: los pasajes se embeben tal cual y solo la consulta
    # lleva el prefijo de instrucción. Cruzarlo degrada en silencio todas las
    # similitudes del sistema. Ver docs/evidence/context_artifact_effect.md.
    vectores = np.array(
        list(modelo.embed([r["text"] for r in todos])), dtype=np.float32
    )

    # Normalizado en construcción, para que la búsqueda sea un solo producto
    # matriz-vector.
    normas = np.linalg.norm(vectores, axis=1, keepdims=True)
    normas[normas == 0.0] = 1.0
    vectores = vectores / normas

    settings.index_dir.mkdir(parents=True, exist_ok=True)
    np.save(settings.embeddings_path, vectores)
    with settings.chunks_path.open("w", encoding="utf-8") as f:
        for registro in todos:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")

    log.info(
        "Índice escrito: %d fragmentos, %d dimensiones",
        vectores.shape[0],
        vectores.shape[1],
    )
    return recuento


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refrescar",
        action="store_true",
        help="Ignora la caché y vuelve a descargar todas las páginas.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    recuento = construir(args.refrescar)

    print("\n--- Fragmentos por fuente ---")
    for fuente in FUENTES:
        print(f"  {fuente.tier}  {fuente.id:<28} {recuento.get(fuente.id, 0):>4}")
    print(f"  {'':>3} {'TOTAL':<28} {sum(recuento.values()):>4}")


if __name__ == "__main__":
    main()
