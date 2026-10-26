<template>
  <AppNavbar />

  <div class="app-container">
    <!-- Estado de carga -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Cargando expediente de la incidencia...</span>
    </div>

    <!-- Error al cargar -->
    <div v-else-if="error" class="error-banner">
      {{ error }}
      <div style="margin-top: 0.75rem;">
        <router-link to="/incidencias" class="btn btn-secondary btn-sm">Volver a la bandeja</router-link>
      </div>
    </div>

    <!-- Vista Principal del Expediente -->
    <div v-else-if="incidencia" class="expediente-wrapper">
      
      <!-- ── Cabecera del Expediente ── -->
      <div class="exp-header">
        <div class="header-breadcrumb">
          <router-link to="/incidencias" class="back-link">
            ← Volver a incidencias
          </router-link>
          <span class="breadcrumb-sep">/</span>
          <span class="inc-code">{{ incidencia.codigo }}</span>
        </div>

        <div class="header-main-row">
          <div class="title-area">
            <h1 class="inc-title">{{ incidencia.titulo }}</h1>
            <div class="badges-row">
              <span class="badge" :style="estadoCss(incidencia.estado)">
                {{ cap(incidencia.estado) }}
              </span>
              <span class="badge" :style="prioCss(incidencia.prioridad)">
                Prioridad {{ cap(incidencia.prioridad) }}
              </span>
              <span class="cat-pill">
                {{ catLabel(incidencia.categoria) }}
              </span>
            </div>
          </div>

          <div class="header-actions">
            <button @click="showJson = !showJson" class="btn btn-secondary btn-sm">
              {{ showJson ? 'Ocultar documento BSON' : '{ } Ver documento BSON' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Alerta TTL si la incidencia está resuelta -->
      <div v-if="incidencia.fecha_resolucion" class="ttl-banner">
        <span class="ttl-icon">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        </span>
        <div class="ttl-text">
          <strong>Índice TTL activo (60 días de retención):</strong>
          Resolución registrada el {{ formatDateTime(incidencia.fecha_resolucion) }}.
          MongoDB Atlas depurará automáticamente este documento una vez transcurridos 60 días naturales.
        </div>
      </div>

      <!-- ── Visor de Documento JSON / BSON Modal o Expandible ── -->
      <div v-if="showJson" class="bson-panel">
        <div class="bson-header">
          <span class="bson-title">db.incidencias_campus.findOne({ codigo: "{{ incidencia.codigo }}" })</span>
          <button @click="showJson = false" class="close-btn">×</button>
        </div>
        <pre class="bson-content"><code>{{ JSON.stringify(incidencia, null, 2) }}</code></pre>
      </div>

      <!-- ── Contenido en 2 Columnas ── -->
      <div class="exp-grid">
        
        <!-- ── Columna Izquierda: Información y Bitácora ── -->
        <div class="col-main">

          <!-- Descripción -->
          <div class="card section-card">
            <h2 class="section-title">Descripción del reporte</h2>
            <p class="desc-text">{{ incidencia.descripcion }}</p>
          </div>

          <!-- Especificaciones Polimórficas -->
          <div class="card section-card">
            <h2 class="section-title">Detalle Polimórfico ({{ catLabel(incidencia.categoria) }})</h2>
            
            <div class="detalle-grid">
              <!-- Cómputo y Redes -->
              <template v-if="incidencia.categoria === 'computo_redes'">
                <div class="detail-item">
                  <span class="detail-label">Equipo afectado</span>
                  <span class="detail-val font-mono">{{ incidencia.detalle_especifico?.equipo_afectado || '—' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Dirección IP</span>
                  <span class="detail-val font-mono">{{ incidencia.detalle_especifico?.direccion_ip || '—' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">VLAN</span>
                  <span class="detail-val font-mono">{{ incidencia.detalle_especifico?.vlan || '—' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Puerto Uplink</span>
                  <span class="detail-val font-mono">{{ incidencia.detalle_especifico?.puerto_uplink || '—' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Equipos afectados</span>
                  <span class="detail-val">{{ incidencia.detalle_especifico?.equipos_afectados ?? '—' }}</span>
                </div>
              </template>

              <!-- Infraestructura -->
              <template v-else-if="incidencia.categoria === 'infraestructura'">
                <div class="detail-item full-width">
                  <span class="detail-label">Tipo de daño</span>
                  <span class="detail-val">{{ incidencia.detalle_especifico?.tipo_dano || '—' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Riesgo de seguridad</span>
                  <span class="detail-val">
                    <span v-if="incidencia.detalle_especifico?.riesgo_seguridad" class="danger-pill">Sí · Riesgo Inmediato</span>
                    <span v-else class="ok-pill">No</span>
                  </span>
                </div>
                <div class="detail-item full-width" v-if="incidencia.detalle_especifico?.insumos_requeridos?.length">
                  <span class="detail-label">Insumos requeridos</span>
                  <div class="insumos-tags">
                    <span v-for="insumo in incidencia.detalle_especifico.insumos_requeridos" :key="insumo" class="insumo-tag">
                      {{ insumo }}
                    </span>
                  </div>
                </div>
                <div class="detail-item full-width" v-if="incidencia.detalle_especifico?.contratista">
                  <span class="detail-label">Contratista asignado</span>
                  <span class="detail-val">
                    {{ incidencia.detalle_especifico.contratista.empresa }} · {{ incidencia.detalle_especifico.contratista.intervencion }}
                  </span>
                </div>
              </template>

              <!-- Académico -->
              <template v-else-if="incidencia.categoria === 'academico'">
                <div class="detail-item">
                  <span class="detail-label">Plataforma</span>
                  <span class="detail-val font-mono">{{ incidencia.detalle_especifico?.plataforma || '—' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Código de curso</span>
                  <span class="detail-val font-mono">{{ incidencia.detalle_especifico?.codigo_curso || '—' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Periodo escolar</span>
                  <span class="detail-val">{{ incidencia.detalle_especifico?.periodo_escolar || '—' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Estudiantes impactados</span>
                  <span class="detail-val">{{ incidencia.detalle_especifico?.estudiantes_impactados ?? '—' }}</span>
                </div>
              </template>
            </div>
          </div>

          <!-- Historial de Seguimiento / Bitácora Atómica -->
          <div class="card section-card">
            <div class="section-header-flex">
              <h2 class="section-title">
                Historial de seguimiento ({{ incidencia.historial_seguimiento?.length || 0 }})
              </h2>
            </div>

            <!-- Lista cronológica -->
            <div v-if="incidencia.historial_seguimiento?.length === 0" class="empty-inline">
              Aún no se han registrado bitácoras de avance para esta incidencia.
            </div>
            
            <div v-else class="timeline">
              <div
                v-for="(h, idx) in sortedHistorial"
                :key="idx"
                class="timeline-item"
              >
                <div class="timeline-dot"></div>
                <div class="timeline-body">
                  <div class="timeline-header">
                    <span class="timeline-user">{{ h.tecnico }}</span>
                    <span class="badge" :style="estadoCss(h.estado)">{{ cap(h.estado) }}</span>
                    <span class="timeline-hours">+{{ h.horas }} h</span>
                    <span class="timeline-date">{{ formatDateTime(h.fecha) }}</span>
                  </div>
                  <p class="timeline-comment">{{ h.comentario }}</p>
                </div>
              </div>
            </div>

            <!-- Formulario de actualización atómica (si tiene permiso) -->
            <div v-if="canActualizar && esEstadoAbierto" class="update-box">
              <h3 class="update-title">Registrar nuevo avance técnico</h3>
              
              <div v-if="updateError" class="error-banner-inline">
                {{ updateError }}
              </div>

              <form @submit.prevent="handleActualizarEstado" class="update-form">
                <div class="update-fields-grid">
                  <div class="field">
                    <label>Nuevo Estado</label>
                    <select v-model="formAvance.nuevo_estado" class="input-field" required>
                      <option value="en proceso">En proceso</option>
                      <option value="en espera">En espera (esperando refacción/insumo)</option>
                      <option value="resuelta">Resuelta (concluido)</option>
                      <option value="cerrada">Cerrada</option>
                    </select>
                  </div>

                  <div class="field">
                    <label>Horas dedicadas en este avance</label>
                    <input
                      v-model.number="formAvance.horas"
                      type="number"
                      min="0"
                      step="0.5"
                      class="input-field"
                      placeholder="Ej. 1.5"
                      required
                    />
                  </div>
                </div>

                <div class="field">
                  <label>Bitácora técnica / Comentario de la intervención *</label>
                  <textarea
                    v-model="formAvance.comentario"
                    class="input-field textarea"
                    rows="2"
                    placeholder="Describe las acciones realizadas, piezas reemplazadas o estado actual..."
                    required
                    minlength="5"
                  ></textarea>
                </div>

                <button
                  type="submit"
                  class="btn btn-primary btn-sm"
                  :disabled="updatingState"
                >
                  <span v-if="updatingState">Guardando avance…</span>
                  <span v-else>Guardar Avance Atómico</span>
                </button>
              </form>
            </div>
            <div v-else-if="!esEstadoAbierto" class="closed-notice">
              Esta incidencia se encuentra <strong>{{ incidencia.estado }}</strong>. El expediente está congelado.
            </div>
          </div>

          <!-- Evidencias Adjuntas -->
          <div class="card section-card">
            <div class="section-header-flex">
              <h2 class="section-title">
                Evidencias adjuntas ({{ incidencia.evidencias_adjuntas?.length || 0 }})
              </h2>
            </div>

            <div v-if="incidencia.evidencias_adjuntas?.length === 0" class="empty-inline">
              Sin evidencias multimedia adjuntas.
            </div>

            <div v-else class="evidencias-list">
              <div
                v-for="(ev, idx) in incidencia.evidencias_adjuntas"
                :key="idx"
                class="evidencia-row"
              >
                <div class="ev-info">
                  <span class="ev-name font-mono">{{ ev.nombre_archivo }}</span>
                  <span class="ev-meta">
                    {{ ev.tipo_mime }} · {{ ev.peso_kb }} KB · {{ formatDate(ev.fecha_carga) }}
                  </span>
                </div>
                <a
                  :href="ev.url_storage"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="btn btn-secondary btn-sm"
                >
                  Ver archivo ↗
                </a>
              </div>
            </div>

            <!-- Formulario para adjuntar evidencia -->
            <div v-if="canEvidencias" class="add-evidencia-box">
              <h3 class="update-title">Adjuntar evidencia al expediente</h3>
              
              <div v-if="evidenciaError" class="error-banner-inline">
                {{ evidenciaError }}
              </div>

              <form @submit.prevent="handleAdjuntarEvidencia" class="evidencia-form">
                <div class="field-grid-3">
                  <div class="field">
                    <label>Nombre del archivo</label>
                    <input
                      v-model="formEvidencia.nombre_archivo"
                      type="text"
                      class="input-field"
                      placeholder="foto_switch_danado.jpg"
                      required
                    />
                  </div>
                  <div class="field">
                    <label>Tipo MIME</label>
                    <select v-model="formEvidencia.tipo_mime" class="input-field" required>
                      <option value="image/jpeg">image/jpeg</option>
                      <option value="image/png">image/png</option>
                      <option value="application/pdf">application/pdf</option>
                      <option value="video/mp4">video/mp4</option>
                    </select>
                  </div>
                  <div class="field">
                    <label>Tamaño (KB)</label>
                    <input
                      v-model.number="formEvidencia.peso_kb"
                      type="number"
                      min="1"
                      class="input-field"
                      placeholder="1024"
                      required
                    />
                  </div>
                </div>

                <div class="field">
                  <label>URL Storage (Supabase / S3)</label>
                  <input
                    v-model="formEvidencia.url_storage"
                    type="url"
                    class="input-field"
                    placeholder="https://storage.utm.example/incidencias/foto_switch_danado.jpg"
                    required
                  />
                </div>

                <button
                  type="submit"
                  class="btn btn-secondary btn-sm"
                  :disabled="uploadingEvidencia"
                >
                  <span v-if="uploadingEvidencia">Adjuntando…</span>
                  <span v-else>+ Registrar Evidencia</span>
                </button>
              </form>
            </div>
          </div>

        </div>

        <!-- ── Columna Derecha: Metadatos y Asignación ── -->
        <div class="col-side">

          <!-- Ficha de Datos Generales -->
          <div class="card meta-card">
            <h3 class="side-card-title">Datos del expediente</h3>

            <div class="meta-row">
              <span class="meta-label">Reportante</span>
              <div class="meta-val-box">
                <span class="meta-val-bold">{{ incidencia.reportante?.nombre }}</span>
                <span class="meta-sub">{{ incidencia.reportante?.correo }} ({{ incidencia.reportante?.tipo }})</span>
              </div>
            </div>

            <div class="meta-row">
              <span class="meta-label">Ubicación</span>
              <div class="meta-val-box">
                <span class="meta-val-bold">{{ incidencia.ubicacion?.edificio }}</span>
                <span class="meta-sub">{{ incidencia.ubicacion?.zona }} · Piso {{ incidencia.ubicacion?.piso ?? 1 }}</span>
              </div>
            </div>

            <div class="meta-row">
              <span class="meta-label">Fecha de apertura</span>
              <span class="meta-val">{{ formatDateTime(incidencia.fecha_creacion) }}</span>
            </div>

            <div class="meta-row">
              <span class="meta-label">Horas acumuladas</span>
              <span class="meta-val font-mono">{{ incidencia.horas_invertidas || 0 }} h</span>
            </div>

            <div class="meta-row">
              <span class="meta-label">Técnico asignado</span>
              <div class="meta-val-box">
                <span class="meta-val-bold">
                  {{ incidencia.tecnico_asignado ? incidencia.tecnico_asignado.nombre : 'Sin asignar' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Asignación de Técnico (Solo Admin General) -->
          <div v-if="auth.can('asignar')" class="card meta-card">
            <h3 class="side-card-title">Asignar Técnico Responsable</h3>
            
            <div v-if="assignError" class="error-banner-inline">
              {{ assignError }}
            </div>

            <div class="assign-form">
              <select v-model="selectedTecnicoId" class="input-field" required>
                <option value="">Selecciona un técnico...</option>
                <option
                  v-for="t in TECNICOS_DEFAULT"
                  :key="t.id"
                  :value="t.id"
                >
                  {{ t.nombre }} ({{ t.especialidad }})
                </option>
              </select>

              <button
                @click="handleAsignarTecnico"
                class="btn btn-primary btn-sm"
                :disabled="!selectedTecnicoId || assigningTecnico"
                style="width: 100%; margin-top: 0.5rem;"
              >
                <span v-if="assigningTecnico">Asignando…</span>
                <span v-else>Asignar Técnico</span>
              </button>
            </div>
          </div>

          <!-- Gestión de Etiquetas Técnicas ($addToSet / $pull) -->
          <div class="card meta-card">
            <h3 class="side-card-title">Etiquetas Técnicas</h3>
            
            <div class="tags-container">
              <span
                v-for="tag in (incidencia.tags || [])"
                :key="tag"
                class="tag-badge"
              >
                {{ tag }}
                <button
                  v-if="canTags"
                  @click="handleEliminarTag(tag)"
                  class="tag-remove-btn"
                  title="Eliminar etiqueta"
                >
                  ×
                </button>
              </span>
              <span v-if="!incidencia.tags?.length" class="empty-inline">
                Sin etiquetas asignadas.
              </span>
            </div>

            <!-- Input para agregar etiqueta -->
            <div v-if="canTags" class="add-tag-box">
              <input
                v-model="nuevoTagInput"
                type="text"
                class="input-field input-sm"
                placeholder="Nueva etiqueta..."
                @keyup.enter="handleAgregarTag"
              />
              <button
                @click="handleAgregarTag"
                class="btn btn-secondary btn-sm"
                :disabled="!nuevoTagInput.trim()"
              >
                +
              </button>
            </div>
          </div>

        </div>

      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import incidenciasApi from '../api/incidencias';
import AppNavbar from '../components/AppNavbar.vue';

const route = useRoute();
const auth = useAuthStore();

const loading = ref(true);
const error = ref('');
const incidencia = ref(null);
const showJson = ref(false);

// Operaciones en curso
const updatingState = ref(false);
const updateError = ref('');
const uploadingEvidencia = ref(false);
const evidenciaError = ref('');
const assigningTecnico = ref(false);
const assignError = ref('');

// Estados de formularios
const formAvance = ref({
  nuevo_estado: 'en proceso',
  horas: 1,
  comentario: '',
});

const formEvidencia = ref({
  nombre_archivo: '',
  tipo_mime: 'image/jpeg',
  peso_kb: 512,
  url_storage: '',
});

const nuevoTagInput = ref('');
const selectedTecnicoId = ref('');

// Lista de técnicos del sistema
const TECNICOS_DEFAULT = [
  { id: '6710a1b2c3d4e5f607182945', nombre: 'Carlos Pech', especialidad: 'Cómputo e Infraestructura' },
  { id: '6710a1b2c3d4e5f607182946', nombre: 'Jorge Cauich', especialidad: 'Infraestructura Física' },
  { id: '6710a1b2c3d4e5f607182947', nombre: 'Diana Euán', especialidad: 'Académico y Cómputo' },
];

// Permisos
const canActualizar = computed(() => auth.can('actualizar_estado'));
const canEvidencias = computed(() => auth.can('evidencias'));
const canTags = computed(() => auth.can('tags'));

const esEstadoAbierto = computed(() => {
  return ['abierta', 'en proceso', 'en espera'].includes(incidencia.value?.estado);
});

const sortedHistorial = computed(() => {
  if (!incidencia.value?.historial_seguimiento) return [];
  return [...incidencia.value.historial_seguimiento].reverse();
});

// Utilidades de formato
function cap(s) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
}
function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' });
}
function formatDateTime(d) {
  if (!d) return '—';
  return new Date(d).toLocaleString('es-MX', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
function catLabel(c) {
  const map = {
    computo_redes: 'Cómputo y Telecomunicaciones',
    infraestructura: 'Infraestructura Física',
    academico: 'Sistemas Académicos',
  };
  return map[c] || c;
}

function estadoCss(e) {
  const map = {
    abierta: { background: 'var(--est-abierta-bg)', color: 'var(--est-abierta-text)' },
    'en proceso': { background: 'var(--est-proceso-bg)', color: 'var(--est-proceso-text)' },
    'en espera': { background: 'var(--est-espera-bg)', color: 'var(--est-espera-text)' },
    resuelta: { background: 'var(--est-resuelta-bg)', color: 'var(--est-resuelta-text)' },
    cerrada: { background: 'var(--est-cerrada-bg)', color: 'var(--est-cerrada-text)' },
  };
  return map[e] || {};
}

function prioCss(p) {
  const map = {
    baja: { background: 'var(--prio-baja-bg)', color: 'var(--prio-baja-text)' },
    media: { background: 'var(--prio-media-bg)', color: 'var(--prio-media-text)' },
    alta: { background: 'var(--prio-alta-bg)', color: 'var(--prio-alta-text)' },
    critica: { background: 'var(--prio-critica-bg)', color: 'var(--prio-critica-text)' },
  };
  return map[p] || {};
}

async function cargarExpediente() {
  loading.value = true;
  error.value = '';
  try {
    const res = await incidenciasApi.obtener(route.params.id);
    incidencia.value = res.data;
    if (res.data.tecnico_asignado?.usuario_id) {
      selectedTecnicoId.value = res.data.tecnico_asignado.usuario_id;
    }
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Error al obtener el expediente.';
  } finally {
    loading.value = false;
  }
}

// CU-03: Actualizar Estado
async function handleActualizarEstado() {
  updateError.value = '';
  updatingState.value = true;
  try {
    const payload = {
      nuevo_estado: formAvance.value.nuevo_estado,
      horas: Number(formAvance.value.horas),
      comentario: formAvance.value.comentario.trim(),
      tecnico: auth.nombre,
    };
    const res = await incidenciasApi.actualizarEstado(incidencia.value._id || incidencia.value.id, payload);
    incidencia.value = res.data;
    formAvance.value.comentario = '';
    formAvance.value.horas = 1;
  } catch (err) {
    updateError.value = err.response?.data?.detail || err.message || 'Error al actualizar estado.';
  } finally {
    updatingState.value = false;
  }
}

// RF-13: Asignar Técnico
async function handleAsignarTecnico() {
  assignError.value = '';
  assigningTecnico.value = true;
  try {
    const res = await incidenciasApi.asignarTecnico(incidencia.value._id || incidencia.value.id, selectedTecnicoId.value);
    incidencia.value = res.data;
  } catch (err) {
    assignError.value = err.response?.data?.detail || err.message || 'Error al asignar técnico.';
  } finally {
    assigningTecnico.value = false;
  }
}

// CU-02: Adjuntar Evidencia
async function handleAdjuntarEvidencia() {
  evidenciaError.value = '';
  uploadingEvidencia.value = true;
  try {
    const payload = {
      nombre_archivo: formEvidencia.value.nombre_archivo.trim(),
      tipo_mime: formEvidencia.value.tipo_mime,
      peso_kb: Number(formEvidencia.value.peso_kb),
      url_storage: formEvidencia.value.url_storage.trim(),
    };
    const res = await incidenciasApi.cargarEvidencia(incidencia.value._id || incidencia.value.id, payload);
    incidencia.value = res.data;
    formEvidencia.value.nombre_archivo = '';
    formEvidencia.value.url_storage = '';
  } catch (err) {
    evidenciaError.value = err.response?.data?.detail || err.message || 'Error al adjuntar evidencia.';
  } finally {
    uploadingEvidencia.value = false;
  }
}

// CU-04: Tags
async function handleAgregarTag() {
  const tag = nuevoTagInput.value.trim().toLowerCase();
  if (!tag) return;
  try {
    const res = await incidenciasApi.gestionarTags(incidencia.value._id || incidencia.value.id, 'agregar', [tag]);
    incidencia.value = res.data;
    nuevoTagInput.value = '';
  } catch (err) {
    console.error('Error al agregar tag:', err);
  }
}

async function handleEliminarTag(tag) {
  try {
    const res = await incidenciasApi.gestionarTags(incidencia.value._id || incidencia.value.id, 'quitar', [tag]);
    incidencia.value = res.data;
  } catch (err) {
    console.error('Error al quitar tag:', err);
  }
}

onMounted(cargarExpediente);
</script>

<style scoped>
.expediente-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* Cabecera */
.header-breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  margin-bottom: 0.4rem;
}
.back-link {
  color: var(--color-primary);
  font-weight: 500;
}
.breadcrumb-sep { color: var(--border-medium); }
.inc-code {
  font-family: var(--font-mono);
  font-weight: 600;
  color: var(--text-tertiary);
}

.header-main-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}
.title-area {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.inc-title {
  font-size: 1.55rem;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: -0.02em;
  line-height: 1.25;
}
.badges-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.cat-pill {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  background: var(--bg-surface-muted);
  padding: 0.2rem 0.6rem;
  border-radius: var(--radius-full);
}

/* Banner TTL */
.ttl-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #FFFBEB;
  border: 1px solid #FCD34D;
  color: #92400E;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  font-size: 0.82rem;
}
.ttl-icon {
  display: flex;
  align-items: center;
}

/* BSON Panel */
.bson-panel {
  background: #0F172A;
  border: 1px solid #1E293B;
  border-radius: var(--radius-md);
  padding: 1rem 1.25rem;
  color: #38BDF8;
}
.bson-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.65rem;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: #94A3B8;
}
.close-btn {
  color: #94A3B8;
  font-size: 1.1rem;
}
.close-btn:hover { color: #fff; }
.bson-content {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  line-height: 1.45;
  color: #A5F3FC;
  max-height: 400px;
  overflow: auto;
}

/* Grid de Contenido */
.exp-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 1.25rem;
  align-items: flex-start;
}

.col-main {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.col-side {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  box-shadow: var(--shadow-sm);
}

.section-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 0.85rem;
}
.desc-text {
  font-size: 0.88rem;
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
}

/* Detalle Polimórfico */
.detalle-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.85rem;
}
.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.detail-item.full-width {
  grid-column: 1 / -1;
}
.detail-label {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-tertiary);
}
.detail-val {
  font-size: 0.85rem;
  color: var(--text-main);
}
.font-mono {
  font-family: var(--font-mono);
}
.danger-pill {
  font-size: 0.72rem;
  font-weight: 700;
  background: #FEE2E2;
  color: #DC2626;
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-full);
}
.ok-pill {
  font-size: 0.72rem;
  font-weight: 600;
  background: #E3F1EA;
  color: var(--color-primary);
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-full);
}
.insumos-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: 0.25rem;
}
.insumo-tag {
  background: var(--bg-surface-muted);
  border: 1px solid var(--border-medium);
  font-size: 0.75rem;
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-sm);
}

/* Timeline */
.timeline {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  border-left: 2px solid var(--border-subtle);
  margin-left: 0.5rem;
  padding-left: 1rem;
  margin-bottom: 1.25rem;
}
.timeline-item {
  position: relative;
}
.timeline-dot {
  position: absolute;
  left: calc(-1rem - 5px);
  top: 4px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
}
.timeline-body {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.timeline-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.timeline-user {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-main);
}
.timeline-hours {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-primary);
}
.timeline-date {
  font-size: 0.72rem;
  color: var(--text-tertiary);
  margin-left: auto;
}
.timeline-comment {
  font-size: 0.82rem;
  color: var(--text-secondary);
  line-height: 1.45;
}

/* Actualización Atómica */
.update-box {
  background: var(--bg-app);
  padding: 1rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}
.update-title {
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-primary);
  margin-bottom: 0.75rem;
}
.update-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.update-fields-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}
.closed-notice {
  font-size: 0.82rem;
  color: var(--text-tertiary);
  padding: 0.5rem;
  background: var(--bg-surface-muted);
  border-radius: var(--radius-sm);
}

/* Evidencias */
.evidencias-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}
.evidencia-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.65rem 0.85rem;
  background: var(--bg-surface-muted);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
}
.ev-info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.ev-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-main);
}
.ev-meta {
  font-size: 0.7rem;
  color: var(--text-tertiary);
}

.add-evidencia-box {
  background: var(--bg-app);
  padding: 1rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
}
.evidencia-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* Columna Lateral (Metadata) */
.side-card-title {
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-tertiary);
  margin-bottom: 0.85rem;
}
.meta-row {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding-bottom: 0.65rem;
  margin-bottom: 0.65rem;
  border-bottom: 1px solid var(--border-subtle);
}
.meta-row:last-child {
  padding-bottom: 0;
  margin-bottom: 0;
  border-bottom: none;
}
.meta-label {
  font-size: 0.72rem;
  color: var(--text-tertiary);
}
.meta-val {
  font-size: 0.82rem;
  color: var(--text-main);
}
.meta-val-bold {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--text-main);
}
.meta-sub {
  font-size: 0.72rem;
  color: var(--text-secondary);
}

/* Tags */
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-bottom: 0.75rem;
}
.tag-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: var(--bg-surface-muted);
  border: 1px solid var(--border-medium);
  font-size: 0.75rem;
  padding: 0.2rem 0.55rem;
  border-radius: var(--radius-full);
}
.tag-remove-btn {
  font-size: 0.9rem;
  color: var(--text-tertiary);
  line-height: 1;
}
.tag-remove-btn:hover { color: #DC2626; }
.add-tag-box {
  display: flex;
  gap: 0.35rem;
}
.input-sm {
  font-size: 0.78rem;
  padding: 0.35rem 0.6rem;
}

/* Common */
.empty-inline {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  font-style: italic;
}
.error-banner-inline {
  background: #FEE2E2;
  color: #991B1B;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-sm);
  font-size: 0.78rem;
  margin-bottom: 0.65rem;
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
  .exp-grid {
    grid-template-columns: 1fr;
  }
}
</style>
