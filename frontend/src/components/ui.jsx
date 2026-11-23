import { useEffect } from "react";
import Icon from "./Icon";

export function Card({ titulo, accion, children, className = "" }) {
  return (
    <section className={`card ${className}`}>
      {(titulo || accion) && (
        <header className="card-head">
          {titulo && <h3>{titulo}</h3>}
          {accion}
        </header>
      )}
      {children}
    </section>
  );
}

export function Encabezado({ titulo, subtitulo, children }) {
  return (
    <div className="page-head">
      <div>
        <h1>{titulo}</h1>
        {subtitulo && <p className="muted">{subtitulo}</p>}
      </div>
      {children && <div className="page-actions">{children}</div>}
    </div>
  );
}

export function Stat({ etiqueta, valor, detalle, tono }) {
  return (
    <div className={`stat ${tono ? `stat-${tono}` : ""}`}>
      <span className="stat-label">{etiqueta}</span>
      <span className="stat-value">{valor}</span>
      {detalle && <span className="stat-detail">{detalle}</span>}
    </div>
  );
}

export function Badge({ tono = "neutro", children }) {
  return <span className={`badge badge-${tono}`}>{children}</span>;
}

export const BadgeRiesgo = ({ riesgo }) =>
  riesgo ? <Badge tono="riesgo">En riesgo</Badge> : <Badge tono="ok">Sin riesgo</Badge>;

export function Boton({ variante = "primario", icono, cargando, children, ...props }) {
  return (
    <button className={`btn btn-${variante}`} disabled={cargando || props.disabled} {...props}>
      {cargando ? <span className="spinner" /> : icono && <Icon nombre={icono} size={16} />}
      {children}
    </button>
  );
}

export function Aviso({ tono = "info", titulo, children }) {
  return (
    <div className={`aviso aviso-${tono}`} role={tono === "error" ? "alert" : "status"}>
      <Icon nombre={tono === "ok" ? "check" : "alerta"} size={18} />
      <div>
        {titulo && <strong>{titulo}</strong>}
        {children && <div>{children}</div>}
      </div>
    </div>
  );
}

export function Cargando({ texto = "Cargando…" }) {
  return <div className="cargando"><span className="spinner" /> {texto}</div>;
}

export function Vacio({ children }) {
  return <div className="vacio">{children}</div>;
}

export function Segmentado({ opciones, valor, onChange, nombre }) {
  return (
    <div className="segmentado" role="radiogroup" aria-label={nombre}>
      {opciones.map(([v, texto]) => (
        <button key={String(v)} type="button" role="radio" aria-checked={valor === v}
          className={valor === v ? "activo" : ""} onClick={() => onChange(v)}>
          {texto}
        </button>
      ))}
    </div>
  );
}

export function Modal({ titulo, onCerrar, children }) {
  useEffect(() => {
    const tecla = (e) => e.key === "Escape" && onCerrar();
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [onCerrar]);
  return (
    <div className="modal-fondo" onClick={onCerrar}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={titulo} onClick={(e) => e.stopPropagation()}>
        <header className="card-head">
          <h3>{titulo}</h3>
          <button className="btn-icono" onClick={onCerrar} aria-label="Cerrar"><Icon nombre="cerrar" /></button>
        </header>
        {children}
      </div>
    </div>
  );
}
