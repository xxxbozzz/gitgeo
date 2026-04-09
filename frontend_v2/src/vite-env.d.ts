/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_OPEN_SOURCE_WATERMARK?: string
  readonly VITE_OPEN_SOURCE_WATERMARK_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
