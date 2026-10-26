<template>
  <!-- Navbar principal -->
  <AppNavbar />

  <!-- Contenido principal -->
  <div class="app-container">

    <!-- ── Cabecera de la vista ── -->
    <div class="view-header">
      <div class="header-left">
        <h1 class="view-title">{{ listTitle }}</h1>
        <p class="view-subtitle">{{ listSubtitle }}</p>
      </div>
      <div class="header-actions">
        <router-link v-if="auth.can('registrar')" to="/incidencias/nueva" class="btn btn-primary">
          + Nueva incidencia
        </router-link>
      </div>
    </div>

    <!-- ── Barra de Búsqueda y Filtros ── -->
    <div class="filters-panel">

      <!-- Búsqueda textual $text -->
      <div class="search-box">
        <span class="search-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></span>
        <input
          v-model="q"
          type="text"
          class="input-field search-input"
          placeholder="Buscar por título, descripción…"
          @input="onSearch"
        />
        <button v-if="q" @click="clearSearch" class="clear-btn">×</button>
      </div>

      <!-- Filtros para todos los usuarios (Categoría, Edificio y Asignadas) -->
      <div class="filter-selects">
        <select v-model="fCat" @change="fetchData" class="input-field select-small">
          <option value="">Todas las categorías</option>
          <option value="computo_redes">Cómputo y Telecomunicaciones</option>
          <option value="infraestructura">Infraestructura Física</option>
          <option value="academico">Sistemas Académicos</option>
        </select>

        <select v-model="fEdi" @change="fetchData" class="input-field select-small">
          <option value="">Todos los edificios</option>
          <option v-for="e in edificios" :key="e" :value="e">{{ e }}</option>
        </select>

        <!-- Toggle: Solo asignadas a mí (para técnicos) -->
        <label v-if="auth.isTecnico" class="toggle-label">
          <input type="checkbox" v-model="soloMias" @change="fetchData" />
          <span>Solo asignadas a mí</span>
        </label>
      </div>

      <!-- Botón limpiar filtros -->
      <button v-if="hasFilters" @click="clearFilters" class="btn btn-secondary btn-sm">
        × Limpiar filtros
      </button>
    </div>

    <!-- ── Pills de Estado (con conteos) ── -->
    <div class="estado-pills">
      <button
        v-for="pill in estadoPills"
        :key="pill.value"
        @click="toggleEstado(pill.value)"
        class="pill"
        :class="{ 'pill-active': fEst === pill.value }"
        :style="pill.style"
      >
        {{ pill.label }}
        <span class="pill-count">{{ pill.count }}</span>
      </button>
    </div>

    <!-- ── Query $text visible (como en el prototipo) ── -->
    <div v-if="q.trim()" class="query-badge">
      <code>db.incidencias_campus.find({ $text: { $search: "{{ q.trim() }}" } }).sort({ score: { $meta: "textScore" } })</code>
    </div>

    <!-- ── Tabla de Incidencias con Tamaño Fijo y Sólido ── -->
    <div class="table-card">
      <div class="table-responsive">
        <table class="incidencias-table">
          <thead>
            <tr>
              <th class="th-codigo">CÓDIGO</th>
              <th class="th-incidencia">INCIDENCIA</th>
              <th class="th-edificio">EDIFICIO</th>
              <th class="th-prioridad">PRIORIDAD</th>
              <th class="th-estado">ESTADO</th>
              <th class="th-tecnico">TÉCNICO</th>
              <th class="th-registro">REGISTRO</th>
              <th v-if="hasTextScore" class="th-score">SCORE</th>
            </tr>
          </thead>
          <tbody>
            <!-- Estado: Cargando dentro de la tabla -->
            <tr v-if="loading">
              <td :colspan="hasTextScore ? 8 : 7" class="table-status-cell">
                <div class="loading-state">
                  <div class="spinner"></div>
                  <span>Consultando incidencias en MongoDB Atlas…</span>
                </div>
              </td>
            </tr>

            <!-- Estado: Sin resultados dentro de la tabla -->
            <tr v-else-if="incidencias.length === 0">
              <td :colspan="hasTextScore ? 8 : 7" class="table-status-cell">
                <div class="empty-state">
                  <div class="empty-icon">
                    <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M22 12h-6l-2 3H10l-2-3H2"/>
                      <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>
                    </svg>
                  </div>
                  <p class="empty-title">Sin incidencias encontradas</p>
                  <p class="empty-sub">{{ q ? 'No hubo coincidencias con la búsqueda textual.' : 'No hay incidencias que coincidan con los filtros aplicados.' }}</p>
                </div>
              </td>
            </tr>

            <!-- Filas con incidencias -->
            <tr
              v-else
              v-for="inc in incidencias"
              :key="inc.id || inc._id"
              class="inc-row"
              @click="navegarA(inc._id || inc.id)"
            >
              <td class="td-codigo font-mono">{{ inc.codigo }}</td>
              <td class="td-incidencia">
                <router-link
                  :to="`/incidencias/${inc._id || inc.id}`"
                  class="inc-title-link"
                  @click.stop
                >
                  {{ inc.titulo }}
                </router-link>
                <div class="inc-meta-sub">
                  <span>{{ catLabel(inc.categoria) }}</span>
                  <span class="sub-sep">·</span>
                  <span>{{ inc.ubicacion?.zona || 'Campus' }}</span>
                </div>
              </td>
              <td class="td-edificio">{{ inc.ubicacion?.edificio || '—' }}</td>
              <td class="td-prioridad">
                <span class="badge" :style="prioCss(inc.prioridad)">
                  {{ cap(inc.prioridad) }}
                </span>
              </td>
              <td class="td-estado">
                <span class="badge" :style="estadoCss(inc.estado)">
                  {{ cap(inc.estado) }}
                </span>
              </td>
              <td class="td-tecnico">
                <span :class="inc.tecnico_asignado ? 'tech-name' : 'tech-unassigned'">
                  {{ inc.tecnico_asignado ? inc.tecnico_asignado.nombre : 'Sin asignar' }}
                </span>
              </td>
              <td class="td-registro">{{ fDate(inc.fecha_creacion) }}</td>
              <td v-if="hasTextScore" class="td-score font-mono">
                {{ inc.score ? Number(inc.score).toFixed(1) : '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ── Paginación ── -->
    <div v-if="!q && total > limit" class="pagination">
      <button :disabled="skip === 0" @click="prevPage" class="btn btn-secondary btn-sm">← Anterior</button>
      <span class="page-info">{{ Math.floor(skip/limit)+1 }} / {{ Math.ceil(total/limit) }}</span>
      <button :disabled="skip + limit >= total" @click="nextPage" class="btn btn-secondary btn-sm">Siguiente →</button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import incidenciasApi from '../api/incidencias';
import AppNavbar from '../components/AppNavbar.vue';

const router = useRouter();
const auth = useAuthStore();

// ── Estado Reactivo ──
const incidencias = ref([]);
const total = ref(0);
const loading = ref(true);
const q = ref('');
const fCat = ref('');
const fEst = ref('');
const fEdi = ref('');
const soloMias = ref(false);
const limit = ref(25);
const skip = ref(0);
let searchTimeout = null;

const hasTextScore = computed(() => incidencias.value.some(i => i.score !== undefined));

function navegarA(id) {
  if (id) {
    router.push(`/incidencias/${id}`);
  }
}

// ── Datos de Conteos para Pills ──
// Conteos independientes del filtro de estado activo
const estadoCounts = ref({});
const loadingCounts = ref(false);

// ── Catálogo de Edificios del Campus ──
const EDIFICIOS_CAMPUS = [
  'Edificio A',
  'Edificio B',
  'Edificio C',
  'Edificio D',
  'Edificio E',
  'Edificio F',
  'Edificio A - Rectoría',
  'Edificio B - Docencia',
  'Edificio C - Talleres',
  'Edificio D - Cómputo',
  'Edificio E - Biblioteca',
  'Edificio F - Laboratorios',
  'Auditorio Principal',
];

const edificios = computed(() => {
  const fromData = incidencias.value.map(i => i.ubicacion?.edificio).filter(Boolean);
  return [...new Set([...EDIFICIOS_CAMPUS, ...fromData])].sort();
});

// ── Título dinámico según rol ──
const listTitle = computed(() => {
  if (auth.isReportante) return 'Mis incidencias';
  if (auth.isTecnico && soloMias.value) return 'Asignadas a mí';
  return 'Incidencias del Campus';
});

const listSubtitle = computed(() => {
  const suffix = auth.isReportante ? ' · solo ves las que tú registraste' : '';
  return `${incidencias.value.length} de ${total.value} incidencias${suffix}`;
});

const hasFilters = computed(() => !!(q.value || fCat.value || fEst.value || fEdi.value || soloMias.value));

// ── Pills de Estado ──
const ESTADOS = ['abierta', 'en proceso', 'en espera', 'resuelta', 'cerrada'];
const EST_CSS = {
  abierta: { background: 'var(--est-abierta-bg)', color: 'var(--est-abierta-text)' },
  'en proceso': { background: 'var(--est-proceso-bg)', color: 'var(--est-proceso-text)' },
  'en espera': { background: 'var(--est-espera-bg)', color: 'var(--est-espera-text)' },
  resuelta: { background: 'var(--est-resuelta-bg)', color: 'var(--est-resuelta-text)' },
  cerrada: { background: 'var(--est-cerrada-bg)', color: 'var(--est-cerrada-text)' },
};

const estadoPills = computed(() =>
  ESTADOS.map(e => ({
    value: e,
    label: cap(e),
    count: estadoCounts.value[e] ?? 0,
    style: EST_CSS[e] || {},
  }))
);

// ── Utilidades de Formato ──
function cap(str) {
  return str ? str.charAt(0).toUpperCase() + str.slice(1) : '';
}
function fDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' });
}
function catLabel(cat) {
  return {
    computo_redes: 'Cómputo y Telecomunicaciones',
    infraestructura: 'Infraestructura Física',
    academico: 'Sistemas Académicos',
  }[cat] || cat;
}
function estadoCss(estado) {
  return EST_CSS[estado] || {};
}
function prioCss(prio) {
  const map = {
    baja: { background: 'var(--prio-baja-bg)', color: 'var(--prio-baja-text)' },
    media: { background: 'var(--prio-media-bg)', color: 'var(--prio-media-text)' },
    alta: { background: 'var(--prio-alta-bg)', color: 'var(--prio-alta-text)' },
    critica: { background: 'var(--prio-critica-bg)', color: 'var(--prio-critica-text)' },
  };
  return map[prio] || {};
}

// ── Fetching de Datos ──
async function fetchData() {
  loading.value = true;
  try {
    if (q.value.trim().length >= 2) {
      // Búsqueda textual ponderada CU-05
      const res = await incidenciasApi.buscar(q.value.trim(), 50);
      incidencias.value = res.data.resultados || [];
      total.value = res.data.total || 0;
    } else {
      // Listado normal con filtros (incluye filtro de estado)
      const res = await incidenciasApi.listar({
        categoria: fCat.value,
        estado: fEst.value,
        edificio: fEdi.value,
        asignadas_a_mi: soloMias.value,
        limit: limit.value,
        skip: skip.value,
      });
      incidencias.value = res.data.incidencias || [];
      total.value = res.data.total || 0;
    }
  } catch (err) {
    console.error('Error al cargar incidencias:', err);
  } finally {
    loading.value = false;
  }
  // Conteos siempre se recalculan sin filtro de estado
  fetchEstadoCounts();
}

/**
 * Obtiene los conteos por estado SIN aplicar el filtro de estado activo.
 * Llama al endpoint de agregación /conteos-estado que usa $group en MongoDB.
 * Así los pills siempre muestran cuántas incidencias hay en cada estado,
 * independientemente de cuál esté seleccionado.
 */
async function fetchEstadoCounts() {
  try {
    const res = await incidenciasApi.conteosPorEstado({
      categoria: fCat.value,
      edificio: fEdi.value,
      asignadas_a_mi: soloMias.value,
    });
    estadoCounts.value = res.data || {};
  } catch (err) {
    console.error('Error al obtener conteos de estado:', err);
  } finally {
    loadingCounts.value = false;
  }
}

function onSearch() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    skip.value = 0;
    fetchData();
  }, 350);
}

function clearSearch() {
  q.value = '';
  skip.value = 0;
  fetchData();
}

function clearFilters() {
  q.value = '';
  fCat.value = '';
  fEst.value = '';
  fEdi.value = '';
  soloMias.value = false;
  skip.value = 0;
  fetchData();
}

function toggleEstado(e) {
  fEst.value = fEst.value === e ? '' : e;
  skip.value = 0;
  fetchData();
}

function prevPage() {
  skip.value = Math.max(0, skip.value - limit.value);
  fetchData();
}

function nextPage() {
  skip.value += limit.value;
  fetchData();
}

onMounted(fetchData);
</script>

<style scoped>
/* ── Cabecera ── */
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  padding-top: 1.5rem;
}
.view-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: -0.02em;
}
.view-subtitle {
  font-size: 0.82rem;
  color: var(--text-tertiary);
  margin-top: 0.2rem;
}

/* ── Panel de Filtros ── */
.filters-panel {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  background: var(--bg-surface);
  padding: 0.85rem 1rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}

.search-box {
  position: relative;
  flex: 1;
  min-width: 220px;
}
.search-icon {
  position: absolute;
  left: 0.7rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.85rem;
}
.search-input {
  padding-left: 2.1rem;
  padding-right: 2rem;
}
.clear-btn {
  position: absolute;
  right: 0.6rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.75rem;
  color: var(--text-tertiary);
  transition: color var(--transition-fast);
}
.clear-btn:hover { color: var(--text-main); }

.filter-selects {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}
.select-small {
  width: auto;
  min-width: 160px;
  font-size: 0.82rem;
}
.toggle-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
}
.btn-sm {
  font-size: 0.8rem;
  padding: 0.4rem 0.75rem;
}

/* ── Pills de Estado ── */
.estado-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 1rem;
}
.pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.8rem;
  border-radius: var(--radius-full);
  font-size: 0.78rem;
  font-weight: 600;
  border: 1.5px solid transparent;
  transition: all var(--transition-fast);
  cursor: pointer;
}
.pill:hover { opacity: 0.85; }
.pill-active { box-shadow: inset 0 0 0 2px currentColor; }
.pill-count {
  background: rgba(0,0,0,0.1);
  border-radius: 99px;
  padding: 0 0.35rem;
  font-size: 0.7rem;
}

/* ── Query badge estilo MongoDB ── */
.query-badge {
  background: #0F172A;
  color: #38BDF8;
  border-radius: var(--radius-md);
  padding: 0.55rem 0.85rem;
  margin-bottom: 1rem;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  overflow-x: auto;
  border: 1px solid #1E293B;
}

/* ── Cargando ── */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 4rem;
  color: var(--text-tertiary);
}
.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-medium);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Sin resultados ── */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--text-tertiary);
}
.empty-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }
.empty-title { font-size: 1rem; font-weight: 600; color: var(--text-secondary); }
.empty-sub { font-size: 0.82rem; margin-top: 0.25rem; }

.app-container {
  max-width: 1380px;
  width: 93%;
  margin: 0 auto;
  padding: 1.5rem 0;
}

/* ── Tabla de Incidencias con Tamaño Fijo y Amplio ── */
.table-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  margin-bottom: 1.5rem;
  width: 100%;
  min-height: 520px;
  display: flex;
  flex-direction: column;
}

.table-responsive {
  width: 100%;
  flex: 1;
  overflow-x: auto;
}

.incidencias-table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  text-align: left;
}

.incidencias-table th {
  padding: 1rem 1.25rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--text-tertiary);
  border-bottom: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  white-space: nowrap;
}

/* Anchos fijos de columnas (no cambian con los filtros) */
.th-codigo { width: 140px; }
.th-incidencia { width: auto; min-width: 320px; }
.th-edificio { width: 155px; }
.th-prioridad { width: 110px; }
.th-estado { width: 125px; }
.th-tecnico { width: 160px; }
.th-registro { width: 125px; }
.th-score { width: 90px; }

.inc-row {
  transition: background var(--transition-fast);
  cursor: pointer;
  height: 64px;
}

.inc-row:hover {
  background: var(--bg-surface-muted);
}

.inc-row:last-child td {
  border-bottom: none;
}

.incidencias-table td {
  padding: 0.9rem 1.25rem;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 0.85rem;
  vertical-align: middle;
}

.table-status-cell {
  padding: 4.5rem 2rem !important;
  text-align: center;
  vertical-align: middle;
}

/* Celdas específicas */
.td-codigo {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-secondary);
  white-space: nowrap;
}

.td-incidencia {
  min-width: 320px;
  overflow: hidden;
}

.inc-title-link {
  font-size: 0.92rem;
  font-weight: 700;
  color: var(--text-main);
  text-decoration: none;
  line-height: 1.3;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color var(--transition-fast);
}

.inc-title-link:hover {
  text-decoration: underline;
  color: var(--color-primary);
}

.inc-meta-sub {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin-top: 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sub-sep {
  color: var(--border-strong);
}

.td-edificio {
  font-weight: 500;
  color: var(--text-main);
  white-space: nowrap;
}

.td-prioridad,
.td-estado {
  white-space: nowrap;
}

.td-tecnico {
  white-space: nowrap;
}

.tech-name {
  color: var(--text-main);
  font-weight: 500;
}

.tech-unassigned {
  color: #B45309;
  font-style: italic;
  font-size: 0.82rem;
}

.td-registro {
  color: var(--text-secondary);
  font-size: 0.82rem;
  white-space: nowrap;
}

.td-score {
  font-size: 0.82rem;
  color: var(--color-primary);
  font-weight: 600;
  white-space: nowrap;
}

/* ── Paginación ── */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 0;
}
.page-info {
  font-size: 0.82rem;
  color: var(--text-secondary);
  font-weight: 500;
}
</style>
