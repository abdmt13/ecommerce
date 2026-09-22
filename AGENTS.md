# Convenciones del proyecto

## Alcance y arquitectura
- Backend Python 3.13+, FastAPI, rmediator, dependency-injector, Pydantic v2 y SQLAlchemy 2.0 asíncrono.
- Flujo obligatorio: Controller -> Mediator Handler -> Service -> Use Case -> Repository Port -> Repository Adapter.
- Dominio independiente de FastAPI y SQLAlchemy. Entidades con `@dataclass(kw_only=True)`.
- Requests CQRS con `@request(DTOResult)`. Resultados encapsulados en clases con sufijo `Result`; no tuplas ni resultados crudos.
- Los handlers delegan a servicios inyectados; nunca construyen casos de uso o repositorios en `handle()`.
- Query y path parameters agrupados en `@dataclass` con `Depends()`; parsing y cálculos mediante `@property`.
- Repositorios definidos mediante ABC en `interfaces/ports`; adaptadores en `infrastructure/adapters`.
- Modelos declarativos en `infrastructure/database/models`; mappers en `application/mappers`.
- Una AsyncSession por operación/unidad de trabajo; nunca compartir una sesión singleton entre peticiones.
- PostgreSQL con asyncpg o MySQL con asyncmy. Sin Alembic ni otras herramientas externas de migración.
- No ejecutar cambios de esquema automáticamente al arrancar. Documentar y versionar los cambios SQL explícitos.

## Frontend
- Next.js App Router y TypeScript estricto, sin `any`; módulos en `src/features`.
- Cada módulo crece con `types.ts`, `service.ts`, `constants.ts` y componentes específicos según se implementa.
- Propiedades de API y formularios declaradas en el `types.ts` del módulo.
- Servicios reutilizan `features/shared/util/createQueryParams.ts` para serializar filtros.
- Tailwind CSS, next-themes, lucide-react y primitivas Radix accesibles.
- Formularios con react-hook-form, @hookform/resolvers/zod y zod; tablas con @tanstack/react-table.
- UUIDs solamente con `import { v4 as uuidv4 } from "uuid"`; nunca `crypto.randomUUID()`.
- Contenedores responsivos y tablas con `overflow-x-auto`. Acciones: `sticky right-0`, fondo sólido claro/oscuro y bordes.
- Emails sin conversión a mayúsculas; `forceUppercase={false}` si el componente ofrece esa prop.
- Ayuda con Info: tooltip flotante encima (`bottom-full`), fondo oscuro, flecha hacia abajo, sin atributo `title`.
- Componentes compartidos en `src/components`; rutas en `src/app/(shop)`, `(admin)` y `api`.

## Calidad
- Imports al inicio del archivo (después de directivas como "use client"). Sin imports o código sin uso.
- camelCase en TS/JS, snake_case en Python y PascalCase en clases/componentes.
- Nombres descriptivos, funciones con verbos y booleanos con prefijos (`isLoading`, `tieneStock`).
- No incorporar reglas de negocio a controllers, handlers o componentes de presentación.
- Ejecutar lint y compilación/tipos pertinentes antes de entregar cambios.
