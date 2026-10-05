# La app enseña el holdout como lo que es, y de qué snapshot sale cada cosa

- **Fecha/hora:** 2026-10-05 10:27
- **Área:** Interconexion · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 5 · `app/streamlit_app.py`
- **Archivos afectados:** `app/streamlit_app.py`

## Qué cambia en las pantallas

`Interconexion/Añadir/2026-10-04_16-35_s4-las-pantallas-de-la-app.md` sigue valiendo: el orden en que
se pinta cada pantalla, la navegación y la naturaleza de cada una. Cambia lo que dicen:

| Dónde | Antes | Ahora |
|---|---|---|
| **La cabecera**, en todas | «holdout de 0 sorteos» | «holdout de **1 sorteo de los 1 778 que necesita la condición 5**», y el snapshot del veredicto. «1 sorteo» en singular, y los miles con un espacio que no parte la línea |
| **Veredicto**: las métricas | el holdout, a secas | el holdout, con «de los 1 778 que necesita la condición 5» debajo |
| **Veredicto**: las condiciones | una rejilla que cortaba el motivo de la condición 5 justo antes de «hacen falta 1778 sorteos» | una tabla estática que parte las frases; cada celda, escapada |
| **Veredicto**: por juego | sorteos y Δ | sorteos, **aciertos por boleto** y Δ; debajo, el mínimo detectable de ese holdout y cuándo podrá cumplirse la condición 5 |
| **Veredicto**: las órdenes | `melate.lab` sin `--datos` | **`python -m melate.ciclo`** para un veredicto nuevo, y `melate.lab --datos data\raw\<snapshot>` para reproducir el de arriba |
| **Veredicto**: el historial | ruta, fecha, condiciones | y su snapshot |
| **Exploración** y **Valor esperado** | los datos del informe | y su snapshot, o que ningún snapshot congelado lo respalda |
| **Procedencia** | un índice de `reportes/` y `prereg/` | y de los `SHA256.txt` de `data/raw/`; una tabla nueva, «Snapshots congelados»; «¿Vale?» y «Por qué no» delante en la tabla de ficheros, que antes quedaban fuera del borde |

La app sigue sin calcular: el «1 778» lo publica el laboratorio en el veredicto
(`resultados.holdout_necesario`), y la app lo pone al lado.

## Comprobado en un navegador, con el veredicto de verdad

El 2026-10-05, con el veredicto del 4274 recién emitido: el lanzador en `127.0.0.1:8507`, un Edge
propio sin interfaz y **clics de ratón de verdad** en la barra lateral —las cinco pantallas, ida y
vuelta—. La cabecera dice *«sin ventaja demostrada · … 2 de 5 condiciones, holdout de 1 sorteo de los
1 778 que necesita la condición 5, … snapshot 2026-10-04_4274»*; los cinco motivos se leen enteros;
las otras pantallas cogen solas el informe del snapshot nuevo. **El servidor no abrió ni una conexión
hacia fuera**, con un proxy que apunta todas.

Cuatro de estos cambios los pidió mirar la app, no un test: el número partido en dos líneas, el motivo
cortado, la columna fuera del borde y que la tabla nueva pasaba sus celdas por Markdown. Están en
`Fases/2026-10-04_ciclo-vivo/Bugs/2026-10-04_20-37_s5-review-c3-app-y-almacen.md`, B4-B8.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests\test_app.py -q
.venv\Scripts\python.exe -m melate.app       # y recorrerla: la cabecera, en cada pantalla
```

## Cómo revertir

Descrito en
`Fases/2026-10-04_ciclo-vivo/Cambios/2026-10-05_10-00_s5-c3-la-app-y-el-almacen-con-sus-snapshots.md`.
No se recomienda quitar ninguna pieza suelta: cada una existe por algo que se vio en la pantalla.

Relacionado: `Interconexion/Añadir/2026-10-04_16-35_s4-las-pantallas-de-la-app.md`,
`Protocolo_Estadistico/Añadir/2026-10-05_10-26_s5-el-primer-veredicto-con-holdout.md`,
`Red/Añadir/2026-10-04_16-35_s4-que-sirve-la-app-y-a-quien.md`.
