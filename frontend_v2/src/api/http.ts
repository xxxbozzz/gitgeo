import axios, { type AxiosError, type AxiosRequestConfig } from 'axios'

import { ApiError, type ApiEnvelope } from '../types/api'

const DEFAULT_API_BASE_URL = import.meta.env.PROD ? '/api/v1' : 'http://localhost:8001/api/v1'
const DEFAULT_TIMEOUT = 10_000
const DEFAULT_ACTION_TIMEOUT = 120_000

export const apiClient = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, ''),
  timeout: DEFAULT_TIMEOUT,
})

function createApiError(error: unknown): ApiError {
  const axiosError = error as AxiosError<ApiEnvelope<unknown>>
  const payload = axiosError.response?.data

  if (payload) {
    return new ApiError(payload.message || 'Request failed', {
      errorCode: payload.error_code,
      statusCode: axiosError.response?.status ?? null,
      data: payload.data,
    })
  }

  return new ApiError(axiosError.message || 'Network request failed', {
    statusCode: axiosError.response?.status ?? null,
  })
}

export async function getData<T>(
  url: string,
  config?: AxiosRequestConfig,
): Promise<T> {
  try {
    const response = await apiClient.get<ApiEnvelope<T>>(url, {
      timeout: DEFAULT_TIMEOUT,
      ...config,
    })

    if (!response.data.success) {
      throw new ApiError(response.data.message || 'Request failed', {
        errorCode: response.data.error_code,
        statusCode: response.status,
        data: response.data.data,
      })
    }

    return response.data.data
  } catch (error) {
    throw createApiError(error)
  }
}

export async function postData<T, TBody = unknown>(
  url: string,
  body?: TBody,
  config?: AxiosRequestConfig,
): Promise<T> {
  try {
    const response = await apiClient.post<ApiEnvelope<T>>(url, body, {
      timeout: DEFAULT_ACTION_TIMEOUT,
      ...config,
    })

    if (!response.data.success) {
      throw new ApiError(response.data.message || 'Request failed', {
        errorCode: response.data.error_code,
        statusCode: response.status,
        data: response.data.data,
      })
    }

    return response.data.data
  } catch (error) {
    throw createApiError(error)
  }
}
