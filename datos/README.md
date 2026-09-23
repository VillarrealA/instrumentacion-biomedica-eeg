# Datos

- `demo/` contiene señales sintéticas para comprobar el flujo de análisis.
- `crudos/` se utiliza localmente para exportaciones BIOPAC y Backyard Brains.
- `physionet/` se crea al descargar los registros R01 y R02.

La plantilla `config/backyard_eventos_plantilla.csv` documenta el formato
opcional para analizar ensayos marcados. Si el software de Backyard Brains no
exporta ese formato, conserven localmente el archivo original y publiquen sólo
la figura, los metadatos y los resultados derivados.

Los datos fisiológicos crudos y las descargas de PhysioNet no deben publicarse
en Git. La atribución y los parámetros de descarga sí deben conservarse.
