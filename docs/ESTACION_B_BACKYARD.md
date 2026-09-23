# Estación B — Backyard Brains

## Propósito

Observar cómo una respuesta pequeña, relacionada temporalmente con un
estímulo repetido, puede recuperarse mediante alineación y promediado de
ensayos.

## División de responsabilidades

- **Profesor:** explica el fenómeno, la necesidad de sincronizar eventos y el
  sentido del promedio.
- **Erin:** enseña el montaje, el software, la adquisición y las precauciones
  específicas del equipo.
- **Estudiantes:** registran metadatos, identifican artefactos, conservan la
  evidencia y justifican la calidad del resultado.

## Procedimiento

El procedimiento operativo exacto es el que muestre Erin. No sustituyan sus
indicaciones por esta guía. Durante la demostración documenten:

1. modalidad del estímulo;
2. posiciones de electrodos, referencia y tierra;
3. frecuencia de muestreo, unidades, ganancia y filtros disponibles;
4. forma de generar o marcar cada evento;
5. número de repeticiones;
6. criterio para rechazar ensayos;
7. archivo, captura o resultado que puede exportarse.

## Análisis opcional de CSV

Si el software proporciona o permite construir un CSV con columnas de tiempo,
señal y evento, utilicen:

```bash
python scripts/analiza_backyard.py \
  datos/crudos/backyard_eventos.csv \
  --time-column time_s \
  --signal-column signal_uv \
  --event-column event \
  --unit uV --pre 0.2 --post 0.6 \
  --output-dir resultados/equipo01/backyard
```

La columna `event` vale 1 en el inicio del estímulo y 0 en el resto de las
muestras. Ajusten `--pre` y `--post` al protocolo real. El programa realiza
corrección de línea base, forma épocas y guarda ensayos, promedio, figura y
métricas descriptivas.

Si el formato no es compatible, no conviertan a ciegas. Entreguen una captura
del trazo o promedio junto con metadatos, número de eventos, artefactos y una
conclusión cualitativa.

## Criterios de calidad

- las marcas corresponden al inicio real de los estímulos;
- existen suficientes ensayos útiles para observar repetibilidad;
- no domina un parpadeo, movimiento o actividad muscular;
- el promedio no depende de uno o dos ensayos extremos;
- la escala, unidades y filtros quedan documentados;
- no se asigna significado clínico a una deflexión aislada.

## Producto

- figura o captura de ensayos y promedio;
- tabla de metadatos y eventos;
- número de ensayos aceptados/rechazados;
- artefacto principal;
- conclusión sobre repetibilidad y limitaciones.
