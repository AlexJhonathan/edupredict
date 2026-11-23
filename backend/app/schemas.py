"""Modelos de entrada y salida de la API (validación con Pydantic y documentación en Swagger)."""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Nivel = Literal["Low", "Medium", "High"]
SiNo = Literal["No", "Yes"]


class EstudianteEntrada(BaseModel):
    """Datos de un estudiante. Los nombres y valores son los mismos del dataset original."""
    codigo_estudiante: Optional[str] = Field(None, max_length=30, description="Código interno opcional (no usar nombres)")
    Hours_Studied: int = Field(..., ge=0, le=80, description="Horas de estudio por semana")
    Attendance: int = Field(..., ge=0, le=100, description="Porcentaje de asistencia")
    Parental_Involvement: Nivel = Field(..., description="Participación de los padres")
    Access_to_Resources: Nivel = Field(..., description="Acceso a recursos educativos")
    Extracurricular_Activities: SiNo = Field(..., description="Participa en actividades extracurriculares")
    Sleep_Hours: int = Field(..., ge=0, le=16, description="Horas de sueño por noche")
    Previous_Scores: int = Field(..., ge=0, le=100, description="Nota en exámenes anteriores")
    Motivation_Level: Nivel = Field(..., description="Nivel de motivación")
    Internet_Access: SiNo = Field(..., description="Tiene acceso a internet")
    Tutoring_Sessions: int = Field(..., ge=0, le=30, description="Sesiones de tutoría por mes")
    Family_Income: Nivel = Field(..., description="Ingreso familiar")
    Teacher_Quality: Nivel = Field(..., description="Calidad de los docentes")
    School_Type: Literal["Public", "Private"] = Field(..., description="Tipo de colegio")
    Peer_Influence: Literal["Negative", "Neutral", "Positive"] = Field(..., description="Influencia de los compañeros")
    Physical_Activity: int = Field(..., ge=0, le=20, description="Horas de actividad física por semana")
    Learning_Disabilities: SiNo = Field(..., description="Tiene alguna dificultad de aprendizaje")
    Parental_Education_Level: Literal["High School", "College", "Postgraduate"] = Field(
        ..., description="Nivel educativo de los padres")
    Distance_from_Home: Literal["Near", "Moderate", "Far"] = Field(..., description="Distancia de casa al colegio")

    model_config = ConfigDict(json_schema_extra={"example": {
        "codigo_estudiante": "EST-0001", "Hours_Studied": 12, "Attendance": 70, "Parental_Involvement": "Low",
        "Access_to_Resources": "Medium", "Extracurricular_Activities": "No", "Sleep_Hours": 7,
        "Previous_Scores": 65, "Motivation_Level": "Low", "Internet_Access": "Yes", "Tutoring_Sessions": 0,
        "Family_Income": "Low", "Teacher_Quality": "Medium", "School_Type": "Public",
        "Peer_Influence": "Negative", "Physical_Activity": 3, "Learning_Disabilities": "No",
        "Parental_Education_Level": "High School", "Distance_from_Home": "Far"}})


class Factor(BaseModel):
    variable: str
    aporte: float = Field(..., description="Puntos que suma o resta frente a un estudiante promedio")


class PrediccionRespuesta(BaseModel):
    id: int
    nota_estimada: float = Field(..., description="Nota estimada del examen (0-100)")
    riesgo: bool = Field(..., description="True si la nota estimada es menor a 65")
    umbral_riesgo: float
    modelo_version: str
    factores_a_favor: list[Factor]
    factores_en_contra: list[Factor]
    advertencias: list[str]
    creado_en: str


class PrediccionHistorial(BaseModel):
    id: int
    creado_en: str
    codigo_estudiante: Optional[str]
    entrada: dict
    nota_estimada: float
    riesgo: bool
    nota_real: Optional[float]
    modelo_version: str
    usuario: str


class PaginaHistorial(BaseModel):
    total: int
    pagina: int
    tamano: int
    items: list[PrediccionHistorial]


class NotaReal(BaseModel):
    nota_real: float = Field(..., ge=0, le=100, description="Nota que el estudiante obtuvo en el examen")


class Requisito(BaseModel):
    metrica: str
    valor: float
    umbral: str
    cumple: bool


class ModeloInfo(BaseModel):
    id: int
    version: str
    algoritmo: str
    hiperparametros: dict
    estado: str
    cumple_requisitos: bool
    dataset_id: int
    filas_entrenamiento: int
    filas_test: int
    mae: float
    rmse: float
    r2: float
    recall_riesgo: float
    precision_riesgo: float
    mae_base: float
    creado_en: str


class MetricasRespuesta(BaseModel):
    modelo: ModeloInfo
    requisitos: list[Requisito]
    produccion: dict


class ReentrenarSolicitud(BaseModel):
    dataset_id: Optional[int] = Field(None, description="Dataset a usar. Si se omite, se usa el último subido")
    incluir_notas_reales: bool = Field(True, description="Agregar las predicciones que ya tienen nota real")


class Entrenamiento(BaseModel):
    id: int
    estado: str
    dataset_id: int
    incluir_notas_reales: bool
    modelo_id: Optional[int]
    modelo_version: Optional[str]
    mensaje: Optional[str]
    solicitado_por: Optional[str]
    iniciado_en: str
    finalizado_en: Optional[str]


class Dataset(BaseModel):
    id: int
    nombre_archivo: str
    filas: int
    filas_validas: int
    origen: str
    subido_por: Optional[str] = None
    creado_en: str


class DatasetSubido(BaseModel):
    dataset: Dataset
    validacion: dict


class Usuario(BaseModel):
    id: int
    usuario: str
    nombre: str
    rol: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: Usuario
