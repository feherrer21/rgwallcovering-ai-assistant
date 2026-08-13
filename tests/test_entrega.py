"""Pruebas de la entrega del lead por correo.

Nunca se envía nada de verdad: se sustituye smtplib por un doble. Lo que más
se prueba aquí es el camino de fallo, porque es el que decide si un cliente
se pierde en silencio.
"""

import logging
import smtplib

import pytest

from agent_core import leads
from agent_core.config import settings

LEAD = {
    "lead_id": "abc123",
    "nombre": "Ana Ruiz",
    "email": "ana.ruiz@example.com",
    "tipo_proyecto": "comercial",
    "ubicacion": "Pawtucket, RI",
    "resumen": "Reception area, no design yet, visit not charged.",
}


class SMTPFalso:
    """Doble de smtplib.SMTP que registra lo que se le pide."""

    ultimo: "SMTPFalso | None" = None

    def __init__(self, host, port, timeout=None):
        self.host, self.port = host, port
        self.mensajes = []
        self.login_llamado = False
        self.starttls_llamado = False
        SMTPFalso.ultimo = self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self):
        self.starttls_llamado = True

    def login(self, usuario, clave):
        self.login_llamado = True

    def send_message(self, mensaje):
        self.mensajes.append(mensaje)


@pytest.fixture
def con_credenciales(monkeypatch):
    monkeypatch.setattr(settings, "smtp_user", "remitente@example.com")
    monkeypatch.setattr(settings, "smtp_password", "clave-de-aplicacion")
    monkeypatch.setattr(settings, "lead_email_to", "ronald@example.com")
    monkeypatch.setattr(smtplib, "SMTP", SMTPFalso)


@pytest.fixture
def sin_credenciales(monkeypatch):
    monkeypatch.setattr(settings, "smtp_user", "")
    monkeypatch.setattr(settings, "smtp_password", "")


# --- Camino feliz ----------------------------------------------------------


def test_se_envia_con_asunto_y_destinatario(con_credenciales):
    assert leads.entregar(LEAD) is True
    mensaje = SMTPFalso.ultimo.mensajes[0]
    assert "Ana Ruiz" in mensaje["Subject"]
    assert mensaje["To"] == "ronald@example.com"
    assert SMTPFalso.ultimo.starttls_llamado
    assert SMTPFalso.ultimo.login_llamado


def test_reply_to_apunta_al_cliente(con_credenciales):
    """Para que Ronald responda desde la bandeja sin copiar la dirección."""
    leads.entregar(LEAD)
    assert SMTPFalso.ultimo.mensajes[0]["Reply-To"] == "ana.ruiz@example.com"


def test_sin_email_del_cliente_no_hay_reply_to(con_credenciales):
    leads.entregar({**LEAD, "email": None})
    assert SMTPFalso.ultimo.mensajes[0]["Reply-To"] is None


def test_el_resumen_va_en_el_cuerpo(con_credenciales):
    leads.entregar(LEAD)
    cuerpo = SMTPFalso.ultimo.mensajes[0].get_content()
    assert cuerpo.startswith("Reception area, no design yet")


def test_varios_destinatarios(con_credenciales, monkeypatch):
    """Ronald adelantó que querrá añadir una o dos direcciones más."""
    monkeypatch.setattr(settings, "lead_email_to", "a@example.com, b@example.com")
    leads.entregar(LEAD)
    assert SMTPFalso.ultimo.mensajes[0]["To"] == "a@example.com, b@example.com"


# --- Caminos de fallo: lo que de verdad importa ----------------------------


def test_sin_credenciales_no_revienta(sin_credenciales):
    assert leads.entregar(LEAD) is False


def test_sin_credenciales_el_error_dice_donde_esta_el_lead(sin_credenciales, caplog):
    with caplog.at_level(logging.ERROR, logger="agent_core.leads"):
        leads.entregar(LEAD)
    mensaje = " ".join(r.getMessage() for r in caplog.records)
    assert "abc123" in mensaje
    assert "leads.jsonl" in mensaje


def test_un_fallo_de_smtp_no_se_propaga(con_credenciales, monkeypatch):
    """El lead ya está en disco; el visitante no debe ver una excepción."""

    def explota(*args, **kwargs):
        raise smtplib.SMTPAuthenticationError(535, b"bad credentials")

    monkeypatch.setattr(smtplib, "SMTP", explota)
    assert leads.entregar(LEAD) is False


def test_un_fallo_de_red_no_se_propaga(con_credenciales, monkeypatch):
    def explota(*args, **kwargs):
        raise OSError("network unreachable")

    monkeypatch.setattr(smtplib, "SMTP", explota)
    assert leads.entregar(LEAD) is False


def test_el_fallo_se_registra_como_error(con_credenciales, monkeypatch, caplog):
    """Un lead que no llega es un cliente perdido y merece ruido en el log."""

    def explota(*args, **kwargs):
        raise smtplib.SMTPException("boom")

    monkeypatch.setattr(smtplib, "SMTP", explota)
    with caplog.at_level(logging.ERROR, logger="agent_core.leads"):
        leads.entregar(LEAD)
    assert any(r.levelno >= logging.ERROR for r in caplog.records)


# --- Datos personales ------------------------------------------------------


def test_el_contenido_del_lead_no_llega_al_log(con_credenciales, caplog):
    with caplog.at_level(logging.DEBUG, logger="agent_core.leads"):
        leads.entregar(LEAD)
    registrado = " ".join(r.getMessage() for r in caplog.records)
    assert "Ana Ruiz" not in registrado
    assert "ana.ruiz@example.com" not in registrado
