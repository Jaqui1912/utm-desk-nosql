import api from './axios';

const BASE = '/usuarios';

export const usuariosApi = {
  /**
   * RF-14: GET /usuarios/ — Directorio de usuarios (Solo admin_sistema)
   */
  listar() {
    return api.get(BASE + '/');
  },

  /**
   * RF-13: GET /usuarios/tecnicos — técnicos activos para asignación (admin_general)
   */
  tecnicos() {
    return api.get(BASE + '/tecnicos');
  },

  /**
   * RF-14: POST /usuarios/ — Registrar usuario con rol
   */
  crear(payload) {
    return api.post(BASE + '/', payload);
  },

  /**
   * RF-14: PATCH /usuarios/:id/estado — Activar o desactivar cuenta
   */
  cambiarEstado(id, activo) {
    return api.patch(`${BASE}/${id}/estado`, { activo });
  },
};

export default usuariosApi;
