import api from './axios';

/**
 * Dispara la descarga en el navegador a partir de datos Blob/JSON
 */
function descargarBlob(data, nombreArchivo) {
  const blob = data instanceof Blob ? data : new Blob([data], { type: 'application/json' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', nombreArchivo);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export const exportarApi = {
  /**
   * Descarga usuarios.json desde MongoDB Atlas
   */
  async exportarUsuarios() {
    const res = await api.get('/admin/exportar/usuarios', { responseType: 'blob' });
    descargarBlob(res.data, 'usuarios.json');
  },

  /**
   * Descarga incidencias_campus.json desde MongoDB Atlas
   */
  async exportarIncidencias() {
    const res = await api.get('/admin/exportar/incidencias', { responseType: 'blob' });
    descargarBlob(res.data, 'incidencias_campus.json');
  },

  /**
   * Descarga esquema_y_indices.json ($jsonSchema e índices vigentes)
   */
  async exportarEsquema() {
    const res = await api.get('/admin/exportar/esquema', { responseType: 'blob' });
    descargarBlob(res.data, 'esquema_y_indices.json');
  },
};

export default exportarApi;
