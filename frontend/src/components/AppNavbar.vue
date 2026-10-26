<template>
  <nav class="app-navbar">
    <div class="navbar-inner">
      <!-- Logo / Identidad -->
      <div class="navbar-brand">
        <div class="brand-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 2 12"/><path d="M5 12V6a7 7 0 0 1 14 0v6"/><rect x="2" y="12" width="20" height="8" rx="1"/></svg></div>
        <div class="brand-text">
          <span class="brand-name">UTM Desk</span>
          <span class="brand-sub">NoSQL Cloud</span>
        </div>
      </div>

      <!-- Navegación Principal -->
      <ul class="navbar-nav">
        <li v-for="item in navItems" :key="item.to">
          <router-link :to="item.to" class="nav-link" :class="{ active: isActive(item.to) }">
            {{ item.label }}
          </router-link>
        </li>
      </ul>

      <!-- Usuario y Logout -->
      <div class="navbar-user">
        <div class="user-info">
          <div class="user-avatar">{{ auth.nombre?.charAt(0)?.toUpperCase() }}</div>
          <div class="user-meta">
            <span class="user-name">{{ auth.nombre }}</span>
            <span class="user-role">{{ rolLabel }}</span>
          </div>
        </div>
        <button @click="handleLogout" class="logout-btn" title="Cerrar sesión">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();

const ROL_LABELS = {
  reportante: 'Reportante',
  tecnico: 'Técnico',
  admin_general: 'Administrador General',
  directivo: 'Directivo',
  admin_sistema: 'Admin. del Sistema',
};

const rolLabel = computed(() => ROL_LABELS[auth.rol] || auth.rol);

const NAV_POR_ROL = {
  reportante: [
    { to: '/incidencias', label: 'Mis Incidencias' },
    { to: '/incidencias/nueva', label: 'Nueva Incidencia' },
  ],
  tecnico: [
    { to: '/incidencias', label: 'Incidencias' },
  ],
  admin_general: [
    { to: '/incidencias', label: 'Incidencias' },
    { to: '/incidencias/nueva', label: 'Nueva Incidencia' },
    { to: '/analitica', label: 'Analítica' },
  ],
  directivo: [
    { to: '/incidencias', label: 'Incidencias' },
    { to: '/analitica', label: 'Analítica' },
  ],
  admin_sistema: [
    { to: '/sysadmin/usuarios', label: 'Usuarios' },
  ],
};

const navItems = computed(() => NAV_POR_ROL[auth.rol] || []);

function isActive(path) {
  if (path === '/incidencias') {
    return route.path === '/incidencias';
  }
  return route.path.startsWith(path);
}

async function handleLogout() {
  const redirectTo = auth.logout();
  router.push(redirectTo);
}
</script>

<style scoped>
.app-navbar {
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-subtle);
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: var(--shadow-sm);
}

.navbar-inner {
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 1.25rem;
  height: 60px;
  display: flex;
  align-items: center;
  gap: 2rem;
}

/* Brand */
.navbar-brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-shrink: 0;
}

.brand-icon {
  font-size: 1.3rem;
  width: 34px;
  height: 34px;
  background: var(--color-primary-light);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.brand-name {
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--text-main);
}

.brand-sub {
  font-size: 0.65rem;
  color: var(--text-tertiary);
  font-weight: 500;
}

/* Nav Links */
.navbar-nav {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  list-style: none;
  flex: 1;
}

.nav-link {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.75rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.nav-link:hover {
  background: var(--bg-surface-muted);
  color: var(--text-main);
}

.nav-link.active {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 600;
}

.nav-icon {
  font-size: 1rem;
}

/* User area */
.navbar-user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-left: auto;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: var(--color-primary);
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
}

.user-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.user-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-main);
}

.user-role {
  font-size: 0.68rem;
  color: var(--text-tertiary);
}

.logout-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  color: var(--text-tertiary);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.logout-btn:hover {
  background: #FEE2E2;
  color: #DC2626;
}
</style>
