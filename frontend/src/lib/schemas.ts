import { z } from 'zod'

/** Client-side validation only; the backend is the source of truth. */
export const loginSchema = z.object({
  email: z.email('Ingresá un email válido'),
  password: z.string().min(1, 'Ingresá tu contraseña'),
})

export type LoginForm = z.infer<typeof loginSchema>
