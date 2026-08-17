/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE: string
  readonly VITE_GLOBAL_PREFIX: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
