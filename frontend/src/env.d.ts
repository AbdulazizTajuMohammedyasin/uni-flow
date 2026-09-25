/// <reference types="vite/client" />

/** Typed `import.meta.env` variables (see frontend/.env.example). */
interface ImportMetaEnv {
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
