# ThreatLens AI — Malware Classification & Threat Detection Dashboard

Production-ready frontend for a malware classification & threat detection platform.
Built with React 18, Vite, TypeScript, Tailwind CSS, Redux Toolkit, React Router,
React Hook Form + Zod, Recharts, Framer Motion, and Lucide icons.

## Getting started

```bash
npm install
npm run dev
```

Then open http://localhost:5173. Log in with any email and a password of 8+ characters —
auth, uploads, reports, alerts, and analytics all run against a mocked in-memory API layer
in `src/api/*.ts`, so the whole app is demoable with zero backend.

## Wiring up a real backend

Every service in `src/api/` (`authApi.ts`, `uploadApi.ts`, `reportsApi.ts`, `alertsApi.ts`,
`threatApi.ts`, `analyticsApi.ts`) currently returns mocked/delayed data. Swap the internals
for real `axiosInstance` calls (already configured with a JWT auth interceptor in
`src/api/axiosInstance.ts`) and set `VITE_API_BASE_URL` in `.env` — no other code needs to
change, since Redux slices and components only depend on each service's exported function
signatures.

## Project structure

```
src/
  api/          Axios instance + one service module per domain (auth, upload, reports, alerts, threats, analytics)
  components/
    ui/         Reusable primitives: Button, Input, Badge, Card, Modal, Toast, Table, Dropdown, Skeleton, ProgressBar
    layout/     Sidebar, Navbar, ProtectedRoute, ErrorBoundary
    dashboard/  StatCard, RecentActivity, RecentScans, LatestThreats, QuickActions, ThreatSeveritySummary
    charts/     Recharts wrappers: Line, Area, Bar, Pie, Radar, HeatMap
  constants/    Route paths, severity color/label config
  data/         Dummy JSON-like data powering the mocked API layer
  hooks/        useAuth, useToast, useDebounce, usePagination
  layouts/      DashboardLayout (sidebar+navbar shell), AuthLayout (centered auth card)
  pages/        One folder per feature: auth, dashboard, upload, reports, analytics, alerts, threats, settings
  redux/        Store + one slice per domain (auth, ui, dashboard, upload, reports, alerts, analytics, user)
  routes/       AppRoutes.tsx — lazy-loaded route tree with public/protected route groups
  types/        Shared TypeScript interfaces
  utils/        cn() class merger, date/number formatters, Zod validation schemas
```

## Pages

- **Login** — email/password with show/hide, remember me, Zod validation, JWT-ready auth flow
- **Dashboard** — 6 stat cards, latest threats, recent activity/scans, quick actions, severity summary
- **Upload** — drag & drop, live progress, scan history table, hash/metadata result panel
- **Reports** — searchable/filterable/paginated table, CSV/PDF export actions, detail modal, delete
- **Analytics** — line, area, bar (horizontal + vertical), pie, radar, and heat-map charts
- **Alerts** — severity + unread filters, mark-as-read, delete, animated list
- **Threat Details** — score gauge, timeline, file metadata, hash values, recommended action
- **Settings** — profile form, dark mode toggle

## Notes

- No backend or network calls are made anywhere except the intentionally-mocked API layer —
  safe to run fully offline.
- Dark cybersecurity theme (deep navy background, cyan/blue/purple accents, glassmorphism
  panels) is defined in `tailwind.config.js` and `src/index.css`.
- Routes are code-split with `React.lazy` + `Suspense`; auth state persists via `localStorage`.
