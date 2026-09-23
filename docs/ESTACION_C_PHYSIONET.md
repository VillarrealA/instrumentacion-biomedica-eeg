# Estación C — EEG multicanal de PhysioNet

## Objetivo

Aplicar el mismo procedimiento de análisis a un EEG multicanal documentado y
comparar dos registros basales del mismo sujeto.

## Conjunto de datos

Se utiliza *EEG Motor Movement/Imagery Dataset* versión 1.0.0:

- R01: un minuto de EEG basal con ojos abiertos;
- R02: un minuto de EEG basal con ojos cerrados;
- 64 señales EEG y un canal de anotaciones;
- frecuencia de muestreo de 160 Hz;
- electrodos distribuidos con el sistema internacional 10-10;
- archivos EDF+.

Fuente: <https://physionet.org/content/eegmmidb/1.0.0/>

DOI: <https://doi.org/10.13026/C28G6P>

## Actividad

1. Ejecuten el programa con el sujeto asignado.
2. Anoten sujeto, registros, canal, referencia, unidades y muestreo.
3. Comparen ventanas de 10 s tomadas del mismo intervalo temporal.
4. Revisen primero la señal temporal.
5. Calculen la PSD con los mismos parámetros.
6. Obtengan potencia alfa absoluta, potencia alfa relativa y `R_alfa`.
7. Repitan opcionalmente en O2 u Oz.
8. Describan artefactos o diferencias entre canales sin formular diagnósticos.

## Ejecución

```bash
python scripts/analiza_physionet.py \
  --subject 1 --channel O1 --start 5 --duration 10 \
  --output-dir resultados/equipo01/physionet
```

La primera ejecución descarga los archivos en `datos/physionet/`. Esa carpeta
está excluida de Git.

## Lectura de resultados

`R_alfa > 1` indica mayor potencia alfa en ojos cerrados para ese canal y esas
ventanas. Comprueben la figura antes de interpretar el número. Un transitorio
de gran amplitud puede aumentar la potencia integrada sin representar un ritmo
alfa estable.

## Producto

- figura de señal temporal y PSD;
- archivo de métricas y resumen;
- canal y ventanas analizadas;
- decisión de calidad;
- comentario sobre diferencias regionales, si se revisaron otros canales.
