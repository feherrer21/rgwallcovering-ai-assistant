"""Prueba del demo con contexto de sesión real.

Existe por un fallo concreto: las dos pestañas protegidas pedían la clave con
la misma `key`, Streamlit lo prohíbe, y la app reventaba nada más abrirse en
Cloud. Ejecutar el script "a pelo" con python no lo detecta —sin sesión no hay
registro de widgets— y servir la página tampoco, porque Streamlit no ejecuta
el script hasta que se conecta un navegador. `AppTest` sí.

No llama al modelo: nadie escribe en el chat. Sí carga el índice, así que
tarda unos segundos.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from agent_core.config import settings

APP = Path(__file__).resolve().parent.parent / "demo_streamlit" / "app.py"


@pytest.fixture
def app(monkeypatch) -> AppTest:
    # Con la clave puesta es cuando se dibujan los dos campos de contraseña, y
    # cuando el fallo de las claves duplicadas aparece.
    monkeypatch.setattr(settings, "admin_token", "clave-de-prueba")
    return AppTest.from_file(str(APP), default_timeout=120)


def test_la_app_arranca_con_las_dos_pestanas_protegidas(app):
    app.run()
    assert not app.exception
    # Una por pestaña protegida: leads y destinatarios.
    assert len(app.text_input) == 2


def test_la_clave_correcta_abre_las_dos_pestanas(app):
    app.run()
    app.text_input[0].input("clave-de-prueba").run()
    assert not app.exception
    assert app.session_state["desbloqueado"] is True
    # Desbloqueadas ambas, ya no se pide la clave en ninguna.
    assert not app.text_input


def test_la_clave_incorrecta_no_abre_nada(app):
    app.run()
    app.text_input[0].input("otra cosa").run()
    assert not app.exception
    assert "desbloqueado" not in app.session_state
    assert app.error
