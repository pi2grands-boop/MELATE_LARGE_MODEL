# `data/cache/melate-e/`: la caché que protege a un servidor ajeno

- **Fecha/hora:** 2026-10-03 05-15
- **Área:** Almacenamiento · **Acción:** Añadir

## Qué se añadió

```
data/cache/melate-e/
  melate/4272.html      ~8 KB
  revancha/4272.html    ~7 KB
```

Una página por sorteo y juego, tal cual la sirvió el sitio. Tras la cosecha de esta fase: **400
ficheros, 2,9 MB**.

## Por qué permanente y no con caducidad

**Una tabla de ganadores de un sorteo pasado no cambia nunca.** Es un hecho histórico: quién
acertó el sorteo 4272 y cuánto cobró ya está decidido. Un TTL solo serviría para volver a molestar
al servidor de otra persona por el mismo dato.

El efecto buscado es concreto y se mide: **una segunda corrida sobre la misma ventana hace cero
peticiones de red.** Comprobado — la verificación completa de esta fase, que recorre 400 sorteos y
dos ventanas distintas, imprime `peticiones de red en toda esta verificacion: 0`.

Esto la hace distinta de los otros dos almacenes del proyecto:

| Almacén | Qué guarda | Por qué |
|---|---|---|
| `data/raw/<fecha>/` | CSV oficiales congelados | Que una cifra publicada se pueda reproducir |
| `prereg/*.json` | Preregistros sellados | Que no se puedan alterar |
| **`data/cache/melate-e/`** | **Páginas de un tercero** | **No volver a pedirle lo mismo** |

Los dos primeros se publican. **Este no.**

## Por qué NO se publica, al contrario que el snapshot

`data/raw/` está en el repositorio a propósito: 435 KB que hacen que el hash del protocolo
signifique algo. Con la caché la respuesta es la contraria, y por dos razones:

1. **Es contenido de un tercero.** Republicar las páginas de alguien no es nuestro papel. Lo que
   el repositorio publica son las **cifras derivadas** —ventas, premios menores, el cociente del
   calendario—, que sí son nuestras.
2. **Es reconstruible**, a 1 solicitud por segundo y con la ventana declarada.

Entrada en `.gitignore`, con el porqué escrito al lado para que nadie la quite por descuido.

## El coste de reconstruirla, con números

| Juego | Sorteos de la era 6/56 | Páginas |
|---|---|---|
| Melate | 2.184 | 2.184 |
| Revancha | 2.184 | 2.184 |
| Revanchita | 1.902 | **0** — no tiene tabla |
| **Total** | | **4.368** · **1 h 13 min** · ~33 MB |

Lo que está cacheado hoy es la ventana 3973-4272 de Melate y 4173-4272 de Revancha: **400 páginas,
6 min 39 s**. El histórico completo **no se ha descargado y no se descargará sin decisión
explícita del usuario** (ver el dictamen).

## Lo que no entra en la caché

Dos guardas, las dos con test, porque una caché que acepta cualquier cosa es peor que no tenerla:
lo malo se queda en disco y se lee como bueno para siempre.

| Caso | Qué pasa |
|---|---|
| HTTP distinto de 200 | `SitioBloqueado`, no se escribe |
| HTTP 404 | `SorteoNoPublicado`, no se escribe — y **no es un bloqueo** |
| 200 sin `<table>` | `SitioBloqueado`: huele a página de bloqueo |
| Más de 1 MB | `SitioBloqueado`: las reales pesan 5-8 KB |
| Revanchita | `ValueError` antes de pedir nada |

## Cómo verificar

```powershell
.venv\Scripts\python.exe -m pytest tests/test_popularidad.py -q -k cache
.venv\Scripts\python.exe -m melate.popularity --desde 4173 --hasta 4272 --datos data\raw\2026-10-02
```

La segunda imprime las peticiones de red de esa corrida. Con la caché poblada: **0**.

## Cómo revertir

Borrar `data/cache/` y su entrada en `.gitignore`. No se pierde nada que no se pueda volver a
descargar.

Relacionado: `Almacenamiento/Añadir/2026-10-03_00-13_s1-snapshots-congelados.md`,
`Conexiones/Añadir/2026-10-03_05-15_s3-tablas-de-ganadores-melate-e.md`,
`Fases/2026-10-03_popularidad/Decisiones/2026-10-03_02-40_s3-dictamen-terminos-melate-e.md`.
