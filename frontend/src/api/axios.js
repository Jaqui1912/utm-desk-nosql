import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'https://utm-desk-nosql.onrender.com',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ── Interceptor de Solicitud (Inyectar Bearer Token) ──
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('utm_desk_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ── Interceptor de Respuesta (Manejo Global 401 / 403) ──
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response ? error.response.status : null;

    if (status === 401) {
      // Token expirado o inválido: limpiar sesión local
      const isSysadmin = window.location.pathname.startsWith('/sysadmin');
      localStorage.removeItem('utm_desk_token');
      localStorage.removeItem('utm_desk_user');

      // Redirigir a la pantalla correspondiente si no está ya en ella
      if (isSysadmin && window.location.pathname !== '/sysadmin/login') {
        window.location.href = '/sysadmin/login';
      } else if (!isSysadmin && window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

/**
 * Helper para extraer un mensaje de error legible de la respuesta de FastAPI
 */
export function extractErrorMessage(error) {
  if (!error.response) {
    return 'No se pudo conectar con el servidor. Verifica que el backend esté en ejecución.';
  }
  const detail = error.response.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    // Errores de validación de Pydantic
    return detail.map((err) => `${err.loc.join('.')}: ${err.msg}`).join(', ');
  }
  return error.response.data?.message || 'Ocurrió un error inesperado al procesar la solicitud.';
}

export default api;
