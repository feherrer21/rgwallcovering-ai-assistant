"""Registro de fuentes del corpus, con su nivel de confianza.

El nivel viaja con cada fragmento hasta el prompt. Ver CLAUDE.md: es el
mecanismo que hace exigible el criterio S2 (cero fabricación), no un adorno
de metadatos.

Procedencia y limitaciones de cada fuente: docs/02_data_provenance.md §1.1.
"""

from dataclasses import dataclass
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"

SITE = "https://rgwallcovering.com"


@dataclass(frozen=True)
class Fuente:
    """Una fuente del corpus.

    kind:
        "page"   una URL concreta
        "index"  una URL de la que se descubren enlaces a más páginas
        "local"  un fichero markdown de este repositorio
    """

    id: str
    kind: str
    tier: str
    ref: str
    titulo: str = ""


# ---------------------------------------------------------------------------
# Nivel A — contenido publicado por el propio negocio.
# El agente puede afirmarlo como hecho sobre RG Wallcovering.
# ---------------------------------------------------------------------------

FUENTES_A: list[Fuente] = [
    # Respuestas del dueño a las preguntas abiertas (2026-08-12). Es la fuente
    # más valiosa del corpus: responde justo lo que el sitio no contesta y los
    # visitantes sí preguntan.
    Fuente(
        "S0-ronald",
        "local",
        "A",
        str(KNOWLEDGE_DIR / "a_ronald.md"),
        "How RG Wallcovering works — confirmed by the owner",
    ),
    Fuente("S1-home", "page", "A", f"{SITE}/", "RG Wallcovering — Home"),
    Fuente("S1-about", "page", "A", f"{SITE}/about-us/", "About Us"),
    Fuente("S1-design", "page", "A", f"{SITE}/interior-design/", "Interior Design"),
    # /contact/ no se ingiere: todo su contenido vive en el pie de página, que
    # el extractor elimina por repetirse en las 35 páginas del sitio. El dato
    # se declara una vez como documento local, con su procedencia.
    Fuente(
        "S1-contacto",
        "local",
        "A",
        str(KNOWLEDGE_DIR / "a_contacto.md"),
        "How to get in touch with RG Wallcovering",
    ),
    # /services/ sirve texto de plantilla (ver EXCLUIDAS), pero sus dos hijas
    # sí tienen contenido real. Se declaran explícitamente para que queden
    # atribuidas como páginas de servicio y no como entradas de blog.
    Fuente("S1-commercial", "page", "A", f"{SITE}/commercial/", "Commercial"),
    Fuente("S1-residential", "page", "A", f"{SITE}/residential/", "Residential"),
    # El índice del blog: de aquí se descubren los ~28 artículos.
    Fuente("S2-blog", "index", "A", f"{SITE}/blog/", "Blog"),
]


# ---------------------------------------------------------------------------
# Nivel B — fichas de directorios de terceros.
# Afirmable, pero arrastrando que es de tercero y puede estar desactualizado.
#
# No se descarga en vivo a propósito. Los datos se extrajeron una vez
# (2026-08-12) y viven como documento local con su cabecera de procedencia:
# raspar BBB y Houzz en cada build sería frágil, maleducado con sus servidores,
# y produciría un corpus que cambia bajo nuestros pies sin que nos enteremos.
# ---------------------------------------------------------------------------

FUENTES_B: list[Fuente] = [
    Fuente(
        "S4-bbb",
        "local",
        "B",
        str(KNOWLEDGE_DIR / "b_directorios.md"),
        "Business details from third-party directories",
    ),
]


# ---------------------------------------------------------------------------
# Nivel C — conocimiento general del oficio, redactado para este proyecto.
# El agente puede explicar QUÉ DETERMINA una respuesta. Nunca puede decir
# "nosotros hacemos X" a partir de esto.
#
# Existe porque el corpus del cliente es temáticamente rico y factualmente
# flaco (docs/02_data_provenance.md §1.2). Sin nivel C el agente derivaría
# absolutamente todo y sería inútil.
# ---------------------------------------------------------------------------

FUENTES_C: list[Fuente] = [
    Fuente("S6-duracion", "local", "C", str(KNOWLEDGE_DIR / "c_duracion.md"),
           "What determines how long a wallcovering job takes"),
    Fuente("S6-coste", "local", "C", str(KNOWLEDGE_DIR / "c_coste.md"),
           "What drives the cost of a wallcovering project"),
    Fuente("S6-preparacion", "local", "C", str(KNOWLEDGE_DIR / "c_preparacion.md"),
           "Wall preparation and wallpaper removal"),
    Fuente("S6-visita", "local", "C", str(KNOWLEDGE_DIR / "c_visita.md"),
           "What a site visit is for"),
    Fuente("S6-residencial-comercial", "local", "C",
           str(KNOWLEDGE_DIR / "c_residencial_comercial.md"),
           "How residential and commercial work differ"),
    Fuente("S6-materiales", "local", "C", str(KNOWLEDGE_DIR / "c_materiales.md"),
           "Types of wallcovering material"),
]


FUENTES: list[Fuente] = FUENTES_A + FUENTES_B + FUENTES_C


# ---------------------------------------------------------------------------
# Exclusiones explícitas
# ---------------------------------------------------------------------------

#: Nunca se ingiere una URL que contenga alguno de estos fragmentos.
#:
#: /services/ está excluida porque sirve texto de plantilla de WordPress sobre
#: paneles solares, energía renovable y turbinas eólicas — restos del theme
#: original, en vivo en el sitio del cliente a fecha 2026-08-12. Un rastreador
#: ingenuo lo habría ingerido y el asistente hablaría de energía solar.
#: Ver docs/02_data_provenance.md §1.3.
EXCLUIDAS: tuple[str, ...] = (
    "/services",
    "/portfolio",       # 84 imágenes sin texto: no aporta nada a un corpus textual
    "/wp-content",
    "/wp-admin",
    "/feed",
    "/author/",
    "/tag/",
    "/category/",
    "/page/",
    "?",
    "#",
)


def excluida(url: str) -> bool:
    """¿Esta URL está en la lista de exclusión?"""
    return any(patron in url for patron in EXCLUIDAS)
