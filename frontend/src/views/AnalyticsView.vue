<template>
  <AppNavbar />

  <div class="app-container">
    <div class="view-header">
      <div class="header-left">
        <h1 class="view-title">Analítica de Resolución y Fallas Crónicas</h1>
        <p class="view-subtitle">
          Pipelines de agregación en MongoDB Atlas para toma de decisiones (CU-06 / RF-09).
        </p>
      </div>
      <div class="header-actions">
        <button @click="cargarAnalitica" class="btn btn-secondary btn-sm" :disabled="loading">
          ↻ Actualizar datos
        </button>
      </div>
    </div>

    <!-- Error Banner -->
    <div v-if="error" class="error-banner" role="alert">
      {{ error }}
    </div>

    <!-- Estado de carga -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Ejecutando pipelines de agregación en MongoDB Atlas...</span>
    </div>

    <div v-else class="analytics-content">
      
      <!-- ── Tarjetas KPI ── -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <span class="kpi-label">Edificios analizados</span>
          <span class="kpi-value">{{ eficienciaPorEdificio.length }}</span>
          <span class="kpi-sub">Con incidencias resueltas</span>
        </div>

        <div class="kpi-card">
          <span class="kpi-label">Total incidencias resueltas</span>
          <span class="kpi-value">{{ totalResueltas }}</span>
          <span class="kpi-sub">Con cálculo de horas de resolución</span>
        </div>

        <div class="kpi-card">
          <span class="kpi-label">Promedio general campus</span>
          <span class="kpi-value">{{ promedioGeneralHoras }} h</span>
          <span class="kpi-sub">Tiempo medio de solución</span>
        </div>

        <div class="kpi-card">
          <span class="kpi-label">Etiquetas indexadas</span>
          <span class="kpi-value">{{ topTags.length }}</span>
          <span class="kpi-sub">Top 10 fallas recurrentes</span>
        </div>
      </div>

      <!-- ── Grid de Agregaciones (Pipeline 1 y Pipeline 2) ── -->
      <div class="dash-grid">
        
        <!-- Pipeline 1: Eficiencia por Edificio -->
        <div class="card dash-card">
          <div class="card-head-flex">
            <div>
              <h2 class="dash-title">Pipeline 1 · Eficiencia y Tiempo por Edificio</h2>
              <p class="dash-sub">Promedio y total de horas invertidas en incidencias resueltas</p>
            </div>
            <button @click="showP1 = !showP1" class="btn btn-secondary btn-xs">
              {{ showP1 ? 'Ocultar MQL' : '{ } Ver Pipeline MQL' }}
            </button>
          </div>

          <!-- MQL Code Box -->
          <div v-if="showP1" class="mql-box">
            <pre><code>db.incidencias_campus.aggregate([
  { $match: { estado: { $in: ["resuelta", "cerrada"] }, fecha_resolucion: { $exists: true } } },
  { $addFields: { horas_resolucion: { $divide: [{ $subtract: ["$fecha_resolucion", "$fecha_creacion"] }, 3600000] } } },
  { $group: {
      _id: "$ubicacion.edificio",
      incidencias: { $sum: 1 },
      promedio_horas: { $avg: "$horas_resolucion" },
      total_horas: { $sum: "$horas_resolucion" }
  } },
  { $sort: { promedio_horas: -1 } }
])</code></pre>
          </div>

          <!-- Bars List -->
          <div v-if="eficienciaPorEdificio.length === 0" class="empty-state-sm">
            Sin datos de incidencias resueltas para calcular promedios.
          </div>
          <div v-else class="bars-list">
            <div
              v-for="ed in eficienciaPorEdificio"
              :key="ed.edificio"
              class="bar-item"
            >
              <div class="bar-info-row">
                <span class="bar-label">{{ ed.edificio }}</span>
                <span class="bar-meta font-mono">
                  <strong>{{ ed.promedio_horas }} h prom.</strong> · {{ ed.total_horas }} h tot. ({{ ed.incidencias }} inc.)
                </span>
              </div>
              <div class="bar-track">
                <div
                  class="bar-fill bar-primary"
                  :style="{ width: calcWidth(ed.promedio_horas, maxHorasEdificio) }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Pipeline 2: Top 10 Etiquetas Frecuentes -->
        <div class="card dash-card">
          <div class="card-head-flex">
            <div>
              <h2 class="dash-title">Pipeline 2 · Ranking de Fallas Crónicas (Top Tags)</h2>
              <p class="dash-sub">Frecuencia de etiquetas técnicas desanidadas con $unwind</p>
            </div>
            <button @click="showP2 = !showP2" class="btn btn-secondary btn-xs">
              {{ showP2 ? 'Ocultar MQL' : '{ } Ver Pipeline MQL' }}
            </button>
          </div>

          <!-- MQL Code Box -->
          <div v-if="showP2" class="mql-box">
            <pre><code>db.incidencias_campus.aggregate([
  { $unwind: "$tags" },
  { $group: { _id: "$tags", total: { $sum: 1 } } },
  { $sort: { total: -1, _id: 1 } },
  { $limit: 10 }
])</code></pre>
          </div>

          <!-- Tags List -->
          <div v-if="topTags.length === 0" class="empty-state-sm">
            No se han registrado etiquetas técnicas en los expedientes.
          </div>
          <div v-else class="bars-list">
            <div
              v-for="t in topTags"
              :key="t.tag"
              class="bar-item"
            >
              <div class="bar-info-row">
                <span class="bar-label font-mono">#{{ t.tag }}</span>
                <span class="bar-meta">
                  <strong>{{ t.total }}</strong> {{ t.total === 1 ? 'incidencia' : 'incidencias' }}
                </span>
              </div>
              <div class="bar-track">
                <div
                  class="bar-fill bar-accent"
                  :style="{ width: calcWidth(t.total, maxTagTotal) }"
                ></div>
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import incidenciasApi from '../api/incidencias';
import AppNavbar from '../components/AppNavbar.vue';

const loading = ref(true);
const error = ref('');
const eficienciaPorEdificio = ref([]);
const topTags = ref([]);

const showP1 = ref(false);
const showP2 = ref(false);

const totalResueltas = computed(() => {
  return eficienciaPorEdificio.value.reduce((acc, curr) => acc + (curr.incidencias || 0), 0);
});

const promedioGeneralHoras = computed(() => {
  if (eficienciaPorEdificio.value.length === 0) return '0.0';
  const totalHoras = eficienciaPorEdificio.value.reduce((acc, curr) => acc + (curr.total_horas || 0), 0);
  const totalInc = totalResueltas.value;
  return totalInc > 0 ? (totalHoras / totalInc).toFixed(1) : '0.0';
});

const maxHorasEdificio = computed(() => {
  const vals = eficienciaPorEdificio.value.map(e => e.promedio_horas || 0);
  return Math.max(1, ...vals);
});

const maxTagTotal = computed(() => {
  const vals = topTags.value.map(t => t.total || 0);
  return Math.max(1, ...vals);
});

function calcWidth(val, max) {
  const pct = Math.max(5, Math.round(((val || 0) / max) * 100));
  return `${pct}%`;
}

async function cargarAnalitica() {
  loading.value = true;
  error.value = '';
  try {
    const res = await incidenciasApi.analitica();
    eficienciaPorEdificio.value = res.data.eficiencia_por_edificio || [];
    topTags.value = res.data.top_10_tags || [];
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Error al ejecutar pipelines de analítica.';
  } finally {
    loading.value = false;
  }
}

onMounted(cargarAnalitica);
</script>

<style scoped>
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}
.view-title {
  font-size: 1.45rem;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: -0.02em;
}
.view-subtitle {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: 0.2rem;
}

/* Error */
.error-banner {
  background: #FEE2E2;
  color: #991B1B;
  padding: 0.85rem 1rem;
  border-radius: var(--radius-md);
  font-size: 0.84rem;
  margin-bottom: 1.25rem;
  border: 1px solid #FCA5A5;
}

/* KPIs */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.kpi-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  box-shadow: var(--shadow-sm);
}
.kpi-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-tertiary);
}
.kpi-value {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--color-primary);
  line-height: 1.2;
}
.kpi-sub {
  font-size: 0.72rem;
  color: var(--text-secondary);
}

/* Dash Grid */
.dash-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}
.dash-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
}
.card-head-flex {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}
.dash-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-main);
}
.dash-sub {
  font-size: 0.78rem;
  color: var(--text-secondary);
  margin-top: 0.15rem;
}
.btn-xs {
  font-size: 0.72rem;
  padding: 0.25rem 0.55rem;
}

/* MQL Code Box */
.mql-box {
  background: #0F172A;
  border: 1px solid #1E293B;
  border-radius: var(--radius-sm);
  padding: 0.85rem;
  margin-bottom: 1.25rem;
  color: #38BDF8;
  font-family: var(--font-mono);
  font-size: 0.72rem;
  line-height: 1.4;
  overflow-x: auto;
}

/* Bars List */
.bars-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}
.bar-item {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.bar-info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
}
.bar-label {
  font-weight: 600;
  color: var(--text-main);
}
.bar-meta {
  color: var(--text-secondary);
  font-size: 0.75rem;
}
.font-mono {
  font-family: var(--font-mono);
}

.bar-track {
  width: 100%;
  height: 8px;
  background: var(--bg-surface-muted);
  border-radius: var(--radius-full);
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width 0.4s ease-out;
}
.bar-primary {
  background: var(--color-primary);
}
.bar-accent {
  background: #2563EB;
}

.empty-state-sm {
  font-size: 0.82rem;
  color: var(--text-tertiary);
  padding: 1.5rem 0;
  text-align: center;
}

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

@media (max-width: 900px) {
  .dash-grid {
    grid-template-columns: 1fr;
  }
}
</style>
