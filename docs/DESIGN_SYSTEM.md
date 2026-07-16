# Saar AI — Design System

This document defines the visual language for Saar AI. All components and pages should follow these guidelines for consistency.

---

## Color Palette

Inspired by Google Colab's dark theme. Clean, muted, professional.

### Core Colors

| Token | Value | Usage |
|---|---|---|
| `--background` | `#202124` | Page background |
| `--foreground` | `#E8EAED` | Primary text |
| `--card` | `#2D2F31` | Card / panel surfaces |
| `--card-foreground` | `#E8EAED` | Card text |
| `--muted` | `#2D2F31` | Subdued backgrounds |
| `--muted-foreground` | `#9AA0A6` | Secondary text, labels |
| `--border` | `#3C4043` | Borders, dividers |

### Interactive Colors

| Token | Value | Usage |
|---|---|---|
| `--primary` | `#8AB4F8` | Primary actions, active states, links |
| `--primary-foreground` | `#202124` | Text on primary backgrounds |
| `--accent` | `#81C995` | Success states, secondary actions |
| `--accent-foreground` | `#202124` | Text on accent backgrounds |
| `--destructive` | `#F28B82` | Error states, destructive actions |

### Chart Colors

| Token | Value | Usage |
|---|---|---|
| `--chart-1` | `#8AB4F8` | Blue |
| `--chart-2` | `#81C995` | Green |
| `--chart-3` | `#FDD663` | Yellow |
| `--chart-4` | `#F28B82` | Red |
| `--chart-5` | `#C58AF9` | Purple |

---

## Typography

### Font Family

- **Sans-serif:** Inter (`--font-sans`) — all UI text
- **Monospace:** JetBrains Mono (`--font-geist-mono`) — code, data values

### Scale

| Level | Size | Weight | Usage |
|---|---|---|---|
| H1 | `text-3xl` (30px) | `font-semibold` (600) | Page titles |
| H2 | `text-lg` (18px) | `font-medium` (500) | Section headers |
| H3 | `text-base` (16px) | `font-medium` (500) | Subsection headers |
| Body | `text-sm` (14px) | `font-normal` (400) | Default body text |
| Small | `text-xs` (12px) | `font-normal` (400) | Labels, captions |

### Line Height

Use Tailwind defaults:
- `leading-tight` for headings
- `leading-normal` for body text

### Tracking

- `tracking-tight` for H1 headings
- Default tracking for all other text

---

## Spacing Scale

Use Tailwind's default spacing scale consistently:

| Token | Value | Common Usage |
|---|---|---|
| `1` | 4px | Inline icon gaps |
| `2` | 8px | Tight element spacing |
| `3` | 12px | List item padding |
| `4` | 16px | Standard component padding |
| `5` | 20px | Medium gaps |
| `6` | 24px | Section padding, page padding |
| `8` | 32px | Card internal padding |
| `12` | 48px | Section margins |
| `16` | 64px | Page top spacing |

---

## Border Radius

| Token | Value | Usage |
|---|---|---|
| `--radius-sm` | 3px | Small elements (badges) |
| `--radius-md` | 4px | Inputs, small buttons |
| `--radius-lg` | 8px | Default (cards, buttons) |
| `--radius-xl` | 11.2px | Large cards, modals |

Base `--radius` is `0.5rem` (8px). Use `rounded-lg` as the default.

---

## Shadows

Minimal shadow usage. The dark theme relies on borders for separation, not shadows.

| Level | CSS | Usage |
|---|---|---|
| None | — | Most components (default) |
| Subtle | `shadow-sm` | Dropdown menus, popovers |
| Elevated | `shadow-md` | Modals, overlays |

---

## Button Variants

Using shadcn/ui button component. Available variants:

| Variant | Appearance | Usage |
|---|---|---|
| `default` | Solid primary background | Primary actions |
| `secondary` | Muted background | Secondary actions |
| `outline` | Border only | Tertiary actions |
| `ghost` | Transparent, hover bg | Toolbar buttons, icon actions |
| `destructive` | Red background | Delete, remove actions |
| `link` | Text-only underline | Inline links |

### Sizes

| Size | Height | Usage |
|---|---|---|
| `sm` | 32px | Compact UIs, table actions |
| `default` | 36px | Standard buttons |
| `lg` | 40px | Prominent CTAs |
| `icon` | 36x36px | Icon-only buttons |

---

## Card Variants

Cards use `--card` background with `--border` border.

```
Container:  rounded-xl border border-border bg-card p-8
Header:     text-lg font-medium text-foreground
Body:       text-sm text-muted-foreground
```

Keep cards simple. One level of elevation. No nested cards.

---

## Input Variants

Inputs use `--input` border with `--background` fill.

```
Default:    rounded-lg border border-input bg-background px-3 py-2 text-sm
Focus:      ring-2 ring-ring
Disabled:   opacity-50 cursor-not-allowed
```

---

## Icon Sizes

Using Lucide icons consistently:

| Context | Class | Size |
|---|---|---|
| Inline (buttons) | `h-4 w-4` | 16px |
| Navigation | `h-5 w-5` | 20px |
| Feature icons | `h-7 w-7` | 28px |
| Empty states | `h-12 w-12` | 48px |

---

## Responsive Breakpoints

Using Tailwind's default breakpoints:

| Breakpoint | Min Width | Usage |
|---|---|---|
| `sm` | 640px | Small tablets |
| `md` | 768px | Tablets |
| `lg` | 1024px | Desktop (sidebar visible) |
| `xl` | 1280px | Wide desktop |
| `2xl` | 1536px | Ultra-wide |

Key behavior:
- **Below `lg`:** Sidebar hidden, hamburger menu in navbar
- **At `lg`+:** Sidebar visible, collapsible

---

## Animation Philosophy

**Principle:** Animations should serve functionality, not decoration.

**Do:**
- Smooth transitions for sidebar collapse/expand (`transition-[width] duration-200`)
- Subtle hover state changes
- Smooth page content reflow when sidebar changes

**Don't:**
- Entrance animations on page load
- Bouncing, shaking, or attention-seeking effects
- Animated gradients or backgrounds
- Loading spinners without real loading state

**Duration:** 150ms–200ms for most transitions. Never exceed 300ms.

**Easing:** `ease-in-out` for layout transitions. `ease-out` for hover effects.
