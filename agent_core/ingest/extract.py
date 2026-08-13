"""Extracción de texto legible a partir de HTML."""

import re

from bs4 import BeautifulSoup

#: Elementos que nunca aportan contenido y sí ruido repetido en cada página.
RUIDO = (
    "script", "style", "nav", "header", "footer", "form",
    "noscript", "iframe", "svg", "button",
)

#: Clases e ids que envuelven navegación, menús y pies. Coincidencia por
#: subcadena, en minúsculas.
#:
#: OJO con la especificidad. La primera versión incluía "widget" y "header"
#: a secas: Elementor envuelve TODO el contenido en clases con "widget", así
#: que el filtro vaciaba la página entera y la ingesta terminaba con cero
#: fragmentos sin lanzar ningún error. Los objetivos reales en un tema
#: Elementor son los contenedores de plantilla (elementor-location-*), no la
#: palabra "widget".
RUIDO_ATRIBUTOS = (
    "elementor-location-header",
    "elementor-location-footer",
    "site-header",
    "site-footer",
    "nav-menu",
    "menu-item",
    "sidebar",
    "cookie",
    "breadcrumb",
    "social-icon",
    "share-button",
)


def _es_ruido(etiqueta) -> bool:
    # Un elemento ya eliminado junto a su padre sigue apareciendo en la lista
    # de find_all, pero con attrs a None. Preguntarle por sus clases revienta.
    atributos_crudos = getattr(etiqueta, "attrs", None)
    if not atributos_crudos:
        return False

    clases = atributos_crudos.get("class") or []
    if isinstance(clases, str):
        clases = [clases]

    atributos = " ".join([*clases, atributos_crudos.get("id") or ""]).lower()
    return any(patron in atributos for patron in RUIDO_ATRIBUTOS)


def extraer(html: str) -> tuple[str, str]:
    """Devuelve (título, texto) de una página HTML.

    El texto sale como párrafos separados por línea en blanco, que es lo que
    el troceador espera para poder partir por límites naturales.
    """
    sopa = BeautifulSoup(html, "html.parser")

    titulo = ""
    if sopa.title and sopa.title.string:
        titulo = sopa.title.string.strip()
    if h1 := sopa.find("h1"):
        titulo = h1.get_text(strip=True) or titulo
    # WordPress arrastra el nombre del sitio en el <title>; sobra.
    titulo = re.sub(r"\s*[-|–]\s*RG Wallcovering.*$", "", titulo).strip()

    for etiqueta in sopa.find_all(RUIDO):
        etiqueta.decompose()
    # list() para congelar la lista antes de mutar el árbol: eliminar un
    # elemento invalida a sus descendientes, que aún están en el iterador.
    for etiqueta in list(sopa.find_all(True)):
        if _es_ruido(etiqueta):
            etiqueta.decompose()

    bloques: list[str] = []
    for etiqueta in sopa.find_all(["h2", "h3", "h4", "p", "li", "blockquote"]):
        texto = etiqueta.get_text(" ", strip=True)
        # Los fragmentos muy cortos son casi siempre restos de interfaz
        # ("Read more", "Home", una fecha suelta).
        if len(texto) < 25:
            continue
        bloques.append(texto)

    # Elementor duplica contenido entre versiones de escritorio y móvil.
    unicos: list[str] = []
    vistos: set[str] = set()
    for bloque in bloques:
        if bloque not in vistos:
            vistos.add(bloque)
            unicos.append(bloque)

    return titulo, "\n\n".join(unicos)


def extraer_markdown(texto: str) -> tuple[str, str]:
    """Devuelve (título, cuerpo) de un documento markdown local.

    Los comentarios HTML se descartan: llevan la nota de procedencia, que es
    para quien mantiene el repositorio, no para el modelo.
    """
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.DOTALL)

    titulo = ""
    lineas = texto.splitlines()
    for i, linea in enumerate(lineas):
        if linea.startswith("# "):
            titulo = linea[2:].strip()
            lineas = lineas[i + 1:]
            break

    cuerpo = "\n".join(lineas)
    cuerpo = re.sub(r"\n{3,}", "\n\n", cuerpo).strip()
    return titulo, cuerpo
