# NEXUS CRM — Meetings Module Layout Design (White Edition)

For AI to build Meetings List + Meeting Detail pages into `nexus-crm-app-white.html`.

---

## 1. New Data: `D.meetings`

Add to `const D = { ... }`:

```javascript
meetings:[
  {
    id:1,
    title:'Vantage Infra Review',
    type:'onsite',          // onsite / online / clientmeal / workshop / internal / call
    date:'2026-07-22',
    start:'10:00',
    end:'11:30',
    location:'Vantage Holdings HQ, Central',
    company:'Vantage Holdings',
    company_id:1,
    contacts:[1],            // array of contact IDs — Ada Cheung
    deal:'Storage Refresh Q3',
    deal_id:1,
    project_id:1,
    status:'upcoming',       // upcoming / in_progress / completed / cancelled
    brief:'Prepared',        // Prepared / Pending / N/A
    brief_summary:'Present storage refresh proposal, Q3 budget approval pending. Key decision maker: Ada Cheung.',
    notes:'Bring latest NetApp ASA A-Series spec sheet and pricing.',
    follow_up:'Send revised SOW after meeting',
    post_logged:false,
    outcome:null,
    calendar_event_id:'evt_abc123'
  },
  {
    id:2,
    title:'Internal Deal Sync',
    type:'internal',
    date:'2026-07-22',
    start:'13:00',
    end:'14:00',
    location:'Zoom',
    company:null,
    company_id:null,
    contacts:[2,3],          // Marcus Yip, Elaine Kwok (internal)
    deal:null,
    deal_id:null,
    project_id:null,
    status:'upcoming',
    brief:'N/A',
    brief_summary:null,
    notes:'Weekly pipeline review — focus on Q3 close plan',
    follow_up:null,
    post_logged:false,
    outcome:null,
    calendar_event_id:'evt_def456'
  },
  {
    id:3,
    title:'Security Compliance Workshop',
    type:'workshop',
    date:'2026-07-15',
    start:'09:00',
    end:'17:00',
    location:'Nova Group Office, Kwun Tong',
    company:'Nova Group',
    company_id:4,
    contacts:[4],            // Ivan Sze
    deal:'VMware Renewal',
    deal_id:3,
    project_id:null,
    status:'completed',
    brief:'Prepared',
    brief_summary:'Compliance workshop covering HKMA requirements for VMware environment audit.',
    notes:'Good session — identified 3 compliance gaps to address.',
    follow_up:'Send remediation timeline by Jul 25',
    post_logged:true,
    outcome:'Identified 3 compliance gaps. Next step: remediation plan.',
    calendar_event_id:'evt_ghi789'
  },
  {
    id:4,
    title:'NetApp Pricing Call',
    type:'call',
    date:'2026-07-20',
    start:'15:00',
    end:'15:30',
    location:'Phone',
    company:'Zentra Asia',
    company_id:null,         // not in companies list yet
    contacts:[5],            // Priya Nair
    deal:'NetApp ASA A-Series',
    deal_id:4,
    project_id:null,
    status:'completed',
    brief:'Prepared',
    brief_summary:'Price negotiation call for NetApp ASA A-Series with Zentra Asia.',
    notes:'Priya confirmed budget approved. Sent final pricing.',
    follow_up:'Send PO template by tomorrow',
    post_logged:true,
    outcome:'Budget approved. PO expected by Jul 25.',
    calendar_event_id:'evt_jkl012'
  },
  {
    id:5,
    title:'Vendor Briefing — NetApp新品',
    type:'vendor',
    date:'2026-07-28',
    start:'11:00',
    end:'12:00',
    location:'Microsoft Teams',
    company:null,
    company_id:null,
    contacts:[],
    deal:null,
    deal_id:null,
    project_id:null,
    status:'upcoming',
    brief:'Pending',
    brief_summary:null,
    notes:'NetApp product update briefing on new ASA C-Series',
    follow_up:null,
    post_logged:false,
    outcome:null,
    calendar_event_id:'evt_mno345'
  }
]
```

---

## 2. Add to Sidebar Nav

Insert after "Touchpoints" nav item, before "NameCards":

```html
<li class="nav-item" data-route="meetings" onclick="navClick(this)">
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
    <line x1="16" y1="2" x2="16" y2="6"/>
    <line x1="8" y1="2" x2="8" y2="6"/>
    <line x1="3" y1="10" x2="21" y2="10"/>
  </svg>
  <span>Meetings</span>
</li>
```

Icon: calendar-check style (rectangle with tick or clock).

---

## 3. Meetings List Page (`#meetings`)

### 3.1 Layout

```
Breadcrumb: Workspace / Meetings

Page Header: Meetings [count] [+ Schedule Meeting button]

Tab bar (3 tabs):
┌──────────┬──────────┬──────────┐
│ Upcoming │ Today    │ Past     │
│    2     │    2     │    3     │
└──────────┴──────────┴──────────┘
    (default active: Upcoming)

Default shows Upcoming tab.
Today tab — meetings with date === today.
Past tab — completed/past meetings.
```

### 3.2 Meeting Cards (not table — card-based for meetings)

```
┌────────────────────────────────────────────────────────┐
│ ┌────────────────────────────────────────────────────┐ │
│ │ 🟢 10:00 – 11:30          badge: On-site           │ │
│ │ Vantage Infra Review                                │ │
│ │ Vantage Holdings · Ada Cheung                       │ │
│ │ 📍 Vantage Holdings HQ, Central                     │ │
│ │ 📎 Storage Refresh Q3              [Brief Ready ✅] │ │
│ └────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────┐ │
│ │ 🔵 13:00 – 14:00          badge: Internal          │ │
│ │ Internal Deal Sync                                  │ │
│ │ Marcus Yip, Elaine Kwok                             │ │
│ │ 📍 Zoom                                             │ │
│ └────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────┐ │
│ │ ⚪ Jul 28 · 11:00–12:00    badge: Vendor            │ │
│ │ Vendor Briefing — NetApp新品                        │ │
│ │                                      [Brief ⏳]    │ │
│ └────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

### 3.3 Color/Icon by Meeting Type

| Type | Icon | Badge color | Dot |
|------|------|:-----------:|:---:|
| onsite | 📍 | `--color-primary` | 🟢 |
| online | 💻 | `--color-blue` | 🔵 |
| clientmeal | 🍽️ | `--color-gold` | 🟡 |
| workshop | 🔧 | `--color-purple` | 🟣 |
| internal | 👥 | `--color-text-muted` | ⚪ |
| call | 📞 | `--color-success` | 🟢 |
| vendor | 🏢 | `--color-blue` | 🔵 |

### 3.4 Sorting

- Upcoming tab: by date ASC (nearest first)
- Today tab: by start time ASC
- Past tab: by date DESC (most recent first)

---

## 4. Meeting Detail Page (`#meeting-detail/:id`)

### 4.1 Layout (two-column, 60/40)

```
Breadcrumb: Workspace / Meetings / {Meeting Title}

Page Header: ← {Meeting Title}  [badge: type]  [Edit]

Status bar (if upcoming):
┌──────────────────────────────────────────────┐
│ 🔔 Meeting starts in 2h 15m                 │
│ [Mark as done]  [Reschedule]  [Cancel]      │
└──────────────────────────────────────────────┘

Layout:
┌────────── 60% ──────────┐ ┌────── 40% ──────┐
│                          │ │                   │
│ Section: Summary         │ │ Panel: Details    │
│ ┌────────────────────┐  │ │ ┌───────────────┐ │
│ │ AI Meeting Brief   │  │ │ │ 📅 Jul 22      │ │
│ │ (if Prepared)      │  │ │ │ 🕐 10:00–11:30 │ │
│ │                    │  │ │ │ 📍 Vantage HQ  │ │
│ │ 7-dimension        │  │ │ │ 🏢 Client site │ │
│ │ analysis card      │  │ │ └───────────────┘ │
│ │ ─────────────      │  │ │                   │
│ │ Purpose: Present   │  │ │ Panel: Attendees  │ │
│ │ storage proposal   │  │ │ ┌───────────────┐ │ │
│ │ Attendees: Ada C.  │  │ │ │ 👤 Ada Cheung │ │
│ │ Background: ...    │  │ │ │   ada@...     │ │
│ │ Topics: budget,    │  │ │ │   +852 912... │ │
│ │   timeline, specs  │  │ │ │   [Contact]   │ │
│ │ Opportunities:     │  │ │ └───────────────┘ │
│ │   $482k deal       │  │ │                   │
│ │ Risks: Q3 budget   │  │ │ Panel: Linked To │ │
│ │   approval pending │  │ │ ┌───────────────┐ │ │
│ │ Suggestions: bring │  │ │ │ 💼 Vantage    │ │
│ │   spec sheet       │  │ │ │    Holdings   │ │
│ └────────────────────┘  │ │ │ 📊 Storage    │ │
│                          │ │ │    Refresh Q3 │ │
│ Section: Notes           │ │ │ 📋 Project #1 │ │
│ ┌────────────────────┐  │ │ └───────────────┘ │
│ │ Editable textarea  │  │ │                   │
│ │ "Bring latest      │  │ │ Panel: Tasks      │ │
│ │  NetApp ASA..."    │  │ │ ┌───────────────┐ │ │
│ └────────────────────┘  │ │ │ [☐] Send SOW  │ │
│                          │ │ │ [☐] Follow up │ │
│ Section: Outcome         │ │ └───────────────┘ │
│ ┌────────────────────┐  │ │                   │
│ │ (if completed)     │  │ │ Panel: Timeline   │ │
│ │ Outcome text area  │  │ │ ┌───────────────┐ │ │
│ │ + Post-logged: ✅  │  │ │ │ 🔔 Nudge sent │ │
│ │ + Follow-up task   │  │ │ │    60min before│ │
│ └────────────────────┘  │ │ │ 📄 Brief sent  │ │
│                          │ │ │    25min before│ │
│ Section: Touchpoints     │ │ │ 📝 Post-logged │ │
│ ┌────────────────────┐  │ │ │    2h after    │ │
│ │ Timeline (existing)│  │ │ └───────────────┘ │
│ └────────────────────┘  │ │                   │
│                          │ └───────────────────┘
└──────────────────────────┘
```

### 4.2 Brief Card (7 dimensions)

Inside the Summary section, a styled card:

```
┌───────────────────────────────────┐
│ 📋 Meeting Brief                  │
│                                   │
│ 🎯 Purpose                        │
│   Present storage refresh proposal│
│                                   │
│ 👥 Attendees                      │
│   Ada Cheung (VP, IT), Terrence   │
│                                   │
│ 📚 Background                     │
│   Previous discussion on Q3 budget│
│                                   │
│ 🔑 Key Topics                     │
│   Budget approval, timeline, specs│
│                                   │
│ 💰 Opportunity                    │
│   Storage Refresh Q3 — $482,000   │
│                                   │
│ ⚠️ Risks                          │
│   CFO approval still pending      │
│                                   │
│ 💡 Suggestions                    │
│   Bring spec sheet, offer trial   │
└───────────────────────────────────┘
```

### 4.3 Status Bar Components

**Upcoming meeting (within 24h):**
```
┌──────────────────────────────────────────────┐
│ 🔔 Meeting starts in 2h 15m                  │
│ [Start Meeting] [Reschedule] [Cancel]        │
└──────────────────────────────────────────────┘
```

**In progress:**
```
┌──────────────────────────────────────────────┐
│ ▶️ Meeting in progress (started 10:02)       │
│ [End Meeting]                                │
└──────────────────────────────────────────────┘
```

**Completed:**
```
┌──────────────────────────────────────────────┐
│ ✅ Completed · 1h 15m duration               │
│ [Edit Outcome] [Log Touchpoint] [Add Task]   │
└──────────────────────────────────────────────┘
```

---

## 5. Meeting Status/Type Badge Functions

Add alongside existing `stageBadge()` / `roleBadge()`:

```javascript
function meetingTypeBadge(t) {
  const m = {
    onsite:['On-site','var(--color-primary)','var(--color-primary-highlight)'],
    online:['Online','var(--color-blue)','var(--color-blue-highlight)'],
    clientmeal:['Client Meal','var(--color-gold)','var(--color-gold-highlight)'],
    workshop:['Workshop','var(--color-purple)','var(--color-purple-highlight)'],
    internal:['Internal','var(--color-text-faint)','var(--color-surface-offset)'],
    call:['Call','var(--color-success)','var(--color-success-highlight)'],
    vendor:['Vendor','var(--color-blue)','var(--color-blue-highlight)']
  };
  const v = m[t] || [t,'var(--color-text-faint)','var(--color-surface-offset)'];
  return `<span class="badge" style="background:${v[2]};color:${v[1]}">${v[0]}</span>`;
}
```

**Meeting type icon SVG** (for list cards):
```javascript
function meetingIcon(t) {
  const icons = {
    onsite:'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
    online:'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
    clientmeal:'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/></svg>',
    workshop:'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>',
    internal:'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="7" r="4"/><path d="M2 21v-1a7 7 0 0 1 14 0v1"/><circle cx="17" cy="7" r="3"/><path d="M22 21v-1a5 5 0 0 0-4-4.9"/></svg>',
    call:'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3-8.7A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7 12.8 12.8 0 0 0 .7 2.8 2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.5 12.8 12.8 0 0 0 2.8.7 2 2 0 0 1 1.7 2z"/></svg>',
    vendor:'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>'
  };
  return icons[t] || icons.internal;
}
```

---

## 6. Update Dashboard

Replace hardcoded "Today's meetings" section in `dashboard()` to read from `D.meetings`:

```html
<!-- Currently hardcoded, should become: -->
${D.meetings.filter(m=>m.date===today && m.status==='upcoming').slice(0,3).map(m=>`
  <div class="meeting-slot" data-nav="meeting-detail" data-id="${m.id}">
    <div class="time">${m.start.split(':')[0] > 11 ? 'PM' : 'AM'}<b>${m.start}</b></div>
    <div class="meeting-card ${m.company?'highlight':''}">
      <div class="m-title">${m.title}</div>
      <div class="m-sub">${m.company||m.location}</div>
    </div>
  </div>`).join('')}
```

Also update weekly grid `weekEvents` to read from meetings data when available.

---

## 7. Router Update

```javascript
'meeting-detail'(id){
  const m = D.meetings.find(x=>x.id==id) || D.meetings[0];
  // ... render detail page
},
meetings(){
  // ... render list with tabs
}
```

Add to hash router:
```javascript
const [route, id] = hash.split('/');
const fn = pages[route] || pages.dashboard;
```
Already handles `meeting-detail/:id` ✓

---

## 8. Desktop Safeguards

- Meeting list: cards layout (not table) — works on all screen sizes
- Detail page: `grid-template-columns: 1fr 380px` (same as project-detail / contact-detail)
- Mobile: collapse to single column at ≤900px (same breakpoint)
- Brief card: same panel style as existing
- Status bar: fixed width, no overflow
- Timeline panel: uses existing `.timeline` / `.tl-item` components
