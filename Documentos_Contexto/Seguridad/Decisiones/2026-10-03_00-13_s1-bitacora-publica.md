# Decisión: la bitácora se publica, y nada personal sale de la máquina

- **Fecha/hora:** 2026-10-03 00:13
- **Área:** Seguridad · **Acción:** Decisiones
- **Decidido por:** usuario · **Estado:** cerrada
- **Alcance:** todo documento `.md` del proyecto, el `.gitignore`, la identidad de git de este
  repositorio y `scripts/colador.ps1`

## La decisión

Publicar la bitácora completa en el repositorio público, y no publicar nada personal: ni
contraseñas, ni usuarios, ni direcciones, ni rutas de la máquina.

Esto **invierte la Regla 0 por defecto** de la bitácora, que es "nunca llega a producción". La regla
existe porque una bitácora contiene rutas internas y detalles de implementación; aquí la decisión es
que el funcionamiento y la documentación son precisamente lo que se quiere compartir, y que lo
personal se excluye por otros medios.

## Alternativas descartadas

| Opción | Por qué no |
|---|---|
| No publicar la bitácora (la regla por defecto) | El usuario quiere que el funcionamiento y el porqué sean públicos. En un proyecto cuyo propósito es medir con honestidad, el razonamiento vale tanto como el código |
| Publicarla con las rutas tachadas antes de cada subida | Un paso manual que hay que recordar 40 veces. Se olvida una vez y ya está hecho. Es más barato no escribir nunca una ruta absoluta |
| Publicar solo los documentos "limpios", a mano | Convierte cada subida en una decisión, y una bitácora con huecos arbitrarios deja de ser fiable |

## Consecuencias

Esto no es una relajación de la regla, es un cambio de su naturaleza, y ata cosas concretas:

1. **Rutas relativas siempre**, en los `.md` y en el código. Nunca la ruta absoluta de la máquina,
   nunca el usuario de Windows, nunca rutas de almacenamiento personal. Esto condiciona cómo se
   escribe **cada documento desde el primero**: reescribir 40 después no es una opción realista, y es
   la razón por la que esta decisión se tomó antes del primer commit y no después.
2. **Ningún correo personal**, ni en documentos ni en metadatos de commit. La identidad de git de
   este repositorio es `pi2grands-boop@users.noreply.github.com`, puesta con `git config` **local**;
   la global, que lleva el correo personal, no se tocó.
3. **El colador es bloqueante.** `scripts/colador.ps1` antes de cada push. Si imprime algo, no se
   sube. Trae autoprueba, porque un colador que no encuentra nada puede ser un colador que no está
   mirando.
4. **El colador busca la forma de ruta absoluta de Windows, no el usuario de Windows a secas.** El
   usuario de Windows es prefijo del usuario de GitHub, que sí es público y legítimo: buscar la
   cadena corta daría falsos positivos en la propia URL del repositorio, y un colador que grita
   siempre se acaba ignorando. Los patrones exactos están en `scripts/colador.ps1`.
5. **El colador se excluye de su propia pasada**, porque contiene los patrones que busca. Es su
   **única** exclusión por nombre de fichero y está comentada a la vista, para que nadie use ese
   hueco; la autoprueba demuestra que los patrones siguen funcionando.
6. **Los documentos que hablan de datos personales los describen, no los reproducen.** Esta regla no
   se dedujo: se aprendió. Un documento de esta misma fase citaba una dirección de correo personal
   literal para explicar dónde había aparecido, y el colador la atrapó justo antes de subirla — un
   documento sobre fugas a punto de filtrar una. Lo mismo vale para las rutas: se nombra la forma, no
   se escribe un ejemplo real.
6. **Este proyecto no tiene secretos**, y conviene dejarlo escrito: las fuentes de datos son HTTP GET
   público sin autenticación. No hay `.env`, ni tokens, ni credenciales. Si alguna fuente futura
   llegara a pedirlas —la ingesta de tablas de ganadores de la Fase 3, por ejemplo—, esta decisión
   hay que reabrirla.

Revertir implicaría quitar `Documentos_Contexto/` del repositorio público, y en un repositorio ya
clonable el borrado no es real: lo que se publicó, se publicó.

## Premisas que esta decisión invalida

**Invalida la Regla 0 de la skill de documentación**, que es la premisa de la que parten todos los
proyectos del usuario con bitácora. En este proyecto concreto, y solo en este, no aplica. Queda
declarado en el §0 del `REGLAS-DOCUMENTACION.md`, que es el primer sitio donde alguien lo buscará.

No invalida ninguna otra decisión: es la primera del proyecto.

**Un efecto colateral que descubrió esta decisión y que no era obvio:** el `Initial commit`
`4270088`, creado por GitHub al dar de alta el repositorio, está autorado con el correo personal del
usuario. Ya era público antes de empezar, y el colador —que inspecciona ficheros— no lo detecta
porque vive en los metadatos del commit. No se puede quitar sin reescribir el historial de un
repositorio público, lo que tampoco lo borraría de cachés ni bifurcaciones. La medida que sí sirve
es para el futuro: activar *Keep my email addresses private* en los ajustes de GitHub.

## Cuándo reabrirla

- Si alguna fuente de datos llega a requerir credenciales (consecuencia 6).
- Si el proyecto pasa a manejar datos de personas. Hoy no maneja ninguno: los sorteos son públicos y
  las tablas de ganadores son agregados sin identidad.
- Si se decide que la app de la Fase 4 deje de ser local. Hoy corre en `localhost` y eso es parte de
  la premisa.

## Cómo verificar

```powershell
.\scripts\colador.ps1 -Autoprueba       # autoprueba 3/3 y 0 coincidencias, exit 0
git config user.email                   # -> pi2grands-boop@users.noreply.github.com
git log --format='%ae' | Sort-Object -Unique
```

La última línea debe devolver solo direcciones `users.noreply.github.com`, con la única excepción
conocida del `Initial commit` `4270088` explicada arriba.

Relacionado: `Despliegue/Añadir/2026-10-03_00-13_s1-primer-push.md`,
`Fases/2026-10-02_arranque/99_CIERRE.md`
