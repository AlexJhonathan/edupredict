# Model Card - modelo_v1

Modelo: Huber (scikit-learn 1.9.1), parámetros {'modelo__alpha': 3.0, 'modelo__epsilon': 2.0}
Uso previsto: estimar la nota del examen para ofrecer tutoría a quien tenga nota estimada < 65.
No usar para: calificar, sancionar ni excluir estudiantes; las decisiones las toma el docente.
Datos: Student Performance Factors (Kaggle), 5284 estudiantes en train y 1322 en test.
Variables: 18 (Gender excluido y usado solo para auditar equidad).

Resultados en test:
- MAE = 0.376 puntos (modelo base: 2.810), RMSE = 1.582, R2 = 0.819
- Recall de riesgo = 1.000, precisión de riesgo = 0.811

Limitaciones:
- Un pequeño grupo de notas muy altas (78-100) no se explica con las variables y el modelo las subestima.
- Fuera de los rangos de entrenamiento (por ejemplo asistencia < 60 %) el modelo extrapola.
- Datos de un solo periodo; hay que monitorear drift en producción.
