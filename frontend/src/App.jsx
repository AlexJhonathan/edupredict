import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth";
import Layout from "./components/Layout";
import Datos from "./pages/Datos";
import Historial from "./pages/Historial";
import Login from "./pages/Login";
import Modelo from "./pages/Modelo";
import Panel from "./pages/Panel";
import Prediccion from "./pages/Prediccion";

function Protegida({ children }) {
  const { usuario } = useAuth();
  return usuario ? children : <Navigate to="/login" replace />;
}

export default function App() {
  const { usuario } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={usuario ? <Navigate to="/" replace /> : <Login />} />
      <Route element={<Protegida><Layout /></Protegida>}>
        <Route index element={<Panel />} />
        <Route path="prediccion" element={<Prediccion />} />
        <Route path="historial" element={<Historial />} />
        <Route path="modelo" element={<Modelo />} />
        <Route path="datos" element={<Datos />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
