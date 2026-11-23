import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { Aviso, BadgeRiesgo, Boton, Card, Cargando, Encabezado, Modal, Segmentado, Vacio } from "../components/ui";
import Icon from "../components/Icon";
import { fecha, n } from "../lib/format";
import { GRUPOS, etiqueta, valorLegible } from "../lib/variables";

const TAMANO = 15;

function NotaReal({ item, onGuardado }) {
  const [valor, setValor] = useState("");
  const [guardando, setGuardando] = useState(false);
  if (item.nota_real !== null) {
    const dif = item.nota_estimada - item.nota_real;
    return <span>{n(item.nota_real)} <small className="muted">({dif >= 0 ? "+" : ""}{n(dif)})</small></span>;
  }
  async function guardar(e) {
    e.preventDefault();
    setGuardando(true);
    try { onGuardado(await api.registrarNotaReal(item.id, Number(valor))); } finally { setGuardando(false); }
  }
  return (
    <form className="nota-real" onSubmit={guardar}>
      <input type="number" min="0" max="100" step="1" placeholder="Nota" value={valor}
        onChange={(e) => setValor(e.target.value)} required aria-label="Nota real" />
      <button className="btn-icono" disabled={guardando} title="Guardar nota real"><Icon nombre="check" size={16} /></button>
    </form>
  );
}

function Detalle({ id, onCerrar }) {
  const [p, setP] = useState(null);
  useEffect(() => { api.detalle(id).then(setP); }, [id]);
  return (
    <Modal titulo={`Predicción #${id}`} onCerrar={onCerrar}>
      {!p ? <Cargando /> : (
        <>
          <div className="detalle-resumen">
            <div><span className="muted">Nota estimada</span><strong>{n(p.nota_estimada)}</strong></div>
            <div><span className="muted">Nota real</span><strong>{p.nota_real === null ? "—" : n(p.nota_real)}</strong></div>
            <div><span className="muted">Estado</span><BadgeRiesgo riesgo={p.riesgo} /></div>
            <div><span className="muted">Modelo</span><strong>{p.modelo_version}</strong></div>
          </div>
          <p className="muted">{fecha(p.creado_en)} · registrado por {p.usuario}{p.codigo_estudiante ? ` · ${p.codigo_estudiante}` : ""}</p>
          <div className="detalle-grupos">
            {GRUPOS.map((g) => (
              <div key={g.titulo}>
                <h4>{g.titulo}</h4>
                <dl>{g.campos.map((c) => (
                  <div key={c}><dt>{etiqueta(c)}</dt><dd>{valorLegible(c, p.entrada[c])}</dd></div>
                ))}</dl>
              </div>
            ))}
          </div>
        </>
      )}
    </Modal>
  );
}

export default function Historial() {
  const [filtros, setFiltros] = useState({ riesgo: null, codigo: "", desde: "", hasta: "" });
  const [pagina, setPagina] = useState(1);
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState(null);
  const [detalle, setDetalle] = useState(null);

  const cargar = useCallback(() => {
    api.historial({ ...filtros, pagina, tamano: TAMANO }).then(setDatos).catch((e) => setError(e.message));
  }, [filtros, pagina]);

  useEffect(() => { cargar(); }, [cargar]);

  const cambiarFiltro = (campo, valor) => { setPagina(1); setFiltros((f) => ({ ...f, [campo]: valor })); };
  const actualizarItem = (nuevo) =>
    setDatos((d) => ({ ...d, items: d.items.map((i) => (i.id === nuevo.id ? nuevo : i)) }));
  const paginas = datos ? Math.max(1, Math.ceil(datos.total / TAMANO)) : 1;

  return (
    <>
      <Encabezado titulo="Historial de predicciones"
        subtitulo="Datos enviados al modelo y su resultado. Registra la nota real cuando el estudiante rinda el examen." />

      <Card>
        <div className="filtros">
          <Segmentado nombre="Estado" valor={filtros.riesgo} onChange={(v) => cambiarFiltro("riesgo", v)}
            opciones={[[null, "Todos"], [true, "En riesgo"], [false, "Sin riesgo"]]} />
          <input placeholder="Buscar código" value={filtros.codigo} onChange={(e) => cambiarFiltro("codigo", e.target.value)} />
          <label>Desde <input type="date" value={filtros.desde} onChange={(e) => cambiarFiltro("desde", e.target.value)} /></label>
          <label>Hasta <input type="date" value={filtros.hasta} onChange={(e) => cambiarFiltro("hasta", e.target.value)} /></label>
        </div>

        {error && <Aviso tono="error">{error}</Aviso>}
        {!datos ? <Cargando /> : datos.total === 0 ? <Vacio>No hay predicciones con esos filtros.</Vacio> : (
          <>
            <div className="tabla-scroll">
              <table className="tabla">
                <thead>
                  <tr>
                    <th>#</th><th>Fecha</th><th>Código</th><th className="num">Nota estimada</th><th>Estado</th>
                    <th>Nota real</th><th>Asistencia</th><th>Estudio</th><th>Modelo</th><th>Usuario</th><th />
                  </tr>
                </thead>
                <tbody>
                  {datos.items.map((i) => (
                    <tr key={i.id}>
                      <td className="muted">{i.id}</td>
                      <td>{fecha(i.creado_en)}</td>
                      <td>{i.codigo_estudiante || "—"}</td>
                      <td className="num fuerte">{n(i.nota_estimada)}</td>
                      <td><BadgeRiesgo riesgo={i.riesgo} /></td>
                      <td><NotaReal item={i} onGuardado={actualizarItem} /></td>
                      <td>{i.entrada.Attendance}%</td>
                      <td>{i.entrada.Hours_Studied} h</td>
                      <td>{i.modelo_version}</td>
                      <td>{i.usuario}</td>
                      <td><button className="btn-icono" title="Ver detalle" onClick={() => setDetalle(i.id)}><Icon nombre="ojo" size={16} /></button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="paginacion">
              <span className="muted">{datos.total} predicciones</span>
              <div>
                <Boton variante="fantasma" disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>Anterior</Boton>
                <span>Página {pagina} de {paginas}</span>
                <Boton variante="fantasma" disabled={pagina >= paginas} onClick={() => setPagina(pagina + 1)}>Siguiente</Boton>
              </div>
            </div>
          </>
        )}
      </Card>
      {detalle && <Detalle id={detalle} onCerrar={() => setDetalle(null)} />}
    </>
  );
}
