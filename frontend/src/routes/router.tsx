import { createBrowserRouter, Navigate } from 'react-router'

import { LoginPage } from '../features/auth/LoginPage'
import { CatalogoPage } from '../features/catalogo/CatalogoPage'
import { PanelPage } from '../features/panel/PanelPage'
import { MisPedidosPage } from '../features/pedidos/MisPedidosPage'
import { ProtectedRoute } from './ProtectedRoute'

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/login" replace /> },
  { path: '/login', element: <LoginPage /> },
  {
    path: '/catalogo',
    element: (
      <ProtectedRoute roles={['ADMIN', 'OPERADOR', 'CLIENTE']}>
        <CatalogoPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/mis-pedidos',
    element: (
      <ProtectedRoute roles={['CLIENTE']}>
        <MisPedidosPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/panel',
    element: (
      <ProtectedRoute roles={['ADMIN', 'OPERADOR']}>
        <PanelPage />
      </ProtectedRoute>
    ),
  },
  { path: '*', element: <Navigate to="/login" replace /> },
])
