"""Demo del asistente en Streamlit.

Desechable a propósito: existe para enseñarle a Ronald cómo se comporta el
asistente y para mirar por dentro lo que la web nunca enseñará —qué pasajes
sostienen cada respuesta y con qué score—. Importa `agent_core` directamente,
sin pasar por la API (docs/03_spec.md §2).

Se arranca con:
    streamlit run demo_streamlit/app.py
"""

import sys
from pathlib import Path

import streamlit as st

# `streamlit run` pone en sys.path la carpeta del script, no la raíz del
# repositorio, así que sin esto `agent_core` no se encuentra.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_core import leads, retrieval, run_turn  # noqa: E402

TIERS = {
    "A": "A · rgwallcovering.com",
    "B": "B · third-party listing",
    "C": "C · trade knowledge",
}


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

    chat, bandeja = st.tabs(["Chat", "Leads"])
    with chat:
        vista_chat()
    with bandeja:
        vista_leads()


def vista_chat() -> None:
    """Conversación con historial de sesión."""
    for mensaje in st.session_state.historial:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

    pregunta = st.chat_input("Ask about wallcovering, painting, a project…")
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


def vista_leads() -> None:
    """Leads capturados en esta máquina.

    Son datos personales. En la demo son personas inventadas; el sistema de
    registro real es la bandeja de correo, no este fichero.
    """
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
