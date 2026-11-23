import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import { Aviso, BadgeRiesgo, Card, Cargando, Encabezado, Stat, Vacio } from "../components/ui";
import { fecha, n, n3, p } from "../lib/format";

const RANGOS = [[0, 60], [60, 62], [62, 64], [64, 65], [65, 66], [66, 68], [68, 70], [70, 72], [72, 75], [75, 101]];

export default function Panel() {
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.metricas(), api.historial({ tamano: 200 }), api.monitoreo()])
      .then(([metricas, historial, monitoreo]) => setDatos({ metricas, historial, monitoreo }))
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <Aviso tono="error" titulo="No se pudo cargar el panel">{error}</Aviso>;
  if (!datos) return <Cargando />;

  const { metricas, historial, monitoreo } = datos;
  const prod = metricas.produccion;
  const cumple = metricas.requisitos.every((r) => r.cumple);
  const distribucion = RANGOS.map(([a, b]) => ({
    rango: a === 0 ? "<60" : b === 101 ? "75+" : `${a}–${b}`,
    desde: a,
    cantidad: historial.items.filter((i) => i.nota_estimada >= a && i.nota_estimada < b).length,
  }));

  return (
    <>
      <Encabezado titulo="Panel" subtitulo="Resumen del servicio de IA y de las últimas predicciones">
        <Link className="btn btn-primario" to="/prediccion">Nueva predicción</Link>
      </Encabezado>

      <div className="grid-stats">
        <Stat etiqueta="Modelo activo" valor={metricas.modelo.version}
          detalle={cumple ? "Cumple los requisitos" : "Revisar requisitos"} tono={cumple ? "ok" : "riesgo"} />
        <Stat etiqueta="Error promedio (MAE)" valor={`${n3(metricas.modelo.mae)} pts`} detalle="En el conjunto de test" />
        <Stat etiqueta="Predicciones" valor={n(prod.predicciones)} detalle={`${n(prod.con_nota_real)} con nota real`} />
        <Stat etiqueta="Estudiantes en riesgo" valor={p(prod.porcentaje_riesgo)}
          detalle={`${n(prod.en_riesgo)} con nota estimada < 65`} tono="riesgo" />
      </div>

      {monitoreo.alertas > 0 && (
        <Aviso tono="alerta" titulo={`Drift detectado en ${monitoreo.alertas} variable(s)`}>
          Los datos recientes se alejan de los de entrenamiento. Revisa <Link to="/modelo">Modelo y métricas</Link>.
        </Aviso>
      )}

      <div className="grid-2">
        <Card titulo="Notas estimadas (últimas 200 predicciones)">
          {historial.total === 0 ? <Vacio>Aún no hay predicciones.</Vacio> : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={distribucion} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="#E7E2D8" />
                <XAxis dataKey="rango" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v) => [v, "Estudiantes"]} />
                <ReferenceLine x="64–65" stroke="#B5523B" strokeDasharray="4 4" />
                <Bar dataKey="cantidad" radius={[4, 4, 0, 0]}>
                  {distribucion.map((d) => <Cell key={d.rango} fill={d.desde < 65 ? "#B5523B" : "#1F4E79"} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
          <p className="nota-grafico">En rojo, las notas menores a 65 (estudiantes en riesgo).</p>
        </Card>

        <Card titulo="Últimas predicciones" accion={<Link to="/historial">Ver historial</Link>}>
          {historial.items.length === 0 ? <Vacio>Aún no hay predicciones.</Vacio> : (
            <table className="tabla compacta">
              <thead><tr><th>Fecha</th><th>Código</th><th className="num">Nota</th><th>Estado</th></tr></thead>
              <tbody>
                {historial.items.slice(0, 7).map((i) => (
                  <tr key={i.id}>
                    <td>{fecha(i.creado_en)}</td>
                    <td>{i.codigo_estudiante || "—"}</td>
                    <td className="num">{n(i.nota_estimada)}</td>
                    <td><BadgeRiesgo riesgo={i.riesgo} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </>
  );
}
