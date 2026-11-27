import type { Usuario } from '../types/usuario'

interface AuthState {
  usuario: Usuario | null
}

/**
 * Placeholder: the real session (login, refresh, logout) is implemented in a later sprint.
 */
export function useAuth(): AuthState {
  return { usuario: null }
}
