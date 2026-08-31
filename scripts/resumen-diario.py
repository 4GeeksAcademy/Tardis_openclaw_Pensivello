#!/usr/bin/env python3
"""Resumen diario - Tardis para Miguel
Se ejecuta a las 7:00 AM (UTC-4 / Caracas)
"""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta

CARACAS = timezone(timedelta(hours=-4))
now = datetime.now(CARACAS)
fecha = now.strftime('%A %d de %B de %Y')
fecha_iso = now.strftime('%Y-%m-%d')

def mcporter_call(tool, **kwargs):
    """Llama un tool mcporter con kwargs."""
    cmd = ['npx', '-y', 'mcporter', 'call', 'zapier.' + tool]
    for k, v in kwargs.items():
        if isinstance(v, bool):
            cmd.append(f'{k}:{"true" if v else "false"}')
        elif isinstance(v, (int, float)):
            cmd.append(f'{k}:{v}')
        elif isinstance(v, (dict, list)):
            cmd.append(f'{k}:{json.dumps(v)}')
        else:
            cmd.append(f'{k}:{v}')
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    stdout = r.stdout.strip()
    if r.returncode != 0:
        raise RuntimeError(r.stderr[:200] if r.stderr else stdout[:200])
    if stdout:
        try:
            parsed = json.loads(stdout)
            if parsed.get('isError'):
                raise RuntimeError(parsed.get('error', 'Error'))
            return parsed
        except json.JSONDecodeError:
            pass
    return {}

def main():
    errores = []

    # 1. Calendario
    evts = []
    try:
        cal = mcporter_call('execute_zapier_read_action',
            selected_api='GoogleCalendarCLIAPI',
            action='event_v2',
            tool_name='google_calendar_find_events',
            params={
                'calendarid': 'miguel.eduardo2401@gmail.com',
                'start_time': f'{fecha_iso}T00:00:00-04:00',
                'end_time': f'{fecha_iso}T23:59:59-04:00',
                'ordering': 'startTime',
                'expand_recurring': 'true'
            })
        evts = cal.get('results', [])
    except Exception as e:
        errores.append(f"Calendario: {e}")

    # 2. Drive
    files = []
    try:
        drv = mcporter_call('execute_zapier_write_action',
            selected_api='GoogleDriveCLIAPI',
            action='ae_42227_google_drive_retrieve_files_from_google_d',
            tool_name='google_drive_retrieve_files_from_google_drive',
            params={
                'pageSize': 5,
                'orderBy': 'modifiedTime desc',
                'spaces': 'drive'
            })
        files = drv.get('results', [{}])[0].get('files', [])
    except Exception as e:
        errores.append(f"Drive: {e}")

    # 3. Mensaje en HTML (Telegram soporta HTML mejor que Markdown)
    msg = f"📋 <b>Resumen Diario — {fecha}</b>\n\n"

    if evts:
        msg += "📅 <b>Calendario:</b>\n"
        for e in evts[:10]:
            start = e.get('start', {}).get('dateTime', e.get('start', {}).get('date', '?'))
            summary = e.get('summary', 'Sin título')
            msg += f"  • {start} — {summary}\n"
    else:
        msg += "📅 Calendario: Sin eventos para hoy 🎉\n"

    msg += "\n"

    if files:
        msg += "📁 <b>Drive — Últimos archivos:</b>\n"
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
        msg += "📁 Drive: Sin archivos recientes\n"

    if errores:
        msg += f"\n⚠️ <b>Advertencias:</b>\n"
        for e in errores:
            msg += f"  • {e}\n"

    # 4. Enviar
    mcporter_call('execute_zapier_write_action',
        selected_api='TelegramCLIAPI',
        action='send_message',
        tool_name='telegram_send_message',
        params={
            'chat_id': '1382253586',
            'text': msg,
            'format': 'html'
        })
    print(f"✅ Resumen enviado a Telegram ({fecha})")

if __name__ == '__main__':
    main()