"""Troceado del texto en fragmentos indexables.

Cada fragmento lleva el título del documento delante. Sin eso, un fragmento
que dice "…se aplicaba a mano sobre el papel…" es irrecuperable: ni el modelo
ni el lector saben de qué documento salió. Es el fallo que el caso nombra
explícitamente — contenido separado del encabezado que le daba sentido.
"""

from ..config import settings

#: Separador entre el título y el cuerpo dentro de un fragmento.
SEPARADOR = " — "


def trocear(
    texto: str,
    titulo: str,
    tamano: int | None = None,
    solape: int | None = None,
) -> list[str]:
    """Parte `texto` en fragmentos, cada uno prefijado con `titulo`.

    Se corta por párrafos: un párrafo nunca se parte salvo que por sí solo
    exceda el tamaño objetivo, en cuyo caso se divide por frases.
    """
    tamano = tamano or settings.chunk_size
    solape = solape or settings.chunk_overlap

    parrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    if not parrafos:
        return []

    prefijo = f"{titulo}{SEPARADOR}" if titulo else ""
    presupuesto = max(tamano - len(prefijo), 200)

    piezas: list[str] = []
    for parrafo in parrafos:
        if len(parrafo) <= presupuesto:
            piezas.append(parrafo)
        else:
            piezas.extend(_partir_largo(parrafo, presupuesto))

    fragmentos: list[str] = []
    actual = ""
    for pieza in piezas:
        candidato = f"{actual}\n\n{pieza}" if actual else pieza
        if len(candidato) <= presupuesto:
            actual = candidato
            continue
        if actual:
            fragmentos.append(actual)
        # El solape arranca con la cola del fragmento anterior, para que una
        # idea que cae justo en el corte siga siendo recuperable.
        cola = actual[-solape:] if actual and solape else ""
        actual = f"{cola}\n\n{pieza}".strip() if cola else pieza

    if actual:
        fragmentos.append(actual)

    return [f"{prefijo}{f}" for f in fragmentos]


def _partir_largo(parrafo: str, presupuesto: int) -> list[str]:
    """Parte un párrafo que por sí solo excede el presupuesto, por frases."""
    frases = parrafo.replace("! ", ". ").replace("? ", ". ").split(". ")
    piezas: list[str] = []
    actual = ""
    for frase in frases:
        frase = frase.strip()
        if not frase:
            continue
        candidato = f"{actual}. {frase}" if actual else frase
        if len(candidato) <= presupuesto:
            actual = candidato
        else:
            if actual:
                piezas.append(actual)
            # Una sola frase más larga que el presupuesto se trocea a lo bruto:
            # es raro y no merece maquinaria propia.
            while len(frase) > presupuesto:
                piezas.append(frase[:presupuesto])
                frase = frase[presupuesto:]
            actual = frase
    if actual:
        piezas.append(actual)
    return piezas
