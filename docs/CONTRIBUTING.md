# Saar AI — Contributing Guide

## Coding Conventions

### TypeScript

- Strict mode enabled
- Prefer `interface` over `type` for object shapes
- Use explicit return types for non-trivial functions
- Avoid `any` — use `unknown` and narrow with type guards
- Use `const` by default, `let` when reassignment is necessary

### React

- Functional components only
- Props interfaces defined above the component
- One component per file
- Component file name matches the exported component (kebab-case files, PascalCase exports)
- Colocate component-specific types in the same file
- Shared types go in `frontend/src/types/`

### CSS / Tailwind

- Use Tailwind utility classes for all styling
- Use `cn()` from `@/lib/utils` for conditional classes
- Design tokens defined in `globals.css` via CSS custom properties
- No inline `style` attributes unless absolutely necessary
- No custom CSS files per component — use Tailwind

---

## Naming Conventions

### Files and Directories

| Type | Convention | Example |
|---|---|---|
| Components | kebab-case | `app-shell.tsx` |
| Hooks | kebab-case with `use-` prefix | `use-datasets.ts` |
| Services | kebab-case with `-service` suffix | `dataset-service.ts` |
| Constants | kebab-case | `navigation.ts` |
| Types | kebab-case | `dataset.ts` |
| Pages | `page.tsx` (Next.js convention) | `app/datasets/page.tsx` |

### Code

| Type | Convention | Example |
|---|---|---|
| Components | PascalCase | `AppShell` |
| Hooks | camelCase with `use` prefix | `useDatasets` |
| Functions | camelCase | `formatDate` |
| Constants | UPPER_SNAKE_CASE or camelCase | `MAX_FILE_SIZE`, `navigationItems` |
| Interfaces | PascalCase | `DatasetMetadata` |
| Enums | PascalCase | `ChartType` |

---

## Folder Conventions

- **`frontend/src/app/`** — Only route pages and layouts. No business logic.
- **`frontend/src/components/ui/`** — shadcn/ui primitives only. Do not modify unless extending the design system.
- **`frontend/src/components/layout/`** — App-wide layout components (navbar, sidebar, shell).
- **`frontend/src/components/common/`** — Shared components used across multiple features.
- **`frontend/src/features/[name]/`** — Feature-specific components, hooks, services, types.
- **`frontend/src/hooks/`** — App-wide custom hooks (not feature-specific).
- **`frontend/src/services/`** — API clients and external integrations.
- **`frontend/src/lib/`** — Pure utility functions.
- **`frontend/src/constants/`** — Static configuration and constants.
- **`frontend/src/types/`** — Shared TypeScript type definitions.

### Rule: No Empty Directories

Do not create directories without files in them. Create directories when the first file is needed.

---

## Commit Message Style

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>
```

### Types

| Type | Usage |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code restructuring, no behavior change |
| `test` | Adding or updating tests |
| `chore` | Build, tooling, dependencies |

### Examples

```
feat(datasets): add CSV upload component
fix(sidebar): correct active state on nested routes
docs: update ARCHITECTURE.md with API flow
chore: upgrade shadcn/ui components
```

---

## Branch Naming Strategy

```
<type>/<short-description>
```

### Examples

```
feat/dataset-upload
fix/sidebar-collapse
docs/update-roadmap
chore/upgrade-dependencies
```

---

## Pull Request Expectations

### Before Submitting

- [ ] Code compiles (`npm run build`)
- [ ] Lint passes (`npm run lint`)
- [ ] No unused files or dependencies
- [ ] Documentation updated if applicable
- [ ] Commit messages follow convention

### PR Description

Include:
- **What** changed
- **Why** it changed
- **How** to test it
- Screenshots for UI changes

### Review

- Every PR requires at least one review
- Address all review comments before merging
- Squash merge to keep history clean
