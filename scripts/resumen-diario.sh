#!/bin/bash
# Resumen diario - Tardis para Miguel
# Se ejecuta a las 7:00 AM (UTC-4 / Caracas)

WORKSPACE="/root/.openclaw/workspace"
cd "$WORKSPACE"

# Fecha en formato Caracas
FECHA=$(TZ="America/Caracas" date '+%A %d de %B de %Y')
FECHA_ISO=$(TZ="America/Caracas" date '+%Y-%m-%d')

# 1. Obtener eventos del calendario de hoy
CALENDAR_JSON=$(npx -y mcporter call zapier.execute_zapier_read_action selected_api:"GoogleCalendarCLIAPI" action:"event_v2" tool_name:"google_calendar_find_events" params:"{\"calendarid\":\"miguel.eduardo2401@gmail.com\",\"start_time\":\"${FECHA_ISO}T00:00:00-04:00\",\"end_time\":\"${FECHA_ISO}T23:59:59-04:00\",\"ordering\":\"startTime\",\"expand_recurring\":\"true\"}" 2>/dev/null)

# 2. Obtener archivos recientes de Drive
DRIVE_JSON=$(npx -y mcporter call zapier.execute_zapier_write_action selected_api:"GoogleDriveCLIAPI" action:"ae_42227_google_drive_retrieve_files_from_google_d" tool_name:"google_drive_retrieve_files_from_google_drive" params:'{"pageSize":5,"orderBy":"modifiedTime desc","spaces":"drive"}' 2>/dev/null)

# 3. Armar mensaje
MENSAJE=$(python3 <<'PYEOF'
import json, sys, os

fecha = os.environ.get('FECHA', 'hoy')
cal_json = os.environ.get('CALENDAR_JSON', '{}')
drv_json = os.environ.get('DRIVE_JSON', '{}')

msg = f"📋 *Resumen Diario — {fecha}*\n\n"

# Parte 1: Calendario
try:
    cal = json.loads(cal_json)
    evts = cal.get('results', [])
    if evts:
        msg += "📅 *Calendario:*\n"
        for e in evts[:10]:
            start = e.get('start', {}).get('dateTime', e.get('start', {}).get('date', '?'))
            summary = e.get('summary', 'Sin título')
            msg += f"  • {start} — {summary}\n"
    else:
        msg += "📅 *Calendario:* Sin eventos para hoy 🎉\n"
except:
    msg += "📅 *Calendario:* Sin datos\n"

msg += "\n"

# Parte 2: Drive
try:
    drv = json.loads(drv_json)
    files = drv.get('results', [{}])[0].get('files', [])
    if files:
        msg += "📁 *Drive — Últimos archivos:*\n"
        for f in files[:5]:
            name = f.get('name', '?')
            mime = f.get('mimeType', '')
            if 'folder' in mime: icon = '📂'
            elif 'pdf' in mime: icon = '📕'
            elif 'image' in mime: icon = '🖼️'
            elif 'spreadsheet' in mime: icon = '📊'
            elif 'presentation' in mime: icon = '📽️'
            else: icon = '📄'
            msg += f"  {icon} {name}\n"
    else:
        msg += "📁 *Drive:* Sin archivos recientes\n"
except:
    msg += "📁 *Drive:* Sin datos\n"

print(msg)
PYEOF
)

# Exportar las variables para python
export FECHA="$FECHA"
export CALENDAR_JSON="$CALENDAR_JSON"
export DRIVE_JSON="$DRIVE_JSON"

# 4. Enviar por Telegram
MESSAGE_TEXT=$(python3 <<'PYEOF'
import json, os

fecha = os.environ.get('FECHA', 'hoy')
cal_json = os.environ.get('CALENDAR_JSON', '{}')
drv_json = os.environ.get('DRIVE_JSON', '{}')

msg = f"📋 *Resumen Diario — {fecha}*\n\n"

# Calendario
try:
    cal = json.loads(cal_json)
    evts = cal.get('results', [])
    if evts:
        msg += "📅 *Calendario:*\n"
        for e in evts[:10]:
            start = e.get('start', {}).get('dateTime', e.get('start', {}).get('date', '?'))
            summary = e.get('summary', 'Sin título')
            msg += f"  • {start} — {summary}\n"
    else:
        msg += "📅 *Calendario:* Sin eventos para hoy 🎉\n"
except:
    msg += "📅 *Calendario:* Sin datos\n"

msg += "\n"

# Drive
try:
    drv = json.loads(drv_json)
    files = drv.get('results', [{}])[0].get('files', [])
    if files:
        msg += "📁 *Drive — Últimos archivos:*\n"
        for f in files[:5]:
            name = f.get('name', '?')
            mime = f.get('mimeType', '')
            if 'folder' in mime: icon = '📂'
            elif 'pdf' in mime: icon = '📕'
            elif 'image' in mime: icon = '🖼️'
            elif 'spreadsheet' in mime: icon = '📊'
            elif 'presentation' in mime: icon = '📽️'
            else: icon = '📄'
            msg += f"  {icon} {name}\n"
    else:
        msg += "📁 *Drive:* Sin archivos recientes\n"
except:
    msg += "📁 *Drive:* Sin datos\n"

print(msg)
PYEOF
)

# Escapar para JSON
MESSAGE_JSON=$(python3 -c "
import json, os
print(json.dumps(os.environ['MESSAGE_TEXT']))
")

npx -y mcporter call zapier.execute_zapier_write_action selected_api:"TelegramCLIAPI" action:"send_message" tool_name:"telegram_send_message" params:"{\"chat_id\":\"1382253586\",\"text\":$MESSAGE_JSON,\"format\":\"markdown\"}" 2>/dev/null