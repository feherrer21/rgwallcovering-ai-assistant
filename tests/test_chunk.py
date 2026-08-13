"""Pruebas del troceado.

El prefijo de título es la propiedad que más importa aquí: es lo que hace que
un fragmento sea atribuible por sí solo, y es el fallo que el caso nombra
explícitamente — contenido separado del encabezado que le daba sentido.
"""

from agent_core.ingest import chunk


def test_todo_fragmento_lleva_el_titulo_delante():
    texto = "\n\n".join(f"Párrafo número {i}. " * 12 for i in range(6))
    fragmentos = chunk.trocear(texto, "MI TÍTULO")

    assert len(fragmentos) > 1, "el texto de prueba debería producir varios"
    assert all(f.startswith("MI TÍTULO — ") for f in fragmentos)


def test_sin_titulo_no_se_inventa_prefijo():
    fragmentos = chunk.trocear("Un párrafo cualquiera con longitud suficiente.", "")
    assert fragmentos == ["Un párrafo cualquiera con longitud suficiente."]


def test_texto_vacio_no_produce_fragmentos():
    assert chunk.trocear("", "T") == []
    assert chunk.trocear("   \n\n  ", "T") == []


def test_se_respeta_el_tamano_objetivo():
    texto = "\n\n".join(f"Párrafo {i}. " * 20 for i in range(10))
    fragmentos = chunk.trocear(texto, "T", tamano=400, solape=50)
    # Se admite algo de holgura: un párrafo entero no se parte salvo que él
    # solo exceda el presupuesto.
    assert all(len(f) <= 500 for f in fragmentos)


def test_un_parrafo_mas_largo_que_el_presupuesto_se_parte():
    parrafo = "Una frase larga que se repite. " * 60
    fragmentos = chunk.trocear(parrafo, "T", tamano=300, solape=0)
    assert len(fragmentos) > 1


def test_un_parrafo_corto_no_se_parte():
    fragmentos = chunk.trocear("Corto pero suficiente para pasar el filtro.", "T")
    assert len(fragmentos) == 1
