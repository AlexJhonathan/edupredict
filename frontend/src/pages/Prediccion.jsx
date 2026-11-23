import { useEffect, useState } from "react";
import { api } from "../api";
import { Aviso, BadgeRiesgo, Boton, Card, Cargando, Encabezado, Segmentado } from "../components/ui";
import { n } from "../lib/format";
import { GRUPOS, VARIABLES, etiqueta, valoresPorDefecto } from "../lib/variables";

function CampoNumerico({ nombre, campo, valor, onChange }) {
  const v = VARIABLES[nombre];
  const fuera = valor < campo.min_entrenamiento || valor > campo.max_entrenamiento;
  return (
    <div className="campo">
      <div className="campo-cabecera">
        <label htmlFor={nombre}>{v.etiqueta}</label>
        <span className="campo-valor">
          <input id={nombre} type="number" min={campo.minimo} max={campo.maximo} value={valor}
            onChange={(e) => onChange(e.target.value === "" ? "" : Number(e.target.value))} />
          <small>{v.unidad}</small>
        </span>
      </div>
      <input type="range" min={campo.minimo} max={campo.maximo} value={valor === "" ? campo.minimo : valor}
        onChange={(e) => onChange(Number(e.target.value))} aria-label={v.etiqueta} />
      <small className={fuera ? "texto-alerta" : "muted"}>
        Rango del entrenamiento: {campo.min_entrenamiento}–{campo.max_entrenamiento}
      </small>
    </div>
  );
}

function CampoCategoria({ nombre, campo, valor, onChange }) {
  const v = VARIABLES[nombre];
  return (
    <div className="campo">
      <span className="campo-etiqueta">{v.etiqueta}</span>
      <Segmentado nombre={v.etiqueta} valor={valor} onChange={onChange}
        opciones={campo.valores.map((x) => [x, v.valores[x] ?? x])} />
    </div>
  );
}

function Escala({ nota }) {
  const pos = (x) => `${Math.min(100, Math.max(0, ((x - 50) / 50) * 100))}%`;
  return (
    <div className="escala" aria-hidden="true">
      <div className="escala-riesgo" style={{ width: pos(65) }} />
      <div className="escala-umbral" style={{ left: pos(65) }}><span>65</span></div>
      <div className="escala-marca" style={{ left: pos(nota) }} />
      <div className="escala-etiquetas"><span>50</span><span>75</span><span>100</span></div>
    </div>
  );
}

function Resultado({ r }) {
  return (
    <Card className={`resultado ${r.riesgo ? "resultado-riesgo" : "resultado-ok"}`}>
      <div className="resultado-cabecera">
        <span className="muted">Nota estimada</span>
        <BadgeRiesgo riesgo={r.riesgo} />
      </div>
      <div className="resultado-nota">{n(r.nota_estimada)}<small>/100</small></div>
      <Escala nota={r.nota_estimada} />
      <p className="resultado-mensaje">
        {r.riesgo
          ? "Se recomienda ofrecer tutoría antes del examen."
          : "No se detecta riesgo de bajo rendimiento."}
      </p>

      <div className="factores">
        <div>
          <h4>Lo que más baja la nota</h4>
          {r.factores_en_contra.length === 0 ? <p className="muted">Nada relevante</p> : (
            <ul>{r.factores_en_contra.map((f) => (
              <li key={f.variable}><span>{etiqueta(f.variable)}</span><b className="negativo">{n(f.aporte)}</b></li>
            ))}</ul>
          )}
        </div>
        <div>
          <h4>Lo que más la sube</h4>
          {r.factores_a_favor.length === 0 ? <p className="muted">Nada relevante</p> : (
            <ul>{r.factores_a_favor.map((f) => (
              <li key={f.variable}><span>{etiqueta(f.variable)}</span><b className="positivo">+{n(f.aporte)}</b></li>
            ))}</ul>
          )}
        </div>
      </div>
      <p className="nota-grafico">Puntos frente a un estudiante promedio. Modelo {r.modelo_version}, predicción #{r.id}.</p>
      {r.advertencias.map((a) => <Aviso key={a} tono="alerta">{a}</Aviso>)}
    </Card>
  );
}

export default function Prediccion() {
  const [contrato, setContrato] = useState(null);
  const [datos, setDatos] = useState(valoresPorDefecto);
  const [codigo, setCodigo] = useState("");
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    api.contrato().then(setContrato).catch((e) => setError(e.message));
  }, []);

  const cambiar = (campo) => (valor) => setDatos((d) => ({ ...d, [campo]: valor }));

  async function enviar(e) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      setResultado(await api.predecir({ ...datos, codigo_estudiante: codigo || null }));
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  if (!contrato) return error ? <Aviso tono="error">{error}</Aviso> : <Cargando />;

  return (
    <>
      <Encabezado titulo="Nueva predicción"
        subtitulo="Completa los datos del estudiante. El modelo estima su nota del examen final." />
      <form className="prediccion" onSubmit={enviar}>
        <div className="prediccion-form">
          <Card>
            <label className="campo campo-codigo">
              <span className="campo-etiqueta">Código del estudiante (opcional)</span>
              <input value={codigo} maxLength={30} placeholder="Ej. EST-0142 (no uses nombres)"
                onChange={(e) => setCodigo(e.target.value)} />
            </label>
          </Card>
          {GRUPOS.map((g) => (
            <Card key={g.titulo} titulo={g.titulo}>
              <div className="campos">
                {g.campos.map((c) => contrato.campos[c].tipo === "entero"
                  ? <CampoNumerico key={c} nombre={c} campo={contrato.campos[c]} valor={datos[c]} onChange={cambiar(c)} />
                  : <CampoCategoria key={c} nombre={c} campo={contrato.campos[c]} valor={datos[c]} onChange={cambiar(c)} />)}
              </div>
            </Card>
          ))}
        </div>

        <div className="prediccion-lado">
          <div className="pegajoso">
            <Boton type="submit" cargando={cargando} icono="prediccion">Estimar nota</Boton>
            <button type="button" className="btn btn-fantasma" onClick={() => { setDatos(valoresPorDefecto()); setResultado(null); setCodigo(""); }}>
              Restablecer valores
            </button>
            {error && <Aviso tono="error">{error}</Aviso>}
            {resultado ? <Resultado r={resultado} /> : (
              <Card className="resultado-vacio">
                <p>El resultado aparecerá aquí: la nota estimada, si el estudiante está en riesgo y qué factores pesan más.</p>
              </Card>
            )}
          </div>
        </div>
      </form>
    </>
  );
}
