# 4Geeks Pendientes — Skill Log

## Descripción breve
Skill que cada día a las 9:00 AM Caracas consulta la API de 4Geeks Academy y envía a Telegram un resumen de los proyectos pendientes del bootcamp de Miguel.

## Archivos
- **Script:** `scripts/4geeks-pendientes.py`
- **Entorno:** `scripts/.env` (permisos 600, contiene `BREATHECODE_TOKEN`)
- **Cron:** `0 13 * * * cd /root/.openclaw/workspace && . ./.env && python3 scripts/4geeks-pendientes.py`

## Endpoints de API usados

### `GET /v1/admissions/user/me`
- **Descripción:** Devuelve datos del usuario autenticado, incluyendo todos los cohorts (bootcamp, módulos) con su progreso de proyectos.
- **Headers:** `Authorization: Token <token>` + `Accept: application/json`
- **Respuesta clave:** `cohorts[]` → cada cohort tiene `completion.required.PROJECT.missing[]` con los slugs de proyectos pendientes.

## Seguridad del token

- **El token de estudiante NO está hardcodeado en el script**. Se lee de la variable de entorno `BREATHECODE_TOKEN`.
- El valor se guarda en `/root/.openclaw/workspace/scripts/.env` con permisos `600` (solo root).
- El cron lo carga con `. ./.env` antes de ejecutar el script.
- **Token activo:** `ac351c8353b0fc7b3b347ca6f9fd3bcbcd3c5a75`
- **Academy Token (público):** `c6fe193405438832e2790dfb1d6253200fe16775` (está en el frontend de learn.4geeks.com, no es secreto)

## Dependencias
- `curl` — para llamar a la API REST
- `npx mcporter` — para enviar el mensaje a Telegram vía Zapier MCP

## Formato del mensaje (Telegram HTML)
```
🎓 4Geeks — Pendientes
      <fecha>

📚 Bootcamp: latam-aie-pt-3
   Día <N> de 72

⚠️  <N> proyectos pendientes:
  1. Nombre Proyecto
  ...

   ✅ X/Y completados (Z%)

📋 Otros módulos con pendientes:
   • Nombre Módulo: N pendiente(s)

✅ Completados:
   ✔️ Nombre Módulo
```

## Notas
- Los slugs de proyectos se formatean automáticamente a nombres legibles.
- Si la API falla (token expirado, red, etc.), el mensaje se envía igual con las advertencias visibles.
- Los tokens de breathecode (Django REST Framework) expiran o se invalidan periódicamente. Si ocurre, Miguel debe generar uno nuevo desde learn.4geeks.com y actualizar `scripts/.env`.

## Historial
- **2026-09-05:** Creación del script y cron a las 9 AM Caracas. Token movido a variable de entorno (`.env`, permisos 600).