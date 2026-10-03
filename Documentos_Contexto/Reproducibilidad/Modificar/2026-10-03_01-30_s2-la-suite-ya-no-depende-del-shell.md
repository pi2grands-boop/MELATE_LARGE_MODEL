# La suite ya no pasa o falla según el shell desde el que se lance

- **Fecha/hora:** 2026-10-03 01:30
- **Área:** Reproducibilidad · **Acción:** Modificar
- **Chat / página:** sesión de arranque · emitido al cerrar la Fase 2
- **Archivos afectados:** `src/melate/informe.py`, `tests/conftest.py`, `tests/test_paridad.py`

## Qué se hizo

La Fase 1 se cerró con 52 tests en verde. Al ejecutar su pendiente de "clonar en limpio y correr la
suite", **17 de los 53 fallaban**. El mismo commit, el mismo repositorio, el mismo código.

La diferencia era el shell. La Fase 1 lanzó pytest desde PowerShell; el clon se probó desde Bash.

### La causa

El resumen del informe imprime `Δ`, `≈` y `–`. **Ninguno de los tres existe en cp1252**, la página de
códigos ANSI de este Windows. Cuando la salida va a una tubería o a un fichero, Python usa la
codificación local:

```
stdout encoding: cp1252 | isatty: False
UnicodeEncodeError: 'charmap' codec can't encode character 'Δ'
```

El proceso muere **a mitad del informe**, después de haber gastado el minuto de cómputo. En una
consola de verdad no pasa, porque Windows usa un escritor UTF-16 aparte — de ahí que el fallo
aparezca solo al redirigir y pueda pasar inadvertido mucho tiempo.

### El arreglo, en dos partes porque hay dos públicos

**`melate.informe._salida_robusta()`**, llamado al principio de `construir()`:

- Salida redirigida → UTF-8, que es lo que espera quien la consume.
- Salida a consola → se respeta su codificación y solo se añade `errors="replace"`, para degradar a
  `?` en vez de reventar.
- Todo dentro de `try/except`: que no se pueda reconfigurar un flujo no es motivo para abortar una
  corrida de dos minutos.

**`tests/conftest.py`** fija `PYTHONIOENCODING=utf-8` en los subprocesos. Es la **única** solución
posible para `baseline_auditoria.py`, que tiene el mismo fallo latente y **no se modifica nunca**, y
además mantiene la comparación de paridad simétrica entre los dos programas.

### El test que lo fija

`test_el_informe_sobrevive_a_una_codificacion_hostil` fuerza `PYTHONIOENCODING=cp1252` y exige que
el informe acabe con código 0 y escriba el JSON. **Verificado que tiene dientes:** desactivando
`_salida_robusta()` a mano, el test falla; restaurándolo, pasa.

## Por qué

Esto es reproducibilidad, no cosmética. Un resultado que depende del shell desde el que se invoca no
es reproducible, y **un test que pasa o falla según quién lo corra no protege nada**: da una señal
verde que no significa lo que parece.

El caso es además instructivo sobre los límites de la propia práctica. La Fase 1 hizo todo lo
correcto —fijó versiones, congeló datos, registró hashes y semillas— y aun así se le escapó una
variable del entorno que no estaba en su lista: la codificación de la salida. **Lo que la salvó no
fue el rigor del cierre, fue haber dejado escrita la lista de pendientes y haberla ejecutado.**

## Impacto en seguridad / conexiones / datos

- **Seguridad:** sin impacto.
- **Conexiones:** sin cambios.
- **Datos:** ninguno. El JSON del reporte ya se escribía con `encoding="utf-8"` explícito, así que
  los datos nunca estuvieron afectados — solo el resumen por pantalla y, con él, el proceso entero.
- **Paridad:** intacta. `test_paridad.py` en verde; el cambio toca la salida, no el reporte.

## Cómo verificar / revertir

```powershell
.venv\Scripts\python.exe -m pytest tests\test_paridad.py -k hostil -v
```

Y la comprobación completa, que es la que destapó todo:

```
git -c core.autocrlf=false -c core.eol=lf clone <url> /tmp/clon
cd /tmp/clon && python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt -e .
.venv/Scripts/python -m pytest tests -q        # 53 en verde desde el clon limpio
```

**Revertir:** quitar `_salida_robusta` y su llamada, el `env=entorno_utf8()` del `conftest` y el test
`hostil`. **No se recomienda:** la suite volvería a depender del shell.

Relacionado: `Fases/2026-10-03_protocolo/Bugs/2026-10-03_01-05_s2-pendientes-heredados.md`,
`Reproducibilidad/Añadir/2026-10-03_00-13_s1-linea-base-reproducida.md`
