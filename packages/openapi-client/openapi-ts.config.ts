import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: 'openapi.json',
  output: {
    format: "prettier",
    lint: "eslint",
    path: "src/client",
  },
  plugins: ['@hey-api/client-next'], 
});