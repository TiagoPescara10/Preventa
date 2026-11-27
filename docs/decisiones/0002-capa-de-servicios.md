# 0002 · Reglas de negocio en una capa de servicios

- **Estado:** aceptada
- **Fecha:** 2026-11-27

## Contexto

Las reglas de negocio (RN-01 a RN-14) involucran varias tablas, transacciones y bloqueos (stock, numeración, cortes horarios). Si quedan en vistas o serializers se dispersan, se duplican y son difíciles de testear.

## Decisión

Cada app separa responsabilidades:

- `views.py`: recibe la request, valida permisos y delega. Sin lógica de negocio.
- `serializers.py`: valida formato y tipos, arma la salida.
- `services.py`: aplica las reglas RN-xx dentro de transacciones.
- `selectors.py`: consultas de lectura reutilizables.
- `models.py`: estructura, restricciones de base y métodos simples.

Los servicios lanzan `core.exceptions.ReglaDeNegocioError` (400) o `ConflictoError` (409); un exception handler de DRF las traduce a `{"codigo": "RN-xx", "detalle": "..."}`.

## Consecuencias

- Las reglas se testean como funciones, sin HTTP (`tests/test_services.py`).
- El frontend puede repetir validaciones para la experiencia de uso, pero la fuente de verdad es el backend.
- Hay algo más de código por app que con vistas "gordas".
