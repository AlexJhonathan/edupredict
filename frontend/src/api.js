// Cliente de la API REST del servicio de IA. Todas las llamadas pasan por aquí.
export const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

let token = null;
let alExpirar = () => {};

export function configurarSesion(nuevoToken, onExpira) {
  token = nuevoToken;
  if (onExpira) alExpirar = onExpira;
}

export class ApiError extends Error {
  constructor(status, detalle) {
    super(typeof detalle === "string" ? detalle : detalle?.mensaje || "Error en la solicitud");
    this.status = status;
    this.detalle = detalle;
  }
}

async function solicitar(ruta, { method = "GET", json, form, body, raw = false } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  } else if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    body = new URLSearchParams(form);
  }

  let res;
  try {
    res = await fetch(`${API_URL}${ruta}`, { method, headers, body });
  } catch {
    throw new ApiError(0, "No se pudo conectar con el servicio de IA. ¿Está encendido el backend?");
  }
  if (res.status === 401 && token) alExpirar();
  if (!res.ok) {
    let detalle = res.statusText;
    try {
      const data = await res.json();
      detalle = Array.isArray(data.detail)
        ? data.detail.map((d) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join(" · ")
        : data.detail;
    } catch { /* respuesta sin JSON */ }
    throw new ApiError(res.status, detalle);
  }
  if (raw) return res;
  return res.status === 204 ? null : res.json();
}

const qs = (params) => {
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => v !== undefined && v !== null && v !== "" && p.set(k, v));
  const s = p.toString();
  return s ? `?${s}` : "";
};

export const api = {
  // sistema y autenticación
  salud: () => solicitar("/api/salud"),
  login: (usuario, password) => solicitar("/api/auth/login", { method: "POST", form: { username: usuario, password } }),
  yo: () => solicitar("/api/auth/yo"),

  // predicciones
  predecir: (datos) => solicitar("/api/predicciones", { method: "POST", json: datos }),
  historial: (filtros = {}) => solicitar(`/api/predicciones${qs(filtros)}`),
  detalle: (id) => solicitar(`/api/predicciones/${id}`),
  registrarNotaReal: (id, nota) => solicitar(`/api/predicciones/${id}/nota-real`, { method: "PUT", json: { nota_real: nota } }),

  // modelo
  metricas: () => solicitar("/api/modelo/metricas"),
  versiones: () => solicitar("/api/modelo/versiones"),
  activarVersion: (id) => solicitar(`/api/modelo/versiones/${id}/activar`, { method: "POST" }),
  contrato: () => solicitar("/api/modelo/contrato"),
  monitoreo: () => solicitar("/api/modelo/monitoreo"),
  reentrenar: (datos) => solicitar("/api/modelo/reentrenar", { method: "POST", json: datos }),
  entrenamientos: () => solicitar("/api/modelo/entrenamientos"),
  entrenamiento: (id) => solicitar(`/api/modelo/entrenamientos/${id}`),

  // datos de entrenamiento
  datasets: () => solicitar("/api/datasets"),
  subirDataset: (archivo) => {
    const fd = new FormData();
    fd.append("archivo", archivo);
    return solicitar("/api/datasets", { method: "POST", body: fd });
  },
  plantilla: async () => {
    const res = await solicitar("/api/datasets/plantilla", { raw: true });
    return res.blob();
  },
};
