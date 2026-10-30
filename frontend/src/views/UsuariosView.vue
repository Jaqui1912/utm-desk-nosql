<template>
  <div class="sysadmin-app">
    <!-- ── Barra Superior Sysadmin ── -->
    <header class="sysadmin-nav">
      <div class="nav-inner">
        <div class="brand-group">
          <div class="sys-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
              <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
              <line x1="6" y1="6" x2="6.01" y2="6"/>
              <line x1="6" y1="18" x2="6.01" y2="18"/>
            </svg>
          </div>
          <div class="brand-titles">
            <span class="sys-name">UTM Desk · Consola Sysadmin</span>
            <span class="sys-cluster">Cluster Atlas M0 · Colección usuarios</span>
          </div>
        </div>

        <div class="nav-user-area">
          <div class="sys-user-badge">
            <span class="user-pill">{{ auth.nombre }}</span>
            <span class="role-pill">{{ auth.rol }}</span>
          </div>
          <router-link v-if="auth.isSuperAdmin" to="/incidencias" class="btn btn-xs back-incidencias">
            ← Incidencias
          </router-link>
          <button @click="handleLogout" class="btn btn-outline-danger btn-xs">
            Cerrar Consola
          </button>
        </div>
      </div>
    </header>

    <!-- ── Contenedor Central ── -->
    <main class="sysadmin-main">
      <div class="console-header">
        <div>
          <h1 class="console-title">Directorio y Control de Acceso (RF-14)</h1>
          <p class="console-subtitle">
            Alta de cuentas con contraseña cifrada (bcrypt), asignación estricta de roles y conmutación de estado.
          </p>
        </div>
        <button @click="cargarUsuarios" class="btn btn-console-sec btn-sm" :disabled="loading">
          ↻ Refrescar directorio
        </button>
      </div>

      <!-- Feedback banners -->
      <div v-if="successMsg" class="success-banner" role="status">
        {{ successMsg }}
      </div>
      <div v-if="errorMsg" class="error-banner" role="alert">
        {{ errorMsg }}
      </div>

      <!-- ── Panel de Respaldo y Exportación NoSQL (JSON) ── -->
      <section class="console-card export-card" aria-labelledby="export-title">
        <div class="export-header">
          <div class="export-titles">
            <div class="export-badge">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              <span>Respaldo y Auditoría NoSQL</span>
            </div>
            <h2 id="export-title" class="card-title">Exportación de Datos en JSON</h2>
            <p class="card-desc">
              Descarga directa en formato JSON estándar de las colecciones vivas en MongoDB Atlas y sus esquemas de validación ($jsonSchema).
            </p>
          </div>
          <div class="export-actions">
            <!-- Botón Usuarios -->
            <button
              type="button"
              @click="handleExportar('usuarios')"
              class="btn-export"
              :disabled="exportando !== null"
              title="Descargar directorio de usuarios en JSON"
            >
              <div class="btn-export-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              </div>
              <div class="btn-export-text">
                <span class="file-name font-mono">usuarios.json</span>
                <span class="file-desc">Directorio de cuentas</span>
              </div>
              <span v-if="exportando === 'usuarios'" class="export-spinner" aria-label="Descargando..."></span>
              <span v-else class="export-tag">JSON</span>
            </button>

            <!-- Botón Incidencias -->
            <button
              type="button"
              @click="handleExportar('incidencias')"
              class="btn-export"
              :disabled="exportando !== null"
              title="Descargar historial de incidencias en JSON"
            >
              <div class="btn-export-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
              </div>
              <div class="btn-export-text">
                <span class="file-name font-mono">incidencias_campus.json</span>
                <span class="file-desc">Historial completo</span>
              </div>
              <span v-if="exportando === 'incidencias'" class="export-spinner" aria-label="Descargando..."></span>
              <span v-else class="export-tag">JSON</span>
            </button>

            <!-- Botón Esquema -->
            <button
              type="button"
              @click="handleExportar('esquema')"
              class="btn-export"
              :disabled="exportando !== null"
              title="Descargar validador e índices en JSON"
            >
              <div class="btn-export-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="3"/>
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                </svg>
              </div>
              <div class="btn-export-text">
                <span class="file-name font-mono">esquema_y_indices.json</span>
                <span class="file-desc">$jsonSchema e índices</span>
              </div>
              <span v-if="exportando === 'esquema'" class="export-spinner" aria-label="Descargando..."></span>
              <span v-else class="export-tag">JSON</span>
            </button>
          </div>
        </div>
      </section>

      <div class="sys-grid">
        
        <!-- ── Formulario de Registro de Usuario ── -->
        <div class="console-card create-card">
          <h2 class="card-title">Registrar nuevo usuario</h2>
          <p class="card-desc">El documento se valida contra el $jsonSchema de usuarios en Atlas.</p>

          <form @submit.prevent="handleCrearUsuario" class="user-form">
            <div class="field">
              <label for="usr-nombre">Nombre completo *</label>
              <input
                id="usr-nombre"
                v-model="form.nombre"
                type="text"
                class="input-dark"
                placeholder="Ej. Ing. Gabriel Pech"
                required
                minlength="3"
              />
            </div>

            <div class="field">
              <label for="usr-correo">Correo institucional (@utm.example) *</label>
              <input
                id="usr-correo"
                v-model="form.correo"
                type="email"
                class="input-dark"
                placeholder="g.pech@utm.example"
                required
              />
            </div>

            <div class="field">
              <label for="usr-pass">Contraseña inicial *</label>
              <input
                id="usr-pass"
                v-model="form.password"
                type="password"
                class="input-dark"
                placeholder="Mínimo 6 caracteres"
                required
                minlength="6"
              />
            </div>

            <div class="field">
              <label for="usr-rol">Rol asignado *</label>
              <select id="usr-rol" v-model="form.rol" class="input-dark" required>
                <option value="reportante">Reportante (Comunidad)</option>
                <option value="tecnico">Técnico de Soporte</option>
                <option value="admin_general">Administrador General</option>
                <option value="directivo">Directivo (Lectura analítica)</option>
                <option value="admin_sistema">Administrador del Sistema (Consola)</option>
                <option value="superAdmin">Super Administrador (acceso total)</option>
              </select>
            </div>

            <!-- Condicional si rol === reportante -->
            <div v-if="form.rol === 'reportante'" class="field sub-field">
              <label>Tipo de reportante (Requerido por $jsonSchema) *</label>
              <select v-model="form.tipo" class="input-dark" required>
                <option value="docente">Docente</option>
                <option value="estudiante">Estudiante</option>
                <option value="administrativo">Personal Administrativo</option>
              </select>
            </div>

            <!-- Condicional si rol === tecnico -->
            <div v-if="form.rol === 'tecnico'" class="field sub-field">
              <label>Especialidades técnicas</label>
              <div class="checkboxes-row">
                <label class="check-item">
                  <input type="checkbox" value="computo_redes" v-model="form.especialidades" />
                  <span>Cómputo</span>
                </label>
                <label class="check-item">
                  <input type="checkbox" value="infraestructura" v-model="form.especialidades" />
                  <span>Infraestructura</span>
                </label>
                <label class="check-item">
                  <input type="checkbox" value="academico" v-model="form.especialidades" />
                  <span>Académico</span>
                </label>
              </div>
            </div>

            <button
              type="submit"
              class="btn btn-console-primary"
              :disabled="saving"
            >
              <span v-if="saving">Registrando en Atlas…</span>
              <span v-else>Guardar Usuario</span>
            </button>
          </form>
        </div>

        <!-- ── Tabla de Directorio de Usuarios ── -->
        <div class="console-card table-card">
          <div class="table-head-row">
            <h2 class="card-title">Cuentas registradas ({{ usuarios.length }})</h2>
            <span class="info-tag">Colección: usuarios</span>
          </div>

          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <span>Consultando usuarios...</span>
          </div>

          <div v-else class="table-responsive">
            <table class="users-table">
              <thead>
                <tr>
                  <th>Usuario</th>
                  <th>Rol</th>
                  <th>Perfil / Especialidad</th>
                  <th>Estado</th>
                  <th>Acción</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in usuarios" :key="u.id" :class="{ 'row-inactive': !u.activo }">
                  <td>
                    <div class="user-meta-cell">
                      <span class="u-name">{{ u.nombre }}</span>
                      <span class="u-email font-mono">{{ u.correo }}</span>
                    </div>
                  </td>
                  <td>
                    <span class="role-badge">{{ formatRol(u.rol) }}</span>
                  </td>
                  <td>
                    <span class="type-text">
                      {{ u.tipo ? formatTipo(u.tipo) : (u.especialidades?.join(', ') || '—') }}
                    </span>
                  </td>
                  <td>
                    <span
                      class="status-pill"
                      :class="u.activo ? 'status-active' : 'status-inactive'"
                    >
                      {{ u.activo ? 'Activo' : 'Inactivo' }}
                    </span>
                  </td>
                  <td>
                    <button
                      v-if="u.id !== auth.userId"
                      @click="handleToggleEstado(u)"
                      class="btn btn-toggle-state btn-xs"
                      :class="u.activo ? 'btn-warn' : 'btn-success'"
                    >
                      {{ u.activo ? 'Desactivar' : 'Activar' }}
                    </button>
                    <span v-else class="self-label">Tu sesión</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import usuariosApi from '../api/usuarios';
import exportarApi from '../api/exportar';

const router = useRouter();
const auth = useAuthStore();

const loading = ref(true);
const saving = ref(false);
const exportando = ref(null);
const errorMsg = ref('');
const successMsg = ref('');
const usuarios = ref([]);

const form = reactive({
  nombre: '',
  correo: '',
  password: '',
  rol: 'reportante',
  tipo: 'docente',
  especialidades: [],
});

function formatRol(r) {
  const map = {
    reportante: 'Reportante',
    tecnico: 'Técnico',
    admin_general: 'Admin General',
    directivo: 'Directivo',
    admin_sistema: 'Admin Sistema',
    superAdmin: 'Super Admin',
  };
  return map[r] || r;
}

function formatTipo(t) {
  const map = {
    docente: 'Docente',
    estudiante: 'Estudiante',
    administrativo: 'Administrativo',
  };
  return map[t] || t;
}

async function cargarUsuarios() {
  loading.value = true;
  errorMsg.value = '';
  try {
    const res = await usuariosApi.listar();
    usuarios.value = res.data.usuarios || [];
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || err.message || 'Error al listar usuarios.';
  } finally {
    loading.value = false;
  }
}

async function handleCrearUsuario() {
  saving.value = true;
  errorMsg.value = '';
  successMsg.value = '';

  try {
    const payload = {
      nombre: form.nombre.trim(),
      correo: form.correo.trim().toLowerCase(),
      password: form.password,
      rol: form.rol,
    };

    if (form.rol === 'reportante') {
      payload.tipo = form.tipo;
    }
    if (form.rol === 'tecnico' && form.especialidades.length) {
      payload.especialidades = form.especialidades;
    }

    await usuariosApi.crear(payload);
    successMsg.value = `Usuario '${payload.nombre}' registrado exitosamente.`;
    
    // Limpiar formulario
    form.nombre = '';
    form.correo = '';
    form.password = '';
    form.rol = 'reportante';
    form.tipo = 'docente';
    form.especialidades = [];

    await cargarUsuarios();
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || err.message || 'Error al registrar usuario.';
  } finally {
    saving.value = false;
  }
}

async function handleToggleEstado(usuario) {
  const nuevoEstado = !usuario.activo;
  try {
    await usuariosApi.cambiarEstado(usuario.id, nuevoEstado);
    usuario.activo = nuevoEstado;
    successMsg.value = `Cuenta de '${usuario.nombre}' ${nuevoEstado ? 'activada' : 'desactivada'}.`;
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || err.message || 'Error al cambiar estado.';
  }
}

async function handleExportar(tipo) {
  exportando.value = tipo;
  errorMsg.value = '';
  try {
    if (tipo === 'usuarios') {
      await exportarApi.exportarUsuarios();
      successMsg.value = 'Archivo "usuarios.json" generado y descargado correctamente desde MongoDB Atlas.';
    } else if (tipo === 'incidencias') {
      await exportarApi.exportarIncidencias();
      successMsg.value = 'Archivo "incidencias_campus.json" generado y descargado correctamente desde MongoDB Atlas.';
    } else if (tipo === 'esquema') {
      await exportarApi.exportarEsquema();
      successMsg.value = 'Archivo "esquema_y_indices.json" ($jsonSchema e índices) generado y descargado correctamente.';
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || err.message || 'Error al exportar los datos.';
  } finally {
    exportando.value = null;
  }
}

function handleLogout() {
  const redir = auth.logout();
  router.push(redir);
}

onMounted(cargarUsuarios);
</script>

<style scoped>
.sysadmin-app {
  min-height: 100vh;
  background: #0B111E;
  color: #E2E8F0;
  display: flex;
  flex-direction: column;
}

/* Nav */
.sysadmin-nav {
  background: #111827;
  border-bottom: 1px solid #1F2937;
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-inner {
  max-width: 1300px;
  margin: 0 auto;
  padding: 0 1.5rem;
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.brand-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.sys-icon {
  width: 34px;
  height: 34px;
  background: #1E293B;
  color: #38BDF8;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #334155;
}
.brand-titles {
  display: flex;
  flex-direction: column;
}
.sys-name {
  font-weight: 700;
  font-size: 0.92rem;
  color: #F8FAFC;
}
.sys-cluster {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  color: #94A3B8;
}

.nav-user-area {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.sys-user-badge {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
}
.user-pill {
  color: #CBD5E1;
  font-weight: 600;
}
.role-pill {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  background: #1E293B;
  color: #38BDF8;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  border: 1px solid #334155;
}

/* Main */
.sysadmin-main {
  max-width: 1300px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
  flex: 1;
  width: 100%;
}

.console-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}
.console-title {
  font-size: 1.45rem;
  font-weight: 700;
  color: #F8FAFC;
}
.console-subtitle {
  font-size: 0.85rem;
  color: #94A3B8;
  margin-top: 0.25rem;
}

/* Banners */
.success-banner {
  background: #064E3B;
  border: 1px solid #059669;
  color: #A7F3D0;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  margin-bottom: 1.25rem;
}
.error-banner {
  background: #7F1D1D;
  border: 1px solid #DC2626;
  color: #FECACA;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  margin-bottom: 1.25rem;
}

/* Grid */
.sys-grid {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 1.5rem;
  align-items: flex-start;
}

.console-card {
  background: #111827;
  border: 1px solid #1F2937;
  border-radius: var(--radius-md);
  padding: 1.5rem;
}
.card-title {
  font-size: 1rem;
  font-weight: 700;
  color: #F8FAFC;
}
.card-desc {
  font-size: 0.78rem;
  color: #94A3B8;
  margin-top: 0.2rem;
  margin-bottom: 1.25rem;
}

/* Forms */
.user-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.field label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #94A3B8;
}
.sub-field {
  background: #1E293B;
  padding: 0.75rem;
  border-radius: var(--radius-sm);
  border: 1px solid #334155;
}

.input-dark {
  width: 100%;
  padding: 0.55rem 0.75rem;
  background: #0B111E;
  border: 1px solid #334155;
  border-radius: var(--radius-sm);
  color: #F8FAFC;
  font-size: 0.82rem;
  outline: none;
}
.input-dark:focus {
  border-color: #38BDF8;
  box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
}

.checkboxes-row {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.25rem;
}
.check-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
  color: #CBD5E1;
  cursor: pointer;
}

.btn-console-primary {
  background: #2563EB;
  color: #fff;
  padding: 0.65rem;
  font-weight: 600;
  font-size: 0.85rem;
  border-radius: var(--radius-sm);
  margin-top: 0.5rem;
}
.btn-console-primary:hover:not(:disabled) { background: #1D4ED8; }

.btn-console-sec {
  background: #1E293B;
  color: #CBD5E1;
  border: 1px solid #334155;
  border-radius: var(--radius-sm);
}
.btn-console-sec:hover { background: #334155; color: #fff; }

.btn-outline-danger {
  border: 1px solid #EF4444;
  color: #EF4444;
  border-radius: var(--radius-sm);
}
.btn-outline-danger:hover { background: #EF4444; color: #fff; }

/* Table */
.table-head-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.info-tag {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: #64748B;
}

.table-responsive {
  overflow-x: auto;
}
.users-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}
.users-table th {
  text-align: left;
  padding: 0.65rem 0.75rem;
  font-size: 0.72rem;
  text-transform: uppercase;
  color: #64748B;
  border-bottom: 1px solid #1F2937;
}
.users-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #1F2937;
  color: #CBD5E1;
}
.row-inactive {
  opacity: 0.6;
}

.user-meta-cell {
  display: flex;
  flex-direction: column;
}
.u-name {
  font-weight: 600;
  color: #F8FAFC;
}
.u-email {
  font-size: 0.72rem;
  color: #94A3B8;
}
.font-mono {
  font-family: var(--font-mono);
}

.role-badge {
  font-size: 0.72rem;
  font-weight: 600;
  background: #1E293B;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  color: #E2E8F0;
}

.type-text {
  font-size: 0.75rem;
  color: #94A3B8;
}

.status-pill {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-full);
}
.status-active {
  background: rgba(16, 185, 129, 0.2);
  color: #34D399;
}
.status-inactive {
  background: rgba(100, 116, 139, 0.2);
  color: #94A3B8;
}

.btn-toggle-state {
  font-size: 0.72rem;
  padding: 0.2rem 0.55rem;
  border-radius: 4px;
}
.btn-warn {
  background: #78350F;
  color: #FDE68A;
}
.btn-warn:hover { background: #92400E; }
.btn-success {
  background: #064E3B;
  color: #A7F3D0;
}
.btn-success:hover { background: #065F46; }

.self-label {
  font-size: 0.72rem;
  color: #64748B;
  font-style: italic;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 3rem;
  color: #64748B;
}
.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #334155;
  border-top-color: #38BDF8;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 960px) {
  .sys-grid {
    grid-template-columns: 1fr;
  }
}
.back-incidencias {
  color: #CBD5E1;
  border: 1px solid #334155;
  text-decoration: none;
}
.back-incidencias:hover {
  color: #FFFFFF;
  border-color: #64748B;
}

/* ── Panel de Respaldo y Exportación NoSQL ── */
.export-card {
  margin-bottom: 1.5rem;
  background: linear-gradient(135deg, #111827 0%, #131E33 100%);
  border: 1px solid #1E293B;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}
.export-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}
.export-titles {
  max-width: 500px;
}
.export-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(56, 189, 248, 0.12);
  color: #38BDF8;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  border: 1px solid rgba(56, 189, 248, 0.25);
  margin-bottom: 0.5rem;
}
.export-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.btn-export {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  background: #1A2234;
  border: 1px solid #334155;
  color: #E2E8F0;
  padding: 0.65rem 0.95rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}
.btn-export:hover:not(:disabled) {
  background: #1E293B;
  border-color: #38BDF8;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(56, 189, 248, 0.15);
}
.btn-export:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-export-icon {
  color: #38BDF8;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-export-text {
  display: flex;
  flex-direction: column;
}
.btn-export-text .file-name {
  font-size: 0.78rem;
  font-weight: 700;
  color: #F8FAFC;
}
.btn-export-text .file-desc {
  font-size: 0.68rem;
  color: #94A3B8;
}
.export-tag {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  font-weight: 700;
  background: #0F172A;
  color: #38BDF8;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  border: 1px solid #1E293B;
}
.export-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #334155;
  border-top-color: #38BDF8;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@media (max-width: 960px) {
  .export-header {
    flex-direction: column;
    align-items: stretch;
  }
  .export-actions {
    flex-direction: column;
  }
  .btn-export {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
