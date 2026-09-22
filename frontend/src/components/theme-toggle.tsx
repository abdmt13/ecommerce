"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();

  return (
    <button
      type="button"
      aria-label="Cambiar entre tema claro y oscuro"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
      className="rounded-full border border-stone-300 p-3 transition-colors hover:bg-stone-200 focus-visible:outline-2 focus-visible:outline-offset-4 dark:border-stone-700 dark:hover:bg-stone-800"
    >
      <Moon aria-hidden="true" className="size-5 dark:hidden" />
      <Sun aria-hidden="true" className="hidden size-5 dark:block" />
    </button>
  );
}
