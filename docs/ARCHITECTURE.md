# Saar AI — Architecture

## Overview

Saar AI is an AI-powered data analytics platform built with a decoupled frontend/backend architecture. The frontend is a Next.js application handling UI, routing, and client-side state. The backend (planned for Phase 2+) is a FastAPI service handling data processing, ML model training, and AI interactions.

---

## Frontend Architecture

### Framework

- **Next.js** with App Router
- **TypeScript** for type safety
- **Tailwind CSS v4** for styling
- **shadcn/ui** for UI primitives

### Folder Structure

```
frontend/src/
├── app/                    # Next.js App Router
│   ├── layout.tsx          # Root layout with fonts, metadata, AppShell
│   ├── page.tsx            # Dashboard (home) page
│   └── globals.css         # Theme, design tokens, Tailwind config
│
├── components/             # Shared components
│   ├── layout/             # App shell, navbar, sidebar
│   ├── ui/                 # shadcn/ui primitives (button, tooltip, etc.)
│   └── common/             # Shared domain-agnostic components (future)
│
├── features/               # Feature modules (Phase 2+)
│   ├── datasets/           # Dataset upload, list, preview
│   ├── visualization/      # Charts, graphs, dashboards
│   ├── ml/                 # Machine learning models
│   ├── assistant/          # AI chat interface
│   ├── reports/            # Report generation
│   └── settings/           # User preferences
│
├── hooks/                  # Custom React hooks (when needed)
├── services/               # API clients, external service integrations
├── lib/                    # Utilities (cn, formatters, validators)
├── constants/              # App-wide configuration and constants
├── types/                  # Shared TypeScript type definitions
└── styles/                 # Additional style modules (if needed)
```

### Key Design Decisions

**Feature-oriented architecture:** Each feature (datasets, visualization, ML, etc.) gets its own directory under `features/`. This keeps related components, hooks, services, and types co-located and prevents a flat `components/` directory from becoming unmanageable.

**Layout composition:** The `AppShell` component composes `Sidebar` + `Navbar` + main content. The root layout wraps all pages with `AppShell`, so every route gets consistent navigation.

**Navigation as data:** Sidebar navigation items are defined in `constants/navigation.ts`, not hardcoded in the sidebar component. Adding a new feature to the nav is a one-line config change.

**Dark theme first:** The `dark` class is applied to `<html>` by default. Theme tokens are CSS custom properties consumed by Tailwind via `@theme inline`.

---

## Routing Strategy

Using Next.js App Router with file-system based routing:

| Route | Page | Phase |
|---|---|---|
| `/` | Dashboard | 1 |
| `/datasets` | Dataset list | 2 |
| `/datasets/[id]` | Dataset detail | 2 |
| `/visualize` | Visualization builder | 4 |
| `/ml` | ML model builder | 5 |
| `/assistant` | AI chat | 6 |
| `/reports` | Report builder | 7 |
| `/settings` | User settings | Future |

---

## State Management Strategy

**Phase 1:** Simple React `useState` for UI state (sidebar collapsed, mobile menu). No global state library.

**Phase 2+:** TanStack Query for server state (dataset lists, previews, statistics). Local component state for UI interactions. A global state library (Zustand or React Context) will be introduced only if cross-cutting state becomes necessary.

**Principle:** Start with the simplest solution. Introduce complexity only when multiple components genuinely need shared state.

---

## Backend Architecture (Planned — Phase 2+)

```
backend/
├── main.py                 # FastAPI application entry point
├── api/                    # Route handlers
│   ├── datasets.py
│   ├── cleaning.py
│   ├── ml.py
│   └── assistant.py
├── services/               # Business logic
│   ├── dataset_service.py
│   ├── cleaning_service.py
│   ├── ml_service.py
│   └── ai_service.py
├── models/                 # Pydantic models
├── core/                   # Config, dependencies
└── storage/                # File storage utilities
```

---

## API Communication Strategy (Planned — Phase 2+)

- Frontend calls backend via REST API
- TanStack Query handles caching, loading states, error handling
- API client abstracted in `services/` directory
- File uploads via multipart/form-data
- WebSocket for AI chat streaming (Phase 6)

---

## Data Flow

```
User Action
    ↓
React Component (UI)
    ↓
Service Layer (API client)
    ↓
FastAPI Endpoint (backend)
    ↓
Processing (Pandas / Scikit-learn / LLM)
    ↓
Response (JSON)
    ↓
TanStack Query Cache
    ↓
React Component (re-render)
```
