# Cómo leer esta bitácora

> Rutas de lectura, no un listado. Se actualiza al cerrar cada fase.
> Si el mapa miente, es peor que si no existe.

## Si acabas de llegar

1. `Mapa/Añadir/` — el inventario del estado de partida
2. `Mapa/Modificar/` — el último cierre de fase: dónde está hoy
3. Este mapa

## Si vas a tocar código

- **Antes:** las `Decisiones/` de tu área. Están cerradas y tienen su porqué.
- **Después:** el pipeline. El `.md` es el último paso, nunca el primero.

## Si buscas algo concreto

| Tu pregunta | Área |
|---|---|
| ¿Cuál es el mapa del sistema? | Mapa |
| ¿Dónde vive este fichero? | Estructura_Carpetas |
| ¿Qué forma tienen los datos? | Estructura_Datos |
| ¿Dónde se guarda algo? | Almacenamiento |
| ¿Quién llama a quién? | Conexiones |
| ¿Cómo se enlazan las piezas del front? | Interconexion |
| ¿Qué cambia en la superficie de ataque? | Seguridad |
| ¿Qué sirve el servidor? | Red |
| ¿Por qué se eligió A y no B? | <Área>/Decisiones |

## Fases

Un cambio normal va directo a la rejilla. Los bloques de trabajo grandes — un
arranque, un rediseño, un cambio de tecnología — viven en
`Fases/<fecha>_<nombre>/`. Al cerrarse, cada dossier emite a las áreas base solo
el estado final. Empieza siempre por su `00_ALCANCE.md`.

## Estado ahora mismo

- **Bugs abiertos:** (ninguno)
- **Pendiente de verificar en vivo:** (nada)
- **Decisiones cerradas que atan el proyecto:** (ninguna)
- **Fases abiertas:** (ninguna)