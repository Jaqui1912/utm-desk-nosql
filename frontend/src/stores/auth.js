import { defineStore } from 'pinia';
import api, { extractErrorMessage } from '../api/axios';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('utm_desk_token') || null,
    user: JSON.parse(localStorage.getItem('utm_desk_user') || 'null'),
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token && !!state.user,
    rol: (state) => state.user?.rol || null,
    userId: (state) => state.user?.id || null,
    nombre: (state) => state.user?.nombre || 'Usuario',
    tipo: (state) => state.user?.tipo || null,

    // Comprobaciones de Roles
    isReportante: (state) => state.user?.rol === 'reportante',
    isTecnico: (state) => state.user?.rol === 'tecnico',
    isAdminGeneral: (state) => state.user?.rol === 'admin_general',
    isDirectivo: (state) => state.user?.rol === 'directivo',
    isSysadmin: (state) => state.user?.rol === 'admin_sistema',
    isSuperAdmin: (state) => state.user?.rol === 'superAdmin',

    // Helper de Matriz de Permisos (RBAC según Tabla 3 del documento)
    can: (state) => (action) => {
      const rol = state.user?.rol;
      if (!rol) return false;
      // superAdmin (cuenta de evaluación del docente): acceso total
      if (rol === 'superAdmin') return true;

      const PERMISOS = {
        registrar: ['reportante', 'admin_general'],
        asignar: ['admin_general'],
        actualizar_estado: ['tecnico', 'admin_general'],
        evidencias: ['reportante', 'tecnico', 'admin_general'],
        tags: ['tecnico', 'admin_general'],
        analitica: ['admin_general', 'directivo'],
        gestionar_usuarios: ['admin_sistema'],
        ver_todas: ['admin_general', 'tecnico', 'directivo', 'admin_sistema'],
      };

      return PERMISOS[action]?.includes(rol) || false;
    },
  },

  actions: {
    /**
     * Inicio de sesión general (comunidad universitaria)
     */
    async login(correo, password) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.post('/auth/login', { correo, password });
        const { access_token, usuario } = response.data;

        this.setSession(access_token, usuario);
        return usuario;
      } catch (err) {
        this.error = err.message || extractErrorMessage(err);
        throw new Error(this.error);
      } finally {
        this.loading = false;
      }
    },

    /**
     * Inicio de sesión exclusivo para Administrador de Sistema (/sysadmin/login)
     */
    async loginSysadmin(correo, password) {
      this.loading = true;
      this.error = null;

      try {
        const response = await api.post('/auth/login', { correo, password });
        const { access_token, usuario } = response.data;

        // Validar que realmente sea admin_sistema
        if (usuario.rol !== 'admin_sistema') {
          throw new Error('Acceso denegado: Esta consola es de uso exclusivo para el Administrador del Sistema.');
        }

        this.setSession(access_token, usuario);
        return usuario;
      } catch (err) {
        this.error = err.message || extractErrorMessage(err);
        throw new Error(this.error);
      } finally {
        this.loading = false;
      }
    },

    /**
     * Guardar sesión local y en estado
     */
    setSession(token, user) {
      this.token = token;
      this.user = user;
      localStorage.setItem('utm_desk_token', token);
      localStorage.setItem('utm_desk_user', JSON.stringify(user));
    },

    /**
     * Cerrar sesión
     */
    logout() {
      const wasSysadmin = this.isSysadmin;
      this.token = null;
      this.user = null;
      localStorage.removeItem('utm_desk_token');
      localStorage.removeItem('utm_desk_user');

      return wasSysadmin ? '/sysadmin/login' : '/login';
    },

    /**
     * Refrescar perfil del usuario desde backend
     */
    async fetchMe() {
      if (!this.token) return null;
      try {
        const res = await api.get('/auth/me');
        this.user = res.data;
        localStorage.setItem('utm_desk_user', JSON.stringify(res.data));
        return this.user;
      } catch (e) {
        this.logout();
        return null;
      }
    },
  },
});
