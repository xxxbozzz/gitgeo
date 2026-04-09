export interface SystemStatusPayload {
  environment: string
  debug: boolean
  database: string
  llm_api_configured: boolean
  build: string
}
