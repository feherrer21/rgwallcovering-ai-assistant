"""Núcleo del asistente de RG Wallcovering.

No sabe nada de HTTP, Streamlit ni WordPress: cualquier frontend es un
consumidor de este paquete. Ver docs/03_spec.md §2.
"""

from .agent import Fuente, Turno, run_turn

__all__ = ["run_turn", "Turno", "Fuente"]
