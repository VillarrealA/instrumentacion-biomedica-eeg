# Estación A — Adquisición EEG con BIOPAC

## Objetivo

Obtener un EEG corto, documentado y sin saturación para comparar ojos abiertos
y ojos cerrados.

## Antes de registrar

1. Identifiquen el modelo, módulo, canal y software utilizados.
2. Anoten posiciones de electrodos, referencia y tierra.
3. Comprueben contacto, cables, escala y ausencia de saturación.
4. Registren frecuencia de muestreo, unidades y filtros activos.
5. Asignen al voluntario un código sin datos personales.

## Protocolo sugerido

1. Mantengan al voluntario sentado, relajado y con indicaciones claras.
2. Registren entre 20 y 30 s con ojos cerrados.
3. Registren entre 20 y 30 s con ojos abiertos y mirada fija.
4. Repitan ojos cerrados para revisar reproducibilidad.
5. Registren un parpadeo marcado fuera de las ventanas principales.
6. Anoten movimiento, habla, tensión mandibular o interrupciones.

## Selección de ventanas

Elijan 10 s de cada condición con:

- ausencia de saturación o recorte;
- contacto estable;
- sin parpadeos grandes dentro del intervalo;
- sin movimiento evidente;
- misma duración y mismo canal;
- unidades y filtros documentados.

## Análisis

Exporte ojos abiertos y cerrados a CSV y ejecute:

```bash
python scripts/analiza_biopac.py \
  datos/crudos/biopac_abiertos.csv \
  datos/crudos/biopac_cerrados.csv \
  --unit uV --open-start 0 --closed-start 0 --duration 10 \
  --output-dir resultados/equipo01/biopac
```

Ajusten unidad, columnas, frecuencia de muestreo y tiempos iniciales a su
archivo. Revisen la figura generada antes de aceptar las métricas.

## Criterio de repetición

Repitan la adquisición si el segmento queda dominado por saturación, pérdida
de contacto, movimiento intenso o una escala incorrecta. El procesamiento no
recupera información perdida durante la adquisición.

## Seguridad y privacidad

- Utilicen sólo BIOPAC y los accesorios indicados por el docente.
- No realicen estimulación eléctrica.
- No coloquen electrodos sobre piel lesionada o irritada.
- Suspendan el registro ante cualquier molestia.
- No suban nombres, matrículas, rostros ni archivos crudos identificables.
