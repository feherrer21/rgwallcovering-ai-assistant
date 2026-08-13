"""Pruebas de captura de leads.

Todos los datos son personas inventadas. Nunca entra un lead real en el
repositorio ni en las pruebas.
"""

import json
import logging

import pytest

from agent_core import leads
from agent_core.config import settings

LEAD = {
    "nombre": "Ana Ruiz",
    "email": "ana.ruiz@example.com",
    "tipo_proyecto": "residencial",
    "espacio": "accent wall in the living room",
    "ubicacion": "Cranston, RI",
    "necesita_diseno": True,
    "resumen": (
        "Ana wants one accent wall in her living room and has no design in "
        "mind yet. She is in Cranston, so the assessment visit is not "
        "charged. She asked about timing but was told the team confirms it."
    ),
}


@pytest.fixture(autouse=True)
def leads_temporales(tmp_path, monkeypatch):
    """Redirige el fichero de leads a un temporal para cada prueba."""
    monkeypatch.setattr(settings, "leads_file", tmp_path / "leads.jsonl")
    yield


def test_guardar_devuelve_registro_con_identificadores():
    registro = leads.guardar(LEAD, conversation_id="conv-1")
    assert registro["lead_id"]
    assert registro["conversation_id"] == "conv-1"
    assert registro["creado_en"].endswith("+00:00")
    assert registro["nombre"] == "Ana Ruiz"


def test_se_descartan_campos_desconocidos():
    """El modelo podría inventarse un campo; no debe acabar en el fichero."""
    registro = leads.guardar({**LEAD, "presupuesto_estimado": "$4000"})
    assert "presupuesto_estimado" not in registro


def test_se_descartan_campos_vacios():
    registro = leads.guardar({**LEAD, "telefono": "", "plazo": None})
    assert "telefono" not in registro
    assert "plazo" not in registro


def test_el_fichero_es_jsonl_valido():
    leads.guardar(LEAD)
    leads.guardar({**LEAD, "nombre": "Beatriz Soto"})
    lineas = settings.leads_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lineas) == 2
    assert [json.loads(l)["nombre"] for l in lineas] == ["Ana Ruiz", "Beatriz Soto"]


def test_listar_devuelve_el_mas_reciente_primero():
    leads.guardar({**LEAD, "nombre": "Primera"})
    leads.guardar({**LEAD, "nombre": "Segunda"})
    assert [r["nombre"] for r in leads.listar()] == ["Segunda", "Primera"]


def test_listar_sin_fichero_no_revienta():
    assert leads.listar() == []


def test_una_linea_corrupta_no_impide_leer_las_demas():
    leads.guardar(LEAD)
    with settings.leads_file.open("a", encoding="utf-8") as f:
        f.write("{esto no es json}\n")
    leads.guardar({**LEAD, "nombre": "Posterior"})
    assert len(leads.listar()) == 2


# --- Datos personales ------------------------------------------------------


def test_no_se_registran_datos_personales_en_el_log(caplog):
    """Los logs viajan a sitios donde un lead no debería estar."""
    with caplog.at_level(logging.DEBUG, logger="agent_core.leads"):
        leads.guardar(LEAD)
    registrado = " ".join(r.getMessage() for r in caplog.records)
    assert "Ana Ruiz" not in registrado
    assert "ana.ruiz@example.com" not in registrado
    assert "Cranston" not in registrado


# --- Presentación ----------------------------------------------------------


def test_el_resumen_va_primero_en_el_formato():
    """Es lo que Ronald necesita antes de marcar el teléfono."""
    texto = leads.formatear(leads.guardar(LEAD))
    assert texto.startswith("Ana wants one accent wall")


def test_los_booleanos_se_leen_como_texto():
    texto = leads.formatear(leads.guardar(LEAD))
    assert "Needs design help: yes" in texto


def test_el_asunto_es_triageable():
    asunto = leads.asunto(leads.guardar(LEAD))
    assert "Ana Ruiz" in asunto
    assert "residential" in asunto


def test_el_asunto_aguanta_un_lead_minimo():
    asunto = leads.asunto(leads.guardar({"nombre": "X", "resumen": "y"}))
    assert asunto.startswith("New enquiry")
