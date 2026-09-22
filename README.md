# Ecommerce

Base inicial para un e-commerce con FastAPI y Next.js. Esta etapa configura dependencias,
directorios, arranque de ambas aplicaciones y temas claro/oscuro. Los módulos de negocio
todavía no contienen endpoints, modelos, autenticación ni integración de pagos.

## Estructura inicial

```text
ecommerce/
├── AGENTS.md
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── .python-version
│   ├── .env.example
│   ├── src/
│   │   ├── presentation/controllers/
│   │   ├── application/
│   │   │   ├── queries/
│   │   │   ├── commands/
│   │   │   ├── handlers/
│   │   │   ├── services/
│   │   │   ├── use_cases/
│   │   │   └── mappers/
│   │   ├── domain/
│   │   │   ├── entity/
│   │   │   └── exceptions/
│   │   ├── interfaces/
│   │   │   ├── ports/
│   │   │   └── dtos/
│   │   ├── infrastructure/
│   │   │   ├── adapters/
│   │   │   └── database/
│   │   │       ├── models/base.py
│   │   │       ├── schema/
│   │   │       └── session.py
│   │   └── config/
│   │       ├── app.py
│   │       ├── container.py
│   │       └── settings.py
│   └── tests/
│       ├── unit/
│       └── integration/
└── frontend/
    ├── package.json
    ├── package-lock.json
    ├── tsconfig.json
    ├── eslint.config.mjs
    ├── postcss.config.mjs
    ├── next.config.ts
    ├── .env.example
    └── src/
        ├── app/
        │   ├── (shop)/page.tsx
        │   ├── (admin)/admin/
        │   ├── api/
        │   ├── layout.tsx
        │   └── globals.css
        ├── components/
        │   ├── theme-provider.tsx
        │   └── theme-toggle.tsx
        └── features/
            ├── catalogo/
            ├── categorias/
            ├── carrito/
            ├── checkout/
            ├── pedidos/
            ├── pagos/
            ├── inventario/
            ├── autenticacion/
            └── shared/
                ├── types/
                │   ├── pagination.types.ts
                │   ├── query-params.types.ts
                │   └── select.types.ts
                └── util/createQueryParams.ts
```

Las carpetas reservadas se conservan en Git con `__init__.py` o `.gitkeep`.
Cada feature tiene `types.ts`, `service.ts` y `constants.ts` reservados; sus contratos
y componentes (`*-table.tsx`, `*-form.tsx`, `*-filtros.tsx`, `*-card.tsx`, `*-skeleton.tsx`)
se implementarán junto con el módulo, sin anticipar propiedades de API inexistentes.
El grupo `(admin)` usará `/admin` para evitar colisiones con las rutas de `(shop)`.

## Dependencias

Las versiones directas se fijan en los manifiestos; los lockfiles fijan las transitivas.
TypeScript 5.9 y ESLint 9 se mantienen por compatibilidad con los plugins de Next.js:
el parser instalado admite TypeScript anterior a 6.1 y varios plugins admiten ESLint hasta 9.
ESLint 9 ya figura como deprecado en npm; revisar estos límites al actualizar los plugins.

| Área | Dependencias |
| --- | --- |
| API y validación | FastAPI, Uvicorn, Pydantic v2 con validación de email, pydantic-settings |
| CQRS e inyección | rmediator, dependency-injector |
| Persistencia | SQLAlchemy 2.0 con asyncio, asyncpg; asyncmy en el extra `mysql` |
| Calidad backend | Ruff, pytest, pytest-asyncio, HTTPX |
| Aplicación web | Next.js App Router, React, TypeScript estricto |
| Interfaz | Tailwind CSS y PostCSS, next-themes, lucide-react |
| Primitivas | Radix Dialog (modal/sheet), Select, Tabs y Tooltip |
| Formularios | react-hook-form, @hookform/resolvers, zod |
| Tablas e identificadores | @tanstack/react-table, uuid (incluye sus tipos) |
| Calidad frontend | ESLint y eslint-config-next |

Requisitos del proyecto: Python 3.13+ (desarrollo fijado a 3.13), uv y Node.js 22.13+
con npm. La versión mínima de Node de este proyecto cubre también las herramientas de lint.

## Arranque local

En PowerShell, desde la raíz, iniciar el backend:

```powershell
cd backend
uv sync --locked
Copy-Item .env.example .env
uv run uvicorn src.config.app:app --reload
```

API: http://localhost:8000/docs. Por ahora solo se expone la documentación de FastAPI;
no hay endpoints de negocio. Crear el engine no abre una conexión: el arranque inicial
no requiere una base SQL disponible. Se necesitará al implementar operaciones de persistencia.
Configurar credenciales propias en `.env` antes de conectar a la base.

En otra terminal, desde la raíz:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env.local
npm run dev
```

Tienda: http://localhost:3000. La portada inicial anuncia la próxima apertura y permite
cambiar de tema. `NEXT_PUBLIC_API_URL` queda reservado para los servicios futuros;
ningún secreto debe exponerse con el prefijo `NEXT_PUBLIC_`.

Para MySQL, ejecutar `uv sync --locked --extra mysql` desde `backend` y configurar
`DATABASE_URL=mysql+asyncmy://usuario:clave@localhost:3306/ecommerce`.

## Límites y flujo de implementación

```text
Controller → Mediator Handler → Service → Use Case → Repository Port → Repository Adapter
```

El contenedor compone las dependencias. Cada handler recibirá un servicio; cada servicio,
un caso de uso; cada caso de uso dependerá de un puerto ABC. Los adaptadores usarán
`AsyncSession` y los mappers de aplicación convertirán modelos, entidades y DTOs.
La dependencia del caso de uso termina en el puerto; el adaptador lo implementa.

Se crea una sesión por operación y una transacción para los cambios que deben ser atómicos,
especialmente pedidos e inventario. No se comparten sesiones entre peticiones concurrentes.
Las entidades usarán `@dataclass(kw_only=True)`, los parámetros de ruta/query se agruparán
con `@dataclass` y `Depends()`, y los resultados llevarán el sufijo `Result`.
Los comandos y queries se decorarán con `@request(DTOResult)` de rmediator.

No se ejecuta DDL al arrancar ni se incluye Alembic. `database/schema/` queda reservado
para scripts SQL versionados y explícitos. `Base.metadata.create_all` solo permitiría
crear tablas nuevas: no sustituye los cambios de esquema sobre tablas existentes.

La autenticación de clientes/admin, autorización, transacciones de inventario, checkout
e integración de pagos se desarrollarán en las siguientes etapas. No hay pantallas ni
rutas administrativas operativas en esta base.

## Verificación

```powershell
cd backend
uv run ruff check .
uv run ruff format --check .
```

```powershell
cd frontend
npm run lint
npm run typecheck
npm run build
```

Las carpetas de tests están reservadas; no existe todavía una suite de negocio.

## Referencias de configuración

- [Next.js: instalación y App Router](https://nextjs.org/docs/app/getting-started/installation)
- [Tailwind CSS: integración con Next.js mediante PostCSS](https://tailwindcss.com/docs/installation/framework-guides/nextjs)
- [rmediator: requests, handlers y registro del mediador](https://pypi.org/project/rmediator/)
