import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { api, configurarSesion } from "./api";

const AuthContext = createContext(null);
const CLAVE = "edupredict.sesion";

function leerSesion() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE)) || null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [sesion, setSesion] = useState(() => {
    const s = leerSesion();
    configurarSesion(s?.token ?? null);
    return s;
  });

  const cerrarSesion = useCallback(() => {
    try { localStorage.removeItem(CLAVE); } catch { /* sin almacenamiento */ }
    configurarSesion(null);
    setSesion(null);
  }, []);

  configurarSesion(sesion?.token ?? null, cerrarSesion);

  const iniciarSesion = useCallback(async (usuario, password) => {
    const r = await api.login(usuario, password);
    const nueva = { token: r.access_token, usuario: r.usuario };
    try { localStorage.setItem(CLAVE, JSON.stringify(nueva)); } catch { /* sin almacenamiento */ }
    configurarSesion(nueva.token, cerrarSesion);
    setSesion(nueva);
  }, [cerrarSesion]);

  const valor = useMemo(() => ({
    usuario: sesion?.usuario ?? null,
    esAdmin: sesion?.usuario?.rol === "admin",
    iniciarSesion,
    cerrarSesion,
  }), [sesion, iniciarSesion, cerrarSesion]);

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
