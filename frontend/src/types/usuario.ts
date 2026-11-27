export type Rol = 'ADMIN' | 'OPERADOR' | 'CLIENTE'

export interface Usuario {
  id: number
  email: string
  nombre: string
  rol: Rol
}
