# NEXUS CRM — White Edition + Projects, Sales, Integrations, Full Mobile Responsive

Single-file HTML/CSS/JS CRM app.

## What's new in this version — Mobile / Tablet responsive overhaul
Tested against real device breakpoints for iPhone, Android, and iPad:

| Breakpoint | Target devices | Key changes |
|---|---|---|
| ≤1200px | Small laptops | KPI/top-row/dashboard grids collapse to 1-2 cols |
| ≤1024px | iPad landscape | Sidebar narrows, integration cards reflow |
| ≤900px | iPad portrait, large phones | Sidebar becomes off-canvas drawer + scrim, search hidden from topbar |
| ≤640px | iPhone / Android portrait | Full single-column layout, tables scroll horizontally, kanban becomes swipeable full-width cards with scroll-snap, forms use 16px font (prevents iOS auto-zoom), all tap targets enforced ≥44px, settings tabs become horizontal scroll |
| ≤380px | iPhone SE / narrow Android | Further-reduced type scale, focus ring shrinks, kbd hint hidden |
| Landscape + short height | Phones in landscape | Compact topbar height |
| `hover:none` | All touch devices | Hover-only shadow/transform effects disabled, active-state tap feedback added instead |

Other mobile-specific fixes:
- `env(safe-area-inset-top)` padding on topbar/sidebar for iPhone notch/Dynamic Island
- `100dvh` app shell height correctly handles Safari's dynamic toolbar show/hide
- `-webkit-overflow-scrolling: touch` on all horizontal-scroll regions (tables, kanban, weekly grid, tabs, settings nav)
- Single scroll region preserved (`.main-content`) — no nested scroll traps on mobile

## Usage
Open `nexus-crm-app-white.html` directly in any modern browser (desktop or mobile). No build step required.

## Routes
`#dashboard` `#contacts` `#contact-detail/:id` `#companies` `#company-detail/:id` `#deals` `#deal-detail`
`#projects` `#project-detail/:id` `#team` `#team-detail/:id` `#sales-dashboard`
`#tasks` `#touchpoints` `#namecards`
`#settings/profile` `#settings/team` `#settings/integrations` `#settings/billing`
