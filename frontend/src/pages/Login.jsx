import { useState } from "react";
import { useAuth } from "../auth";
import { Aviso, Boton } from "../components/ui";

export default function Login() {
  const { iniciarSesion } = useAuth();
  const [usuario, setUsuario] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [cargando, setCargando] = useState(false);

  async function enviar(e) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      await iniciarSesion(usuario, password);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="login">
      <div className="login-arte">
        <div className="login-texto">
          <img src="/favicon.svg" alt="" width="48" height="48" />
          <h1>EduPredict</h1>
          <p>Estima la nota del examen de cada estudiante y detecta a tiempo a quienes necesitan tutoría.</p>
          <ul>
            <li>Predicción con un modelo de regresión validado con CRISP-ML(Q)</li>
            <li>Historial de predicciones y registro de la nota real</li>
            <li>Métricas, monitoreo y reentrenamiento del modelo</li>
          </ul>
        </div>
      </div>
      <form className="login-form" onSubmit={enviar}>
        <h2>Iniciar sesión</h2>
        <p className="muted">Ingresa con tu usuario de docente o administrador.</p>
        <label>
          Usuario
          <input value={usuario} onChange={(e) => setUsuario(e.target.value)} autoComplete="username" required autoFocus />
        </label>
        <label>
          Contraseña
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password" required />
        </label>
        {error && <Aviso tono="error">{error}</Aviso>}
        <Boton type="submit" cargando={cargando}>Entrar</Boton>
        <p className="pista">Usuarios de prueba: <code>admin / admin123</code> · <code>docente / docente123</code></p>
      </form>
    </div>
  );
}
