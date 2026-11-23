import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import { Aviso, Badge, Boton, Card, Cargando, Encabezado, Vacio } from "../components/ui";
import Icon from "../components/Icon";
import { fecha, n } from "../lib/format";

const TONO = { pendiente: "neutro", en_progreso: "alerta", completado: "ok", fallido: "riesgo" };
const TEXTO = { pendiente: "Pendiente", en_progreso: "En progreso", completado: "Completado", fallido: "Fallido" };

function Subida({ onSubido }) {
  const [archivo, setArchivo] = useState(null);
  const [arrastrando, setArrastrando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(false);
  const input = useRef(null);

  async function subir() {
    setCargando(true); setError(null); setResultado(null);
    try {
      const r = await api.subirDataset(archivo);
      setResultado(r); setArchivo(null); onSubido();
    } catch (e) {
      setError(e.detalle?.validacion ? { mensaje: e.detalle.mensaje, validacion: e.detalle.validacion } : { mensaje: e.message });
    } finally { setCargando(false); }
  }

  async function plantilla() {
    const blob = await api.plantilla();
    const url = URL.createObjectURL(blob);
    const a = Object.assign(document.createElement("a"), { href: url, download: "plantilla_entrenamiento.csv" });
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <Card titulo="Enviar archivo de entrenamiento" accion={
      <button className="enlace" onClick={plantilla}><Icon nombre="bajar" size={14} /> Descargar plantilla</button>}>
      <div className={`zona-subida ${arrastrando ? "arrastrando" : ""}`}
        onClick={() => input.current.click()}
        onDragOver={(e) => { e.preventDefault(); setArrastrando(true); }}
        onDragLeave={() => setArrastrando(false)}
        onDrop={(e) => { e.preventDefault(); setArrastrando(false); setArchivo(e.dataTransfer.files[0]); }}>
        <Icon nombre="subir" size={28} />
        <p>{archivo ? <strong>{archivo.name}</strong> : "Arrastra un CSV aquí o haz clic para elegirlo"}</p>
        <small className="muted">18 variables + Exam_Score · máximo 10 MB · al menos 200 filas válidas</small>
        <input ref={input} type="file" accept=".csv" hidden onChange={(e) => setArchivo(e.target.files[0])} />
      </div>
      <Boton icono="subir" disabled={!archivo} cargando={cargando} onClick={subir}>Validar y subir</Boton>

      {error && (
        <Aviso tono="error" titulo={error.mensaje}>
          {error.validacion && (
            <ul>
              {error.validacion.columnas_faltantes.length > 0 &&
                <li>Faltan columnas: {error.validacion.columnas_faltantes.join(", ")}</li>}
              {error.validacion.advertencias.map((a) => <li key={a}>{a}</li>)}
            </ul>
          )}
        </Aviso>
      )}
      {resultado && (
        <Aviso tono="ok" titulo={`Dataset #${resultado.dataset.id} registrado`}>
          {n(resultado.validacion.filas_validas)} de {n(resultado.validacion.filas)} filas son válidas.
          {resultado.validacion.advertencias.length > 0 && (
            <ul>{resultado.validacion.advertencias.map((a) => <li key={a}>{a}</li>)}</ul>
          )}
        </Aviso>
      )}
    </Card>
  );
}

function Reentrenamiento({ datasets, onTerminado }) {
  const [datasetId, setDatasetId] = useState("");
  const [incluirReales, setIncluirReales] = useState(true);
  const [trabajo, setTrabajo] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!trabajo || ["completado", "fallido"].includes(trabajo.estado)) return;
    const t = setTimeout(async () => {
      const actualizado = await api.entrenamiento(trabajo.id);
      setTrabajo(actualizado);
      if (["completado", "fallido"].includes(actualizado.estado)) onTerminado();
    }, 1500);
    return () => clearTimeout(t);
  }, [trabajo, onTerminado]);

  async function iniciar() {
    setError(null);
    try {
      setTrabajo(await api.reentrenar({ dataset_id: datasetId ? Number(datasetId) : null, incluir_notas_reales: incluirReales }));
      onTerminado();
    } catch (e) { setError(e.message); }
  }

  const enCurso = trabajo && !["completado", "fallido"].includes(trabajo.estado);
  return (
    <Card titulo="Reentrenar el modelo">
      <p className="muted">
        Se entrena un modelo nuevo (Huber con búsqueda de hiperparámetros) y se compara con el activo en el mismo
        conjunto de test. Solo se activa si cumple los requisitos y su error es igual o menor.
      </p>
      <div className="form-fila">
        <label>Dataset
          <select value={datasetId} onChange={(e) => setDatasetId(e.target.value)}>
            <option value="">El más reciente</option>
            {datasets.map((d) => <option key={d.id} value={d.id}>#{d.id} · {d.nombre_archivo} ({n(d.filas_validas)} filas)</option>)}
          </select>
        </label>
        <label className="check">
          <input type="checkbox" checked={incluirReales} onChange={(e) => setIncluirReales(e.target.checked)} />
          Incluir las predicciones con nota real registrada
        </label>
      </div>
      <Boton icono="refrescar" cargando={enCurso} onClick={iniciar}>{enCurso ? "Entrenando…" : "Iniciar reentrenamiento"}</Boton>
      {error && <Aviso tono="error">{error}</Aviso>}
      {trabajo && (
        <Aviso tono={trabajo.estado === "fallido" ? "error" : trabajo.estado === "completado" ? "ok" : "info"}
          titulo={`Entrenamiento #${trabajo.id}: ${TEXTO[trabajo.estado]}`}>
          {trabajo.mensaje || "El modelo se está entrenando en segundo plano…"}
        </Aviso>
      )}
    </Card>
  );
}

export default function Datos() {
  const { esAdmin } = useAuth();
  const [datasets, setDatasets] = useState(null);
  const [entrenamientos, setEntrenamientos] = useState(null);
  const [error, setError] = useState(null);

  const cargar = useCallback(() => {
    Promise.all([api.datasets(), api.entrenamientos()])
      .then(([d, e]) => { setDatasets(d); setEntrenamientos(e); })
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => { cargar(); }, [cargar]);

  if (!datasets) return error ? <Aviso tono="error">{error}</Aviso> : <Cargando />;

  return (
    <>
      <Encabezado titulo="Datos y reentrenamiento"
        subtitulo="Envía información actualizada y reentrena el modelo sin detener el servicio." />
      {!esAdmin && (
        <Aviso tono="info" titulo="Solo lectura">
          Subir archivos y reentrenar requiere el rol de administrador.
        </Aviso>
      )}
      {esAdmin && (
        <div className="grid-2">
          <Subida onSubido={cargar} />
          <Reentrenamiento datasets={datasets} onTerminado={cargar} />
        </div>
      )}

      <Card titulo="Archivos de entrenamiento">
        {datasets.length === 0 ? <Vacio>No hay archivos.</Vacio> : (
          <div className="tabla-scroll">
            <table className="tabla">
              <thead><tr><th>#</th><th>Archivo</th><th>Origen</th><th className="num">Filas</th><th className="num">Válidas</th><th>Subido por</th><th>Fecha</th></tr></thead>
              <tbody>
                {datasets.map((d) => (
                  <tr key={d.id}>
                    <td className="muted">{d.id}</td><td className="fuerte">{d.nombre_archivo}</td>
                    <td><Badge tono={d.origen === "inicial" ? "neutro" : "info"}>{d.origen}</Badge></td>
                    <td className="num">{n(d.filas)}</td><td className="num">{n(d.filas_validas)}</td>
                    <td>{d.subido_por || "sistema"}</td><td>{fecha(d.creado_en)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card titulo="Historial de entrenamientos">
        <div className="tabla-scroll">
          <table className="tabla">
            <thead><tr><th>#</th><th>Estado</th><th>Dataset</th><th>Notas reales</th><th>Resultado</th><th>Solicitado por</th><th>Inicio</th><th>Fin</th></tr></thead>
            <tbody>
              {entrenamientos.map((e) => (
                <tr key={e.id}>
                  <td className="muted">{e.id}</td>
                  <td><Badge tono={TONO[e.estado]}>{TEXTO[e.estado]}</Badge></td>
                  <td>#{e.dataset_id}</td>
                  <td>{e.incluir_notas_reales ? "Sí" : "No"}</td>
                  <td className="ancho">{e.mensaje || "—"}</td>
                  <td>{e.solicitado_por || "sistema"}</td>
                  <td>{fecha(e.iniciado_en)}</td>
                  <td>{fecha(e.finalizado_en)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}
