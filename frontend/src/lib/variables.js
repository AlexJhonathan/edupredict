// Etiquetas en español para las variables del modelo (la API usa los nombres originales del dataset)

export const NIVEL = { Low: "Bajo", Medium: "Medio", High: "Alto" };
export const SI_NO = { No: "No", Yes: "Sí" };

export const VARIABLES = {
  Hours_Studied: { etiqueta: "Horas de estudio", unidad: "h/semana", defecto: 20 },
  Attendance: { etiqueta: "Asistencia", unidad: "%", defecto: 80 },
  Previous_Scores: { etiqueta: "Nota anterior", unidad: "/100", defecto: 75 },
  Tutoring_Sessions: { etiqueta: "Tutorías", unidad: "por mes", defecto: 1 },
  Sleep_Hours: { etiqueta: "Horas de sueño", unidad: "por noche", defecto: 7 },
  Physical_Activity: { etiqueta: "Actividad física", unidad: "h/semana", defecto: 3 },
  Motivation_Level: { etiqueta: "Motivación", valores: NIVEL, defecto: "Medium" },
  Extracurricular_Activities: { etiqueta: "Actividades extracurriculares", valores: SI_NO, defecto: "Yes" },
  Learning_Disabilities: { etiqueta: "Dificultad de aprendizaje", valores: SI_NO, defecto: "No" },
  Parental_Involvement: { etiqueta: "Participación de los padres", valores: NIVEL, defecto: "Medium" },
  Parental_Education_Level: {
    etiqueta: "Educación de los padres",
    valores: { "High School": "Secundaria", College: "Universitaria", Postgraduate: "Posgrado" },
    defecto: "High School",
  },
  Family_Income: { etiqueta: "Ingreso familiar", valores: NIVEL, defecto: "Medium" },
  Internet_Access: { etiqueta: "Acceso a internet", valores: SI_NO, defecto: "Yes" },
  Distance_from_Home: {
    etiqueta: "Distancia al colegio",
    valores: { Near: "Cerca", Moderate: "Media", Far: "Lejos" },
    defecto: "Near",
  },
  Access_to_Resources: { etiqueta: "Acceso a recursos", valores: NIVEL, defecto: "Medium" },
  Teacher_Quality: { etiqueta: "Calidad docente", valores: NIVEL, defecto: "Medium" },
  School_Type: { etiqueta: "Tipo de colegio", valores: { Public: "Público", Private: "Privado" }, defecto: "Public" },
  Peer_Influence: {
    etiqueta: "Influencia de compañeros",
    valores: { Negative: "Negativa", Neutral: "Neutral", Positive: "Positiva" },
    defecto: "Neutral",
  },
};

export const GRUPOS = [
  { titulo: "Hábitos de estudio", campos: ["Hours_Studied", "Attendance", "Previous_Scores", "Tutoring_Sessions", "Motivation_Level", "Extracurricular_Activities"] },
  { titulo: "Bienestar", campos: ["Sleep_Hours", "Physical_Activity", "Learning_Disabilities"] },
  { titulo: "Entorno familiar", campos: ["Parental_Involvement", "Parental_Education_Level", "Family_Income", "Internet_Access", "Distance_from_Home"] },
  { titulo: "Entorno escolar", campos: ["Access_to_Resources", "Teacher_Quality", "School_Type", "Peer_Influence"] },
];

export const etiqueta = (variable) => VARIABLES[variable]?.etiqueta ?? variable;

export const valorLegible = (variable, valor) => {
  const v = VARIABLES[variable];
  if (v?.valores) return v.valores[valor] ?? valor;
  return v?.unidad ? `${valor} ${v.unidad}` : String(valor);
};

export const valoresPorDefecto = () =>
  Object.fromEntries(Object.entries(VARIABLES).map(([k, v]) => [k, v.defecto]));
