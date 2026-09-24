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
- **Estudiantes:** registran metadatos, identifican artefactos, conservan los
  archivos y justifican la calidad del resultado.

## Procedimiento

El procedimiento operativo exacto es el que muestre Erin. No sustituyan sus
indicaciones por esta guía. Durante la demostración documenten:

1. modalidad del estímulo;
2. posiciones de electrodos, referencia y tierra;
3. frecuencia de muestreo, ganancia y filtros disponibles;
4. forma de generar o marcar cada evento;
5. número de repeticiones;
6. criterio para rechazar ensayos;
7. modelo del equipo y forma de conexión con la computadora.

En Spike Recorder de escritorio, inicien explícitamente la grabación. Al
terminar, conserven juntos el WAV y el archivo de eventos asociado:

```text
registro.wav
registro-events.txt
```

El archivo `-events.txt` contiene renglones `nombre,tiempo_en_segundos`. Antes
de analizar, ábranlo como texto y comprueben que las marcas correspondan al
protocolo. Para una respuesta evocada, la marca debe representar el inicio real
del estímulo; una anotación manual tardía sólo sirve como referencia aproximada.

## Análisis directo de Spike Recorder

Coloquen ambos archivos en `datos/crudos/`. Si comparten el nombre base, el
programa encuentra automáticamente el archivo de eventos:

```bash
python scripts/analiza_backyard.py \
  datos/crudos/registro.wav \
  --pre 0.2 --post 0.6 \
  --output-dir resultados/equipo01/backyard
```

Si el archivo de eventos tiene otro nombre:

```bash
python scripts/analiza_backyard.py \
  datos/crudos/registro.wav \
  --events datos/crudos/mis-eventos.txt \
  --output-dir resultados/equipo01/backyard
```

Para analizar solamente una clase de evento, por ejemplo `2`, añadan
`--event-name 2`. La opción puede repetirse. En un WAV multicanal, seleccionen
el canal con `--channel 0`, `--channel 1`, etcétera.

El programa filtra la señal, corrige la línea base, forma épocas y guarda
ensayos, promedio, figura y métricas descriptivas. Los WAV clásicos se reportan
en **unidades arbitrarias (u.a.)**. No conviertan automáticamente la amplitud a
µV sin una calibración documentada del modelo y del sistema de adquisición.

## Compatibilidad con CSV

El programa conserva el formato CSV de demostración y lo admite como
alternativa:

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
muestras. La plantilla permanece en
`config/backyard_eventos_plantilla.csv`.

## Criterios de calidad

- las marcas corresponden al inicio real de los estímulos;
- existen suficientes ensayos útiles para observar repetibilidad;
- no domina un parpadeo, movimiento o actividad muscular;
- el promedio no depende de uno o dos ensayos extremos;
- el modelo, muestreo, filtros y unidades quedan documentados;
- no se asigna significado clínico a una deflexión aislada.

## Producto

- figura del registro continuo, eventos, ensayos y promedio;
- tabla de metadatos y clases de evento utilizadas;
- número de ensayos aceptados/rechazados;
- artefacto principal;
- conclusión sobre repetibilidad, sincronización y limitaciones.
