# Tres reportes cambian de forma: el veredicto, la popularidad y la cartera

- **Fecha/hora:** 2026-10-04 16:35
- **Área:** Estructura_Datos · **Acción:** Modificar
- **Chat / página:** cierre de la Fase 4 · `Fases/2026-10-04_app-local/`
- **Archivos afectados:** `src/melate/lab.py`, `src/melate/popularity.py`, `src/melate/portfolio.py`,
  `reportes/2026-10-04_veredicto.json`, `reportes/2026-10-03_popularidad.json`,
  `reportes/2026-10-04_popularidad-melate-300-sorteos.json`, `reportes/2026-10-03_cartera.json`

Los tres cambios **añaden** claves; ninguno quita ni renombra una. Un lector de la forma anterior
sigue funcionando, y la base de la app distingue un reporte viejo («no se sabe») de uno nuevo que dice
«ninguno».

## 1 · El veredicto de `melate.lab` dice sobre qué datos juzgó

Clave nueva **`datos`**, un bloque por juego:

```
datos.<Juego>   {sha256, origen, bytes, ultimo_concurso, ultima_fecha}
```

La regla 6 del protocolo pide el hash del dataset en cada corrida, y el veredicto —lo único que
juzga— no lo guardaba. Se encontró al leer el código antes de empezar la fase. El porqué y el test,
en `Reproducibilidad/Arreglos_Bugs/2026-10-04_16-35_s4-el-veredicto-registra-sus-datos.md`.
`reportes/2026-10-04_veredicto.json` es el primero que la lleva; el de la Fase 2 se conserva tal cual,
y la app dice que no la registra.

## 2 · La popularidad distingue un sorteo sin premios publicados

Actualiza la forma de `Estructura_Datos/Añadir/2026-10-03_05-15_s3-tabla-de-ganadores-y-cartera.md`:

```
juegos.<Juego>
  sorteos_sin_premios     NUEVO  lista de los sorteos cuya tabla trae ganadores y no importes
  muestras[]
    premios_publicados    NUEVO  false si alguna categoría menor con ganadores trae $0.00
    bolsa_repartida, menores_directo, menores_por_bolsa   null en esos sorteos
```

**Por qué** (C1, decidido por el usuario): tres tablas de la ventana de 300 —los sorteos 4107, 4111 y
4119— traían todos los premios a `$0.00`. Una categoría con ganadores siempre paga algo, así que eso
es un dato que falta, no un premio de cero. Esos sorteos siguen contando para las ventas y el efecto
calendario, que solo usan los ganadores, y dejan de contar para los premios menores.

| Ventana de 300, premios menores por bolsa | Antes | Ahora |
|---|---|---|
| Sorteos que cuentan | 300 | **297** |
| Media | 4,6035 | **4,6500** |
| Mediana | 4,6422 | **4,6465** |
| cv | 0,1156 | **0,0565** |
| Mínimo | 0,0 | **3,1007** |

Las ventas, el efecto calendario y la ventana de 100 —la que da el EV medido del `CLAUDE.md`— no
cambian una cifra. Los dos reportes se regeneraron desde la caché, con 0 peticiones de red.

## 3 · La valoración de una cartera dice con qué se hizo

```
valoracion   {bolsa, menores_brutos, impuesto,     NUEVOS, al principio
              coste, valor_esperado, rendimiento, …el resto, igual}
```

**Por qué** (C4, decidido por el usuario): `portfolio.valorar` no guardaba la bolsa ni los premios
menores que recibía, y una valoración sin sus supuestos no se puede comprobar. La cartera se regeneró
con sus parámetros originales y salió **idéntica** —los 20 boletos, el EV de 128,82 $— más los tres
campos.

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests\test_almacen.py -k registra_los_datos -q
.venv\Scripts\python.exe -m pytest tests\test_popularidad.py -k sin_premios -q
.venv\Scripts\python.exe -m pytest tests\test_cartera.py -k con_que_se_hizo -q
```

Los tres tests dan dos valores a lo que miden (el snapshot frente a unos datos recortados; la tabla
real frente a la misma con los importes borrados; dos bolsas), y los tres tienen su mutación en
`scripts/mutar.py`.

## Cómo revertir

Cada cambio es independiente: quitar `datos` de `lab.evaluar`; quitar `premios_publicados` y su uso
en `popularity.analizar`; quitar las tres claves de `portfolio.valorar`. Y regenerar los reportes
afectados. Ninguno toca el oráculo ni la paridad.

Relacionado: `Estructura_Datos/Añadir/2026-10-03_05-15_s3-tabla-de-ganadores-y-cartera.md`,
`Estructura_Datos/Añadir/2026-10-04_16-35_s4-esquema-de-melate-duckdb.md`,
`Reproducibilidad/Arreglos_Bugs/2026-10-04_16-35_s4-el-veredicto-registra-sus-datos.md`,
`Fases/2026-10-04_app-local/Decisiones/2026-10-04_11-00_s4-lo-que-decidio-el-usuario.md`.
