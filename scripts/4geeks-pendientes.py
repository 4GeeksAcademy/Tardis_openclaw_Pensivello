#!/usr/bin/env python3
"""Resumen de pendientes en 4Geeks Academy - Tardis para Miguel
Se ejecuta a las 9:00 AM (UTC-4 / Caracas)
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta

CARACAS = timezone(timedelta(hours=-4))
now = datetime.now(CARACAS)
fecha = now.strftime('%A %d de %B')

TOKEN = os.environ.get('BREATHECODE_TOKEN', '').strip()
if not TOKEN:
    print('❌ BREATHECODE_TOKEN no configurado', file=sys.stderr)
    sys.exit(1)
BASE = "https://breathecode.herokuapp.com"

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

def api_get(endpoint):
    """Consulta la API de breathecode."""
    cmd = ['curl', '-s', f'{BASE}{endpoint}',
           '-H', f'Authorization: Token {TOKEN}',
           '-H', 'Accept: application/json']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        raise RuntimeError(f"curl failed: {r.stderr[:200]}")
    return json.loads(r.stdout)

def main():
    errores = []

    try:
        data = api_get('/v1/admissions/user/me')
    except Exception as e:
        errores.append(f"API: {e}")
        data = {}

    cohorts = data.get('cohorts', [])

    # Buscar el cohort del bootcamp principal (latam-aie-pt-3)
    bootcamp = None
    otros_activos = []
    completados = []

    for c in cohorts:
        cohort = c.get('cohort', {})
        slug = cohort.get('slug', '')
        name = cohort.get('name', slug)
        stage = cohort.get('stage', '')
        completion = c.get('completion', {})
        required = completion.get('required', {}).get('PROJECT', {})
        missing = required.get('missing', [])
        completed_count = required.get('completed', 0)
        total = required.get('total', 0)
        overall_percent = completion.get('overall', {}).get('percent', 0)

        if slug == 'latam-aie-pt-3':
            bootcamp = {
                'name': name,
                'slug': slug,
                'stage': stage,
                'current_day': cohort.get('current_day', 0),
                'total_days': cohort.get('syllabus_version', {}).get('duration_in_days', '?'),
                'missing': missing,
                'completed': total - len(missing),
                'total': total,
                'percent': overall_percent
            }
        elif stage == 'STARTED' or (missing and stage != 'INACTIVE'):
            # Cohorts activos con pendientes
            otros_activos.append({
                'name': name,
                'slug': slug,
                'stage': stage,
                'missing': missing,
                'completed': total - len(missing),
                'total': total,
                'percent': overall_percent
            })
        elif completion.get('is_complete'):
            completados.append(name)

    # Armar mensaje
    msg = f"🎓 <b>4Geeks — Pendientes</b>\n      {fecha}\n\n"

    # Bootcamp principal
    if bootcamp:
        bc = bootcamp
        if bc['stage'] == 'STARTED':
            msg += f"📚 <b>Bootcamp: {bc['name']}</b>\n"
            msg += f"   Día {bc['current_day']} de {bc['total_days']}\n"
        else:
            msg += f"📚 <b>{bc['name']}</b> ({bc['stage']})\n"

        if bc['missing']:
            msg += f"\n⚠️  <b>{len(bc['missing'])} proyectos pendientes:</b>\n"
            for i, p in enumerate(bc['missing'], 1):
                # Limpiar nombre: reemplazar guiones por espacios, capitalizar
                pretty = p.replace('ai-eng-', '').replace('-milestone-', ': ').replace('-', ' ').strip().title()
                msg += f"  {i}. {pretty}\n"
            msg += f"\n   ✅ {bc['completed']}/{bc['total']} completados ({bc['percent']}%)\n"
        else:
            msg += f"\n🎉 ¡Sin proyectos pendientes! ({bc['completed']}/{bc['total']})\n"
    else:
        msg += "No se encontró el bootcamp principal\n"

    # Otros cohorts con pendientes
    if otros_activos:
        msg += f"\n📋 <b>Otros módulos con pendientes:</b>\n"
        for oc in otros_activos:
            if oc['missing']:
                msg += f"   • {oc['name']}: {len(oc['missing'])} pendiente(s)\n"

    # Completados recientes
    if completados:
        msg += f"\n✅ <b>Completados:</b>\n"
        for name in completados:
            msg += f"   ✔️ {name}\n"

    if errores:
        msg += f"\n⚠️ <b>Advertencias:</b>\n"
        for e in errores:
            msg += f"  • {e}\n"

    # Enviar a Telegram
    try:
        mcporter_call('execute_zapier_write_action',
            selected_api='TelegramCLIAPI',
            action='send_message',
            tool_name='telegram_send_message',
            params={
                'chat_id': '1382253586',
                'text': msg,
                'format': 'html'
            })
        print(f"✅ Pendientes enviados a Telegram")
    except Exception as e:
        print(f"❌ Error al enviar: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()