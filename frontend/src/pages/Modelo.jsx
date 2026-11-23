import { useCallback, useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import { useAuth } from "../auth";
import { Aviso, Badge, Boton, Card, Cargando, Encabezado, Stat, Vacio } from "../components/ui";
import Icon from "../components/Icon";
import { fecha, n, n3, p } from "../lib/format";
import { etiqueta } from "../lib/variables";

const TONO_ESTADO = { activo: "ok", archivado: "neutro", rechazado: "riesgo" };
const TONO_DRIFT = { estable: "ok", moderado: "alerta", alto: "riesgo" };
const COLOR_DRIFT = { estable: "#2F7D5B", moderado: "#B7791F", alto: "#B5523B" };

export default function Modelo() {
  const { esAdmin } = useAuth();
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState(null);
  const [activando, setActivando] = useState(null);

  const cargar = useCallback(() => {
    Promise.all([api.metricas(), api.versiones(), api.monitoreo()])
      .then(([metricas, versiones, monitoreo]) => setDatos({ metricas, versiones, monitoreo }))
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => { cargar(); }, [cargar]);

  async function activar(v) {
    setActivando(v.id);
    try { await api.activarVersion(v.id); cargar(); }
    catch (e) { setError(e.message); }
    finally { setActivando(null); }
  }

  if (!datos) return error ? <Aviso tono="error">{error}</Aviso> : <Cargando />;
  const { metricas, versiones, monitoreo } = datos;
  const m = metricas.modelo;
  const prod = metricas.produccion;

  return (
    <>
      <Encabezado titulo="Modelo y métricas"
        subtitulo={`Versión activa ${m.version} · ${m.algoritmo} · entrenada el ${fecha(m.creado_en, false)}`}>
        <Boton variante="fantasma" icono="refrescar" onClick={cargar}>Actualizar</Boton>
      </Encabezado>
      {error && <Aviso tono="error">{error}</Aviso>}

      <Card titulo="Rendimiento en el conjunto de test" accion={
        <span className="muted">{n(m.filas_entrenamiento)} filas de entrenamiento · {n(m.filas_test)} de test</span>}>
        <div className="grid-requisitos">
          {metricas.requisitos.map((r) => (
            <div key={r.metrica} className={`requisito ${r.cumple ? "cumple" : "no-cumple"}`}>
              <span className="requisito-nombre">{r.metrica}</span>
              <span className="requisito-valor">
                {r.metrica.startsWith("Mejora") ? p(r.valor) : n3(r.valor)}
              </span>
              <span className="requisito-umbral">
                <Icon nombre={r.cumple ? "check" : "alerta"} size={14} /> Requisito {r.umbral}
              </span>
            </div>
          ))}
        </div>
        <p className="nota-grafico">
          RMSE {n3(m.rmse)} · MAE del modelo base (predecir el promedio) {n3(m.mae_base)} ·
          Hiperparámetros: {Object.entries(m.hiperparametros).map(([k, v]) => `${k} = ${v}`).join(", ")}
        </p>
      </Card>

      <div className="grid-stats">
        <Stat etiqueta="Predicciones realizadas" valor={n(prod.predicciones)} />
        <Stat etiqueta="Marcados en riesgo" valor={p(prod.porcentaje_riesgo)} tono="riesgo" />
        <Stat etiqueta="Con nota real registrada" valor={n(prod.con_nota_real)} />
        <Stat etiqueta="MAE con notas reales" valor={prod.mae_real === null ? "—" : `${n3(prod.mae_real)} pts`}
          detalle={prod.recall_riesgo_real === null ? "Registra notas reales en el historial" : `Recall de riesgo real ${p(prod.recall_riesgo_real)}`} />
      </div>

      <Card titulo="Monitoreo de drift (PSI)" accion={
        <span className="muted">{n(monitoreo.predicciones_analizadas)} predicciones analizadas</span>}>
        {!monitoreo.suficientes_datos ? (
          <Vacio>Se necesitan al menos {monitoreo.minimo_requerido} predicciones para medir el drift.</Vacio>
        ) : (
          <div className="grid-2 sin-margen">
            <ResponsiveContainer width="100%" height={monitoreo.variables.length * 26 + 40}>
              <BarChart data={monitoreo.variables.map((v) => ({ ...v, nombre: etiqueta(v.variable) }))}
                layout="vertical" margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid horizontal={false} stroke="#E7E2D8" />
                <XAxis type="number" tick={{ fontSize: 12 }} />
                <YAxis type="category" dataKey="nombre" width={190} tick={{ fontSize: 12 }} interval={0} />
                <Tooltip formatter={(v) => [n3(v), "PSI"]} />
                <ReferenceLine x={0.2} stroke="#B5523B" strokeDasharray="4 4" />
                <Bar dataKey="psi" radius={[0, 4, 4, 0]}>
                  {monitoreo.variables.map((v) => <Cell key={v.variable} fill={COLOR_DRIFT[v.estado]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div>
              <p className="muted">
                El PSI compara la distribución de los datos que llegan a la API con la del entrenamiento.
                Menor a 0,1 es estable, entre 0,1 y 0,2 moderado y mayor a 0,2 indica drift.
              </p>
              {monitoreo.alertas > 0
                ? <Aviso tono="alerta" titulo={`${monitoreo.alertas} variable(s) con drift alto`}>
                    Conviene subir datos actualizados y reentrenar el modelo.</Aviso>
                : <Aviso tono="ok" titulo="Sin drift relevante">Los datos recientes se parecen a los de entrenamiento.</Aviso>}
              <ul className="lista-drift">
                {monitoreo.variables.slice(0, 6).map((v) => (
                  <li key={v.variable}><span>{etiqueta(v.variable)}</span><Badge tono={TONO_DRIFT[v.estado]}>{v.estado} · {n3(v.psi)}</Badge></li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </Card>

      <Card titulo="Versiones del modelo">
        <div className="tabla-scroll">
          <table className="tabla">
            <thead>
              <tr><th>Versión</th><th>Fecha</th><th>Estado</th><th className="num">MAE</th><th className="num">R²</th>
                <th className="num">Recall riesgo</th><th className="num">Precisión riesgo</th><th>Requisitos</th><th>Dataset</th><th /></tr>
            </thead>
            <tbody>
              {versiones.map((v) => (
                <tr key={v.id}>
                  <td className="fuerte">{v.version}</td>
                  <td>{fecha(v.creado_en)}</td>
                  <td><Badge tono={TONO_ESTADO[v.estado]}>{v.estado}</Badge></td>
                  <td className="num">{n3(v.mae)}</td>
                  <td className="num">{n3(v.r2)}</td>
                  <td className="num">{n3(v.recall_riesgo)}</td>
                  <td className="num">{n3(v.precision_riesgo)}</td>
                  <td>{v.cumple_requisitos ? "Cumple" : "No cumple"}</td>
                  <td>#{v.dataset_id}</td>
                  <td>{esAdmin && v.estado !== "activo" && v.cumple_requisitos && (
                    <Boton variante="fantasma" cargando={activando === v.id} onClick={() => activar(v)}>Activar</Boton>
                  )}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}
