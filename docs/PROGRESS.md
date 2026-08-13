# Estado del proyecto

**Actualizado:** 2026-08-13 · **Commits:** 17 · **Pruebas:** 31 en verde

Documento vivo. **Se actualiza según avanza el trabajo, no al cerrar cada
fase** — cuando una tarea se mueve, cuando aparece o se resuelve un bloqueo, y
cuando una estimación resulta equivocada. Convención registrada en
`CLAUDE.md`.

Fuente de la verdad para "qué queda": `04_plan.md` (fases) y `05_tasks.md`
(tareas). Este fichero es el estado, no el plan.

**Último movimiento:** fase 3 **completa**. Primera conversación real de
extremo a extremo ejecutada; un fallo alto encontrado y corregido en el
resumen del lead (entrada 8 del registro de revisión).

---

## Resumen

```
Especificación  ████████████████████  100%   5 documentos
Fase 0  Contexto ███████████████████  100%   T0.1–T0.4
Fase 1  Ingesta  ███████████████████  100%   T1.1–T1.7
Fase 2  Retrieval███████████████████  100%   T2.1–T2.4
Fase 3  Agente   ███████████████████  100%   T3.1–T3.6
Fase 4  Frontends░░░░░░░░░░░░░░░░░░░    0%
Fase 4.5 Entrega ░░░░░░░░░░░░░░░░░░░    0%
Fase 5  Evaluación░░░░░░░░░░░░░░░░░░    0%   ← el hito que importa
Fase 6  Mejora   ░░░░░░░░░░░░░░░░░░░    0%
Fase 7  Fallos   ░░░░░░░░░░░░░░░░░░░    0%
Fase 8  Revisión ████████░░░░░░░░░░░   40%   registro abierto, 8 entradas
Fase 9  Comunicar░░░░░░░░░░░░░░░░░░░    0%
```

**Estimado 25 h · consumido ~14 h · restante ~11 h.**
Las horas consumidas son una estimación mía a partir del plan; Fabián las
ajusta con el tiempo real para `06_effort.md`.

---

## Bloqueos

| Qué | Bloquea | Quién lo desbloquea |
|---|---|---|
| Credenciales de correo saliente | T4.5.1 (entrega del lead) | Fabián / Ronald |
| ⚠️ La clave de API se pegó en el chat y no se rotó | nada ahora; sí antes de desplegar | Fabián: rotarla en la consola |

`ANTHROPIC_API_KEY` resuelto — `.env` configurado y verificado 2026-08-12.

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

### Fases 4 a 9 — pendientes

Sin empezar. Ver `05_tasks.md` para el desglose completo.

La **fase 5 es el hito crítico**: hasta que exista un baseline commiteado, la
fase 6 no tiene contra qué medir y la fase 7 es especulación. Si el tiempo
aprieta, el recorte sale de la fase 4, nunca de la 5, 6 o 7.

### Fase 8 — Revisión del output de IA · registro abierto

8 entradas en `ai_review_log.md`, escritas cuando ocurrieron. Las que importan
son la 2 (el filtro de ruido vaciaba el corpus y el build reportaba éxito) y la
8 (el resumen para Ronald narraba una corrección que nunca ocurrió).

---

## Cobertura del checklist de entrega

Es la medida real de "cuánto falta", porque es lo que se califica.

| | Casilla | Dónde |
|:--:|---|---|
| ✅ | Problem statement: dominio, usuario, problema, éxito | `01` |
| ✅ | Por qué merece resolverse, en términos del cliente | `01` |
| ✅ | Data provenance: origen, límites, datos sensibles | `02` |
| ✅ | Prototipo funcionando de extremo a extremo | T3.6 ejecutada, lead capturado |
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
| Sin rate limiting en `/chat` | T4.6, requisito antes de desplegar |
| `GET /leads` expone datos personales | quitar o autenticar antes de producción |
| Piso de relevancia sin calibrar | fase 6 |
| Una fuente que devuelve 0 fragmentos no es error | detectado en la entrada 2 del registro; sin arreglar |
| Inspiración de diseño fuera de alcance | cortada a propósito; requiere que Ronald etiquete 15-20 fotos |

---

## Pendiente de Fabián

| | |
|---|---|
| ⬜ | Rotar la clave de API: se pegó en el chat y sigue activa |
| ⬜ | Credenciales de correo saliente para la entrega de leads (T4.5.1) |

## Pendiente de Ronald

| | |
|---|---|
| ⬜ | **La página de Services sirve texto sobre turbinas eólicas.** Está en vivo. |
| ⬜ | Cuánto cobra por una visita lejana (que cerca no cobra ya está confirmado) |
| ⬜ | Cuánto tarda en pasar un presupuesto desde el primer contacto |
| ⬜ | Condiciones concretas de la garantía |
| ⬜ | Si instala wallpaper comprado por el cliente |
| ⬜ | Etiquetar 15-20 fotos del portafolio (opcional, revive una función) |
