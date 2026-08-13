# Estado del proyecto

**Actualizado:** 2026-08-13 · **Commits:** 38 · **Pruebas:** 56 en verde

Documento vivo. **Se actualiza según avanza el trabajo, no al cerrar cada
fase** — cuando una tarea se mueve, cuando aparece o se resuelve un bloqueo, y
cuando una estimación resulta equivocada. Convención registrada en
`CLAUDE.md`.

Fuente de la verdad para "qué queda": `04_plan.md` (fases) y `05_tasks.md`
(tareas). Este fichero es el estado, no el plan.

**Último movimiento:** `Q-02` arreglado y medido (2026-08-13) — el lead que se
perdía en 2 de 7 muestras ahora se registra en 6 de 6, y el asistente registra
**antes** de seguir preguntando. Con eso, **las nueve fases cerradas, las 13
casillas del checklist y el último fallo abierto que dependía de nosotros.**

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
Fase 5  Evaluación███████████████████  100%   baseline commiteado
Fase 6  Mejora   ███████████████████  100%   3 experimentos, 6 corridas
Fase 7  Fallos   ███████████████████  100%   6 nombrados, 2 arreglados
Fase 8  Revisión ███████████████████  100%   14 entradas, cerrado
Fase 9  Comunicar███████████████████  100%   slide, demo y horas
```

**Estimado 25 h · real ~16 h medidas sobre el historial de git.**
Desglose por fase, qué se cortó y el gasto de API: `06_effort.md`.

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
- Árbol de git limpio, 38 commits
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

**Las nueve fases están cerradas y las 13 casillas del checklist también.**
Lo que queda no es entrega, es producto:

1. **Las cinco respuestas de Ronald** (seis con la nueva pregunta 7). Cada una convierte una derivación en
   una respuesta real y no cuesta ni una línea de código.
2. **Antes de publicarlo en su web:** IP real detrás del proxy,
   `ALLOWED_ORIGINS` al dominio y `LEAD_EMAIL_TO` a su correo.
3. **Los dos fallos que quedan abiertos con su razón** (`A-02` y el "no
   hacemos suelos"), uno de los cuales se destraba con la respuesta de Ronald.

### Hilos abiertos que no están en ninguna tarea

- El piso de relevancia en 0.62 falla en tres casos ya observados: deriva
  *"do you work in Boston?"* y *"where are you based?"* aunque la respuesta
  existe en nivel A, y en la prueba de humo no derivaba *"can you install
  flooring for me?"* —esto último ya lo resuelve el inventario del prompt—.
  El barrido de la fase 6 va en pasos de 0.02, no de 0.1.
- La regresión de la entrada 8 (resumen que narra una corrección que nunca
  ocurrió) apareció 1 vez en 33 leads. La regla del prompt sigue puesta y
  aguanta casi siempre; ahora tiene 33 muestras detrás en vez de una.
  `07_failure_analysis.md` §F5.
- ~~`Q-02` pierde el lead~~ — arreglado y medido: 6 de 6 muestras limpias y,
  lo que sostiene la afirmación, el asistente registra y **luego** pregunta en
  las seis. §F2 y entrada 14 del registro.
- `LEAD_EMAIL_TO` apunta al correo de Fabián, no al de Ronald. Cambiarlo solo
  cuando esto deje de ser una prueba.
- La latencia por turno (4–10 s en la demo grabada) es mucho tiempo mirando
  una pantalla quieta en una web. El contrato de §5 responde de una pieza, sin
  streaming; el streaming está cortado a propósito y el corte está declarado
  en `06_effort.md`. Si se decide añadirlo, el contrato es aditivo y no rompe
  a nadie.

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

### Fase 5 — Evaluación · completa

| | Tarea | Resultado |
|:--:|---|---|
| ✅ | T5.1 `eval/questions.yaml` | 30 casos, reparto 8/8/4/5/5 exacto al de `02` §2.2, con A1–A5 |
| ✅ | T5.2 `eval/run.py` | JSON completo + hoja CSV para etiquetar a mano |
| ✅ | T5.3 Etiquetado contra S1–S4 | rubro en `eval/rubric.md`, escrito antes de leer resultados |
| ✅ | T5.4 Baseline commiteado **antes** de tocar nada | `evidence/baseline_results.md` |

**El baseline: S1 80% (falla, objetivo 90) · S2 0 violaciones (pasa, y es la
puerta dura) · S3 100% · S4 80%, justo en la línea.**

Los seis fallos de S1 son respuestas **correctas** que no se pueden rastrear a
un pasaje recuperado: cuatro salen del inventario de servicios que vive en el
prompt, y dos de que el piso de 0.62 tapa un documento que sí existe. Y S4 cae
por la regresión de la entrada 8: el resumen de `Q-05` narra una corrección que
nunca ocurrió, en español, en una conversación en inglés.

Las cinco conversaciones de calificación son multiturno: 30 casos son 40
llamadas al modelo. Durante la corrida los leads van a `eval/results/` y el
envío por correo se apaga — lo que se mide es el asistente, no el SMTP, y sin
eso cada corrida serían cinco correos.

### Fase 6 — Mejora medida · completa

| | Tarea | Resultado |
|:--:|---|---|
| ✅ | T6.1 Barrido del piso | `eval/sweep.py`, solo recuperación, sin gastar modelo |
| ✅ | T6.2 S1 contra S2 en tres experimentos | 6 corridas, 2 muestras por configuración |
| ✅ | T6.3 Piso elegido: **se queda en 0.62** | justificado contra S2, no contra la media |
| ✅ | T6.4 `evidence/measured_improvement.md` | con lo que empeoró y lo que no se movió |

**Lo medido, en una línea: ninguna de las tres intervenciones movió S1 más de
lo que se mueve solo entre dos corridas idénticas.** Esa es la conclusión, y
está escrita como tal.

Lo que sí cambió con la recuperación determinista (experimento 3, el que se
queda): los tokens de entrada bajan de 64.179 a ~41.000 —un tercio menos, que
lo paga Ronald— y los casos que fallan **dejan de cambiar entre corridas**. Con
el modelo decidiendo si buscaba, dos corridas de la misma configuración
discrepaban en cinco casos; ahora fallan los mismos cinco, con dos causas
nombradas, y ambas son del corpus. Eso es lo que hace posible la fase 7.

**Experimento 1 — bajar el piso de 0.62 a 0.58.** S1 80% → 83,3% (un caso),
S2 0 violaciones, S3 100%. La diferencia está dentro del ruido declarado en
`02` §2.3. Lo que el barrido enseñó es más útil que el resultado: justo debajo
del piso esperan un ensayo decorativo (0.602 para *"where are you based?"*,
por encima del documento que sí tiene la dirección, a 0.559) y prosa de
marketing (0.597 en la pregunta de suelos). Bajar el piso compra un caso y
mete el material que empuja al sí accidental.

**El diagnóstico del baseline estaba a medias.** Con las consultas del agente
ya registradas se ve que en A-02, A-06, F-03, F-04 y X-A5 **el agente no buscó
nada**: no era el piso, era que el prompt ya contenía la respuesta. Ningún
valor del piso arregla eso.

### Fase 7 — Análisis de fallos · completa

| | Tarea | Resultado |
|:--:|---|---|
| ✅ | T7.1 A1–A5 con entrada, salida y causa | los cinco aguantaron; ninguno falló donde yo apuntaba |
| ✅ | T7.2 Recoger todo lo que soltaron las fases 5 y 6 | 6 fallos nombrados |
| ✅ | T7.3 Arreglar uno y medirlo | resúmenes en español: **45% → 0** en 15 muestras |
| ✅ | T7.4 `07_failure_analysis.md` | 6 fallos, 2 sin arreglar con su razón |

**El arreglo:** el campo `resumen` del esquema de `registrar_lead` decía *"in
the conversation's language"*. El resumen tiene un solo lector, siempre el
mismo. Ahora dice inglés siempre.

**Dos sin arreglar a propósito.** `A-02` no se arregla bajando el piso porque
el ranking está invertido —un ensayo del blog a 0.602 por encima del documento
con la dirección a 0.559— y las tres salidas posibles son peores que el fallo.
Y el "no hacemos suelos" no se puede hacer auditable sin escribir en el corpus
un hecho que Ronald **no ha confirmado**: que la lista de servicios es
exhaustiva. Eso es ahora la pregunta 7 de `client_questions_ronald.md`.

### Fases 8 y 9 — pendientes

Sin empezar. Ver `05_tasks.md` para el desglose completo.

La **fase 5 es el hito crítico**: hasta que exista un baseline commiteado, la
fase 6 no tiene contra qué medir y la fase 7 es especulación. Si el tiempo
aprieta, el recorte sale de la fase 4, nunca de la 5, 6 o 7.

### Fase 8 — Revisión del output de IA · registro abierto

11 entradas en `ai_review_log.md`, escritas cuando ocurrieron. Las que importan
son la 2 (el filtro de ruido vaciaba el corpus y el build reportaba éxito), la
8 (el resumen para Ronald narraba una corrección que nunca ocurrió) y la 9 con
la 10, que son el mismo fallo de método: comprobar el demo con algo que no
puede ver la capa donde vive el error. La 10 se cerró con `AppTest`, que
ejecuta el script con sesión real, y dejó tres pruebas de regresión.

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
| ✅ | Revisión del output de IA + un error cazado | 11 entradas; las 2, 8, 9 y 10 son errores cazados y corregidos |
| ✅ | Análisis de fallos con inputs concretos | `07_failure_analysis.md`, 6 fallos |
| ✅ | Una mejora medida, con lo que empeoró | `measured_improvement.md` |
| ✅ | Slide para el cliente | `08_client_slide.md` |
| ✅ | Demo con un caso que falla | `evidence/demo_transcript.md`, `Q-02` |
| ✅ | Declaración de horas y qué se cortó | `06_effort.md` |

**13 de 13 completas.**

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
| ⬜ | **¿La lista de servicios está completa?** Pregunta 7, nueva: sin su respuesta el "no hacemos suelos" no se puede hacer auditable (F4) |
