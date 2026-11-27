# Reglas de negocio

> Copia de la sección "Reglas de negocio" de la especificación del proyecto.

Cada regla tiene un código que se usa en issues, commits y nombres de tests (`test_rn01_...`). Se implementan en `services.py` y se responden con errores claros: **400** para datos inválidos y **409** para conflictos con el estado actual.

Formato de error: `{"codigo": "RN-xx", "detalle": "..."}`.

**Supuestos comunes:** la hora de referencia es la de Córdoba (`America/Argentina/Cordoba`) y los feriados quedan fuera del MVP.

## RN-01 · Pedido mínimo por zona

**Regla.** Un pedido solo se confirma si su total es mayor o igual al monto mínimo de la zona del cliente.

**Ejemplo.** Zona Norte tiene mínimo de $150.000. Un pedido de $149.999 se rechaza con el faltante; uno de $150.000 se acepta.

**Tests.** Total por debajo del mínimo devuelve 400 con el faltante · total igual al mínimo se confirma · al modificar un pedido y bajar del mínimo, la modificación se rechaza.

## RN-02 · Fecha de entrega y horario de corte

**Regla.** Cada zona tiene días de reparto y una hora de corte. El corte de un reparto es el día anterior a esa hora. Al confirmar, el pedido se asigna al próximo reparto cuyo corte no pasó. Un pedido tardío no se rechaza: pasa al reparto siguiente y se le avisa al cliente.

**Ejemplo.** Zona Norte reparte martes y viernes, corte 18:00. Un pedido del lunes 17:59 sale el martes. Uno del lunes 18:01 sale el viernes.

**Tests.** Un minuto antes del corte asigna el reparto más cercano · un minuto después asigna el siguiente · cruce de semana (pedido del sábado) · zona sin días de reparto no permite pedir.

## RN-03 · Modificación y cancelación por el cliente

**Regla.** El cliente puede modificar o cancelar su pedido solo si está en estado CONFIRMADO y no pasó el corte de su fecha de entrega. Después del corte, el pedido queda bloqueado para el cliente.

**Ejemplo.** Pedido para el martes de Zona Norte: se puede modificar hasta el lunes 17:59.

**Tests.** Modificar antes del corte funciona · después del corte devuelve 409 · un pedido EN_PREPARACION no se puede modificar aunque falte para el corte.

## RN-04 · Un pedido activo por cliente y fecha

**Regla.** Un cliente tiene como máximo un pedido no cancelado por fecha de entrega. Si quiere agregar productos, modifica el existente.

**Ejemplo.** Almacén Doña Rosa ya tiene el A-1042 para el martes. Un segundo pedido para el martes devuelve 409 con el número A-1042.

**Tests.** Segundo pedido misma fecha devuelve 409 · si el primero está cancelado, se permite uno nuevo · otra fecha de entrega se permite.

## RN-05 · Precios según la lista del cliente

**Regla.** El cliente ve y paga los precios de su lista. Un producto sin precio en esa lista no aparece en su catálogo y no se puede pedir. El precio unitario se copia al ítem al confirmar; si el pedido se modifica, los ítems sin cambios conservan su precio y los nuevos o cambiados toman el vigente.

**Ejemplo.** La yerba cuesta $38.500 en la lista Minorista. Después del pedido sube a $41.000: el pedido ya confirmado sigue en $38.500.

**Tests.** El catálogo filtra productos sin precio en la lista · pedir uno sin precio devuelve 400 · un cambio de precio no altera pedidos confirmados.

## RN-06 · Stock disponible y reserva

**Regla.** No se puede pedir más cantidad que el stock disponible. Al confirmar, el stock se reserva (se descuenta). Al modificar se ajusta solo la diferencia. Al cancelar o marcar NO_ENTREGADO, se devuelve. Todo ocurre en una transacción con bloqueo de filas (`select_for_update`) para que dos pedidos simultáneos no vendan la misma unidad.

**Ejemplo.** Hay 5 bultos de aceite. Un pedido de 3 deja 2; otro de 3 se rechaza indicando que quedan 2.

**Tests.** Pedir más que el stock devuelve 400 · confirmar descuenta · cancelar devuelve · modificar de 3 a 5 descuenta 2 · dos confirmaciones concurrentes no dejan stock negativo.

## RN-07 · Cantidades e ítems válidos

**Regla.** Cada ítem tiene cantidad entera entre 1 y 999 bultos. Un producto aparece una sola vez por pedido. Un pedido tiene al menos un ítem.

**Tests.** Cantidad 0, negativa, decimal o mayor a 999 devuelve 400 · producto repetido devuelve 400 · pedido sin ítems devuelve 400.

## RN-08 · Total calculado en el servidor

**Regla.** El total y los subtotales los calcula siempre el backend con los precios de la base. Cualquier precio o total enviado por el frontend se ignora.

**Tests.** Un request con un total adulterado guarda el total correcto · subtotal = cantidad × precio unitario · total = suma de subtotales.

## RN-09 · Baja lógica

**Regla.** Zonas, clientes, productos, listas y usuarios no se borran: se desactivan. Un producto inactivo desaparece del catálogo pero sigue en los pedidos que ya lo tienen. Un cliente inactivo no puede crear pedidos. No se puede desactivar una zona que tenga clientes activos.

**Tests.** El catálogo excluye inactivos · pedir un producto inactivo devuelve 400 · un cliente inactivo recibe 403 al crear pedido · desactivar una zona con clientes activos devuelve 409.

## RN-10 · Transiciones de estado e historial

**Regla.** El estado de un pedido solo cambia por las transiciones permitidas (ver diagrama de estados en la especificación). Solo Administrador y Operador avanzan estados. Cada cambio guarda una fila en HistorialEstado con usuario, fecha y estado anterior. Una transición no permitida devuelve 409.

**Tests.** Cada transición válida funciona y deja historial · ENTREGADO a CONFIRMADO devuelve 409 · un Cliente que intenta avanzar estado recibe 403.

## RN-11 · Cancelación después del corte

**Regla.** Pasado el corte, solo el Administrador puede cancelar, y solo si el pedido todavía no fue DESPACHADO. El motivo es obligatorio y queda en el historial.

**Tests.** Admin cancela EN_PREPARACION con motivo · sin motivo devuelve 400 · un Operador recibe 403 · un pedido DESPACHADO devuelve 409.

## RN-12 · Visibilidad por rol

**Regla.** Un Cliente solo ve sus pedidos, su comercio y el catálogo de su lista. Pedir un recurso ajeno responde 404.

**Tests.** El listado de pedidos de un Cliente solo trae los suyos · GET de un pedido de otro cliente devuelve 404.

## RN-13 · Consolidado de armado

**Regla.** Para una zona y una fecha de entrega, el consolidado suma la cantidad de cada producto de los pedidos CONFIRMADO y EN_PREPARACION. Los cancelados no cuentan.

**Ejemplo.** Dos pedidos del martes en Zona Norte con 2 y 4 bultos de yerba dan 6 bultos de yerba en el consolidado.

**Tests.** Suma correcta por producto · excluye cancelados y otras zonas o fechas · consolidado vacío devuelve lista vacía.

## RN-14 · Numeración de pedidos

**Regla.** Cada pedido recibe un número correlativo y único con prefijo (A-1001, A-1002…) generado en el backend dentro de la transacción.

**Tests.** Dos pedidos seguidos tienen números consecutivos · no hay duplicados con creaciones concurrentes.

## RN-15 · Protección del administrador

**Regla.** Un administrador no puede desactivarse a sí mismo ni quitarse el rol ADMIN, para que no pierda el acceso por error. Sí puede desactivar a otro administrador o quitarle el rol. Cualquiera de los dos intentos sobre sí mismo devuelve 409.

**Tests.** Desactivarse a sí mismo devuelve 409 y el usuario sigue activo · quitarse el rol ADMIN devuelve 409 y el rol no cambia · editar su propio nombre manteniendo el rol ADMIN funciona · quitarle el rol ADMIN a otro administrador funciona.
