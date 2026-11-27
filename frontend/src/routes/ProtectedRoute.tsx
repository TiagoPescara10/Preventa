import type { ReactNode } from 'react'
import { Navigate } from 'react-router'

import { useAuth } from '../hooks/useAuth'
import type { Rol } from '../types/usuario'

interface Props {
  roles: Rol[]
  children: ReactNode
}

/**
 * Shows `children` only to users with one of `roles`.
 * This only hides UI: the backend enforces permissions on every endpoint.
 * Real session handling comes with the auth sprint (useAuth is a placeholder).
 */
export function ProtectedRoute({ roles, children }: Props) {
  const { usuario } = useAuth()

  if (!usuario) return <Navigate to="/login" replace />
  if (!roles.includes(usuario.rol)) return <Navigate to="/login" replace />

  return children
}
