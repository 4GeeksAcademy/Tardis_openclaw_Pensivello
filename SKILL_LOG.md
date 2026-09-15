# Skills — Tardis para Miguel

Estructura: 4 core + 2 extras. Cada skill documenta su prompt inicial, endpoint/API usado y evidencia de prueba.

---

## ⭐ Core 1 — Conexión Zapier MCP + Telegram

### Prompt inicial
*"Conecta Tardis a Miguel's cuenta de Zapier y configura Telegram como canal de salida."*

### Endpoints / APIs
- **Zapier MCP** vía `mcporter call zapier.<action>`:
  - `execute_zapier_write_action` (Telegram send_message)
  - `execute_zapier_read_action` (Calendar, Drive)
- **Telegram API** (a través de Zapier): bot `@MelameTARDIS_bot`

### Archivos
- `TOOLS.md` — credenciales y config
- `AGENTS.md` — reglas de grupo/telegram

### Configuración
```bash
npm install -g mcporter
mcporter auth zapier  # OAuth con cuenta miguel.eduardo2401@gmail.com
```

### Evidencia de prueba
✅ Telegram send_message probado desde mcporter al chat `1382253586` (@Pensivello).  
✅ Código de acción `telegramcliapi__read_latest_message` creado en Zapier.  
✅ Formato confirmado: usar `text` plano (ni HTML ni Markdown) con `ensure_ascii=True` en json.dumps.

---

## ⭐ Core 2 — Resumen Diario (Calendar + Drive → Telegram)

### Prompt inicial
*"Cada mañana a las 7 AM, consulta el calendario de Google y los archivos recientes de Drive, y envía un resumen a Telegram."*

### Endpoints / APIs
- **Google Calendar API** vía Zapier: `google_calendar_find_events`
  - Endpoint: `event_v2` con `calendarid=miguel.eduardo2401@gmail.com`
- **Google Drive API** vía Zapier: `google_drive_retrieve_files_from_google_drive`
  - Parámetros: `pageSize=5`, `orderBy=modifiedTime desc`

### Archivo
- `scripts/resumen-diario.py`

### Cron
```
0 11 * * * cd /root/.openclaw/workspace && python3 scripts/resumen-diario.py
```
(11 UTC = 7 AM Caracas)

### Evidencia de prueba
✅ Script ejecutado manualmente, respuesta "Resumen enviado a Telegram".  
✅ Calendario devuelve eventos del día.  
✅ Drive devuelve últimos 5 archivos modificados.  
✅ Mensaje llega a Telegram en formato HTML.

---

## ⭐ Core 3 — Recordatorio Nocturno (Agenda → Telegram)

### Prompt inicial
*"A las 7:30 PM pregunta a Miguel qué quiere hacer mañana, agéndalo y confirma."*

### Endpoints / APIs
- **Google Calendar API** vía Zapier: `google_calendar_create_event`
  - Crea eventos con `summary`, `start`, `end`, `description`
- **Telegram** vía `send_message` + `read_latest_message` en ciclo de polling

### Archivo
- `scripts/recordatorio-nocturno.py`

### Cron
```
30 23 * * * cd /root/.openclaw/workspace && python3 scripts/recordatorio-nocturno.py
```
(23:30 UTC = 7:30 PM Caracas)

### Evidencia de prueba
✅ Script ejecutado manualmente.  
✅ Polling: 30s timeout × 10 intentos (5 min total).  
✅ Si el usuario responde, crea evento en calendario.  
✅ Si no responde, envía "no se pudo confirmar".

---

## ⭐ Core 4 — Resumen Correos (Gmail → Telegram)

### Prompt inicial
*"A las 8 PM revisa correos no leídos de Gmail y envía un resumen a Telegram en texto plano."*

### Endpoints / APIs
- **Gmail API** vía Zapier: `execute_zapier_read_action`
  - Parámetros: `maxResults=10`, `labelIds=["INBOX"]`, `q=is:unread`
  - Campos leídos: `from`, `subject` (top-level keys, no `payload.headers`)

### Archivo
- `scripts/resumen-correos.py`

### Cron
```
0 0 * * * cd /root/.openclaw/workspace && python3 scripts/resumen-correos.py
```
(00 UTC = 8 PM Caracas)

### Evidencia de prueba
✅ Script ejecutado manualmente, devuelve emails no leídos.  
✅ Encoding UTF-8 manejado correctamente (subprocess con `encoding='utf-8'`).  
✅ Mensaje enviado en texto plano para evitar errores de parsing con caracteres especiales.

---

## 🚀 Extra 5 — 4Geeks Pendientes (breathecode API → Telegram)

### Prompt inicial
*"Cada día a las 9 AM consulta la API de 4Geeks Academy y envía los proyectos pendientes del bootcamp a Telegram."*

### Endpoints / APIs
- **`GET /v1/admissions/user/me`** — breathecode.herokuapp.com
  - Headers: `Authorization: Token <token>`, `Accept: application/json`
  - Devuelve: datos del usuario, cohorts, progreso de proyectos
  - Campo clave: `cohorts[].completion.required.PROJECT.missing[]`

### Archivos
- `scripts/4geeks-pendientes.py`
- `.env` (permisos 600) — contiene `BREATHECODE_TOKEN`
- `.env.example` — plantilla sin credenciales

### Cron
```
0 13 * * * cd /root/.openclaw/workspace && . ./.env && python3 scripts/4geeks-pendientes.py
```
(13 UTC = 9 AM Caracas)

### Seguridad
- Token en variable de entorno, NO hardcodeado
- `.env` en `.gitignore`
- `.env.example` como template

### Evidencia de prueba
✅ Token `ac351c…5a75` autenticó correctamente en `user/me`.  
✅ Datos devueltos: user ID 21636, email migueleduardo2401@gmail.com.  
✅ Cohorts listados con pendientes (7 proyectos en bootcamp principal).  
✅ Script envió mensaje a Telegram correctamente.

---

## 🚀 Extra 6 — Telegram Code Actions + Zapier Tools

### Prompt inicial
*"Crea un mecanismo para leer el último mensaje de Telegram desde Zapier y responder automáticamente."*

### Endpoints / APIs
- **Telegram CLI API** vía Zapier:
  - `telegramcliapi__read_latest_message` (code action personalizado)
  - Parámetros: `chat_id=1382253586`
- **Zapier Code Action** (JavaScript)

### Archivos
- Referencia en `TOOLS.md` (código de acción creado en Zapier)

### Evidencia de prueba
✅ Code action `telegramcliapi__read_latest_message` creado y probado.  
✅ Lee el último mensaje del chat @Pensivello.  
✅ Integrado en recordatorio-nocturno.py para el ciclo de polling.

---

## Historial

| Fecha | Cambio |
|-------|--------|
| 2026-09-05 | Skills 1-4 iniciales (resumen diario, nocturno, correos, Telegram) |
| 2026-09-05 | Skill 5: 4Geeks Pendientes creado y probado |
| 2026-09-05 | Token movido a `.env`, `.gitignore` + `.env.example` |
| 2026-09-05 | SKILL_LOG.md reestructurado por skills (4 core + 2 extras) |