"""API HTTP sobre `agent_core`.

Envoltorio fino y sin estado: la conversación viaja en cada petición, no en el
servidor. Toda la lógica vive en `agent_core`; aquí solo se traduce JSON a
`run_turn()` y de vuelta. Contrato en docs/03_spec.md §5.
"""

import hmac
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent_core import leads, retrieval, run_turn
from agent_core.config import settings

from .limits import Limitador

log = logging.getLogger(__name__)

limitador = Limitador(settings.rate_limit_por_minuto, settings.rate_limit_por_hora)


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Carga índice y modelo al arrancar, no en la primera visita."""
    try:
        retrieval.precalentar()
    except retrieval.ErrorDeIndice:
        # Arrancar igual: /health lo reporta y el fallo se ve ahí, en lugar de
        # que el proceso muera y no haya nada a lo que preguntarle qué pasa.
        log.exception("El índice no se pudo cargar")
    if not settings.envio_configurado:
        log.warning("Sin credenciales SMTP: los leads se guardarán sin entregarse")
    yield


app = FastAPI(title="RG Wallcovering assistant", lifespan=ciclo_de_vida)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class Mensaje(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=8000)


class PeticionChat(BaseModel):
    # Los topes no son validación defensiva porque sí: cada carácter que entra
    # aquí acaba en un prompt que paga Ronald.
    message: str = Field(min_length=1, max_length=2000)
    history: list[Mensaje] = Field(default_factory=list, max_length=40)
    conversation_id: str = Field(default="", max_length=64)


class FuenteJSON(BaseModel):
    title: str
    url: str
    tier: str


class RespuestaChat(BaseModel):
    reply: str
    sources: list[FuenteJSON]
    #: Sin fuentes y sin derivar sería una respuesta sin fundamento: por eso
    #: ambos campos salen aunque la interfaz apenas los pinte.
    deferred: bool
    lead: dict | None
    conversation_id: str


def limitar(request: Request) -> None:
    """Aplica el límite por IP. Ver `limits.py`."""
    ip = request.client.host if request.client else "desconocida"
    permitido, espera = limitador.permitido(ip)
    if not permitido:
        raise HTTPException(
            status_code=429,
            detail=(
                "Too many messages in a short time. Please wait a moment — or "
                "reach us directly at info@rgwallcovering.com / "
                "+1 (401) 722-9255."
            ),
            headers={"Retry-After": str(espera)},
        )


@app.post("/chat", response_model=RespuestaChat, dependencies=[Depends(limitar)])
def chat(peticion: PeticionChat) -> RespuestaChat:
    """Un turno de conversación."""
    conversation_id = peticion.conversation_id or uuid.uuid4().hex[:12]

    turno = run_turn(
        peticion.message,
        historial=[m.model_dump() for m in peticion.history],
        conversation_id=conversation_id,
    )

    return RespuestaChat(
        reply=turno.respuesta,
        sources=[
            FuenteJSON(title=f.titulo, url=f.url, tier=f.tier) for f in turno.fuentes
        ],
        deferred=turno.derivado,
        lead=turno.lead,
        conversation_id=conversation_id,
    )


@app.get("/health")
def health() -> dict:
    """Liveness, y si el índice está realmente cargado."""
    try:
        fragmentos = len(retrieval.indice().fragmentos)
        indice_ok = True
    except retrieval.ErrorDeIndice:
        fragmentos, indice_ok = 0, False

    return {
        "status": "ok" if indice_ok else "degraded",
        "index_loaded": indice_ok,
        "chunks": fragmentos,
        "email_delivery": settings.envio_configurado,
    }


@app.get("/leads")
def listar_leads(
    limite: int = 50, x_admin_token: str = Header(default="")
) -> list[dict]:
    """Leads recientes. Devuelve datos personales: solo con token.

    Es una comodidad de desarrollo, no una funcionalidad: el sistema de
    registro es la bandeja de Ronald. Sin `ADMIN_TOKEN` configurado el
    endpoint no existe para nadie.
    """
    if not settings.admin_token:
        raise HTTPException(status_code=503, detail="Not available")
    if not hmac.compare_digest(x_admin_token, settings.admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return leads.listar(limite)
