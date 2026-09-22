import { ShoppingBag } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";

export default function ShopPage() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-16 overflow-x-auto px-6 py-8 sm:px-10">
      <header className="flex items-center justify-between gap-4">
        <span className="flex items-center gap-3 text-lg font-semibold">
          <ShoppingBag aria-hidden="true" className="size-5" />
          Ecommerce
        </span>
        <ThemeToggle />
      </header>
      <section className="my-auto max-w-2xl py-16">
        <p className="mb-4 text-sm font-medium tracking-widest text-stone-500 dark:text-stone-400">
          PRÓXIMAMENTE
        </p>
        <h1 className="text-4xl font-semibold tracking-tight sm:text-6xl">
          Una nueva forma de encontrar lo que buscas.
        </h1>
        <p className="mt-6 text-lg leading-relaxed text-stone-600 dark:text-stone-400">
          Estamos preparando nuestra tienda. Pronto podrás explorar el catálogo y descubrir
          nuestros productos.
        </p>
      </section>
    </main>
  );
}
