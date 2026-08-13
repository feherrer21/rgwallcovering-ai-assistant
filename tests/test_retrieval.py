"""Pruebas de recuperación.

Se construye un índice sintético con un embebedor de mentira: las pruebas no
deben depender de descargar un modelo de 130 MB ni de que el corpus real esté
construido.
"""

import json

import numpy as np
import pytest

from agent_core import retrieval
from agent_core.retrieval import ErrorDeIndice, Fragmento, Indice

DIM = retrieval.EMBEDDING_DIM


def _vector(*, eje: int) -> np.ndarray:
    """Vector unitario sobre un eje concreto."""
    v = np.zeros(DIM, dtype=np.float32)
    v[eje] = 1.0
    return v


class EmbebedorFalso:
    """Devuelve siempre el mismo vector, elegido por la prueba."""

    def __init__(self, vector: np.ndarray):
        self.vector = vector

    def query_embed(self, pregunta: str):
        return [self.vector]


def _fragmento(n: int, tier: str = "A", url: str = "doc1") -> Fragmento:
    return Fragmento(
        chunk_id=f"c{n}",
        text=f"Título — cuerpo del fragmento {n}",
        title="Título",
        source_id="S-test",
        tier=tier,
        url=url,
        date="",
    )


def _indice(vectores: list[np.ndarray], fragmentos: list[Fragmento],
            consulta: np.ndarray) -> Indice:
    return Indice(
        embeddings=np.vstack(vectores),
        fragmentos=fragmentos,
        embebedor=EmbebedorFalso(consulta),
    )


# --- El piso de relevancia -------------------------------------------------


def test_por_debajo_del_piso_devuelve_vacio():
    """Es LA prueba de este módulo: no encontrar nada es un resultado válido.

    Si esto se rompe, el asistente empieza a responder con el vecino más
    cercano aunque sea irrelevante, que es exactamente el fallo que el
    criterio S2 veta.
    """
    idx = _indice(
        vectores=[_vector(eje=1)],          # ortogonal a la consulta
        fragmentos=[_fragmento(0)],
        consulta=_vector(eje=0),
    )
    assert idx.buscar("cualquier cosa", piso=0.5) == []


def test_por_encima_del_piso_devuelve_resultado():
    idx = _indice(
        vectores=[_vector(eje=0)],          # idéntico a la consulta
        fragmentos=[_fragmento(0)],
        consulta=_vector(eje=0),
    )
    resultados = idx.buscar("cualquier cosa", piso=0.5)
    assert len(resultados) == 1
    assert resultados[0].score == pytest.approx(1.0)


def test_el_piso_se_puede_ajustar_por_llamada():
    """La fase 6 barre este valor: tiene que ser un parámetro, no una constante."""
    idx = _indice(
        vectores=[_vector(eje=0)],
        fragmentos=[_fragmento(0)],
        consulta=_vector(eje=0),
    )
    assert idx.buscar("x", piso=0.99) != []
    assert idx.buscar("x", piso=1.01) == []


# --- El nivel de confianza sobrevive el viaje ------------------------------


def test_el_tier_llega_intacto():
    """Sin tier no se puede decidir qué se puede afirmar del negocio."""
    idx = _indice(
        vectores=[_vector(eje=0)],
        fragmentos=[_fragmento(0, tier="C")],
        consulta=_vector(eje=0),
    )
    assert idx.buscar("x", piso=0.5)[0].fragmento.tier == "C"


# --- Diversidad de fuentes -------------------------------------------------


def test_un_documento_no_acapara_los_resultados():
    """Con 27 artículos de longitud dispar, uno largo podría copar el contexto."""
    idx = _indice(
        vectores=[_vector(eje=0)] * 3 + [_vector(eje=0)],
        fragmentos=[
            _fragmento(0, url="largo"),
            _fragmento(1, url="largo"),
            _fragmento(2, url="largo"),
            _fragmento(3, url="otro"),
        ],
        consulta=_vector(eje=0),
    )
    resultados = idx.buscar("x", piso=0.5, top_k=5, max_por_fuente=2)
    urls = [r.fragmento.url for r in resultados]
    assert urls.count("largo") == 2
    assert "otro" in urls


# --- Entradas degeneradas --------------------------------------------------


@pytest.mark.parametrize("pregunta", ["", "   ", "\n"])
def test_pregunta_vacia_no_consulta_el_indice(pregunta):
    idx = _indice([_vector(eje=0)], [_fragmento(0)], _vector(eje=0))
    assert idx.buscar(pregunta) == []


def test_top_k_invalido_es_error():
    idx = _indice([_vector(eje=0)], [_fragmento(0)], _vector(eje=0))
    with pytest.raises(ValueError):
        idx.buscar("x", top_k=0)


# --- Carga del índice ------------------------------------------------------


def test_indice_ausente_da_error_accionable(tmp_path):
    with pytest.raises(ErrorDeIndice, match="agent_core.ingest.build"):
        retrieval.cargar(tmp_path)


def test_indice_desalineado_da_error(tmp_path):
    """Dos vectores y un fragmento: reconstruir el índice, no seguir adelante."""
    np.save(tmp_path / "embeddings.npy", np.zeros((2, DIM), dtype=np.float32))
    (tmp_path / "chunks.jsonl").write_text(
        json.dumps(
            {
                "chunk_id": "c0", "text": "t", "title": "T",
                "source_id": "S", "tier": "A", "url": "", "date": "",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ErrorDeIndice, match="desalineado"):
        retrieval.cargar(tmp_path)


def test_fragmento_sin_campo_obligatorio_da_error(tmp_path):
    np.save(tmp_path / "embeddings.npy", np.zeros((1, DIM), dtype=np.float32))
    (tmp_path / "chunks.jsonl").write_text(
        json.dumps({"chunk_id": "c0", "text": "t"}) + "\n", encoding="utf-8"
    )
    with pytest.raises(ErrorDeIndice, match="tier|title|source_id"):
        retrieval.cargar(tmp_path)


def test_dimension_inesperada_da_error(tmp_path):
    np.save(tmp_path / "embeddings.npy", np.zeros((1, 99), dtype=np.float32))
    (tmp_path / "chunks.jsonl").write_text(
        json.dumps(
            {
                "chunk_id": "c0", "text": "t", "title": "T",
                "source_id": "S", "tier": "A", "url": "", "date": "",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ErrorDeIndice, match="384"):
        retrieval.cargar(tmp_path)
