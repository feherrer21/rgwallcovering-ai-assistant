"""Captura y persistencia de leads.

Contiene datos personales: nombre, email, teléfono. `data/leads.jsonl` está en
.gitignore desde el primer commit, antes de que pudiera existir ningún lead.

El fichero local es un registro operativo, NO el sistema de registro. El lead
se entrega a Ronald por correo en el momento de capturarlo (fase 4.5): su
bandeja de entrada es donde ya vive, tiene búsqueda, copia de seguridad y un
botón de responder que llega al cliente. `entregar()` es la costura por donde
se añadirían otros destinos.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from .config import settings

log = logging.getLogger(__name__)

#: Campos que puede traer un lead, en el orden en que se leen bien.
CAMPOS = (
    "nombre",
    "email",
    "telefono",
    "tipo_proyecto",
    "espacio",
    "ubicacion",
    "necesita_diseno",
    "estilo_referencia",
    "plazo",
    "resumen",
)


def guardar(datos: dict[str, Any], conversation_id: str = "") -> dict[str, Any]:
    """Persiste un lead y devuelve el registro completo."""
    registro = {
        "lead_id": uuid.uuid4().hex[:12],
        "conversation_id": conversation_id,
        "creado_en": datetime.now(timezone.utc).isoformat(),
        **{k: v for k, v in datos.items() if k in CAMPOS and v not in (None, "")},
    }

    settings.leads_file.parent.mkdir(parents=True, exist_ok=True)
    with settings.leads_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")

    # Nunca se registra el contenido: son datos personales y los logs viajan
    # a sitios donde un lead no debería estar.
    log.info("Lead guardado (%s)", registro["lead_id"])
    return registro


def listar(limite: int = 100) -> list[dict[str, Any]]:
    """Devuelve los leads guardados, del más reciente al más antiguo."""
    if not settings.leads_file.exists():
        return []

    registros: list[dict[str, Any]] = []
    with settings.leads_file.open(encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            try:
                registros.append(json.loads(linea))
            except json.JSONDecodeError:
                # Una línea corrupta no debe impedir leer las demás.
                log.warning("Línea ilegible en %s", settings.leads_file)
                continue

    return list(reversed(registros))[:limite]


def formatear(registro: dict[str, Any]) -> str:
    """Formatea un lead para que lo lea una persona.

    El resumen va primero: es lo que Ronald necesita antes de marcar, y lo
    que se lee en la pantalla de bloqueo del móvil.
    """
    lineas = [registro.get("resumen", "").strip(), ""]

    etiquetas = {
        "nombre": "Name",
        "email": "Email",
        "telefono": "Phone",
        "tipo_proyecto": "Project type",
        "espacio": "Space",
        "ubicacion": "Location",
        "necesita_diseno": "Needs design help",
        "estilo_referencia": "Style / reference",
        "plazo": "Timing",
    }
    # Los valores del enum están en español porque el esquema de la
    # herramienta lo está; el correo que lee Ronald va en inglés como el resto
    # de la interfaz.
    traduccion = {
        "residencial": "residential",
        "comercial": "commercial",
        "no_definido": "not established",
    }

    for campo, etiqueta in etiquetas.items():
        valor = registro.get(campo)
        if valor in (None, ""):
            continue
        if isinstance(valor, bool):
            valor = "yes" if valor else "no"
        elif campo == "tipo_proyecto":
            valor = traduccion.get(valor, valor)
        lineas.append(f"{etiqueta}: {valor}")

    lineas.append("")
    lineas.append(f"Captured: {registro.get('creado_en', '')}")
    lineas.append(f"Reference: {registro.get('lead_id', '')}")
    return "\n".join(lineas).strip()


def asunto(registro: dict[str, Any]) -> str:
    """Asunto del correo: triageable desde la pantalla de bloqueo."""
    tipo = registro.get("tipo_proyecto", "")
    partes = ["New enquiry"]
    if registro.get("nombre"):
        partes.append(f"— {registro['nombre']}")
    if tipo in ("residencial", "comercial"):
        partes.append(f"({'residential' if tipo == 'residencial' else 'commercial'})")
    return " ".join(partes)
