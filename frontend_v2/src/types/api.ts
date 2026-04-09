export interface ApiEnvelope<T> {
  success: boolean
  message: string
  data: T
  error_code: string | null
}

export interface PaginatedPayload<T> {
  items: T[]
  total: number
  limit: number
  offset: number
  warning: string | null
}

export interface QueryFilters {
  limit?: number
  offset?: number
}

export class ApiError extends Error {
  errorCode: string | null
  statusCode: number | null
  data: unknown

  constructor(
    message: string,
    options?: {
      errorCode?: string | null
      statusCode?: number | null
      data?: unknown
    },
  ) {
    super(message)
    this.name = 'ApiError'
    this.errorCode = options?.errorCode ?? null
    this.statusCode = options?.statusCode ?? null
    this.data = options?.data ?? null
  }
}
