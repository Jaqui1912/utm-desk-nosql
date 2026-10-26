# UTM Desk — Documentación del Frontend

> **Rama:** dev_frontend  
> **Framework:** Vue 3 (Composition API · \<script setup>\) + Vite 8  
> **Última actualización:** Octubre 2026  

---

## Índice

1. [Stack tecnológico](#1-stack-tecnológico)
2. [Estructura de carpetas](#2-estructura-de-carpetas)
3. [Sistema de diseño](#3-sistema-de-diseño)
4. [Estado global - Pinia Store](#4-estado-global--pinia-store)
5. [Capa API - Axios](#5-capa-api--axios)
6. [Router y protección de rutas (RBAC)](#6-router-y-protección-de-rutas-rbac)
7. [Componentes](#7-componentes)
8. [Vistas implementadas](#8-vistas-implementadas)
9. [Pendientes y mejoras](#9-pendientes-y-mejoras)
10. [Cómo levantar el proyecto](#10-cómo-levantar-el-proyecto)

---

## 1. Stack tecnológico

| Tecnología | Versión | Rol |
|---|---|---|
| **Vue 3** | ^3.5 | Framework principal (Composition API, <script setup>) |
| **Vite** | ^8.x | Bundler y dev-server ultra-rápido |
| **Vue Router 4** | ^4.x | Enrutamiento SPA con navigation guards para control de acceso (RBAC) |
| **Pinia** | ^2.x | Gestión de estado global reactivo (reemplazo moderno de Vuex) |
| **Axios** | ^1.x | Cliente HTTP para comunicarse con el backend FastAPI con interceptores |
| **Vanilla CSS** | - | Estilos personalizados limpios; sin Tailwind |
| **JetBrains Mono** + **Inter** | Google Fonts | Tipografías del sistema de diseño institucional |

### Variables de entorno

Crear un archivo .env en la raíz de /frontend con:

`env
VITE_API_URL=http://127.0.0.1:8000
`

Si no existe, Axios usa http://127.0.0.1:8000 como fallback predeterminado.

---

## 2. Estructura de carpetas

`	ext
frontend/
├── index.html                  # Entry point HTML con tipografías Inter y JetBrains Mono
├── package.json                # Dependencias (vue, vue-router, pinia, axios)
├── vite.config.js              # Configuración de Vite con proxy hacia FastAPI
├── FRONTEND_DOCS.md            # Documentación técnica del frontend
└── src/
    ├── main.js                 # Inicialización de la app Vue, Pinia y Router
    ├── App.vue                 # Componente raíz con layout condicional (Navbar + RouterView)
    ├── api/                    # Capa de comunicación HTTP con Axios
    │   ├── axios.js            # Instancia configurada e interceptor de Authorization Bearer
    │   ├── auth.js             # Servicios de autenticación (/auth/login, /auth/me)
    │   ├── incidencias.js      # Servicios CRUD de incidencias (/incidencias/...)
    │   └── usuarios.js         # Servicios de gestión de usuarios (/usuarios/...)
    ├── components/             # Componentes reutilizables
    │   ├── AppNavbar.vue       # Barra de navegación principal con control según rol y logout
    │   └── EstadoBadge.vue     # Badge visual con color por estado de incidencia
    ├── router/
    │   └── index.js            # Definición de rutas, metadatos y guard global RBAC
    ├── stores/
    │   └── auth.js             # Store de autenticación Pinia persistido en localStorage
    ├── styles/                 # Hojas de estilo globales
    │   ├── main.css            # Reset, tipografía base y estilos globales
    │   └── tokens.css          # Design tokens CSS (colores, espaciados, bordes, sombras)
    └── views/                  # Vistas principales de la aplicación
        ├── LoginView.vue           # Login para la comunidad universitaria
        ├── SysadminLoginView.vue   # Consola de acceso para el Administrador del Sistema
        ├── IncidenciasListView.vue # Tabla de incidencias con filtros y conteos en tiempo real
        ├── NuevaIncidenciaView.vue # Registro de incidencia con BSON preview reactivo
        ├── IncidenciaDetailView.vue# Expediente detallado, transiciones de estado y bitácora
        ├── AnalyticsView.vue       # Analítica directiva y métricas del sistema
        └── UsuariosView.vue        # Directorio y gestión de usuarios (Admin Sistema)
`

---

## 3. Sistema de diseño

Definido en src/styles/tokens.css usando variables CSS personalizadas:

- **Colores primarios:**
  - Azul institucional: --color-primary (#2563EB)
  - Variante hover: --color-primary-dark (#1D4ED8)
  - Fondo suave: --color-primary-light (#EFF6FF)
- **Estados de incidencias:**
  - Abierta / Activada: --color-estado-abierta (#3B82F6)
  - En Proceso: --color-estado-en-proceso (#F59E0B)
  - Resuelta: --color-estado-resuelta (#10B981)
  - Cerrada: --color-estado-cerrada (#6B7280)
  - Rechazada / Cancelada: --color-estado-rechazada (#EF4444)
- **Superficies y bordes:**
  - Fondo general: --bg-body (#F8FAFC)
  - Tarjetas / Superficies: --bg-surface (#FFFFFF)
  - Bordes tenues: --border-subtle (#E2E8F0)

---

## 4. Estado global — Pinia Store (src/stores/auth.js)

Maneja la identidad del usuario y sincronización con localStorage:

- **Estado (state):**
  - 	oken: JWT recibido del backend.
  - user: Datos del usuario autenticado (id, 
ombre, correo, 
ol, 	ipo, especialidades).
- **Getters:**
  - isAuthenticated: Booleano !!token.
  - 
ol: Rol del usuario actual (
eportante, 	ecnico, dmin_general, directivo, dmin_sistema).
  - isSysadmin: 	rue si el rol es dmin_sistema.
  - isTecnico: 	rue si el rol es 	ecnico.
  - isAdminGeneral: 	rue si el rol es dmin_general.
  - isDirectivo: 	rue si el rol es directivo.
  - isReportante: 	rue si el rol es 
eportante.
- **Acciones:**
  - setSession(token, user): Guarda en el store y en localStorage.
  - logout(): Limpia el store, localStorage y devuelve la ruta a redirigir (/login o /sysadmin/login).

---

## 5. Capa API — Axios (src/api/)

- xios.js: Configura la base URL (VITE_API_URL o fallback a http://127.0.0.1:8000) e inyecta el token Bearer en el encabezado Authorization automáticamente en cada petición mediante un interceptor.
- uth.js:
  - loginApi(correo, password) ➔ POST /auth/login
  - getMeApi() ➔ GET /auth/me
- incidencias.js:
  - getIncidenciasApi(filtros) ➔ GET /incidencias
  - getIncidenciaByIdApi(id) ➔ GET /incidencias/:id
  - crearIncidenciaApi(payload) ➔ POST /incidencias
  - ctualizarEstadoApi(id, nuevoEstado, observaciones) ➔ PATCH /incidencias/:id/estado
  - signarTecnicoApi(id, tecnicoId) ➔ PATCH /incidencias/:id/asignar
  - getAnaliticaApi() ➔ GET /incidencias/analitica
- usuarios.js:
  - getUsuariosApi() ➔ GET /usuarios
  - crearUsuarioApi(payload) ➔ POST /usuarios
  - cambiarEstadoUsuarioApi(id, activo) ➔ PATCH /usuarios/:id/estado

---

## 6. Router y protección de rutas (RBAC) (src/router/index.js)

El router implementa un Navigation Guard global (
outer.beforeEach) que valida:

1. **Rutas públicas:** /login y /sysadmin/login. Si el usuario ya está autenticado, lo redirige a su pantalla correspondiente.
2. **Autenticación requerida:** Si no hay token, redirige a /sysadmin/login si la URL empieza con /sysadmin, o a /login para el resto.
3. **Control de acceso por roles (RBAC):**
   - Si un usuario intenta entrar a una ruta no autorizada en meta.roles, se bloquea el acceso y se le redirige a su área permitida.

| Ruta | Nombre | Componente | Roles permitidos |
|---|---|---|---|
| /login | login | LoginView | Público |
| /sysadmin/login | sysadmin-login | SysadminLoginView | Público |
| / | - | *Redirect* a /incidencias | - |
| /incidencias | incidencias-list | IncidenciasListView | 
eportante, 	ecnico, dmin_general, directivo |
| /incidencias/nueva | 
ueva-incidencia | NuevaIncidenciaView | 
eportante, dmin_general |
| /incidencias/:id | incidencia-detail | IncidenciaDetailView | Todos los roles autenticados |
| /analitica | nalytics | AnalyticsView | dmin_general, directivo |
| /sysadmin/usuarios | sysadmin-usuarios | UsuariosView | dmin_sistema |

---

## 7. Componentes

- **AppNavbar.vue:** Barra de navegación superior fija. Muestra enlaces dinámicos según el rol autenticado, avatar con inicial, nombre, rol y botón para cerrar sesión.
- **EstadoBadge.vue:** Etiqueta visual con código de color y texto amigable para cada estado de incidencia.

---

## 8. Vistas implementadas

### LoginView.vue (/login)
Pantalla de inicio de sesión para estudiantes, docentes, técnicos y administrativos con diseño moderno, banner de errores y validaciones de formulario.

### SysadminLoginView.vue (/sysadmin/login)
Consola especializada con temática oscura (dark theme) para el Administrador de Infraestructura / Sysadmin.

### IncidenciasListView.vue (/incidencias)
- Tabla completa de incidencias con ancho optimizado para pantallas medianas y grandes.
- Filtros por categoría, edificio y estado.
- Badges de conteo reactivos por estado que mantienen la cuenta real total de cada estado en todo momento.

### NuevaIncidenciaView.vue (/incidencias/nueva)
- Formulario de captura de incidencias con campos dinámicos según aula/laboratorio/oficina.
- Preview en tiempo real del documento BSON con scroll horizontal/vertical contenido para no romper el layout con descripciones extensas.

### IncidenciaDetailView.vue (/incidencias/:id)
- Expediente completo de la incidencia con detalles, técnico asignado y bitácora histórica.
- Panel de cambio de estado y asignación de técnicos para perfiles con permisos (dmin_general, 	ecnico).

### AnalyticsView.vue (/analitica)
- Dashboard analítico con métricas clave: total de incidencias, tasa de resolución, tiempo promedio.
- Gráficos y desglose por categorías y estados.

### UsuariosView.vue (/sysadmin/usuarios)
- Directorio de usuarios para el Administrador del Sistema.
- Formulario modal para registrar usuarios con rol, tipo y especialidades.
- Toggle para activar o desactivar cuentas.

---

## 9. Pendientes y mejoras para próximas iteraciones

### Vistas adicionales recomendadas
1. **Perfil de usuario (/perfil):** Visualización de información de cuenta, especialidades asignadas y cambio de contraseña.
2. **Página 404 personalizada:** Vista amigable para URLs inexistentes con botón de retorno al inicio.
3. **Página 403 (Acceso denegado):** Retroalimentación visual cuando un rol intenta acceder a un recurso sin permisos.
4. **Dashboard Sysadmin (/sysadmin):** Vista de bienvenida y estado general de la plataforma antes de ir al directorio.

### Mejoras funcionales
1. **Dropdown en Navbar:** Menú contextual al pulsar el avatar del usuario con acceso rápido a perfil y configuración.
2. **Edición completa de usuarios:** Modal para modificar nombres, correos o especialidades desde UsuariosView.
3. **Sistema centralizado de notificaciones (Toasts):** Para confirmar acciones exitosas (creación, edición, cambio de estado).

---

## 10. Cómo levantar el proyecto

### Requisitos previos
- Node.js >= 18
- Backend FastAPI corriendo en http://127.0.0.1:8000

### Instrucciones
`ash
# 1. Ingresar a la carpeta frontend
cd frontend

# 2. Instalar dependencias (solo la primera vez)
npm install

# 3. Iniciar el servidor de desarrollo Vite
npm run dev
`

La aplicación estará accesible en: http://localhost:5173/
