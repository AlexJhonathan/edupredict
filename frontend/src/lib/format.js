const num = new Intl.NumberFormat("es-BO", { maximumFractionDigits: 2, minimumFractionDigits: 0 });
const num3 = new Intl.NumberFormat("es-BO", { maximumFractionDigits: 3, minimumFractionDigits: 3 });
const pct = new Intl.NumberFormat("es-BO", { style: "percent", maximumFractionDigits: 1 });

export const n = (v) => (v === null || v === undefined ? "—" : num.format(v));
export const n3 = (v) => (v === null || v === undefined ? "—" : num3.format(v));
export const p = (v) => (v === null || v === undefined ? "—" : pct.format(v));

// SQLite guarda las fechas en UTC con el formato "AAAA-MM-DD HH:MM:SS"
export function fecha(texto, conHora = true) {
  if (!texto) return "—";
  const d = new Date(texto.replace(" ", "T") + "Z");
  return d.toLocaleString("es-BO", conHora
    ? { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" }
    : { day: "2-digit", month: "short", year: "numeric" });
}
