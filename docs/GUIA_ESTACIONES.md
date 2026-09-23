# Guía de trabajo por estaciones

## Preguntas de la práctica

1. ¿La potencia alfa aumenta al cerrar los ojos en BIOPAC y PhysioNet?
2. ¿Una respuesta pequeña ligada a un estímulo se vuelve más visible al
   alinear y promediar ensayos adquiridos con Backyard Brains?

No se busca que las tres estaciones produzcan la misma métrica. Se busca
reconocer cómo la pregunta fisiológica determina el protocolo, el análisis y la
evidencia que debe conservarse.

## Organización flexible

La estación Backyard Brains inicia con una demostración común. El profesor
explica el fenómeno de respuesta evocada y Erin muestra el montaje, el software,
la adquisición y las precauciones. Después, los grupos trabajan en tres frentes:

- **A. BIOPAC:** EEG espontáneo con ojos abiertos y cerrados.
- **B. Backyard Brains:** estímulos repetidos, eventos y promedio.
- **C. PhysioNet:** EEG multicanal de referencia.

BIOPAC y Backyard Brains son equipos compartidos. PhysioNet permanece disponible
para avanzar en paralelo. Los cambios de estación dependen de haber dejado un
registro útil y documentado, no de cumplir un tiempo fijo.

## Ruta 1: EEG espontáneo

BIOPAC y PhysioNet aplican el mismo flujo:

1. documentar fuente, canal, referencia, unidades y frecuencia de muestreo;
2. inspeccionar el registro antes de filtrar;
3. elegir ventanas comparables de 10 s;
4. calcular PSD y potencia entre 8 y 13 Hz;
5. obtener `R_alfa = P_alfa(cerrados) / P_alfa(abiertos)`;
6. decidir si el segmento se acepta o se rechaza;
7. registrar limitaciones y artefactos.

## Ruta 2: respuesta ligada a eventos

Backyard Brains sigue la operación indicada por Erin. El equipo debe:

1. registrar la modalidad del estímulo y el número de repeticiones;
2. conservar las marcas temporales o describir cómo se sincronizaron;
3. revisar el trazo continuo y reconocer ensayos con artefactos;
4. formar épocas antes y después de cada evento, si el formato lo permite;
5. corregir la línea base y promediar los ensayos aceptados;
6. comparar la variabilidad individual con el promedio;
7. concluir si la respuesta es repetible y temporalmente relacionada con el
   estímulo, sin asignar significado clínico.

## Productos mínimos

- figura de BIOPAC con señal temporal y PSD;
- figura o captura de Backyard Brains con eventos y promedio;
- figura de PhysioNet con señal temporal y PSD;
- tabla de metadatos y decisiones de calidad de las tres estaciones;
- `R_alfa` para BIOPAC y PhysioNet;
- número de eventos y ensayos aceptados/rechazados en Backyard Brains;
- conclusión instrumental breve;
- historial de Git con commits descriptivos.

## Preguntas para la discusión

1. ¿Cambió la potencia alfa en la misma dirección en BIOPAC y PhysioNet?
2. ¿Qué cambió entre un ensayo Backyard y el promedio de varios?
3. ¿Qué canal, montaje y referencia se utilizaron en cada adquisición?
4. ¿Qué artefacto dominó cada registro?
5. ¿La respuesta Backyard conserva una latencia semejante entre subconjuntos
   de ensayos?
6. ¿Qué comparaciones de amplitud serían inválidas entre sistemas?
7. ¿El filtrado intentó corregir un problema que debió resolverse durante la
   adquisición?
8. ¿Qué adquisición repetirían y qué cambiarían primero?

## Interpretación

Un valor `R_alfa > 1` es compatible con mayor potencia alfa durante ojos
cerrados en la ventana analizada. Una deflexión en el promedio Backyard es
compatible con una respuesta ligada al evento sólo si la sincronía, la
repetibilidad y los artefactos son defendibles. Ninguno de estos resultados
constituye por sí solo una conclusión clínica.
