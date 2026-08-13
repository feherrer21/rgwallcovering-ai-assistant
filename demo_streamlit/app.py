"""Demo del asistente en Streamlit.

Desechable a propósito: existe para enseñarle a Ronald cómo se comporta el
asistente y para mirar por dentro lo que la web nunca enseñará —qué pasajes
sostienen cada respuesta y con qué score—. Importa `agent_core` directamente,
sin pasar por la API (docs/03_spec.md §2).

Se arranca con:
    streamlit run demo_streamlit/app.py

Publicado en Streamlit Community Cloud la URL es pública, así que aquí viven
dos protecciones que en la web irían en la API: un tope de turnos por sesión
—este camino no pasa por el limitador por IP de `backend/`— y la clave que
tapa los leads.
"""

import hmac
import os
import sys
from pathlib import Path

import streamlit as st

# `streamlit run` pone en sys.path la carpeta del script, no la raíz del
# repositorio, así que sin esto `agent_core` no se encuentra.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# En Streamlit Cloud los secretos llegan en st.secrets; `config.py` los espera
# en el entorno y construye `settings` al importarse, así que el volcado tiene
# que ocurrir antes de importar `agent_core`. En local no hay secrets.toml y
# esto no hace nada: manda el .env.
try:
    for _clave, _valor in st.secrets.items():
        if isinstance(_valor, str):
            os.environ.setdefault(_clave, _valor)
except Exception:  # noqa: BLE001 — sin fichero de secretos, seguir con .env
    pass

from agent_core import leads, retrieval, run_turn  # noqa: E402
from agent_core.config import settings  # noqa: E402

TIERS = {
    "A": "A · rgwallcovering.com",
    "B": "B · third-party listing",
    "C": "C · trade knowledge",
}

#: Turnos por sesión. La URL es pública y cada turno es una llamada al modelo
#: que paga Ronald; el limitador por IP vive en la API y este camino no pasa
#: por él. Una conversación real son 5-8 turnos.
MAX_TURNOS = int(os.environ.get("MAX_TURNOS_DEMO", "20"))


@st.cache_resource(show_spinner="Loading the index…")
def preparar() -> bool:
    """Carga índice y modelo una vez por proceso, no en cada pregunta."""
    try:
        retrieval.precalentar()
        return True
    except retrieval.ErrorDeIndice:
        return False


def main() -> None:
    st.set_page_config(page_title="RG Wallcovering assistant", page_icon="🎨")
    st.title("RG Wallcovering assistant")

    if not preparar():
        st.error(
            "The index is not built. Run `python -m agent_core.ingest.build` "
            "and reload."
        )
        return

    st.session_state.setdefault("historial", [])
    st.session_state.setdefault("ultimo", None)

    panel_lateral()

    chat, bandeja, entrega = st.tabs(["Chat", "Leads", "Recipients"])
    with chat:
        vista_chat()
    with bandeja:
        vista_leads()
    with entrega:
        vista_destinatarios()


def vista_chat() -> None:
    """Conversación con historial de sesión."""
    for mensaje in st.session_state.historial:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

    agotada = len(st.session_state.historial) // 2 >= MAX_TURNOS
    if agotada:
        st.info(
            "This demo allows a limited number of messages per session. Start "
            "a new conversation from the sidebar, or reach the team at "
            "info@rgwallcovering.com."
        )

    pregunta = st.chat_input(
        "Ask about wallcovering, painting, a project…", disabled=agotada
    )
    if not pregunta:
        return

    with st.chat_message("user"):
        st.markdown(pregunta)

    with st.chat_message("assistant"), st.spinner("Thinking…"):
        turno = run_turn(pregunta, historial=st.session_state.historial)
        st.markdown(turno.respuesta)

    st.session_state.historial = turno.historial
    st.session_state.ultimo = turno

    if turno.lead:
        st.success("Enquiry captured and sent to the team.")

    # Para que el panel lateral se repinte con las fuentes de este turno.
    st.rerun()


def desbloqueado(seccion: str) -> bool:
    """Pide la clave guardada en los secretos de la app.

    La URL es pública: sin esto, los datos de quien escribiera antes quedarían
    a la vista del siguiente visitante. Sin `ADMIN_TOKEN` configurado la
    pestaña no se abre para nadie, que es el estado por defecto.

    `seccion` solo distingue el widget: las dos pestañas protegidas se dibujan
    en la misma pasada y Streamlit no admite dos claves iguales. El desbloqueo
    sí es compartido —una clave, las dos pestañas.
    """
    if not settings.admin_token:
        st.info("Set ADMIN_TOKEN in the app secrets to open this tab.")
        return False

    if st.session_state.get("desbloqueado"):
        return True

    clave = st.text_input("Password", type="password", key=f"clave_{seccion}")
    if not clave:
        return False
    if hmac.compare_digest(clave, settings.admin_token):
        st.session_state.desbloqueado = True
        st.rerun()
    st.error("Wrong password.")
    return False


def vista_leads() -> None:
    """Leads capturados en esta máquina.

    Son datos personales. En la demo son personas inventadas; el sistema de
    registro real es la bandeja de correo, no este fichero. En Streamlit Cloud
    el disco es efímero, así que esta lista se vacía en cada reinicio y no se
    pierde nada: el lead salió por correo en el momento de capturarlo.
    """
    if not desbloqueado("leads"):
        return

    registros = leads.listar(limite=20)
    if not registros:
        st.info("No enquiries captured yet.")
        return

    st.caption(
        f"{len(registros)} most recent, newest first — from the local log. "
        "Each one was also emailed to the team when it was captured."
    )
    for registro in registros:
        etiqueta = registro.get("nombre") or registro.get("lead_id", "")
        tipo = registro.get("tipo_proyecto", "")
        with st.expander(f"{etiqueta} — {tipo}" if tipo else etiqueta):
            st.text(leads.formatear(registro))


def valida(direccion: str) -> bool:
    """Comprobación mínima: si esto pasa algo roto, el lead no llega a nadie."""
    if direccion.count("@") != 1 or " " in direccion:
        return False
    usuario, dominio = direccion.split("@")
    return bool(usuario) and "." in dominio and not dominio.endswith(".")


def vista_destinatarios() -> None:
    """Quién recibe los leads. Editable en caliente, y honesta sobre su límite.

    En Streamlit Cloud los secretos son de solo lectura desde la app y el disco
    es efímero: lo que se cambie aquí vale para el contenedor vivo y se pierde
    en el siguiente reinicio o redespliegue. Por eso la pantalla no dice
    "guardado" y calla — enseña la línea exacta que hay que pegar en los
    secretos para que sea permanente.

    Escribe sobre `settings`, que es el mismo objeto que lee `leads.entregar()`
    y sobrevive a los reruns porque el módulo ya está importado.
    """
    if not desbloqueado("recipients"):
        return

    if not settings.envio_configurado:
        st.warning(
            "No email credentials configured, so enquiries are stored but not "
            "delivered. Set SMTP_USER and SMTP_PASSWORD in the app secrets."
        )

    st.caption("Every enquiry captured in a conversation is emailed to these.")
    texto = st.text_area(
        "One address per line",
        value="\n".join(settings.destinatarios_lead),
        height=120,
    )

    if st.button("Apply"):
        direcciones = [linea.strip() for linea in texto.splitlines() if linea.strip()]
        invalidas = [d for d in direcciones if not valida(d)]
        if not direcciones:
            st.error("At least one address is needed, or enquiries reach nobody.")
        elif invalidas:
            st.error("These do not look like addresses: " + ", ".join(invalidas))
        else:
            settings.lead_email_to = ", ".join(direcciones)
            st.success("Applied. The next enquiry goes to these addresses.")

    st.divider()
    st.caption(
        "This change lasts as long as the app stays running — a restart or a "
        "redeploy brings back whatever is in the secrets. To make it "
        "permanent, paste this line into the app's Secrets:"
    )
    st.code(
        f'LEAD_EMAIL_TO = "{", ".join(settings.destinatarios_lead)}"',
        language="toml",
    )


def panel_lateral() -> None:
    """Fuentes del último turno: es lo que hace auditable la respuesta."""
    turno = st.session_state.ultimo

    with st.sidebar:
        st.subheader("Sources")

        if turno is None:
            st.caption("Ask something to see what the answer rests on.")
        elif turno.derivado:
            st.warning(
                "No passage cleared the relevance floor. The assistant "
                "deferred instead of guessing — that is the intended outcome."
            )
        else:
            for fuente in turno.fuentes:
                st.markdown(f"**{fuente.titulo}**")
                st.caption(
                    f"{TIERS.get(fuente.tier, fuente.tier)} · "
                    f"score {fuente.score:.2f}"
                )
                if fuente.url:
                    st.caption(fuente.url)

        if turno is not None:
            st.divider()
            st.caption(
                f"{turno.segundos:.1f}s · {turno.tokens_entrada} in / "
                f"{turno.tokens_salida} out tokens"
            )

        st.divider()
        if st.button("New conversation"):
            st.session_state.historial = []
            st.session_state.ultimo = None
            st.rerun()


main()
