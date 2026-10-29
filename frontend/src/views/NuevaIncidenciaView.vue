<template>
  <AppNavbar />

  <div class="app-container">
    <!-- ── Cabecera de la vista ── -->
    <div class="view-header">
      <div>
        <router-link to="/incidencias" class="back-link">
          ← Volver a la bandeja
        </router-link>
        <h1 class="view-title">Registrar Nueva Incidencia</h1>
        <p class="view-subtitle">
          Completa los datos generales y el detalle técnico de la categoría. Los campos marcados con * son obligatorios.
        </p>
      </div>
    </div>

    <!-- Error Banner -->
    <div v-if="errorMessage" class="error-banner" role="alert">
      {{ errorMessage }}
    </div>

    <div class="form-layout">
      <!-- ── Columna Formulario ── -->
      <form @submit.prevent="handleSubmit" class="form-card" novalidate>
        
        <!-- 1. Selección de Categoría (Polimórfica) -->
        <div class="form-section">
          <label class="section-label">1. Categoría del reporte</label>
          <div class="cat-grid">
            <button
              type="button"
              v-for="cat in CATEGORIAS"
              :key="cat.id"
              class="cat-card"
              :class="{ 'cat-active': form.categoria === cat.id }"
              @click="seleccionarCategoria(cat.id)"
            >
              <div class="cat-header">
                <span class="cat-title">{{ cat.label }}</span>
                <span v-if="form.categoria === cat.id" class="check-pill">Seleccionado</span>
              </div>
              <span class="cat-desc">{{ cat.desc }}</span>
            </button>
          </div>
        </div>

        <!-- 2. Información General -->
        <div class="form-section">
          <label class="section-label">2. Información general</label>
          
          <div class="field">
            <label for="form-titulo">Título de la incidencia *</label>
            <input
              id="form-titulo"
              v-model="form.titulo"
              type="text"
              class="input-field"
              placeholder="Ej. Switch de laboratorio 3 sin enlace troncal"
              required
              minlength="5"
              maxlength="150"
            />
          </div>

          <div class="field">
            <label for="form-descripcion">Descripción detallada *</label>
            <textarea
              id="form-descripcion"
              v-model="form.descripcion"
              class="input-field textarea"
              rows="3"
              placeholder="Describe detalladamente los síntomas, fallas detectadas y el impacto actual..."
              required
              minlength="10"
            ></textarea>
          </div>

          <div class="field-grid-2">
            <div class="field">
              <label for="form-prioridad">Prioridad *</label>
              <select id="form-prioridad" v-model="form.prioridad" class="input-field" required>
                <option value="baja">Baja · No interrumpe actividades</option>
                <option value="media">Media · Afectación parcial</option>
                <option value="alta">Alta · Afecta clases o servicios</option>
                <option value="critica">Crítica · Paro total de infraestructura</option>
              </select>
            </div>

            <div class="field">
              <label for="form-tags">Etiquetas técnicas (separadas por coma)</label>
              <input
                id="form-tags"
                v-model="tagsInput"
                type="text"
                class="input-field"
                placeholder="redes, switch, fibra, cisco"
              />
            </div>
          </div>
        </div>

        <!-- 3. Ubicación en el Campus -->
        <div class="form-section">
          <label class="section-label">3. Ubicación en el Campus</label>
          <div class="field-grid-3">
            <div class="field">
              <label for="form-edificio">Edificio *</label>
              <select id="form-edificio" v-model="form.ubicacion.edificio" class="input-field" required>
                <option value="">Selecciona edificio...</option>
                <option v-for="ed in EDIFICIOS" :key="ed" :value="ed">{{ ed }}</option>
              </select>
            </div>

            <div class="field">
              <label for="form-zona">Zona / Aula / Espacio *</label>
              <input
                id="form-zona"
                v-model="form.ubicacion.zona"
                type="text"
                class="input-field"
                placeholder="Ej. Laboratorio D-204"
                required
                minlength="2"
              />
            </div>

            <div class="field">
              <label for="form-piso">Nivel / Piso</label>
              <input
                id="form-piso"
                v-model.number="form.ubicacion.piso"
                type="number"
                min="0"
                max="10"
                class="input-field"
                placeholder="1"
              />
            </div>
          </div>
        </div>

        <!-- 4. Detalle Específico Polimórfico ($jsonSchema) -->
        <div v-if="form.categoria" class="form-section polymorphic-section">
          <label class="section-label">
            4. Especificaciones técnicas (Detalle Polimórfico: {{ categoriaLabel }})
          </label>

          <!-- Caso A: Cómputo y Telecomunicaciones -->
          <div v-if="form.categoria === 'computo_redes'" class="poly-fields">
            <div class="field-grid-2">
              <div class="field">
                <label>Equipo o Dispositivo afectado *</label>
                <input
                  v-model="form.detalle.equipo_afectado"
                  type="text"
                  class="input-field"
                  placeholder="Ej. Switch Cisco Catalyst 2960"
                  required
                />
              </div>
              <div class="field">
                <label>Dirección IP asignada *</label>
                <input
                  v-model="form.detalle.direccion_ip"
                  type="text"
                  class="input-field"
                  placeholder="Ej. 192.168.10.15"
                  required
                  pattern="^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$"
                  title="Ingresa una IPv4 válida (ej. 192.168.1.10)"
                />
              </div>
            </div>

            <div class="field-grid-3">
              <div class="field">
                <label>VLAN (1 - 4094) *</label>
                <input
                  v-model.number="form.detalle.vlan"
                  type="number"
                  min="1"
                  max="4094"
                  class="input-field"
                  placeholder="100"
                  required
                />
              </div>
              <div class="field">
                <label>Puerto Uplink *</label>
                <input
                  v-model="form.detalle.puerto_uplink"
                  type="text"
                  class="input-field"
                  placeholder="Ej. Gi0/1 o Fa0/24"
                  required
                />
              </div>
              <div class="field">
                <label>Equipos afectados *</label>
                <input
                  v-model.number="form.detalle.equipos_afectados"
                  type="number"
                  min="0"
                  class="input-field"
                  placeholder="24"
                  required
                />
              </div>
            </div>
          </div>

          <!-- Caso B: Infraestructura Física -->
          <div v-if="form.categoria === 'infraestructura'" class="poly-fields">
            <div class="field-grid-2">
              <div class="field">
                <label>Tipo de daño detectado *</label>
                <input
                  v-model="form.detalle.tipo_dano"
                  type="text"
                  class="input-field"
                  placeholder="Ej. Filtración de agua en techo o falla de luminarias"
                  required
                />
              </div>
              <div class="field">
                <label>Insumos requeridos (separados por coma)</label>
                <input
                  v-model="insumosInput"
                  type="text"
                  class="input-field"
                  placeholder="Ej. Balastro LED 40W, cable uso rudo"
                />
              </div>
            </div>

            <div class="checkbox-box">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  v-model="form.detalle.riesgo_seguridad"
                />
                <span class="checkbox-text">
                  <strong>Representa un riesgo inmediato de seguridad física</strong>
                  <small>Marcar si existe riesgo eléctrico, fuga, riesgo de desplome o corte.</small>
                </span>
              </label>
            </div>

            <div class="sub-card">
              <span class="sub-title">Contratista externo asignado (Opcional)</span>
              <div class="field-grid-2">
                <div class="field">
                  <label>Empresa contratista</label>
                  <input
                    v-model="form.detalle.contratista_empresa"
                    type="text"
                    class="input-field"
                    placeholder="Ej. Servicios Eléctricos del Sureste S.A."
                  />
                </div>
                <div class="field">
                  <label>Tipo de intervención</label>
                  <input
                    v-model="form.detalle.contratista_intervencion"
                    type="text"
                    class="input-field"
                    placeholder="Ej. Mantenimiento mayor de subestación"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Caso C: Sistemas Académicos -->
          <div v-if="form.categoria === 'academico'" class="poly-fields">
            <div class="field-grid-2">
              <div class="field">
                <label>Plataforma o Sistema *</label>
                <input
                  v-model="form.detalle.plataforma"
                  type="text"
                  class="input-field"
                  placeholder="Ej. Saeko, Moodle UTM, Correo Institucional"
                  required
                />
              </div>
              <div class="field">
                <label>Código del curso o grupo *</label>
                <input
                  v-model="form.detalle.codigo_curso"
                  type="text"
                  class="input-field"
                  placeholder="Ej. TI-501 o RED-2026-A"
                  required
                />
              </div>
            </div>

            <div class="field-grid-2">
              <div class="field">
                <label>Periodo escolar *</label>
                <input
                  v-model="form.detalle.periodo_escolar"
                  type="text"
                  class="input-field"
                  placeholder="Ej. Enero - Abril 2026"
                  required
                />
              </div>
              <div class="field">
                <label>Estudiantes impactados *</label>
                <input
                  v-model.number="form.detalle.estudiantes_impactados"
                  type="number"
                  min="0"
                  class="input-field"
                  placeholder="35"
                  required
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Botones de Acción -->
        <div class="form-actions">
          <router-link to="/incidencias" class="btn btn-secondary">
            Cancelar
          </router-link>
          <button
            type="submit"
            class="btn btn-primary btn-submit-action"
            :disabled="loading"
          >
            <span v-if="loading" class="spinner-sm"></span>
            <span v-if="loading">Registrando…</span>
            <span v-else>Registrar Expediente</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import incidenciasApi from '../api/incidencias';
import AppNavbar from '../components/AppNavbar.vue';

const router = useRouter();
const auth = useAuthStore();

const loading = ref(false);
const errorMessage = ref('');
const tagsInput = ref('');
const insumosInput = ref('');

const CATEGORIAS = [
  { id: 'computo_redes', label: 'Cómputo y Telecom.', desc: 'Switches, enlaces, Wi-Fi, servidores y laboratorios' },
  { id: 'infraestructura', label: 'Infraestructura Física', desc: 'Edificios, clima, electricidad, techos y cerraduras' },
  { id: 'academico', label: 'Sistemas Académicos', desc: 'Saeko, calificaciones, plataformas LMS y correos' },
];

const EDIFICIOS = ['Edificio A', 'Edificio B', 'Edificio C', 'Edificio D', 'Biblioteca'];

const form = reactive({
  categoria: 'computo_redes',
  titulo: '',
  descripcion: '',
  prioridad: 'media',
  ubicacion: {
    edificio: '',
    zona: '',
    piso: 1,
  },
  detalle: {
    // computo
    equipo_afectado: '',
    direccion_ip: '',
    vlan: 10,
    puerto_uplink: '',
    equipos_afectados: 1,
    // infra
    tipo_dano: '',
    riesgo_seguridad: false,
    contratista_empresa: '',
    contratista_intervencion: '',
    // academico
    plataforma: '',
    codigo_curso: '',
    periodo_escolar: 'Sep-Dic 2026',
    estudiantes_impactados: 1,
  },
});

const categoriaLabel = computed(() => {
  const cat = CATEGORIAS.find(c => c.id === form.categoria);
  return cat ? cat.label : form.categoria;
});

function seleccionarCategoria(id) {
  form.categoria = id;
}


// Campo numérico vacío → null (la API responde 400 indicando el campo, en lugar de mandar 0)
function aNumero(v) {
  return v === '' || v === null || v === undefined ? null : Number(v);
}

async function handleSubmit() {
  errorMessage.value = '';
  loading.value = true;

  try {
    let detalle_especifico = {};

    if (form.categoria === 'computo_redes') {
      detalle_especifico = {
        equipo_afectado: form.detalle.equipo_afectado.trim(),
        direccion_ip: form.detalle.direccion_ip.trim(),
        vlan: aNumero(form.detalle.vlan),
        puerto_uplink: form.detalle.puerto_uplink.trim(),
        equipos_afectados: aNumero(form.detalle.equipos_afectados),
      };
    } else if (form.categoria === 'infraestructura') {
      detalle_especifico = {
        tipo_dano: form.detalle.tipo_dano.trim(),
        riesgo_seguridad: Boolean(form.detalle.riesgo_seguridad),
      };
      if (insumosInput.value.trim()) {
        detalle_especifico.insumos_requeridos = insumosInput.value
          .split(',')
          .map(s => s.trim())
          .filter(Boolean);
      }
      if (form.detalle.contratista_empresa.trim() && form.detalle.contratista_intervencion.trim()) {
        detalle_especifico.contratista = {
          empresa: form.detalle.contratista_empresa.trim(),
          intervencion: form.detalle.contratista_intervencion.trim(),
        };
      }
    } else if (form.categoria === 'academico') {
      detalle_especifico = {
        plataforma: form.detalle.plataforma.trim(),
        codigo_curso: form.detalle.codigo_curso.trim(),
        periodo_escolar: form.detalle.periodo_escolar.trim(),
        estudiantes_impactados: aNumero(form.detalle.estudiantes_impactados),
      };
    }

    const tags = tagsInput.value
      .split(',')
      .map(t => t.trim().toLowerCase())
      .filter(Boolean);

    const payload = {
      titulo: form.titulo.trim(),
      descripcion: form.descripcion.trim(),
      categoria: form.categoria,
      prioridad: form.prioridad,
      reportante: {
        usuario_id: auth.userId || '654321000000000000000001',
        nombre: auth.nombre,
        tipo: auth.tipo || 'administrativo',
        correo: auth.user?.correo || 'reportante@utm.example',
      },
      ubicacion: {
        edificio: form.ubicacion.edificio,
        zona: form.ubicacion.zona.trim(),
        piso: Number(form.ubicacion.piso) || 1,
      },
      tags: tags,
      detalle_especifico: detalle_especifico,
    };

    const res = await incidenciasApi.crear(payload);
    const nuevaId = res.data.id || res.data._id;
    router.push(`/incidencias/${nuevaId}`);
  } catch (err) {
    // Mostrar el código HTTP que devuelve la API (p. ej. 400 cuando falla la validación)
    const status = err.response?.status;
    const detalle = err.response?.data?.detail || err.message || 'Error al registrar la incidencia.';
    errorMessage.value = status ? `Error ${status} · ${detalle}` : detalle;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.view-header {
  margin-bottom: 1.5rem;
}
.back-link {
  display: inline-flex;
  align-items: center;
  font-size: 0.82rem;
  color: var(--color-primary);
  font-weight: 500;
  margin-bottom: 0.5rem;
}
.back-link:hover { text-decoration: underline; }

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

.error-banner {
  background: #FEE2E2;
  color: #991B1B;
  padding: 0.85rem 1.1rem;
  border-radius: var(--radius-md);
  font-size: 0.84rem;
  margin-bottom: 1.25rem;
  border: 1px solid #FCA5A5;
}

.form-layout {
  display: grid;
  max-width: 860px;
  grid-template-columns: 1fr;
  gap: 1.5rem;
  align-items: flex-start;
}

.form-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  box-shadow: var(--shadow-sm);
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.section-label {
  font-size: 0.82rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-primary);
  padding-bottom: 0.35rem;
  border-bottom: 1px solid var(--border-subtle);
}

.cat-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.6rem;
}

.cat-card {
  padding: 0.85rem 1rem;
  background: var(--bg-surface-muted);
  border: 1.5px solid var(--border-medium);
  border-radius: var(--radius-md);
  text-align: left;
  transition: all var(--transition-fast);
  cursor: pointer;
}
.cat-card:hover {
  border-color: var(--color-primary);
  background: var(--bg-surface);
}
.cat-active {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.cat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}
.cat-title {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-main);
}
.check-pill {
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--color-primary);
  background: #fff;
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-full);
}
.cat-desc {
  font-size: 0.78rem;
  color: var(--text-secondary);
  line-height: 1.35;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.field label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-secondary);
}
.textarea {
  resize: vertical;
  min-height: 75px;
}

.field-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.85rem;
}

.field-grid-3 {
  display: grid;
  grid-template-columns: 1.2fr 1.2fr 0.6fr;
  gap: 0.85rem;
}

.polymorphic-section {
  background: var(--bg-app);
  padding: 1.1rem;
  border-radius: var(--radius-md);
  border: 1px dashed var(--color-primary-border);
}

.poly-fields {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.checkbox-box {
  padding: 0.65rem 0.85rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  cursor: pointer;
}
.checkbox-text {
  display: flex;
  flex-direction: column;
  font-size: 0.82rem;
  line-height: 1.3;
}
.checkbox-text small {
  color: var(--text-tertiary);
  margin-top: 0.15rem;
}

.sub-card {
  padding: 0.85rem;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}
.sub-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-secondary);
  text-transform: uppercase;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-subtle);
}

.btn-submit-action {
  gap: 0.5rem;
  min-width: 170px;
}

/* ── Panel de Preview BSON ── */
.preview-panel {
  background: #0F172A;
  border: 1px solid #1E293B;
  border-radius: var(--radius-md);
  padding: 1.25rem;
  color: #E2E8F0;
  position: sticky;
  top: 80px;
  /* Altura fija: no crece con el contenido */
  max-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.75rem;
  margin-bottom: 0.85rem;
  border-bottom: 1px solid #334155;
}

.preview-title-box {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.preview-badge {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  font-weight: 700;
  color: #38BDF8;
}

.preview-sub {
  font-size: 0.7rem;
  color: #94A3B8;
}

.json-code {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  line-height: 1.45;
  color: #A5F3FC;
  /* Scroll interno — el panel no se expande */
  flex: 1;
  overflow-x: auto;
  overflow-y: auto;
  margin: 0;
  /* Scrollbar discreta para tema oscuro */
  scrollbar-width: thin;
  scrollbar-color: #334155 transparent;
}
.json-code::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}
.json-code::-webkit-scrollbar-track { background: transparent; }
.json-code::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 99px;
}

@media (max-width: 900px) {
  .form-layout {
    grid-template-columns: 1fr;
  }
  .preview-panel {
    position: static;
  }
}
</style>
