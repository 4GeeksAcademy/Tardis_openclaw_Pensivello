#!/usr/bin/env python3
"""Recordatorio nocturno - Tardis para Miguel
Se ejecuta a las 7:30 PM (UTC-4 / Caracas)
Pregunta → espera respuesta → agenda → confirma
"""

import json
import subprocess
import sys
import re
import time
from datetime import datetime, timezone, timedelta

CARACAS = timezone(timedelta(hours=-4))
now = datetime.now(CARACAS)
fecha = now.strftime('%A %d de %B de %Y')
manana = now + timedelta(days=1)
manana_fmt = manana.strftime('%d/%m')
manana_iso = manana.strftime('%Y-%m-%d')

CHAT_ID = '1382253586'

def mcporter_call(tool, **kwargs):
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
    if r.returncode != 0:
        raise RuntimeError(r.stderr[:200] if r.stderr else 'error')
    if r.stdout.strip():
        parsed = json.loads(r.stdout)
        if parsed.get('isError'):
            raise RuntimeError(parsed.get('error', 'Error'))
        return parsed
    return {}

def send_telegram(text):
    mcporter_call('execute_zapier_write_action',
        selected_api='TelegramCLIAPI',
        action='send_message',
        tool_name='telegram_send_message',
        params={'chat_id': CHAT_ID, 'text': text, 'format': 'html'})

def read_latest_message():
    try:
        r = mcporter_call('execute_zapier_write_action',
            selected_api='TelegramCLIAPI',
            action='code_action_telegramcliapi__read_latest_message',
            tool_name='telegram_read_latest_message',
            params={'chat_id': CHAT_ID, 'limit': '1'})
        results = r.get('results', [{}])
        if results:
            return results[0].get('text', '').strip()
        return ''
    except:
        return ''

def parse_events(text):
    """Extrae items con/sin hora."""
    lines = text.strip().split('\n')
    items = []

    # Patrones de hora: "a las 10", "a las 10:30", "10am", "3pm"
    time_pattern = r'(?:a\s+las\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?'

    for line in lines:
        raw = line.strip()
        if not raw:
            continue
        # Limpiar bullets
        clean = re.sub(r'^[\s\-•*]+', '', raw).strip()

        match = re.search(time_pattern, clean, re.IGNORECASE)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            ampm = match.group(3).lower() if match.group(3) else None

            if ampm == 'pm' and hour < 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            elif not ampm and hour < 7:
                hour += 12

            # Título sin la hora
            title = re.sub(time_pattern, '', clean, flags=re.IGNORECASE).strip(' ,-•*').strip()

            items.append({
                'title': title or clean,
                'hour': hour,
                'minute': minute,
                'has_time': True
            })
        else:
            items.append({
                'title': clean,
                'hour': None,
                'minute': None,
                'has_time': False
            })

    return items

def main():
    # 1. Preguntar
    msg = (
        f"🤖 <b>Planificación nocturna — {fecha}</b>\n\n"
        f"Miguel, ¿qué tenemos pendiente para mañana ({manana_fmt})?\n\n"
        f"Dime las cosas — si tienen hora las agendo en tu calendario. "
        f"Ej: \"Reunión a las 10am, comprar víveres, estudiar a las 3pm\""
    )
    send_telegram(msg)
    print(f"✅ Pregunta enviada")

    # 2. Esperar respuesta (polling 30s x 10 intentos = ~5 min)
    time.sleep(30)
    respuesta = ''
    for i in range(10):
        respuesta = read_latest_message()
        if respuesta and len(respuesta) > 3:
            print(f"Respuesta recibida: {respuesta[:80]}...")
            break
        if i < 9:
            print(f"Esperando... ({i+1}/10)")
            time.sleep(30)

    if not respuesta or len(respuesta) <= 3:
        send_telegram("⏰ No recibí respuesta. Pregúntame cuando quieras planificar.")
        return

    # 3. Parsear
    eventos = parse_events(respuesta)
    if not eventos:
        send_telegram("No entendí bien. Intenta: 'tarea a las 10am' o solo 'tarea'")
        return

    # 4. Agendar
    agendados = []
    sin_hora = []

    for ev in eventos:
        if ev['has_time']:
            # Quick Add Event parsea lenguaje natural
            desc = f"{ev['title']} {manana_iso}T{ev['hour']:02d}:{ev['minute']:02d}"
            try:
                mcporter_call('execute_zapier_write_action',
                    selected_api='GoogleCalendarCLIAPI',
                    action='event',
                    tool_name='google_calendar_quick_add_event',
                    params={
                        'calendarid': 'miguel.eduardo2401@gmail.com',
                        'text': desc
                    })
                agendados.append(ev['title'])
            except Exception as e:
                print(f"Error agendando '{ev['title']}': {e}")
                sin_hora.append(f"{ev['title']} (error al agendar)")
        else:
            sin_hora.append(ev['title'])

    # 5. Confirmar
    resumen = "✅ <b>LISTO</b>\n\n"
    if agendados:
        resumen += "📅 <b>Agendado en calendario:</b>\n"
        for a in agendados:
            resumen += f"  • {a}\n"
        resumen += "\n"
    if sin_hora:
        resumen += "📋 <b>Sin agendar:</b>\n"
        for s in sin_hora:
            resumen += f"  • {s}\n"

    send_telegram(resumen)
    print("✅ Confirmación enviada")

if __name__ == '__main__':
    main()