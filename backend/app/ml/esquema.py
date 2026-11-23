"""Variables del modelo, valores permitidos y requisitos de aceptación (Fase 1 de CRISP-ML(Q))."""

TARGET = "Exam_Score"
NOTA_RIESGO = 65.0

# variables numéricas: (mínimo, máximo) que acepta la API
NUMERICAS = {
    "Hours_Studied": (0, 80),
    "Attendance": (0, 100),
    "Sleep_Hours": (0, 16),
    "Previous_Scores": (0, 100),
    "Tutoring_Sessions": (0, 30),
    "Physical_Activity": (0, 20),
}

# variables con orden natural: se codifican 0, 1, 2 respetando ese orden
ORDINALES = {
    "Parental_Involvement": ["Low", "Medium", "High"],
    "Access_to_Resources": ["Low", "Medium", "High"],
    "Motivation_Level": ["Low", "Medium", "High"],
    "Family_Income": ["Low", "Medium", "High"],
    "Teacher_Quality": ["Low", "Medium", "High"],
    "Peer_Influence": ["Negative", "Neutral", "Positive"],
    "Parental_Education_Level": ["High School", "College", "Postgraduate"],
    "Distance_from_Home": ["Near", "Moderate", "Far"],
}

BINARIAS = {
    "Extracurricular_Activities": ["No", "Yes"],
    "Internet_Access": ["No", "Yes"],
    "School_Type": ["Private", "Public"],
    "Learning_Disabilities": ["No", "Yes"],
}

# orden de las columnas igual al CSV original (sin Gender ni Exam_Score)
VARIABLES = [
    "Hours_Studied", "Attendance", "Parental_Involvement", "Access_to_Resources",
    "Extracurricular_Activities", "Sleep_Hours", "Previous_Scores", "Motivation_Level",
    "Internet_Access", "Tutoring_Sessions", "Family_Income", "Teacher_Quality", "School_Type",
    "Peer_Influence", "Physical_Activity", "Learning_Disabilities", "Parental_Education_Level",
    "Distance_from_Home",
]

CATEGORICAS = {**ORDINALES, **BINARIAS}

# requisitos de aceptación definidos en la Fase 1
REQUISITOS = {
    "mae_max": 1.0,
    "mejora_vs_base_min": 0.50,
    "r2_min": 0.70,
    "recall_riesgo_min": 0.90,
    "precision_riesgo_min": 0.70,
}

# hiperparámetros encontrados en la Fase 3 (notebook) para el modelo inicial
PARAMETROS_INICIALES = {"epsilon": 2.0, "alpha": 3.0}
GRILLA_REENTRENAMIENTO = {"modelo__epsilon": [1.35, 2.0, 3.0], "modelo__alpha": [0.1, 1.0, 3.0, 10.0]}

MIN_FILAS_ENTRENAMIENTO = 200


def columna_sql(variable: str) -> str:
    """Hours_Studied -> hours_studied (nombre de la columna en la tabla predicciones)."""
    return variable.lower()
