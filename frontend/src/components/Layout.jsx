import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import Icon from "./Icon";

const MENU = [
  { a: "/", texto: "Panel", icono: "panel" },
  { a: "/prediccion", texto: "Nueva predicción", icono: "prediccion" },
  { a: "/historial", texto: "Historial", icono: "historial" },
  { a: "/modelo", texto: "Modelo y métricas", icono: "modelo" },
  { a: "/datos", texto: "Datos y reentrenamiento", icono: "datos" },
];

export default function Layout() {
  const { usuario, cerrarSesion } = useAuth();
  const [salud, setSalud] = useState(null);

  useEffect(() => {
    api.salud().then(setSalud).catch(() => setSalud({ estado: "sin conexión" }));
  }, []);

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="marca">
          <img src="/favicon.svg" alt="" width="34" height="34" />
          <div>
            <strong>EduPredict</strong>
            <span>Rendimiento académico</span>
          </div>
        </div>
        <nav>
          {MENU.map((m) => (
            <NavLink key={m.a} to={m.a} end={m.a === "/"} className={({ isActive }) => (isActive ? "activo" : "")}>
              <Icon nombre={m.icono} /> {m.texto}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-pie">
          <div className={`estado-servicio ${salud?.estado === "ok" ? "ok" : "mal"}`}>
            <span className="punto" />
            {salud?.estado === "ok" ? `Servicio activo · modelo ${salud.modelo_activo}` : "Servicio sin conexión"}
          </div>
        </div>
      </aside>

      <div className="contenido">
        <header className="topbar">
          <div className="usuario">
            <Icon nombre="usuario" />
            <span>{usuario?.nombre}</span>
            <span className={`rol rol-${usuario?.rol}`}>{usuario?.rol === "admin" ? "Administrador" : "Docente"}</span>
          </div>
          <button className="btn btn-fantasma" onClick={cerrarSesion}>
            <Icon nombre="salir" size={16} /> Salir
          </button>
        </header>
        <main>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
