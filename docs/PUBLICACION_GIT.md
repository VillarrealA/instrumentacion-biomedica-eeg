# Publicación de la entrega en Git

## 1. Preparar la carpeta del equipo

1. Descomprimir el repositorio.
2. Copiar resúmenes, métricas y figuras a `resultados/equipoXX/`.
3. Completar `informes/equipoXX.md`.
4. Colocar en `figuras/` únicamente las figuras finales.
5. Confirmar que `datos/crudos/` y `datos/physionet/` no contienen archivos
   rastreados por Git.

Compruébenlo con:

```bash
git status
```

Si aparece un archivo con todas las muestras del voluntario, no debe agregarse
al repositorio. Los CSV procesados muestra por muestra también están excluidos.

## 2. Crear el repositorio local

```bash
git init
git add .
git commit -m "Estructura inicial y protocolo EEG"
git branch -M main
```

## 3. Crear un repositorio remoto

Crear en GitHub o GitLab un repositorio privado llamado, por ejemplo:

```text
instrumentacion-biomedica-eeg-equipo01
```

No soliciten que el servicio agregue otro README, licencia o `.gitignore`, pues
ya están incluidos.

## 4. Enlazar y publicar

Reemplacen la dirección por la correspondiente a su equipo:

```bash
git remote add origin https://github.com/USUARIO/instrumentacion-biomedica-eeg-equipo01.git
git push -u origin main
```

## 5. Actualizaciones

```bash
git add resultados figuras informes docs
git commit -m "Integra Backyard Brains y comparación EEG"
git push
```

## Lista de revisión

- [ ] El README identifica al equipo mediante un código.
- [ ] El informe registra canal, referencia, muestreo, unidades y filtros.
- [ ] Todas las ventanas incluyen tiempo inicial, final y duración.
- [ ] Las figuras muestran unidades y condiciones.
- [ ] Se reportan `P_alfa` y `R_alfa` para BIOPAC y PhysioNet.
- [ ] Backyard Brains incluye eventos, ensayos aceptados/rechazados y promedio.
- [ ] La comparación no mezcla amplitudes absolutas sin justificar unidades y
      ganancia.
- [ ] Se identifican artefactos y criterio de aceptación.
- [ ] No se incluyen datos crudos, bases completas ni identificadores.
- [ ] Otro equipo puede ejecutar el programa con archivos del mismo formato.

## Historial sugerido

```text
1. Estructura inicial y protocolo EEG
2. Análisis del sujeto asignado de PhysioNet
3. Adquisición y documentación BIOPAC
4. PSD, potencia alfa y R_alfa
5. Eventos y promedio de Backyard Brains
6. Integración de las tres estaciones
7. Discusión y revisión final
```
