"""Descarga de páginas con caché en disco.

La caché no es una optimización: es cortesía con el servidor de Ronald. La
ingesta se reconstruye muchas veces mientras se ajusta el troceado, y no hay
razón para golpear su sitio en cada iteración.
"""

import hashlib
import logging
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ..config import settings
from .sources import SITE, excluida

log = logging.getLogger(__name__)

CABECERAS = {
    "User-Agent": (
        "RGWallcoveringAssistant/0.1 (+https://rgwallcovering.com; "
        "corpus ingestion for the site's own assistant)"
    )
}

#: Pausa entre descargas reales. No hay prisa y el sitio es de un negocio
#: pequeño.
PAUSA_S = 1.0

#: Páginas que ya están declaradas en el registro de fuentes con su propio id.
#: El descubrimiento del blog las salta para no duplicarlas ni atribuirlas mal.
PAGINAS_PROPIAS = {
    "about-us",
    "interior-design",
    "contact",
    "blog",
    "commercial",
    "residential",
}


def _ruta_cache(url: str) -> Path:
    clave = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return settings.cache_dir / f"{clave}.html"


def obtener(url: str, refrescar: bool = False) -> str | None:
    """Devuelve el HTML de `url`, desde caché si existe.

    Devuelve None si la descarga falla: una fuente caída no debe tumbar la
    ingesta entera, solo quedar registrada y ausente del corpus.
    """
    cache = _ruta_cache(url)
    if cache.exists() and not refrescar:
        return cache.read_text(encoding="utf-8")

    try:
        respuesta = requests.get(url, headers=CABECERAS, timeout=30)
        respuesta.raise_for_status()
    except requests.RequestException as exc:
        log.warning("No se pudo descargar %s: %s", url, exc)
        return None

    # requests adivina latin-1 cuando la cabecera no declara charset, y el
    # sitio es UTF-8: sin esto los títulos llegan con caracteres corruptos y
    # se cuelan tal cual en el corpus.
    if respuesta.encoding is None or respuesta.encoding.lower() == "iso-8859-1":
        respuesta.encoding = respuesta.apparent_encoding or "utf-8"

    html = respuesta.text
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(html, encoding="utf-8")
    time.sleep(PAUSA_S)
    return html


def descubrir_enlaces(html: str, base: str = SITE) -> list[str]:
    """Extrae del índice del blog las URLs de los artículos.

    WordPress no marca los enlaces a entradas de forma distinguible, así que
    el filtro es por descarte: mismo dominio, no excluida, y con al menos un
    segmento de ruta. El recuento real se contrasta después contra los 28
    artículos que anuncia el índice — ver docs/02_data_provenance.md §1.3.
    """
    sopa = BeautifulSoup(html, "html.parser")
    dominio = urlparse(base).netloc

    encontradas: list[str] = []
    vistas: set[str] = set()

    for etiqueta in sopa.find_all("a", href=True):
        url = urljoin(base, etiqueta["href"]).split("#")[0].rstrip("/")

        if not url or url in vistas:
            continue
        if urlparse(url).netloc != dominio:
            continue
        if excluida(url + "/"):
            continue

        ruta = urlparse(url).path.strip("/")
        # La raíz y las páginas de primer nivel ya están en el registro de
        # fuentes; aquí solo buscamos entradas del blog. Sin esta lista,
        # /commercial y /residential entran como si fueran artículos y quedan
        # atribuidos al blog, que es procedencia incorrecta.
        if not ruta or ruta in PAGINAS_PROPIAS:
            continue

        vistas.add(url)
        encontradas.append(url)

    return encontradas
