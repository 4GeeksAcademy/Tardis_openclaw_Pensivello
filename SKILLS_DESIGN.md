# SKILLS_DESIGN

Diseños y bocetos de skills para Tardis.

---

## 1. Resumen Matutino

**Trigger:** Cron — 7:00 AM (UTC-4 / Caracas)

### Flujo
1. Leer eventos del calendario de hoy (Google Calendar)
2. Leer últimos 5 archivos modificados en Drive
3. Armar mensaje en HTML
4. Enviar a Telegram @Pensivello

### Apps involucradas
- 📅 GoogleCalendarCLIAPI → `event_v2` (find_events)
- 📁 GoogleDriveCLIAPI → `ae_42227_google_drive_retrieve_files_from_google_d`
- 💬 TelegramCLIAPI → `send_message`

### Fixed values
- Chat ID: `1382253586` (@Pensivello)
- Calendar ID: `miguel.eduardo2401@gmail.com`
- Formato: HTML (más permisivo que Markdown)

### Script
`scripts/resumen-diario.py`

---

## 2. Planificación Nocturna

**Trigger:** Cron — 7:30 PM (UTC-4 / Caracas)

### Flujo
1. Preguntar por Telegram: "¿qué tenemos pendiente para mañana?"
2. Esperar respuesta (polling 30s × 10 intentos ≈ 5 min)
3. Parsear respuesta → detectar tareas con/sin hora
4. Quick Add Event en Calendar para cada tarea con hora
5. Confirmar "LISTO" con resumen

### Apps involucradas
- 💬 TelegramCLIAPI → `send_message` (preguntar + confirmar)
- 💬 TelegramCLIAPI → `code_action_telegramcliapi__read_latest_message` (leer respuesta)
- 📅 GoogleCalendarCLIAPI → `event` (quick_add_event)

### Code actions creadas
- `telegramcliapi__read_latest_message` — lee el último mensaje de un chat_id específico

### Fixed values
- Chat ID: `1382253586`
- Calendar ID: `miguel.eduardo2401@gmail.com`
- Zona horaria: America/Caracas (UTC-4)
- Formato: HTML

### Parsing de respuesta
Los eventos con hora se detectan mediante regex:
- `"a las 10"` → agendar a las 10:00
- `"a las 10:30"` → agendar a las 10:30
- `"reunión 10am"` → agendar a las 10:00
- `"estudiar 3pm"` → agendar a las 15:00
- Sin hora → listar como pendiente sin agendar

### Script
`scripts/recordatorio-nocturno.py`

---

## 3. Google Drive — Carpeta DOCs_Tardis

**Configuración permanente**
- Carpeta creada: `DOCs_Tardis` en la raíz del Drive
- ID: `15vHPvNYp_cQODFkA1cpj4kPrU-uTXeji`
- Todos los Google Docs que cree Tardis se guardan aquí
- Al crear docs vía API, usar `folder: "15vHPvNYp_cQODFkA1cpj4kPrU-uTXeji"`

---

## 4. Resumen de Correos

**Trigger:** Cron — 8:00 PM (UTC-4 / Caracas)

### Flujo
1. Buscar correos no leídos de hoy en Gmail (`is:unread after:{fecha}`)
2. Armar resumen: remitente, asunto, snippet (máx 10 correos)
3. Enviar por Telegram en HTML

### Apps involucradas
- 📧 GoogleMailV2CLIAPI → `message` (gmail_find_email)
- 💬 TelegramCLIAPI → `send_message`

### Fixed values
- Chat ID: `1382253586` (@Pensivello)
- Zona horaria: America/Caracas (UTC-4)
- Formato: HTML
- Query: `is:unread after:YYYY-MM-DD` (fecha del día)
- Máximo 10 correos en el resumen

### Script
`scripts/resumen-correos.py`

---

## Cron del sistema

```
0 11 * * *  → scripts/resumen-diario.py       (7:00 AM Caracas)
30 23 * * * → scripts/recordatorio-nocturno.py  (7:30 PM Caracas)
0 0 * * *  → scripts/resumen-correos.py        (8:00 PM Caracas)
```

## Skills guardados en Zapier
- `resumen matutino`
- `planificacion nocturna`
- `resumen correos`

## Apps conectadas (5)
- 📅 Google Calendar
- 📁 Google Drive
- 📝 Google Docs
- 💬 Telegram
- 📧 Gmail