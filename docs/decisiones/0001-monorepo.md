# 0001 · Monorepo con backend y frontend separados

- **Estado:** aceptada
- **Fecha:** 2026-11-27

## Contexto

El proyecto tiene una API REST en Django y una SPA en React. Los supervisores revisan el código y cada parte se despliega en un servicio distinto (Render y Vercel).

## Decisión

Un solo repositorio `preventa` con `backend/`, `frontend/` y `docs/`. Cada parte tiene sus dependencias, su configuración de lint y su workflow de CI, que corre solo cuando cambian sus archivos.

## Consecuencias

- Un issue, una rama y un PR pueden tocar API y frontend juntos.
- Los supervisores revisan todo en un solo lugar; la documentación vive junto al código.
- Cada deploy apunta a su subcarpeta y no depende del otro.
- Hay que mantener dos toolchains (Python y Node) en el mismo repo.
