import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

export default defineConfig([
  ...nextVitals,
  ...nextTypescript,
  {
    files: ["**/*.ts", "**/*.tsx"],
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "no-restricted-syntax": [
        "error",
        {
          selector: "CallExpression[callee.property.name='randomUUID']",
          message: "Usar v4 as uuidv4 de la librería uuid.",
        },
      ],
    },
  },
  globalIgnores([".next/**", "out/**", "next-env.d.ts"]),
]);
