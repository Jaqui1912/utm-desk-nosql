import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const routes = [
  // ── Rutas Públicas de Acceso ──
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true, title: 'Iniciar Sesión · UTM Desk' },
  },
  {
    path: '/sysadmin/login',
    name: 'sysadmin-login',
    component: () => import('../views/SysadminLoginView.vue'),
    meta: { public: true, title: 'Consola de Infraestructura · Sysadmin' },
  },

  // ── Rutas Protegidas de Incidencias (Comunidad Universitaria) ──
  {
    path: '/',
    redirect: '/incidencias',
  },
  {
    path: '/incidencias',
    name: 'incidencias-list',
    component: () => import('../views/IncidenciasListView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['reportante', 'tecnico', 'admin_general', 'directivo'],
      title: 'Incidencias · UTM Desk',
    },
  },
  {
    path: '/incidencias/nueva',
    name: 'nueva-incidencia',
    component: () => import('../views/NuevaIncidenciaView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['reportante', 'admin_general'],
      title: 'Nueva Incidencia · UTM Desk',
    },
  },
  {
    path: '/incidencias/:id',
    name: 'incidencia-detail',
    component: () => import('../views/IncidenciaDetailView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['reportante', 'tecnico', 'admin_general', 'directivo', 'admin_sistema'],
      title: 'Expediente de Incidencia · UTM Desk',
    },
  },

  // ── Analítica Directiva (RF-09 / Pipelines de Agregación) ──
  {
    path: '/analitica',
    name: 'analytics',
    component: () => import('../views/AnalyticsView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['admin_general', 'directivo'],
      title: 'Analítica Directiva · UTM Desk',
    },
  },

  // ── Consola del Administrador del Sistema (RF-14 / Backoffice) ──
  {
    path: '/sysadmin/usuarios',
    name: 'sysadmin-usuarios',
    component: () => import('../views/UsuariosView.vue'),
    meta: {
      requiresAuth: true,
      roles: ['admin_sistema'],
      title: 'Directorio de Usuarios · Consola Sysadmin',
    },
  },

  // ── Captura de Rutas Desconocidas ──
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// ── Navigation Guard Global (RBAC y Sesión) ──
router.beforeEach(async (to, from) => {
  const auth = useAuthStore();

  // Actualizar título de pestaña
  if (to.meta.title) {
    document.title = to.meta.title;
  }

  const isPublic = to.meta.public;
  const requiresAuth = to.meta.requiresAuth;
  const allowedRoles = to.meta.roles;

  // 1. Si no está autenticado y la ruta requiere sesión
  if (requiresAuth && !auth.isAuthenticated) {
    if (to.path.startsWith('/sysadmin')) {
      return { name: 'sysadmin-login' };
    }
    return { name: 'login' };
  }

  // 2. Si ya está autenticado e intenta ir al login
  if (isPublic && auth.isAuthenticated) {
    if (auth.isSysadmin) {
      return { name: 'sysadmin-usuarios' };
    }
    return { name: 'incidencias-list' };
  }

  // 3. Verificación de Roles (RBAC)
  if (requiresAuth && allowedRoles && !allowedRoles.includes(auth.rol) && !auth.isSuperAdmin) {
    // Si un sysadmin entra a una vista que no le compete, enviarlo a su consola
    if (auth.isSysadmin) {
      return { name: 'sysadmin-usuarios' };
    }
    // Para otros roles, enviarlos al listado principal de incidencias
    return { name: 'incidencias-list' };
  }

  return true;
});

export default router;
