# NEXUS CRM — Project & Sales Layout Design (Ivory Edition)

For AI to build the visual UI only. Data connections handled separately.

---

## 1. Project Details Page

### 1.1 Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│ Breadcrumb:  Workspace / Projects / {Project Name}      │
├─────────────────────────────────────────────────────────┤
│ Page Header                                              │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ◄ Project Name                    [Edit] [Delete]   │ │
│ │ badge: In Progress  badge: P1  stage: Execution    │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Two-column layout:                                       │
│                                                          │
│ ┌────────── 65% ──────────┐ ┌────── 35% ──────┐        │
│ │                         │ │                    │        │
│ │ Section: Description    │ │ Panel: Details     │        │
│ │ ┌───────────────────┐  │ │ ┌────────────────┐ │        │
│ │ │ Multi-line text   │  │ │ │ Company        │ │        │
│ │ │ Lorem ipsum       │  │ │ │ ┌────────────┐ │ │        │
│ │ │                   │  │ │ │ │Vantage Hld │ │ │        │
│ │ └───────────────────┘  │ │ │ └────────────┘ │ │        │
│ │                         │ │ │                │ │        │
│ │ Section: Tasks          │ │ │ Customer       │ │        │
│ │ ┌───────────────────┐  │ │ │ ┌────────────┐ │ │        │
│ │ │ [ ] Follow up     │  │ │ │ │Ada Cheung  │ │ │        │
│ │ │ [x] Done task     │  │ │ │ │ada@...     │ │ │        │
│ │ │ [ ] Another one   │  │ │ │ │+852 912... │ │ │        │
│ │ │ + Add task        │  │ │ │ └────────────┘ │ │        │
│ │ └───────────────────┘  │ │ │                │ │        │
│ │                         │ │ │ Related Deal   │ │        │
│ │ Section: Touchpoints    │ │ │ ┌────────────┐ │ │        │
│ │ ┌───────────────────┐  │ │ │ │Storage Ref │ │ │        │
│ │ │ Timeline items    │  │ │ │ │$482,000    │ │ │        │
│ │ │ (existing style)  │  │ │ │ └────────────┘ │ │        │
│ │ └───────────────────┘  │ │ │                │ │        │
│ │                         │ │ │ Owner          │ │        │
│ │                         │ │ │ ┌────────────┐ │ │        │
│ │                         │ │ │ │Terrence Lm │ │ │        │
│ │                         │ │ │ └────────────┘ │ │        │
│ │                         │ │ │                │ │        │
│ │                         │ │ │ Timeline       │ │        │
│ │                         │ │ │ ┌────────────┐ │ │        │
│ │                         │ │ │ │Start       │ │ │        │
│ │                         │ │ │ │2026-06-15  │ │ │        │
│ │                         │ │ │ │Target end  │ │ │        │
│ │                         │ │ │ │2026-09-30  │ │ │        │
│ │                         │ │ │ └────────────┘ │ │        │
│ │                         │ │ │                │ │        │
│ │                         │ │ │ Budget         │ │        │
│ │                         │ │ │ ┌────────────┐ │ │        │
│ │                         │ │ │ │ $482,000   │ │ │        │
│ │                         │ │ │ │ █████░░░   │ │ │        │
│ │                         │ │ │ │ $210k/482k │ │ │        │
│ │                         │ │ │ └────────────┘ │ │        │
│ │                         │ │ │                │ │        │
│ │                         │ │ │ Tags           │ │        │
│ │                         │ │ │ ┌────────────┐ │ │        │
│ │                         │ │ │ │storage │   │ │ │        │
│ │                         │ │ │ │netapp  │   │ │ │        │
│ │                         │ │ │ │infra   │   │ │ │        │
│ │                         │ │ │ └────────────┘ │ │        │
│ │                         │ │ └────────────────┘ │        │
│ └─────────────────────────┘ └────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Component Specs

**Breadcrumb:** Same as existing design02 — `color:var(--color-text-faint)` for parent, `current` class for active

**Page Header:**
- Title: `<h1>` with back arrow button (←) that navigates to Projects list
- Badge row: existing `statusBadge()` for status, `prioBadge()` for priority, new `stageBadge()` for stage
- Actions: `btn-secondary` Edit, `btn-danger` Delete (same style as other page headers)

**Left column (65%):**

| Section | Component | Reuse existing? |
|---------|-----------|-----------------|
| Description | Panel with textarea or rich text div | New — plain `<div>` styled like `.form-row textarea` |
| Tasks | Checklist with checkboxes, priority chip, due date | New — similar to dashboard's task-row but with checkbox |
| Touchpoints | Same timeline as existing (`tl-item`, `tl-card`) | ✅ Same as touchpoints page |

**Right column (35%):**

| Field | Component |
|-------|-----------|
| Company | Clickable card (avatar-sm + name), navigates to company-detail |
| Customer | Contact card (avatar-sm + name + email + phone), navigates to contact-detail |
| Related Deal | Small card with deal name + amount |
| Owner | Avatar-sm + name |
| Timeline | Icon + date fields (calendar style) |
| Budget | Progress bar (green/yellow/red based on % spent) + labels |
| Tags | Tag chips (same as `.tag` in profile-card) |

### 1.3 New CSS Variables Needed

```css
/* None — reuses existing design02 variables */
/* New class for budget progress bar: */
.project-budget-bar {
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--color-surface-offset);
  overflow: hidden;
}
.project-budget-fill {
  height: 100%;
  border-radius: var(--radius-full);
  transition: width var(--transition-interactive);
}
.project-budget-fill.safe { background: var(--color-success); }
.project-budget-fill.warn { background: var(--color-warning); }
.project-budget-fill.danger { background: var(--color-notification); }
```

### 1.4 Checklist Component (new, for tasks section)

```
┌──────────────────────────────────────────┐
│ ☐ Follow up on NetApp quote    P0  Today │
│ ☑ Send revised SOW             P1  Overdue│
│ ☐ Schedule call                 P2  Jul 24│
│ + Add task                                │
└──────────────────────────────────────────┘
```

Style: same background as `.list-row`, checkbox circle (CSS-only), priority badge right-aligned.

---

## 2. Projects List Page

### 2.1 Table Layout

Same as existing Companies page layout:

```
Breadcrumb: Workspace / Projects

Page Header: [h1: Projects] [count badge] [+ New Project button]

Toolbar: [search box] [Status: All ▼] [Priority: All ▼]

Data Table:
┌─────────┬────────┬────────┬────────┬────────┬────────┬────────┐
│ Project │ Status │ Stage  │ Budget │ Company│ Owner  │ Due    │
├─────────┼────────┼────────┼────────┼────────┼────────┼────────┤
│ Storage │ 🟡 P1  │ Exec   │$482k   │Vantage │ TL     │ Sep 30 │
│ DR      │ 🔵 P2  │ Kickoff│$210k   │Harbour │ TL     │ Dec 31 │
└─────────┴────────┴────────┴────────┴────────┴────────┴────────┘
```

Rows clickable → navigates to project-detail/:id

### 2.2 Grid View (optional, toggleable)

Card-based layout like existing NameCards page:

```
┌──────────┐ ┌──────────┐ ┌──────────┐
│Storage   │ │DR Migratn│ │Project 3 │
│🟡 P1     │ │🔵 P2     │ │🟢 P3     │
│Vantage   │ │Harbour   │ │Company   │
│$482k     │ │$210k     │ │$120k     │
│Sep 30    │ │Dec 31    │ │Aug 15    │
└──────────┘ └──────────┘ └──────────┘
```

---

## 3. Sales — Team List Page

### 3.1 Layout (table)

```
Breadcrumb: Workspace / Sales / Team

Page Header: Team [count] [+ Add Member button]

Toolbar: [search] [Role: All ▼] [Territory: All ▼]

Data Table:
┌──────────┬───────────┬───────────┬──────────┬──────────┬──────────┬──────────┐
│ Name     │ Role      │ Territory │ Quota/M  │ Achieved │ Pipeline │ Manager  │
├──────────┼───────────┼───────────┼──────────┼──────────┼──────────┼──────────┤
│Terrence  │ Director  │ HK All    │$500k     │ 45% ███  │ $978k    │ —        │
│Ada C.    │ Sales Rep │ HK Island │$200k     │ 16% █    │ $340k    │ Terrence │
│Marcus Y. │ Sales Rep │ Kln East  │$200k     │ 21% ██   │ $128k    │ Terrence │
└──────────┴───────────┴───────────┴──────────┴──────────┴──────────┴──────────┘
```

Each row clickable → navigates to team-detail/:id

### 3.2 Achieved % Column

Progress bar inline in table cell (smaller version of budget bar):
- >80% = green
- 50-80% = yellow  
- <50% = red

---

## 4. Sales — Team Member Detail

```
Breadcrumb: Workspace / Sales / Team / {Name}

Page Header: [Name] badge: role [Edit]

Layout:
┌────────── 40% ──────────┐ ┌────── 60% ──────┐
│                          │ │                   │
│ Panel: Profile Card      │ │ Section: Quota    │
│ ┌────────────────────┐   │ │ ┌───────────────┐ │
│ │   [Avatar initials] │   │ │ Q3 2026        │ │
│ │   Name              │   │ │ ████████░░ 45% │ │
│ │   Role              │   │ │ $675k / $1.5M  │ │
│ │   Email             │   │ │                │ │
│ │   Phone             │   │ │ Pipeline $978k │ │
│ │   Territory         │   │ │ Closed 1 deal  │ │
│ │   Manager: name     │   │ │ Avg $675k      │ │
│ │   Status: active    │   │ └───────────────┘ │
│ └────────────────────┘   │                   │
│                           │ Section: Deals    │
│ Panel: Quick Stats       │ ┌───────────────┐ │
│ ┌────────────────────┐   │ │ Kanban cards   │ │
│ │ Closed this Q: 1   │   │ │ filtered by    │ │
│ │ Pipeline value:    │   │ │ this owner     │ │
│ │   $978k            │   │ └───────────────┘ │
│ │ Win rate: 33%      │   │                   │
│ │ Avg deal: $297k    │   │ Section: Projects │
│ └────────────────────┘   │ ┌───────────────┐ │
│                           │ │ Mini table    │ │
│                           │ │ of linked     │ │
│                           │ │ projects      │ │
│                           │ └───────────────┘ │
└──────────────────────────┘ └───────────────────┘
```

---

## 5. Sales Dashboard Page

### 5.1 Layout

```
Breadcrumb: Workspace / Sales / Dashboard

Page Header: Sales Dashboard

Top Row (3 stat cards, same as existing top-row in dashboard):
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Pipeline     │ │ Team Quota  │ │ Win Rate     │
│ Total        │ │ Achievement │ │              │
│ $2.18M       │ │ 31% ███    │ │ 42%          │
│ ↑12% from Q2 │ │ of $5.1M   │ │ +5pts from Q2│
└─────────────┘ └─────────────┘ └─────────────┘

Middle Row (2 panels):
┌────────────── 50% ──────────────┐ ┌────── 50% ──────┐
│ Panel: Team Ranking              │ │ Panel: Territory│
│ ┌────────────────────────────┐  │ │ Breakdown       │
│ │ #  Name        Quota  Ach% │  │ │ ┌────────────┐  │
│ │ 1  Marcus Y.  $600k  21%  │  │ │ │ Pie/donut  │  │
│ │ 2  Ada C.     $600k  16%  │  │ │ │ chart      │  │
│ │ 3  Terrence   $1.5M  45%  │  │ │ │ HK Is 31%  │  │
│ └────────────────────────────┘  │ │ │ Kln E 17%  │  │
│                                  │ │ │ HK All 52% │  │
│ Panel: Recent Activity           │ └────────────┘  │
│ ┌────────────────────────────┐  │ └────────────────┘ │
│ │ Timeline (existing style)  │  │                    │
│ │ filtered by all team       │  │                    │
│ └────────────────────────────┘  │                    │
└──────────────────────────────────┴────────────────────┘

Bottom Row:
┌──────────────────────────────────────────────────────┐
│ Panel: Team Activity Heatmap (optional)               │
│ ┌──────────────────────────────────────────────────┐ │
│ │ Mon ████  Tue ██  Wed ██████  Thu ██  Fri ████  │ │
│ └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### 5.2 Stat Cards

Reuse same style as dashboard's focus-timer / today's-tasks / today's-meetings cards in `.top-row .panel`.

---

## 6. Sidebar Nav Update

Add these items to existing sidebar nav:

```
🟦 Projects      → #projects
💼 Team          → #team
📊 Sales         → #sales-dashboard
```

Position after existing "Deals" item, before "Tasks".

Icon style: same as existing nav items (sidebar svg + text).

---

## 7. Color & Styling Rules

- **All new pages** follow existing design02 CSS variables — no new theme
- **Status badges**: reuse `statusBadge()` function (active/warm/cold, but add: planning/in_progress/on_hold/completed/cancelled)
- **Stage badges**: new function `stageBadge(s)` — same pill style, colours:
  - kickoff = `--color-blue`
  - discovery = `--color-purple`
  - execution = `--color-primary`
  - uat = `--color-warning`
  - handover = `--color-gold`
  - closed = `--color-success`
- **Role badges**: new function `roleBadge(r)`:
  - director = `--color-gold`
  - sales_manager = `--color-blue`
  - sales_rep = `--color-primary`
  - admin = `--color-text-faint`
- **Priority**: reuse existing `prioBadge()` — same P0-P3 colours

---

## 8. Layout Rules

- **Left/right columns**: use CSS Grid `grid-template-columns: 1fr 380px` (same as existing `.detail-grid` in contact-detail)
- **Mobile**: collapse to single column at ≤900px (same breakpoint as sidebar collapse)
- **Spacing**: same as existing — panel padding `20px`, gap `16px`
- **Animations**: same `animate-in` class for staggered fade-in
- **Breadcrumbs**: same style as all existing pages
- **Tables**: same `.data-table` class
- **Panels**: same `.panel` + `.panel-head` structure

---

## 9. New Badge Functions

Add these alongside existing `statusBadge()`, `prioBadge()`, `initials()`:

```javascript
function stageBadge(s) {
  const m = {
    kickoff: ['Kickoff','--color-blue'],
    discovery: ['Discovery','--color-purple'],
    execution: ['Execution','--color-primary'],
    uat: ['UAT','--color-warning'],
    handover: ['Handover','--color-gold'],
    closed: ['Closed','--color-success']
  };
  const [label, color] = m[s] || [s, '--color-text-faint'];
  return `<span class="badge" style="background:color-mix(in srgb, ${color} 20%, transparent);color:${color}">${label}</span>`;
}

function roleBadge(r) {
  const m = {
    director: ['Director','--color-gold'],
    sales_manager: ['Manager','--color-blue'],
    sales_rep: ['Sales Rep','--color-primary'],
    admin: ['Admin','--color-text-faint']
  };
  const [label, color] = m[r] || [r, '--color-text-faint'];
  return `<span class="badge" style="background:color-mix(in srgb, ${color} 20%, transparent);color:${color}">${label}</span>`;
}
```

---

## 10. All New Pages Summary

| Page | Hash Route | Layout |
|------|-----------|--------|
| Projects List | `#projects` | Table (same as companies) |
| Project Detail | `#project-detail/:id` | Two-column: description+tasks+touchpoints / details sidebar |
| Team List | `#team` | Table with progress bars |
| Team Member Detail | `#team-detail/:id` | Two-column: profile+stats / quota+deals+projects |
| Sales Dashboard | `#sales-dashboard` | 3 stat cards + 2-panel row + activity timeline |
