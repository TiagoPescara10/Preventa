const moneda = new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' })

/** Formats an amount as Argentine pesos, e.g. 38500 -> "$ 38.500,00". */
export function formatearMoneda(monto: number | string): string {
  return moneda.format(Number(monto))
}

const fecha = new Intl.DateTimeFormat('es-AR', {
  timeZone: 'America/Argentina/Cordoba',
  weekday: 'long',
  day: 'numeric',
  month: 'long',
})

/** Formats an ISO date (YYYY-MM-DD) in Cordoba time, e.g. "martes, 1 de diciembre". */
export function formatearFecha(iso: string): string {
  return fecha.format(new Date(`${iso}T12:00:00-03:00`))
}
