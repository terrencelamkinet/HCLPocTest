"""Import CRM export data into G08 NEXUS CRM under Kinetix tenant."""
import asyncio, sys, uuid
from datetime import datetime, timezone, timedelta
sys.path.insert(0, '/home/airoot/projects/nexus-crm-saas/backend')
from app.database import engine
from sqlalchemy import text

TENANT_ID = "00000000-0000-0000-0000-000000000001"
USER_ID = "a77d12c5-c02f-4335-88b2-1f293a74fe6f"
HKT = timezone(timedelta(hours=8))
NOW = datetime(2026, 7, 23, 16, 0, 0, tzinfo=HKT)

COMPANIES = {
    "CPCE – Poly University":           "cdca2ea9-3a52-4183-8364-1105edb18b65",
    "Queens Mary Hospital":             "d93ecb76-6d08-4dd3-8c36-79d77dda0d22",
    "Haven of Hope Christian Service":  "09b7ac32-55fd-4345-ab31-5bc5d680615c",
    "HKMC Annuity Limited":             "4cd9383d-dcd1-4f5a-8773-c9da059eeee6",
    "太興集團 (Tai Hing Group Holdings Limited)": "f7e033e7-ee10-48e4-9f5b-8041ec9fc9bf",
    "Kinetix HK":                       "2bc2b684-3a9e-4fc3-ab5d-f077cebf830d",
}

CONTACTS = {
    "Jackie Siu":   "57d1144e-a40f-49dd-9956-e31d5421231c",
    "John Cheung":  "25f0badb-50fa-46bc-803d-4a9b14971fe0",
    "Arthur To":    "0a5fe192-8b14-439d-ac58-ab2ea4f2431c",
    "Mourice Pang": "ae0c8163-0129-45e7-9236-0975f8cc1dec",
    "San Chung":    "ed14b138-08a1-45d1-aef1-46566364b088",
}

NEW_CONTACTS = [
    ("Christy TSUI", None, None, "Queens Mary Hospital"),
    ("IVY Chan", None, None, "Queens Mary Hospital"),
    ("Kenneth Chan", None, None, "Haven of Hope Christian Service"),
    ("Alvin FAN", None, None, "Haven of Hope Christian Service"),
    ("raymond", None, None, "Haven of Hope Christian Service"),
    ("Sam Wong", None, None, "CPCE – Poly University"),
    ("Keith Lee", None, None, "CPCE – Poly University"),
    ("Angnes Ng", None, None, "CPCE – Poly University"),
    ("Kris Wong", None, None, "CPCE – Poly University"),
]

def uid():
    return str(uuid.uuid4())

async def main():
    async with engine.connect() as conn:
        await conn.execute(text(f"SET app.tenant_id = '{TENANT_ID}'"))
        await conn.execute(text("BEGIN"))

        # 1. UPDATE companies
        updates = [
            ("CPCE – Poly University", {
                "ceo_name": "Prof. Peter P. Yuen (Dean)",
                "address": "3/F, North Tower, PolyU West Kowloon Campus, 9 Hoi Ting Road, Yau Ma Tei, Kowloon",
                "category": "Client", "industry": "Education",
            }),
            ("Queens Mary Hospital", {
                "ceo_name": "Dr Theresa LI (Cluster Chief Executive, Hong Kong Island Cluster)",
                "address": "102 Pokfulam Road, Hong Kong",
                "category": "Client", "industry": "Hospitality",
            }),
            ("Haven of Hope Christian Service", {
                "ceo_name": "Dr. Lam Ching-choi",
                "address": "7 Haven of Hope Road, Tseung Kwan O, New Territories, Hong Kong",
                "category": "Client", "industry": "Services",
            }),
            ("HKMC Annuity Limited", {
                "ceo_name": "Daniel Leong Ling-chi",
                "address": "19/F, Two Harbour Square, 180 Wai Yip Street, Kwun Tong, Kowloon, Hong Kong",
                "category": "Client", "industry": "Services Provider",
                "linkedin_url": "https://www.linkedin.com/company/hkmc-annuity-limited/",
            }),
            ("太興集團 (Tai Hing Group Holdings Limited)", {
                "ceo_name": "Chan Wing On (陳永安)",
                "address": "13/F, Chinachem Exchange Square, 1 Hoi Wan Street, Quarry Bay, Hong Kong",
                "category": "Client", "industry": "Manufactures",
                "linkedin_url": "https://hk.linkedin.com/company/tai-hing-group-holdings-limited",
            }),
        ]
        for name, fields in updates:
            cid = COMPANIES[name]
            sets = ", ".join(f"{k} = :{k}" for k in fields)
            await conn.execute(text(f"UPDATE nexus_crm.companies SET {sets}, updated_at = :now WHERE id = :cid AND tenant_id = :t"), 
                {**fields, "cid": cid, "t": TENANT_ID, "now": NOW})
            print(f"  ✅ Updated: {name}")

        # 2. CREATE contacts
        created = {}
        for cname, email, title, company in NEW_CONTACTS:
            cid = uid()
            await conn.execute(text(
                "INSERT INTO nexus_crm.contacts (id, tenant_id, company_id, name, email, job_title, created_at, updated_at) "
                "VALUES (:id, :t, :cid, :name, :email, :title, :now, :now)"
            ), {"id": cid, "t": TENANT_ID, "cid": COMPANIES[company], "name": cname, "email": email, "title": title, "now": NOW})
            created[cname] = cid
            print(f"  ✅ Created contact: {cname}")

        ALL_CONTACTS = {**CONTACTS, **created}

        # 3. Ensure project stages
        r = await conn.execute(text("SELECT id, stage_key FROM nexus_crm.project_stages WHERE tenant_id = :t"), {"t": TENANT_ID})
        stages = {row[1]: row[0] for row in r}
        default_stages = [
            ("first_touch", "First Touch", 1),
            ("review", "Review Existing Environment", 2),
            ("quotation", "Quotation", 3),
            ("solution_presentation", "Solution Presentation", 4),
            ("rfq", "RFQ/Tender", 5),
            ("award", "Award", 6),
            ("project_start", "Project Start", 7),
            ("project_closing", "Project Closing", 8),
        ]
        for sk, sn, so in default_stages:
            if sk not in stages:
                sid = uid()
                await conn.execute(text(
                    "INSERT INTO nexus_crm.project_stages (id, tenant_id, stage_key, stage_name, stage_order) VALUES (:id, :t, :k, :n, :o)"
                ), {"id": sid, "t": TENANT_ID, "k": sk, "n": sn, "o": so})
                stages[sk] = sid

        # 4. CREATE projects
        projects = [
            ("CPCE - ManageEngine Endpoint Central", "CPCE – Poly University", "quotation", "in_progress", "high",
             "ManageEngine Endpoint Central UEM deployment for CPCE PolyU. ~2,000 workstations across 3 campuses. Phase 1: 30x workstations pilot."),
            ("CPCE – SentinelOne Presentation Prep", "CPCE – Poly University", "solution_presentation", "in_progress", "high",
             "Preparing for SentinelOne presentation at PolyU CPCE."),
            ("Tai Hing – ITAM Discovery + OpenText ITAM Presentation", "太興集團 (Tai Hing Group Holdings Limited)", "quotation", "pending", "high",
             "ITAM discovery meeting + OpenText ITAM presentation."),
            ("HOHCS Hypervisor Upgrade", "Haven of Hope Christian Service", "quotation", "in_progress", "medium", None),
            ("Sangfor – Virtualization Implementation", "CPCE – Poly University", "quotation", "pending", "low", None),
        ]
        proj_ids = {}
        for pname, company, stage_key, status, priority, desc in projects:
            pid = uid()
            sql = """INSERT INTO nexus_crm.projects (id, tenant_id, project_code, name, company_id, stage_id, status, priority, description, created_at, updated_at)
                     VALUES (:id, :t, :pc, :name, :cid, :sid, :status, :priority, :desc, :now, :now)"""
            await conn.execute(text(sql), {
                "id": pid, "t": TENANT_ID, "pc": f"PRJ-{pid[:8].upper()}",
                "name": pname, "cid": COMPANIES[company],
                "sid": stages.get(stage_key), "status": status,
                "priority": priority, "desc": desc, "now": NOW,
            })
            proj_ids[pname] = pid
            print(f"  ✅ Created project: {pname}")

        # 5. Link contacts -> projects
        links = [
            ("CPCE - ManageEngine Endpoint Central", ["Jackie Siu", "John Cheung", "Sam Wong", "Keith Lee"]),
            ("CPCE – SentinelOne Presentation Prep", ["Jackie Siu", "Sam Wong"]),
            ("Tai Hing – ITAM Discovery + OpenText ITAM Presentation", ["San Chung"]),
            ("HOHCS Hypervisor Upgrade", ["Kenneth Chan", "Alvin FAN", "raymond"]),
        ]
        for pname, cnames in links:
            pid = proj_ids.get(pname)
            if not pid:
                continue
            for cname in cnames:
                cid = ALL_CONTACTS.get(cname)
                if cid:
                    await conn.execute(text(
                        "INSERT INTO nexus_crm.project_contacts (project_id, contact_id, relation_role) "
                        "VALUES (:pid, :cid, 'team_member')"
                    ), {"pid": pid, "cid": cid})
                    print(f"  ✅ Linked {cname} -> {pname}")

        # 6. CREATE touchpoints
        tps = [
            ("Discussion with Kinetix on HKMA AppScan Project", "Meeting", "Kinetix HK", NOW.replace(hour=10), None,
             "Discussion with Kinetix on HKMA AppScan Project"),
            ("HCL AppScan POC Discussion w/ Kinetix", "Meeting", "Kinetix HK", NOW.replace(day=16, hour=10), "Online",
             "HCL AppScan POC Discussion w/ Kinetix, HCLSoftware"),
            ("Product Introduction w/ Kinetix Team", "Meeting", "Kinetix HK", NOW.replace(day=15, hour=10), "Kinetix Office",
             "Product Introduction with digiDations and Wymax Technologies"),
            ("Fubon Bank – API Gateway Quotation & Technical Proposal Discussion", "Meeting", "Kinetix HK",
             NOW.replace(day=10, hour=10), "Central",
             "Fubon Bank API Gateway quotation discussion"),
            ("Systex NetApp Briefing", "Meeting", "Kinetix HK", NOW.replace(day=8, hour=10), None,
             "Systex NetApp Briefing with NetApp and Systex teams"),
        ]
        for title, tp_type, company, dt, location, desc in tps:
            await conn.execute(text(
                "INSERT INTO nexus_crm.touchpoints (id, tenant_id, company_id, type, title, description, date, location, created_by, created_at, updated_at) "
                "VALUES (:id, :t, :cid, :type, :title, :desc, :dt, :loc, :uid, :now, :now)"
            ), {"id": uid(), "t": TENANT_ID, "cid": COMPANIES[company], "type": tp_type,
                "title": title, "desc": desc, "dt": dt, "loc": location, "uid": USER_ID, "now": NOW})
            print(f"  ✅ Created touchpoint: {title[:50]}")

        await conn.commit()
        print("\n🎉 Import complete!")
        
        # Final counts
        for tbl in ['companies', 'contacts', 'projects', 'touchpoints', 'tasks', 'deals']:
            r = await conn.execute(text(f"SELECT COUNT(*) FROM nexus_crm.{tbl} WHERE tenant_id = :t"), {"t": TENANT_ID})
            print(f"  {tbl}: {r.fetchone()[0]}")

asyncio.run(main())
