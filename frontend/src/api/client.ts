import axios from 'axios'

/**
 * Shared axios instance for the whole app.
 *
 * - The access token lives only in memory (never in localStorage).
 * - The refresh token is an httpOnly cookie, so requests use `withCredentials`.
 */
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

let accessToken: string | null = null

export function setAccessToken(token: string | null) {
  accessToken = token
}

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})
