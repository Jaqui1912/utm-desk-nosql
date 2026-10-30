import api from './axios';

const BASE = '/incidencias';

export const incidenciasApi = {
  /**
   * CU listar: GET /incidencias/ con filtros
   */
  listar({ categoria, estado, edificio, asignadas_a_mi, limit = 25, skip = 0 } = {}) {
    const params = { limit, skip };
    if (categoria) params.categoria = categoria;
    if (estado) params.estado = estado;
    if (edificio) params.edificio = edificio;
    if (asignadas_a_mi) params.asignadas_a_mi = true;
    return api.get(BASE + '/', { params });
  },

  /**
   * CU-05: GET /incidencias/buscar?q=termino — búsqueda textual ponderada
   */
  buscar(q, limite = 25) {
    return api.get(BASE + '/buscar', { params: { q, limite } });
  },

  /**
   * GET /incidencias/conteos-estado — conteo agrupado por estado (para pills)
   * No aplica filtro de estado; devuelve { estado: count } para todos los estados.
   */
  conteosPorEstado({ categoria, edificio, asignadas_a_mi } = {}) {
    const params = {};
    if (categoria) params.categoria = categoria;
    if (edificio) params.edificio = edificio;
    if (asignadas_a_mi) params.asignadas_a_mi = true;
    return api.get(BASE + '/conteos-estado', { params });
  },

  /**
   * GET /incidencias/:id — obtener un expediente completo
   */
  obtener(id) {
    return api.get(`${BASE}/${id}`);
  },

  /**
   * CU-01: POST /incidencias/ — registrar incidencia polimórfica
   */
  crear(payload) {
    return api.post(BASE + '/', payload);
  },

  /**
   * RF-13: PATCH /incidencias/:id/asignar-tecnico
   */
  asignarTecnico(id, tecnico_id) {
    return api.patch(`${BASE}/${id}/asignar-tecnico`, { tecnico_id });
  },

  /**
   * CU-03: PATCH /incidencias/:id/estado — operación atómica
   */
  actualizarEstado(id, payload) {
    return api.patch(`${BASE}/${id}/estado`, payload);
  },

  /**
   * CU-02: POST /incidencias/:id/evidencias — adjuntar metadatos de archivos
   */
  cargarEvidencia(id, payload) {
    return api.post(`${BASE}/${id}/evidencias`, payload);
  },

  /**
   * CU-02: POST /incidencias/:id/evidencias/archivo — sube el archivo al bucket (multipart)
   */
  subirEvidencia(id, archivo) {
    const datos = new FormData();
    datos.append('archivo', archivo);
    return api.post(`${BASE}/${id}/evidencias/archivo`, datos, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
  },

  /**
   * CU-02: GET /incidencias/:id/evidencias/:indice/url — URL firmada temporal
   */
  urlEvidencia(id, indice) {
    return api.get(`${BASE}/${id}/evidencias/${indice}/url`);
  },

  /**
   * CU-02: DELETE /incidencias/:id/evidencias/:indice — eliminar una evidencia
   */
  eliminarEvidencia(id, indice) {
    return api.delete(`${BASE}/${id}/evidencias/${indice}`);
  },

  /**
   * CU-04: PATCH /incidencias/:id/tags — gestionar etiquetas
   */
  gestionarTags(id, accion, tags) {
    return api.patch(`${BASE}/${id}/tags`, { accion, tags });
  },

  /**
   * CU-06: GET /incidencias/analitica — pipelines directivos
   */
  analitica() {
    return api.get(BASE + '/analitica');
  },
};

export default incidenciasApi;
