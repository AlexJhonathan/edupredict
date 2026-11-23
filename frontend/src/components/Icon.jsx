const RUTAS = {
  panel: "M3 13h8V3H3zM13 21h8V11h-8zM3 21h8v-6H3zM13 3v6h8V3z",
  prediccion: "M12 3v4M12 17v4M3 12h4M17 12h4M12 12m-5 0a5 5 0 1 0 10 0a5 5 0 1 0-10 0",
  historial: "M3 12a9 9 0 1 0 3-6.7M3 4v5h5M12 7v5l3 2",
  modelo: "M4 19V5M4 19h16M8 15l4-4 3 3 5-6",
  datos: "M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3-3.6 3-8 3-8-1.3-8-3zM4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6",
  salir: "M15 4h4v16h-4M10 8l-4 4 4 4M6 12h11",
  subir: "M12 16V4M7 9l5-5 5 5M4 20h16",
  bajar: "M12 4v12M7 11l5 5 5-5M4 20h16",
  check: "M5 12l4 4 10-10",
  alerta: "M12 9v4M12 17h.01M10.3 3.9L2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z",
  refrescar: "M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7",
  ojo: "M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12zM12 12m-3 0a3 3 0 1 0 6 0a3 3 0 1 0-6 0",
  cerrar: "M6 6l12 12M18 6L6 18",
  arriba: "M12 19V5M6 11l6-6 6 6",
  abajo: "M12 5v14M6 13l6 6 6-6",
  usuario: "M12 12m-4 0a4 4 0 1 0 8 0a4 4 0 1 0-8 0M4 21c0-4 3.6-6 8-6s8 2 8 6",
  escudo: "M12 3l8 3v6c0 5-3.4 8-8 9-4.6-1-8-4-8-9V6z",
};

export default function Icon({ nombre, size = 18, className = "" }) {
  return (
    <svg className={`icon ${className}`} width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={RUTAS[nombre]} />
    </svg>
  );
}
