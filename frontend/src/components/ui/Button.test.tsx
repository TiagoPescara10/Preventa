import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { Button } from './Button'

describe('Button', () => {
  it('muestra el texto y responde al click', async () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Confirmar pedido</Button>)

    await userEvent.click(screen.getByRole('button', { name: 'Confirmar pedido' }))

    expect(onClick).toHaveBeenCalledOnce()
  })
})
