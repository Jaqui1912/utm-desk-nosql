# UTM Desk NoSQL Cloud – Backend API & Microservicios

API REST desarrollada con **FastAPI**, **Motor** (driver asíncrono oficial de MongoDB) y **Redis**, diseñada bajo una arquitectura NoSQL documental en la nube (**MongoDB Atlas M0**) para la gestión y analítica de incidencias en el campus universitario.

---

## 🏛️ Justificación de Arquitectura y Tecnologías

| Componente | Tecnología | Justificación de Ingeniería |
|---|---|---|
| **Base de Datos NoSQL** | MongoDB Atlas M0 | Modelo polimórfico mediante `$jsonSchema` (`oneOf`) para albergar atributos dispares de las 3 ramas universitarias (`computo_redes`, `infraestructura`, `academico`) sin columnas nulas. Índices compuestos, Full-Text Search en español y TTL a 60 días. |
| **API Backend** | Python 3.11+ / FastAPI | Framework asíncrono de alto rendimiento (`uvicorn`, `asyncio`), validación estricta de esquemas con Pydantic v2 y documentación interactiva OpenAPI/Swagger automática. |
| **Autenticación & RBAC** | JWT + Bcrypt | Autenticación basada en tokens JWT portadores del rol de usuario; control de acceso basado en roles (RBAC) conforme a la Matriz de Permisos (Tabla 3). |
| **Driver de Conexión** | Motor (async Mongo) | Operaciones no bloqueantes hacia MongoDB Atlas, optimizando el *throughput* de lectura/escritura en endpoints transaccionales y agregaciones analíticas. |
| **Caché & Consecutivos** | Redis (`INCR`) | Generación atómica y libre de condiciones de carrera para los folios formales (`INC-YYYY-XXXX`) con fallback atómico en MongoDB si Redis no estuviera disponible. |
| **Pruebas de Integración** | Postman v2.1 | Suite formal de pruebas cubriendo todos los casos de uso, respuestas HTTP (200, 201, 400, 401, 403, 404), operadores atómicos y pipelines de agregación. |

---

## 📋 Mapeo de Casos de Uso, Requisitos y Operaciones NoSQL

| Req / CU | Endpoint | Método | Roles Permitidos | Operador / Motor | Descripción |
|---|---|:---:|---|---|---|
| **RF-12** | `/auth/login` | `POST` | Público | `find_one` + `bcrypt.checkpw` | Inicio de sesión y emisión de token JWT portador de rol. |
| **RF-12** | `/auth/me` | `GET` | Autenticado | Token JWT | Perfil del usuario con sesión activa. |
| **RF-14** | `/usuarios/` | `GET` | `admin_sistema` | `find` | Listado de cuentas del sistema. |
| **RF-14** | `/usuarios/` | `POST` | `admin_sistema` | `insertOne` + `bcrypt.hashpw` | Alta de usuario con rol y contraseña cifrada (201 Created). |
| **RF-14** | `/usuarios/{id}/estado` | `PATCH` | `admin_sistema` | `$set: { activo }` | Activar o desactivar cuenta de usuario. |
| **RF-13** | `/incidencias/{id}/asignar-tecnico` | `PATCH` | `admin_general` | `$set: { tecnico_asignado }` | Asignación de técnico responsable (403 para otros roles). |
| **CU-01 / RF-01** | `/incidencias/` | `POST` | `reportante`, `admin_general` | `insertOne` + `$jsonSchema` + Redis `INCR` | Alta polimórfica con folio único `INC-YYYY-XXXX` (201 Created). |
| **CU-02 / RF-05** | `/incidencias/{id}/evidencias` | `POST` | `reportante`, `tecnico`, `admin_general` | `$push` | Registro de metadatos de evidencias multimedia. |
| **CU-03 / RF-06** | `/incidencias/{id}/estado` | `PATCH` | `tecnico`, `admin_general` | `$set`, `$inc`, `$push` | Actualización atómica de estado, horas y bitácora. |
| **CU-04 / RF-07** | `/incidencias/{id}/tags` | `PATCH` | `tecnico`, `admin_general` | `$addToSet` / `$pull` | Gestión dinámica de etiquetas técnicas sin duplicados. |
| **CU-05 / RF-08** | `/incidencias/buscar` | `GET` | Todos autenticados | `$text: { $search }` + `$meta: "textScore"` | Búsqueda textual ponderada en español (reportante ve solo las suyas). |
| **CU-06 / RF-09** | `/incidencias/analitica` | `GET` | `admin_general`, `directivo` | Aggregation Pipelines 1 & 2 (`$unwind`, `$group`) | Eficiencia operativa por edificio y Top 10 fallas recurrentes. |
| **CU-07 / RF-10** | *Automático Atlas* | – | – | Índice TTL `{ fecha_resolucion: 1 }` (60 días) | Depuración y purga automática por ciclo de vida en segundo plano. |

---

## 👥 Matriz de Roles y Credenciales de Prueba

Todos los usuarios del dataset de prueba comparten la contraseña: **`Utm2026!`**

| Rol | Correo de Prueba | Permisos Destacados |
|---|---|---|
| **Administrador General** | `l.medina@utm.example` | Asignar técnicos, ver todas las incidencias, analítica directiva, modificar estado y tags. |
| **Administrador del Sistema** | `soporte@utm.example` | Crear y desactivar usuarios, asignar roles, consultar sistema. |
| **Técnico** | `c.pech@utm.example` | Actualizar estado, acumular horas, cargar evidencias y gestionar tags. |
| **Directivo** | `r.cetina@utm.example` | Acceso de solo lectura al catálogo completo y a la analítica directiva. |
| **Reportante (Docente)** | `m.lopez@utm.example` | Levantar incidencias, consultar solo sus propias incidencias y cargar evidencias. |
| **Reportante (Desactivado)** | `m.dzul@utm.example` | Usuario inactivo para validar rechazo HTTP 401 en inicio de sesión. |

---

## 🚀 Guía de Instalación y Despliegue Local

### 1. Requisitos Previos
* Python 3.10 o superior instalado.
* Clúster activo en MongoDB Atlas (Capa Gratuita M0).
* (Opcional) Servidor Redis en ejecución (puerto 6379).

### 2. Configurar Entorno Virtual y Dependencias
```powershell
# En Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### 3. Variables de Entorno (`.env`)
Copia la plantilla y configura tu URI de Atlas:
```powershell
Copy-Item .env.example .env
```
Asegúrate de que contenga:
```env
MONGODB_URI=mongodb+srv://<usuario>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=utm_desk
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=utm_desk_jwt_secret_key_2026_nosql_cloud
```

### 4. Orquestación y Poblado de Base de Datos
Ejecuta el script maestro automatizado que valida, crea colecciones, índices y puebla el dataset sintético (27 incidencias y 13 usuarios):
```powershell
python db/script_maestro.py --yes
```

### 5. Iniciar Servidor FastAPI
Desde la raíz del proyecto, ejecuta:
```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

* **API Base:** `http://127.0.0.1:8000`
* **Swagger UI (Documentación Interactiva):** `http://127.0.0.1:8000/docs`
* **ReDoc:** `http://127.0.0.1:8000/redoc`

---

## 🧪 Pruebas con Postman

1. Abre Postman y haz clic en **Import**.
2. Selecciona el archivo:
   `backend/UTM_Desk_NoSQL_Cloud.postman_collection.json`
3. Ejecuta la carpeta `1. Autenticación y Tokens` primero:
   * Al ejecutar los logins, Postman guardará automáticamente los tokens correspondientes (`token_admin_general`, `token_reportante`, `token_tecnico`, `token_admin_sistema`).
4. Ejecuta las demás carpetas para comprobar el control de acceso, las operaciones atómicas y las respuestas HTTP esperadas (200, 201, 400, 401, 403).
