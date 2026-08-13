# Estado del proyecto

**Actualizado:** 2026-08-13 · **Commits:** 30 · **Pruebas:** 53 en verde

Documento vivo. **Se actualiza según avanza el trabajo, no al cerrar cada
fase** — cuando una tarea se mueve, cuando aparece o se resuelve un bloqueo, y
cuando una estimación resulta equivocada. Convención registrada en
`CLAUDE.md`.

Fuente de la verdad para "qué queda": `04_plan.md` (fases) y `05_tasks.md`
(tareas). Este fichero es el estado, no el plan.

**Último movimiento:** fase 4 completa (2026-08-13) — API, demo, README y
límite por IP, con los endpoints ejercitados contra el proceso real y la
transcripción commiteada. Antes, la entrega de leads de extremo a extremo con
correo recibido en bandeja.

---

## Resumen

```
Especificación  ████████████████████  100%   5 documentos
Fase 0  Contexto ███████████████████  100%   T0.1–T0.4
Fase 1  Ingesta  ███████████████████  100%   T1.1–T1.7
Fase 2  Retrieval███████████████████  100%   T2.1–T2.4
Fase 3  Agente   ███████████████████  100%   T3.1–T3.6
Fase 4  Frontends███████████████████  100%   T4.1–T4.4, API + demo
Fase 4.5 Entrega ████████████████░░░   83%   correo real recibido
Fase 5  Evaluación░░░░░░░░░░░░░░░░░░    0%   ← el hito que importa
Fase 6  Mejora   ░░░░░░░░░░░░░░░░░░░    0%
Fase 7  Fallos   ░░░░░░░░░░░░░░░░░░░    0%
Fase 8  Revisión ████████░░░░░░░░░░░   40%   registro abierto, 9 entradas
Fase 9  Comunicar░░░░░░░░░░░░░░░░░░░    0%
```

**Estimado 25 h · consumido ~17 h · restante ~8 h.**
Las horas consumidas son una estimación mía a partir del plan; Fabián las
ajusta con el tiempo real para `06_effort.md`.

---

## Bloqueos

**Ninguno bloquea el trabajo ahora mismo, y ya ninguno bloquea el despliegue.**

Resueltos: `ANTHROPIC_API_KEY` (2026-08-12), credenciales SMTP con correo real
recibido en bandeja (2026-08-13) y **la clave de API rotada** (2026-08-13) — la
anterior se había pegado en un chat; la nueva está en el `.env` y verificada
contra la API.

Lo que queda antes de publicar en la web de Ronald no son bloqueos sino
trabajo pendiente, y está en la tabla de deuda: IP real detrás del proxy,
`ALLOWED_ORIGINS` al dominio, `LEAD_EMAIL_TO` a su correo y el piso de
relevancia calibrado.

---

## Cómo retomar

Estado del entorno en la máquina de Fabián a 2026-08-13:

- `.venv` creado con las dependencias instaladas
- `.env` configurado y verificado: clave de Anthropic + SMTP de Gmail
- `data/index/` construido: 365 fragmentos
- `data/cache/` con las páginas del sitio descargadas
- Árbol de git limpio, 30 commits
- Remoto: **github.com/feherrer21/rgwallcovering-ai-assistant**, público.
  Verificado tras el push que ni `.env` ni `data/leads.jsonl` llegaron allí

```bash
# pruebas
./.venv/Scripts/python.exe -m pytest tests/ -q

# el demo (es lo que se le enseña a Ronald)
./.venv/Scripts/python.exe -m streamlit run demo_streamlit/app.py

# la API
./.venv/Scripts/python.exe -m uvicorn backend.app.main:app --reload --port 8000

# reconstruir el índice (solo si cambian las fuentes o el troceado)
./.venv/Scripts/python.exe -m agent_core.ingest.build

# una conversación desde Python
./.venv/Scripts/python.exe -c "from agent_core import run_turn; \
    print(run_turn('do you work in Boston?').respuesta)"
```

### Lo siguiente

**Fase 5, la evaluación.** Era la decisión abierta —fase 4 o fase 5 primero— y
se resolvió haciendo la 4, que ya está cerrada: ahora hay demo que enseñarle a
Ronald, que es lo que hace que conteste las preguntas que faltan. Sin baseline
commiteado, la fase 6 no tiene contra qué medir y la fase 7 es especulación,
así que a partir de aquí no hay nada por delante de la 5.

### Hilos abiertos que no están en ninguna tarea

- El piso de relevancia en 0.62 falla en dos casos ya observados: deriva
  *"do you work in Boston?"* aunque la respuesta existe, y no deriva
  *"can you install flooring for me?"* aunque debería. Material para la
  fase 6; el barrido va en pasos de 0.02, no de 0.1.
- La entrada 8 del registro de revisión (el resumen inventaba una corrección)
  se guarda como caso de regresión para el set de evaluación de la fase 5.
- `LEAD_EMAIL_TO` apunta al correo de Fabián, no al de Ronald. Cambiarlo solo
  cuando esto deje de ser una prueba.
- La latencia medida por HTTP (5,4 s y 7,3 s en la transcripción de T4.3)
  encaja con los 6–13 s de T3.6, pero en una web son muchos segundos mirando
  una pantalla quieta. El contrato de §5 responde de una pieza, sin streaming;
  si se decide cambiarlo, cambia el contrato. Anotado para la fase 6.

---

## Detalle por fase

### Especificación — completa

| | Documento | Commit |
|:--:|---|---|
| ✅ | `01_problem_statement.md` — problema, usuarios, éxito medible (S1–S5) | `6ba5650` |
| ✅ | `02_data_provenance.md` — corpus, set de evaluación, datos personales | `47d7729` |
| ✅ | `03_spec.md` — arquitectura, RAG sobre n8n, alternativas rechazadas | `074c09b` |
| ✅ | `04_plan.md` + `05_tasks.md` | `d458b37` |
| ✅ | `client_questions_ronald.md` | `e7ba8c9` |

### Fase 0 — Artefacto de contexto · completa

| | Tarea | Resultado |
|:--:|---|---|
| ✅ | T0.1 Generación en frío sin `CLAUDE.md` | 639 líneas, 0 apariciones de `tier` |
| ✅ | T0.2 Escribir `CLAUDE.md` | `d659265` |
| ✅ | T0.3 Regeneración en frío con `CLAUDE.md` | 232 líneas, tiers presentes |
| ✅ | T0.4 Análisis del diff | `context_artifact_effect.md` |

### Fase 1 — Ingesta · completa

| | Tarea | Resultado |
|:--:|---|---|
| ✅ | T1.1 Registro de fuentes con niveles y exclusiones | 15 fuentes |
| ✅ | T1.2 Descarga con caché | pausa de 1 s, cortesía con el servidor |
| ✅ | T1.3 Extracción HTML → texto | 2 errores corregidos |
| ✅ | T1.4 Troceado con título prefijado | 0 fragmentos sin prefijo |
| ✅ | T1.5 Documentos de nivel C | 6 documentos, 33 fragmentos |
| ✅ | T1.6 Embeddings y persistencia | 365 × 384 |
| ✅ | T1.7 Recuento real | `corpus_stats.md`; 28-vs-27 resuelto → **27** |

### Fase 2 — Recuperación · completa

| | Tarea | Resultado |
|:--:|---|---|
| ✅ | T2.1 Coseno sobre numpy | sin base vectorial |
| ✅ | T2.2 Piso de relevancia | 0.62 **provisional**, se calibra en fase 6 |
| ✅ | T2.3 Nivel, título, url y score por pasaje | |
| ✅ | T2.4 Pruebas | 19 pruebas, índice sintético |

### Fase 3 — Agente · completa

| | Tarea | Resultado |
|:--:|---|---|
| ✅ | T3.1 System prompt | reglas de nivel, inventario cerrado de servicios |
| ✅ | T3.2 Herramientas y despacho | `buscar_informacion`, `registrar_lead` |
| ✅ | T3.3 Persistencia de leads | + formato legible y asunto triageable |
| ✅ | T3.4 `run_turn()` | bucle, `refusal`, cacheo del prompt |
| ✅ | T3.5 Pruebas de leads | 12 pruebas, personas inventadas |
| ✅ | T3.6 Conversación real de extremo a extremo | 5 turnos, lead capturado con resumen |

**Hallazgo de T3.6:** el resumen para Ronald narraba una autocorrección que
nunca ocurrió. Corregido en el prompt y verificado reejecutando la misma
conversación. Entrada 8 del registro de revisión; se guarda como caso de
regresión para el set de evaluación.

Latencia observada: 6–13 s por turno. Tokens de entrada por turno: 1.558 →
4.979 según crece la conversación.

### Fase 4 — Frontends · completa

| | Tarea | Resultado |
|:--:|---|---|
| ✅ | T4.1 Demo en Streamlit | chat, panel de fuentes con nivel y score, pestaña de leads |
| ✅ | T4.2 API FastAPI | `POST /chat`, `GET /health`, `GET /leads`, CORS |
| ✅ | T4.3 Endpoints ejercitados con curl | `evidence/api_transcript.md`, 9 llamadas |
| ✅ | T4.4 `README.md` | instalación, arranque de ambos, reconstrucción del índice |

11 pruebas nuevas en `tests/test_api.py`, sin gastar llamadas al modelo.

Dos decisiones que el spec dejaba abiertas, resueltas: `/leads` va detrás de
`X-Admin-Token` y sin `ADMIN_TOKEN` configurado responde 503 —o sea, por
defecto no existe—, y el límite por IP entra ahora y no antes de desplegar,
porque `/chat` gasta el presupuesto de Ronald desde el primer visitante.

**Preparado para Streamlit Community Cloud** (2026-08-13), que es el canal
elegido para enseñárselo a Ronald. La URL es pública, así que el demo lleva
ahora lo que en la web haría la API: tope de 20 turnos por sesión —este camino
no pasa por el limitador por IP— y clave (`ADMIN_TOKEN`) delante de los leads y
de la pestaña de destinatarios. El índice pasa a estar versionado: Cloud
despliega desde el repositorio. El repositorio será **público**, decisión de
Fabián.

**Hallazgo de T4.1:** `streamlit run` pone en `sys.path` la carpeta del script,
no la raíz del repositorio, así que el demo no encontraba `agent_core`. No
salió en el arranque —el servidor devuelve 200 antes de ejecutar el script— y
solo apareció al ejecutarlo de verdad. Corregido en `demo_streamlit/app.py`.

### Fase 4.5 — Entrega del lead · 5 de 6

| | Tarea | Resultado |
|:--:|---|---|
| ✅ | T4.5.1 `entregar()` por correo | resumen arriba, `Reply-To` al cliente |
| ✅ | T4.5.2 Capturar y entregar en un solo paso | un lead guardado y no enviado es un cliente perdido |
| ✅ | T4.5.3 Camino de fallo | no propaga, log a ERROR con id y ruta, visitante no se entera |
| ✅ | T4.5.4 **Correo real recibido en bandeja** | verificado 2026-08-13 |
| ⬜ | T4.5.5 Confirmar destinatario con Ronald | pendiente de él |
| ✅ | T4.6 Rate limiting por IP | 10/min y 60/h, ventana deslizante en memoria |

El circuito completo está cerrado: conversación → calificación → lead en una
bandeja real. Con el correo como sistema de registro, un reinicio del proceso
no pierde nada.

### Fases 6 a 9 — pendientes

Sin empezar. Ver `05_tasks.md` para el desglose completo.

La **fase 5 es el hito crítico**: hasta que exista un baseline commiteado, la
fase 6 no tiene contra qué medir y la fase 7 es especulación. Si el tiempo
aprieta, el recorte sale de la fase 4, nunca de la 5, 6 o 7.

### Fase 8 — Revisión del output de IA · registro abierto

9 entradas en `ai_review_log.md`, escritas cuando ocurrieron. Las que importan
son la 2 (el filtro de ruido vaciaba el corpus y el build reportaba éxito), la
8 (el resumen para Ronald narraba una corrección que nunca ocurrió) y la 9 (el
demo devolvía 200 sin haber ejecutado una línea de la aplicación).

---

## Cobertura del checklist de entrega

Es la medida real de "cuánto falta", porque es lo que se califica.

| | Casilla | Dónde |
|:--:|---|---|
| ✅ | Problem statement: dominio, usuario, problema, éxito | `01` |
| ✅ | Por qué merece resolverse, en términos del cliente | `01` |
| ✅ | Data provenance: origen, límites, datos sensibles | `02` |
| ✅ | Prototipo funcionando de extremo a extremo | T3.6 con lead capturado; API y demo en T4.3 |
| ✅ | Spec, plan y tareas, con historial que prueba precedencia | `074c09b`, `d458b37` |
| ✅ | Artefacto de contexto + evidencia antes/después | `d659265`, `270b9c4` |
| ✅ | Retrieval o n8n, con la razón del rechazo | `03` §1 |
| 🔶 | Revisión del output de IA + un error cazado | registro abierto, 8 entradas |
| ⬜ | Análisis de fallos con inputs concretos | fase 7 |
| ⬜ | Una mejora medida, con lo que empeoró | fase 6 |
| ⬜ | Slide para el cliente | fase 9 |
| ⬜ | Demo con un caso que falla | fase 9 |
| ⬜ | Declaración de horas y qué se cortó | fase 9 |

**8 de 13 completas, 1 a medias, 4 sin empezar.**

---

## Deuda y huecos conocidos

Declarados, no descubiertos. Ninguno bloquea la entrega; todos bloquean el
uso real en la web de Ronald.

| Hueco | Estado |
|---|---|
| ~~Sin rate limiting en `/chat`~~ | cerrado en T4.6 |
| ~~`GET /leads` expone datos personales~~ | cerrado: token, y 503 si no se configura |
| El limitador usa la IP del socket e ignora `X-Forwarded-For` | detrás de un proxy inverso todos los visitantes comparten un cubo; hay que limitar en el proxy o resolver allí la IP real. Documentado en el README |
| Un solo proceso, límite en memoria | con dos réplicas el tope se aplica por réplica. Para lo que protege, sirve |
| El demo no pasa por el limitador por IP | llama a `run_turn()` directamente; en la URL pública lo tapa el tope de turnos por sesión, que es más burdo |
| Cambiar destinatarios desde la app no persiste | los secretos son de solo lectura y el disco es efímero; la pestaña lo dice y da la línea TOML para dejarlo fijo |
| Piso de relevancia sin calibrar | fase 6 |
| Una fuente que devuelve 0 fragmentos no es error | detectado en la entrada 2 del registro; sin arreglar |
| Inspiración de diseño fuera de alcance | cortada a propósito; requiere que Ronald etiquete 15-20 fotos |

---

## Pendiente de Fabián

| | |
|---|---|
| ✅ | Rotar la clave de API (2026-08-13). La nueva está en `.env` y verificada |

## Pendiente de Ronald

| | |
|---|---|
| ⬜ | **La página de Services sirve texto sobre turbinas eólicas.** Está en vivo. |
| ⬜ | Cuánto cobra por una visita lejana (que cerca no cobra ya está confirmado) |
| ⬜ | Cuánto tarda en pasar un presupuesto desde el primer contacto |
| ⬜ | Condiciones concretas de la garantía |
| ⬜ | Si instala wallpaper comprado por el cliente |
| ⬜ | Etiquetar 15-20 fotos del portafolio (opcional, revive una función) |
