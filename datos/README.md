# Datos

- `demo/` contiene señales sintéticas para comprobar el flujo de análisis.
- `crudos/` se utiliza localmente para exportaciones BIOPAC y Backyard Brains.
- `physionet/` se crea al descargar los registros R01 y R02.

Para Backyard Brains, conserven juntos los archivos nativos de Spike Recorder:

```text
datos/crudos/registro.wav
datos/crudos/registro-events.txt
```

`scripts/analiza_backyard.py` infiere el nombre del archivo de eventos a partir
del WAV. Si tiene otro nombre, utilicen `--events RUTA`; si el WAV es
multicanal, seleccionen con `--channel N`. Los WAV clásicos se analizan en
unidades arbitrarias y no deben etiquetarse como µV sin una calibración
documentada.

El CSV sigue admitido como alternativa y para la demostración. La plantilla se
encuentra en `config/backyard_eventos_plantilla.csv`.

Los datos fisiológicos crudos y las descargas de PhysioNet no deben publicarse
en Git. La atribución y los parámetros de descarga sí deben conservarse.
