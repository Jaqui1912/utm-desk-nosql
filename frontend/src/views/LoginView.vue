<template>
  <div class="login-page">

    <!-- ══ Panel Izquierdo: Branding ══ -->
    <div class="panel-left">
      <!-- Forma decorativa superior derecha -->
      <div class="deco deco-top"></div>
      <div class="deco deco-mid"></div>

      <!-- Logo / Marca -->
      <div class="brand">
        <div class="brand-mark">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <span class="brand-name">UTM Desk</span>
      </div>

      <!-- Copy central -->
      <div class="panel-copy">
        <p class="copy-tag">NoSQL Cloud · MongoDB Atlas</p>
        <h1 class="copy-heading">
          Gestión, resolución y analítica de incidencias del campus
        </h1>
        <p class="copy-sub">
          Reporta fallas de cómputo, infraestructura y sistemas académicos
          y da seguimiento a cada una en un solo expediente.
        </p>
      </div>

      <!-- Forma decorativa inferior -->
      <div class="deco deco-bottom"></div>

      <!-- Footer del panel -->
      <p class="panel-footer">Universidad Tecnológica Metropolitana · Equipo 6</p>
    </div>

    <!-- ══ Panel Derecho: Formulario ══ -->
    <div class="panel-right">
      <div class="form-wrapper">

        <div class="form-header">
          <h2 class="form-title">Iniciar sesión</h2>
          <p class="form-sub">Entra con tu correo institucional.</p>
        </div>

        <!-- Error -->
        <div v-if="auth.error" class="error-banner" role="alert">
          {{ auth.error }}
        </div>

        <!-- Formulario -->
        <form @submit.prevent="handleLogin" class="login-form" id="login-form">
          <div class="field">
            <label for="login-correo">Correo</label>
            <input
              id="login-correo"
              v-model="correo"
              type="email"
              class="input-field"
              placeholder="usuario@utm.example"
              autocomplete="email"
              required
            />
          </div>

          <div class="field">
            <label for="login-password">Contraseña</label>
            <input
              id="login-password"
              v-model="password"
              type="password"
              class="input-field"
              placeholder="••••••••"
              autocomplete="current-password"
              required
            />
          </div>

          <button
            type="submit"
            class="btn btn-submit"
            :disabled="auth.loading"
            id="login-submit-btn"
          >
            <span v-if="auth.loading" class="btn-loading">
              <span class="spinner-sm"></span> Verificando…
            </span>
            <span v-else>Entrar</span>
          </button>
        </form>

        <!-- Cuentas de demostración -->
        <div class="demo-section">
          <p class="demo-label">CUENTAS DE DEMOSTRACIÓN · CONTRASEÑA: Utm2026!</p>
          <div class="demo-list">
            <button
              v-for="u in demoUsers"
              :key="u.correo"
              @click="quickLogin(u.correo)"
              class="demo-row"
              :id="`demo-btn-${u.id}`"
            >
              <div class="demo-info">
                <span class="demo-nombre">{{ u.nombre }}</span>
                <span class="demo-correo">{{ u.correo }}</span>
              </div>
              <span class="demo-badge" :class="u.badgeClass">{{ u.rolLabel }}</span>
            </button>
          </div>
        </div>

        <!-- Link sysadmin -->
        <div class="sysadmin-link-wrap">
          <router-link to="/sysadmin/login" class="sysadmin-link">
            Acceso a Consola de Infraestructura (Sysadmin)
          </router-link>
        </div>

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

const correo = ref('');
const password = ref('Utm2026!');

const demoUsers = [
  { id: 'maria',   nombre: 'María López',    correo: 'm.lopez@utm.example',  rolLabel: 'Reportante',              badgeClass: 'badge-reportante' },
  { id: 'patricia',nombre: 'Patricia Ek',    correo: 'p.ek@utm.example',     rolLabel: 'Administrador General',   badgeClass: 'badge-admin' },
  { id: 'carlos',  nombre: 'Carlos Pech',    correo: 'c.pech@utm.example',   rolLabel: 'Técnico',                 badgeClass: 'badge-tecnico' },
  { id: 'roberto', nombre: 'Roberto Dzib',   correo: 'r.dzib@utm.example',   rolLabel: 'Directivo',               badgeClass: 'badge-directivo' },
  { id: 'daniel',  nombre: 'Daniel May',     correo: 'd.may@utm.example',    rolLabel: 'Administrador del Sistema',badgeClass: 'badge-sysadmin' },
];

async function handleLogin() {
  try {
    const usuario = await auth.login(correo.value, password.value);
    // Si viene del admin_sistema lo redirigirá el guard, pero por las dudas:
    if (usuario?.rol === 'admin_sistema') {
      router.push('/sysadmin/usuarios');
    } else {
      router.push('/incidencias');
    }
  } catch (err) {
    // Error ya almacenado en auth.error
  }
}

function quickLogin(userCorreo) {
  correo.value = userCorreo;
  password.value = 'Utm2026!';
  handleLogin();
}
</script>

<style scoped>
/* ══ Layout ══ */
.login-page {
  min-height: 100vh;
  display: flex;
}

/* ══ Panel Izquierdo ══ */
.panel-left {
  position: relative;
  width: 45%;
  background: var(--color-primary);
  display: flex;
  flex-direction: column;
  padding: 2rem 2.5rem;
  overflow: hidden;
  flex-shrink: 0;
}

/* Formas decorativas */
.deco {
  position: absolute;
  border-radius: 6px;
  opacity: 0.35;
}
.deco-top {
  top: -30px;
  right: -40px;
  width: 180px;
  height: 180px;
  background: #1B8A61;
  transform: rotate(20deg);
}
.deco-mid {
  top: 60px;
  right: 40px;
  width: 90px;
  height: 90px;
  background: #2AAC76;
  transform: rotate(15deg);
}
.deco-bottom {
  bottom: 80px;
  left: -40px;
  width: 140px;
  height: 140px;
  background: #8DC63F;
  transform: rotate(-10deg);
  border-radius: 8px;
  opacity: 0.45;
}

/* Marca superior */
.brand {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 0.55rem;
  color: #fff;
}
.brand-mark {
  width: 28px;
  height: 28px;
  background: rgba(255,255,255,0.2);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #A3E4C1;
}
.brand-name {
  font-weight: 700;
  font-size: 1rem;
  letter-spacing: -0.01em;
}

/* Copy central */
.panel-copy {
  position: relative;
  z-index: 1;
  margin-top: auto;
  margin-bottom: auto;
  padding: 2rem 0;
}
.copy-tag {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: #7ECBA1;
  font-weight: 500;
  letter-spacing: 0.02em;
  margin-bottom: 1rem;
}
.copy-heading {
  font-size: 1.85rem;
  font-weight: 800;
  color: #fff;
  line-height: 1.2;
  letter-spacing: -0.02em;
  margin-bottom: 1rem;
}
.copy-sub {
  font-size: 0.84rem;
  color: rgba(255,255,255,0.72);
  line-height: 1.6;
  max-width: 340px;
}

/* Footer */
.panel-footer {
  position: relative;
  z-index: 1;
  font-size: 0.7rem;
  color: rgba(255,255,255,0.4);
  margin-top: 1rem;
}

/* ══ Panel Derecho ══ */
.panel-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #FAFAF8;
  padding: 2rem 1.5rem;
  overflow-y: auto;
}

.form-wrapper {
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-header { }
.form-title {
  font-size: 1.55rem;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: -0.02em;
}
.form-sub {
  font-size: 0.85rem;
  color: var(--color-primary);
  margin-top: 0.2rem;
}

/* Error */
.error-banner {
  background: #FEE2E2;
  color: #991B1B;
  padding: 0.7rem 1rem;
  border-radius: var(--radius-md);
  font-size: 0.82rem;
  border: 1px solid #FCA5A5;
}

/* Formulario */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.field label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.btn-submit {
  width: 100%;
  padding: 0.75rem;
  font-size: 0.95rem;
  font-weight: 600;
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.25rem;
}
.btn-submit:hover:not(:disabled) { background: var(--color-primary-hover); }
.btn-submit:disabled { opacity: 0.65; cursor: not-allowed; }

.btn-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.spinner-sm {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ══ Cuentas Demo ══ */
.demo-section {
  border-top: 1px solid var(--border-subtle);
  padding-top: 1.25rem;
}

.demo-label {
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--text-tertiary);
  letter-spacing: 0.07em;
  text-transform: uppercase;
  margin-bottom: 0.75rem;
}

.demo-list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.demo-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 0.85rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  text-align: left;
  transition: all var(--transition-fast);
  cursor: pointer;
}
.demo-row:hover {
  border-color: var(--color-primary-border);
  background: var(--color-primary-light);
}

.demo-info {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}
.demo-nombre {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-main);
}
.demo-correo {
  font-size: 0.72rem;
  color: var(--color-primary);
}

/* Badges de Rol */
.demo-badge {
  font-size: 0.68rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: var(--radius-full);
  white-space: nowrap;
  flex-shrink: 0;
}
.badge-reportante  { background: #DBEAFE; color: #1E40AF; }
.badge-admin       { background: #D1FAE5; color: #065F46; }
.badge-tecnico     { background: #FEF3C7; color: #92400E; }
.badge-directivo   { background: #EDE9FE; color: #5B21B6; }
.badge-sysadmin    { background: #F3F4F6; color: #374151; }

/* Link sysadmin */
.sysadmin-link-wrap {
  text-align: center;
}
.sysadmin-link {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  transition: color var(--transition-fast);
}
.sysadmin-link:hover { color: var(--color-primary); }

/* ══ Responsive ══ */
@media (max-width: 768px) {
  .login-page { flex-direction: column; }
  .panel-left {
    width: 100%;
    min-height: 220px;
    padding: 1.5rem;
  }
  .copy-heading { font-size: 1.4rem; }
  .panel-right { padding: 2rem 1.25rem; }
}
</style>
