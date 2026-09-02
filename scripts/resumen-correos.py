#!/usr/bin/env python3
"""Resumen de correos no leídos del día
Se ejecuta a las 8:00 PM (UTC-4 / Caracas)
"""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from email.header import decode_header

CARACAS = timezone(timedelta(hours=-4))
now = datetime.now(CARACAS)
fecha = now.strftime('%Y-%m-%d')
CHAT_ID = '1382253586'

def decode_mime(s):
    if not s:
        return ''
    try:
        parts = decode_header(s)
        result = []
        for part, charset in parts:
            if isinstance(part, bytes):
                if charset:
                    result.append(part.decode(charset, errors='replace'))
                else:
                    result.append(part.decode('utf-8', errors='replace'))
            else:
                result.append(part)
        return ''.join(result)
    except:
        return s

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
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8')
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
        params={'chat_id': CHAT_ID, 'text': text, 'format': 'plaintext'})

def main():
    errores = []
    msgs = []

    try:
        r = mcporter_call('execute_zapier_read_action',
            selected_api='GoogleMailV2CLIAPI',
            action='message',
            tool_name='gmail_find_email',
            params={'query': f'is:unread after:{fecha}'})
        msgs = r.get('results', [])
    except Exception as e:
        errores.append(f"Gmail: {e}")

    msg = f"Correos pendientes — {fecha}\n\n"

    if msgs:
        n = len(msgs)
        msg += f"{n} sin leer:\n\n"
        for i, mail in enumerate(msgs[:10], 1):
            # Los datos están en claves top-level del mail
            sender_raw = mail.get('from', '?')
            subject_raw = mail.get('subject', '?')

            sender = decode_mime(sender_raw)
            subject = decode_mime(subject_raw)

            if '<' in sender:
                sender = sender.split('<')[0].strip().strip('"\'')

            msg += f"{i}. {sender} — {subject[:60]}\n"

        if n > 10:
            msg += f"\n... y {n - 10} más"
    else:
        msg += "Sin correos nuevos"

    if errores:
        msg += "\n\nErrores:\n"
        for e in errores:
            msg += f"  - {e}\n"

    try:
        send_telegram(msg)
        print(f"Enviado ({fecha}) — {len(msgs)} correos")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()