<template>
  <div class="sysadmin-login-page">
    <div class="sysadmin-card">
      <div class="terminal-badge">
        <span class="dot"></span>
        <span>ROOT INFRASTRUCTURE CONSOLE</span>
      </div>

      <div class="header">
        <h1 class="title">Administración del Sistema</h1>
        <p class="subtitle">Acceso exclusivo para gestión de usuarios y roles</p>
      </div>

      <div v-if="auth.error" class="error-banner">
        {{ auth.error }}
      </div>

      <form @submit.prevent="handleSysadminLogin" class="form">
        <div class="field">
          <label>Cuenta de Administrador</label>
          <input
            v-model="correo"
            type="email"
            class="input-field input-dark"
            placeholder="soporte@utm.example"
            required
          />
        </div>

        <div class="field">
          <label>Contraseña Maestra</label>
          <input
            v-model="password"
            type="password"
            class="input-field input-dark"
            placeholder="••••••••"
            required
          />
        </div>

        <button type="submit" class="btn btn-sysadmin" :disabled="auth.loading">
          <span v-if="auth.loading">Autenticando en Clúster...</span>
          <span v-else>Entrar a Consola</span>
        </button>
      </form>

      <div class="quick-admin">
        <button @click="quickAdmin" class="quick-admin-btn">
          Usar cuenta de prueba: soporte@utm.example
        </button>
      </div>

      <div class="footer-links">
        <router-link to="/login" class="back-link">
          ← Volver al portal general de incidencias
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const auth = useAuthStore();

const correo = ref('soporte@utm.example');
const password = ref('Utm2026!');

async function handleSysadminLogin() {
  try {
    await auth.loginSysadmin(correo.value, password.value);
    router.push('/sysadmin/usuarios');
  } catch (err) {
    // Error manejado en store
  }
}

function quickAdmin() {
  correo.value = 'soporte@utm.example';
  password.value = 'Utm2026!';
  handleSysadminLogin();
}
</script>

<style scoped>
.sysadmin-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background-color: #0F172A;
  color: #F8FAFC;
}

.sysadmin-card {
  width: 100%;
  max-width: 440px;
  background: #1E293B;
  border-radius: var(--radius-lg);
  padding: 2.25rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  border: 1px solid #334155;
}

.terminal-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-family: var(--font-mono);
  font-size: 0.675rem;
  font-weight: 600;
  color: #38BDF8;
  background: rgba(56, 189, 248, 0.1);
  padding: 0.25rem 0.6rem;
  border-radius: var(--radius-sm);
  margin-bottom: 1.25rem;
  border: 1px solid rgba(56, 189, 248, 0.2);
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #38BDF8;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #FFFFFF;
}

.subtitle {
  font-size: 0.8rem;
  color: #94A3B8;
  margin-top: 0.25rem;
  margin-bottom: 1.5rem;
}

.error-banner {
  background: rgba(239, 68, 68, 0.15);
  color: #FCA5A5;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  font-size: 0.825rem;
  margin-bottom: 1.25rem;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.field label {
  display: block;
  font-size: 0.8rem;
  font-weight: 500;
  color: #CBD5E1;
  margin-bottom: 0.35rem;
}

.input-dark {
  background: #0F172A;
  border-color: #334155;
  color: #FFFFFF;
}

.input-dark:focus {
  border-color: #38BDF8;
  box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
}

.btn-sysadmin {
  width: 100%;
  padding: 0.75rem;
  background: #2563EB;
  color: #FFFFFF;
  border-radius: var(--radius-md);
  font-weight: 600;
  margin-top: 0.5rem;
  transition: background var(--transition-fast);
}

.btn-sysadmin:hover {
  background: #1D4ED8;
}

.quick-admin {
  margin-top: 1.5rem;
  text-align: center;
}

.quick-admin-btn {
  font-size: 0.75rem;
  color: #94A3B8;
  padding: 0.35rem 0.6rem;
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.04);
  transition: all var(--transition-fast);
}

.quick-admin-btn:hover {
  color: #38BDF8;
  background: rgba(56, 189, 248, 0.1);
}

.footer-links {
  margin-top: 1.5rem;
  text-align: center;
}

.back-link {
  font-size: 0.775rem;
  color: #64748B;
  transition: color var(--transition-fast);
}

.back-link:hover {
  color: #94A3B8;
}
</style>
