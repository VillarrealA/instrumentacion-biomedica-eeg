# Instrumentación Biomédica — Práctica EEG

Repositorio de apoyo para la práctica de electroencefalografía del Módulo 2 de
Instrumentación Biomédica.

## Objetivo general

Integrar tres fuentes de señal mediante una documentación común y dos rutas de
análisis relacionadas:

1. **BIOPAC** — adquisición experimental de EEG de superficie durante ojos
   abiertos y ojos cerrados.
2. **Backyard Brains** — demostración guiada de una respuesta ligada a un
   estímulo y del efecto del promediado de ensayos.
3. **PhysioNet** — análisis de registros multicanal documentados del conjunto
   *EEG Motor Movement/Imagery Dataset*.

El objetivo no es decidir cuál sistema es mejor ni forzar una sola métrica.
BIOPAC y PhysioNet estudian EEG espontáneo y reactividad alfa; Backyard Brains
introduce una respuesta sincronizada con un evento. En los tres casos se
documentan montaje, referencia, filtros, muestreo, artefactos y calidad.

## Pregunta experimental

La práctica responde dos preguntas:

1. ¿La potencia alfa aumenta al cerrar los ojos en BIOPAC y PhysioNet?
2. ¿El promedio de ensayos de Backyard Brains permite observar una respuesta
   temporalmente relacionada con el estímulo?

La métrica común es

```text
R_alfa = P_alfa(ojos cerrados) / P_alfa(ojos abiertos)
```

El cociente se calcula dentro de cada sistema. Las amplitudes absolutas de
BIOPAC y PhysioNet no se comparan directamente si no se demuestra que tienen
unidades, ganancia, filtros y referencia equivalentes.

## Flujo de trabajo

```text
BIOPAC ───────┐
              ├── ventanas ── PSD ── potencia alfa ── R_alfa
PhysioNet ────┘

Backyard Brains ── eventos ── épocas ── línea base ── promedio

Ambas rutas ──────────────────────────────────────────── documentación en Git
```

## Qué se documenta

Para cada fuente se registran, cuando estén disponibles:

- identificación del sistema o del registro;
- código del voluntario o número del sujeto de PhysioNet;
- posiciones de electrodos, canal, referencia y tierra;
- condición de ojos abiertos o cerrados;
- frecuencia de muestreo, unidades y duración;
- ganancia, filtros analógicos o digitales y notch;
- intervalo analizado y criterio de selección;
- saturación, deriva, ruido de red, parpadeo y movimiento;
- potencia alfa absoluta y relativa;
- valor de `R_alfa` y criterio de aceptación del segmento.
- modalidad del estímulo, marcas de evento, número de ensayos y rechazos;
- ventana de época, corrección de línea base y evidencia del promedio.

## Estructura del repositorio

```text
instrumentacion-biomedica-eeg/
├── README.md
├── requirements.txt
├── environment.yml
├── .gitignore
├── LICENSE
├── CITATION.cff
│
├── scripts/
│   ├── eeg_core.py
│   ├── analiza_biopac.py
│   ├── analiza_backyard.py
│   ├── analiza_physionet.py
│   ├── comparar_resultados.py
│   ├── generar_datos_demo.py
│   └── ejecutar_demo.py
│
├── docs/
│   ├── GUIA_ESTACIONES.md
│   ├── ESTACION_A_BIOPAC.md
│   ├── ESTACION_B_BACKYARD.md
│   ├── ESTACION_C_PHYSIONET.md
│   └── PUBLICACION_GIT.md
│
├── config/
│   └── metadatos_plantilla.json
│
├── informes/
│   └── equipoXX.md
│
├── datos/
│   ├── README.md
│   ├── demo/
│   └── crudos/
│
├── figuras/
├── resultados/
└── tests/
```

## Instalación

### Opción 1 — pip

```bash
python -m pip install -r requirements.txt
```

### Opción 2 — Conda

```bash
conda env create -f environment.yml
conda activate eeg-instrumentacion
```

## Comprobación inicial

Antes de trabajar con señales reales puede comprobarse la instalación mediante
dos registros sintéticos:

```bash
python scripts/ejecutar_demo.py
```

El comando genera datos de prueba y guarda una figura, un resumen y un archivo
de métricas en `resultados/demo/`. Los datos sintéticos sirven para comprobar el
flujo; no representan un registro clínico.

También puede ejecutarse la prueba automática:

```bash
python -m pytest -q
```

## Uso durante las estaciones

### Estación A — BIOPAC

Exporte por separado una condición de ojos abiertos y otra de ojos cerrados.
Los archivos deben contener tiempo y un canal EEG. Guárdelos localmente en
`datos/crudos/` y ejecute, por ejemplo:

```bash
python scripts/analiza_biopac.py \
  datos/crudos/biopac_abiertos.csv \
  datos/crudos/biopac_cerrados.csv \
  --unit uV --duration 10 --output-dir resultados/equipo01/biopac
```

Si la señal está expresada en voltios o milivoltios, utilice `--unit V` o
`--unit mV`. Si no existe columna de tiempo, añada `--fs` con la frecuencia de
muestreo. Para elegir columnas específicas están disponibles `--time-column` y
`--signal-column`.

### Estación B — Backyard Brains

Erin mostrará el montaje, el software y el procedimiento operativo. El equipo
de estudiantes debe concentrarse en registrar los metadatos, los eventos, el
número de ensayos y la calidad. Si se obtiene un CSV con columnas de tiempo,
señal y evento, puede analizarse con:

```bash
python scripts/analiza_backyard.py \
  datos/crudos/backyard_eventos.csv \
  --time-column time_s --signal-column signal_uv --event-column event \
  --unit uV --pre 0.2 --post 0.6 \
  --output-dir resultados/equipo01/backyard
```

La plantilla esperada está en `config/backyard_eventos_plantilla.csv`. Si el
software no exporta datos compatibles, se entrega una captura del trazo o del
promedio, acompañada por la hoja de metadatos y una descripción de los ensayos.
No se debe improvisar una conversión durante la clase.

### Estación C — PhysioNet

El programa descarga localmente R01, ojos abiertos, y R02, ojos cerrados, del
sujeto asignado. Por omisión analiza el canal O1:

```bash
python scripts/analiza_physionet.py \
  --subject 1 --channel O1 --start 5 --duration 10 \
  --output-dir resultados/equipo01/physionet
```

La descarga queda en `datos/physionet/`, carpeta excluida de Git. Fuente:
<https://physionet.org/content/eegmmidb/1.0.0/>.

R01 y R02 deben analizarse como registros basales separados. El conjunto tiene
64 señales EEG muestreadas a 160 Hz en formato EDF+.

### Comparación de reactividad alfa

Después de obtener los archivos de métricas de ambas estaciones:

```bash
python scripts/comparar_resultados.py \
  resultados/equipo01/biopac/biopac_metricas.json \
  resultados/equipo01/physionet/physionet_metricas.json \
  --output-dir resultados/equipo01/comparacion
```

La gráfica normaliza la condición de ojos abiertos a uno dentro de cada
estación. Así se compara la dirección de la reactividad alfa sin confundirla
con una comparación de amplitudes absolutas entre instrumentos.

El resultado de Backyard Brains se discute por separado: se compara el trazo
de ensayos individuales con el promedio, se revisa la sincronía de los eventos
y se decide si la respuesta es repetible. No se compara su amplitud directamente
con `R_alfa`.

Los programas funcionan como herramientas de visualización y análisis. La
práctica evalúa las decisiones de instrumentación, la trazabilidad y la
interpretación de los resultados, no la programación.

## Datos fisiológicos

Los registros crudos obtenidos de estudiantes deben permanecer en
`datos/crudos/` y **no se incluyen en el repositorio público**. Tampoco se
redistribuyen las descargas completas de PhysioNet.

No deben publicarse nombres, matrículas, fotografías identificables ni otros
datos personales. En Git se conservan el código, los parámetros, las ventanas
analizadas, los resultados derivados, las figuras y las conclusiones.

## Seguridad y alcance

El material tiene fines docentes y no permite establecer diagnósticos. La
adquisición en personas sólo debe realizarse con BIOPAC o Backyard Brains, los
accesorios indicados y el esquema autorizado por el responsable del
laboratorio. La operación del Backyard Brains seguirá la demostración de Erin.
No se realiza estimulación eléctrica.

## Control de versiones

Un historial posible sería:

```text
Documenta protocolo y parámetros de EEG
Agrega análisis del sujeto asignado de PhysioNet
Agrega adquisición BIOPAC y selección de ventanas
Calcula PSD, potencia alfa y R_alfa
Documenta eventos y promedio de Backyard Brains
Integra las tres estaciones sin mezclar métricas
Revisa discusión y conclusiones finales
```

Así se conserva no sólo el resultado final, sino también cómo se construyó.

## Referencias principales

- Malmivuo, J., y Plonsey, R. *Bioelectromagnetism*. Oxford University
  Press, 1995.
- Webster, J. G., y Nimunkar, A. J. (eds.). *Medical Instrumentation:
  Application and Design*, 5.a ed., Wiley, 2020.
- Husar, P., y Gašpar, G. *Electrical Biosignals in Biomedical Engineering*.
  Springer, 2023.
- PhysioNet. *EEG Motor Movement/Imagery Dataset*, versión 1.0.0,
  DOI: 10.13026/C28G6P.

## Licencias

El código se distribuye con licencia MIT. Los datos de PhysioNet conservan su
propia licencia y atribución; los programas los descargan desde la fuente
oficial y no los redistribuyen dentro de este repositorio.
