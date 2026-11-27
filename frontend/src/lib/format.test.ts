import { describe, expect, it } from 'vitest'

import { formatearFecha, formatearMoneda } from './format'

describe('formatearMoneda', () => {
  it('formatea en pesos argentinos', () => {
    expect(formatearMoneda(38500)).toMatch(/\$\s?38\.500,00/)
  })
})

describe('formatearFecha', () => {
  it('muestra el dia de la semana en espanol', () => {
    expect(formatearFecha('2026-12-01')).toContain('martes')
  })
})
