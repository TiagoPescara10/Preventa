# Modelo de datos

## Diagrama entidad-relación

[PENDIENTE] Imagen generada desde los modelos cuando estén implementados.

## Entidades

Diez tablas en cuatro apps de Django. Todas tienen `id`, `creado_en` y `actualizado_en`; las que admiten baja lógica tienen `activo` (booleano).

| Entidad | App | Campos principales | Relaciones y restricciones |
|---|---|---|---|
| Usuario | usuarios | email (único, se usa para el login), nombre, rol (ADMIN, OPERADOR, CLIENTE), activo | Extiende `AbstractUser`. Si rol es CLIENTE, tiene cliente obligatorio |
| Zona | clientes | nombre (único), días de reparto (lunes a sábado), hora de corte, monto mínimo de pedido, activo | Tiene muchos clientes |
| Cliente | clientes | razón social, nombre de fantasía, CUIT (único), dirección, localidad, teléfono, activo | FK a Zona y a ListaPrecios. Un cliente puede tener varios usuarios |
| Categoría | catalogo | nombre (único), activo | Tiene muchos productos |
| Producto | catalogo | código (único), nombre, presentación (ej. "Bulto x10"), stock disponible (entero ≥ 0), activo | FK a Categoría |
| ListaPrecios | catalogo | nombre (único, ej. "Minorista", "Mayorista"), activo | Una lista se asigna a muchos clientes |
| Precio | catalogo | precio (decimal, > 0) | FK a ListaPrecios y a Producto. Único por par (lista, producto) |
| Pedido | pedidos | número (único, ej. A-1042), fecha de entrega, estado, total, observaciones | FK a Cliente, a Zona (copia al confirmar) y a Usuario (quien lo creó) |
| ItemPedido | pedidos | cantidad (entero > 0), precio unitario (copiado al confirmar), subtotal | FK a Pedido y a Producto. Único por par (pedido, producto) |
| HistorialEstado | pedidos | estado anterior, estado nuevo, fecha y hora, motivo (opcional) | FK a Pedido y a Usuario |

## Decisiones de diseño

- Montos en `DecimalField(max_digits=12, decimal_places=2)`, nunca `float`.
- Precio unitario y zona se copian en el pedido al confirmar, para que un cambio posterior no altere pedidos ya hechos (RN-05).
- Nada se borra físicamente si tiene pedidos asociados: se desactiva (RN-09).
- Índices en `Pedido(fecha_entrega, estado)`, `Pedido(cliente)` y `Cliente(zona)`, que son los filtros del panel.

## Estado actual (Sprint 0)

- Implementado: `Usuario` (login por email, campo `rol`) y los modelos abstractos `core.models.TimeStampedModel` y `SoftDeleteModel`.
- En `Usuario`, el campo `activo` es el `is_active` de Django (expuesto también como propiedad `activo`).
- El vínculo Usuario → Cliente se agrega cuando exista el modelo `Cliente`.
