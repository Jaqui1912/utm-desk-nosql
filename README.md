# UTM Desk NoSQL Cloud

Sistema de gestión, resolución y analítica de incidencias del campus (Equipo 6).

| Capa | Tecnología | Carpeta |
|---|---|---|
| Base de datos | MongoDB Atlas M0 | `db/` (scripts de esquema, índices y datos) |
| API REST | Python + FastAPI | `backend/` |
| Interfaz | Vue 3 + Vite | `frontend/` |
| Evidencias | Supabase Storage (URLs firmadas) | — |
| Pruebas | Postman | `backend/UTM_Desk_NoSQL_Cloud.postman_collection.json` |

## Cómo correrlo en Windows

Necesitas **Python 3.10+** y **Node.js 18+**. Usa dos terminales (PowerShell) abiertas en la carpeta del proyecto.

### 1. Variables de entorno (solo la primera vez)

```powershell
Copy-Item .env.example .env
```

Abre `.env` y pon el `MONGODB_URI` real del clúster (con usuario y contraseña de Atlas).
En Atlas, en **Network Access**, agrega tu IP (o `0.0.0.0/0` para pruebas).

### 2. Backend (terminal 1)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt

# Solo si la base está vacía o quieres reiniciarla (BORRA y vuelve a cargar los datos):
python db/script_maestro.py --yes

# Si ya tienen datos y solo falta la cuenta del profesor:
python db/crear_superadmin.py

python -m uvicorn backend.app.main:app --reload --port 8000
```

La API queda en http://127.0.0.1:8000 y la documentación en http://127.0.0.1:8000/docs.

> Si PowerShell no deja activar el entorno: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 3. Frontend (terminal 2)

```powershell
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173.

## Cuentas

| Rol | Correo | Contraseña |
|---|---|---|
| superAdmin (profesor) | lizandro.reyes@utmetropolitana.edu.mx | lizandro_2026 |
| Administrador General | l.medina@utm.example | Utm2026! |
| Técnico | c.pech@utm.example | Utm2026! |
| Directivo | r.cetina@utm.example | Utm2026! |
| Reportante | m.lopez@utm.example | Utm2026! |
| Administrador del Sistema | soporte@utm.example (entra por `/sysadmin/login`) | Utm2026! |

## Evidencias (Supabase Storage)

1. Crea un proyecto gratuito en supabase.com y un bucket **privado** llamado `evidencias`.
2. En *Project Settings → API* copia la URL y la `service_role key` en `SUPABASE_URL` y `SUPABASE_SERVICE_KEY` del `.env`.

Sin esas variables, el backend guarda los archivos en `backend/uploads/` (sirve para probar en local, no para el despliegue).

## Despliegue

- **Backend en Render:** conecta el repositorio; el archivo `render.yaml` ya trae los comandos. Captura en Render las variables `MONGODB_URI`, `SUPABASE_URL` y `SUPABASE_SERVICE_KEY`.
- **Frontend en Vercel:** importa el repositorio con *Root Directory* = `frontend` y agrega la variable `VITE_API_URL` con la URL de Render.
