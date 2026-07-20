import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
})

// ── Request interceptor: attach JWT bearer token ──────────────────────────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("auth_token")
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  }
  return config
})

// ── Response interceptor: surface errors cleanly ─────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token")
        window.location.href = "/login"
      }
    }
    const message =
      error.response?.data?.detail ??
      error.message ??
      "An unexpected error occurred"
    return Promise.reject(new Error(message))
  },
)

export default api
