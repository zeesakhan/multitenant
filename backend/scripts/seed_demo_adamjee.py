"""Seed demo data using raw SQL for reliability."""
import sys, uuid, json, os, re
from decimal import Decimal
from datetime import datetime, date, timedelta, timezone
import psycopg2

# Read DATABASE_URL from .env if available, otherwise fall back to current OS user
def _get_db_conn():
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    db_url = None
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                m = re.match(r'^DATABASE_URL\s*=\s*(.+)', line.strip())
                if m:
                    db_url = m.group(1).strip()
                    break
    if db_url:
        return psycopg2.connect(db_url)
    # Fallback: connect as current OS user
    return psycopg2.connect(database='health_insurance', user=os.getenv('USER', os.getenv('LOGNAME', '')))

conn = _get_db_conn()
cur = conn.cursor()

# Lookup tenant by code (works on any machine after main.py seed)
cur.execute("SELECT id FROM tenants WHERE code = 'ADAMJEE' LIMIT 1")
row = cur.fetchone()
if not row:
    print("ERROR: Adamjee tenant not found. Run: venv/bin/python main.py  first.")
    sys.exit(1)
TENANT_ID = row[0]

# Lookup admin user
cur.execute("SELECT id FROM users WHERE email = 'admin@adamjee.ae' AND tenant_id = %s LIMIT 1", (TENANT_ID,))
row = cur.fetchone()
if not row:
    print("ERROR: admin@adamjee.ae not found. Run: venv/bin/python main.py  first.")
    sys.exit(1)
ADMIN_USER = row[0]

print(f"Tenant: {TENANT_ID}")
print(f"Admin:  {ADMIN_USER}")

uid = lambda: str(uuid.uuid4())
ago = lambda n: (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()
future = lambda n: (datetime.now(timezone.utc) + timedelta(days=n)).isoformat()

# Get plans
cur.execute("SELECT id, name, product_id FROM plans WHERE tenant_id = %s ORDER BY created_at", (TENANT_ID,))
plans = cur.fetchall()
if not plans:
    print("ERROR: No plans found")
    sys.exit(1)
print(f"Found {len(plans)} plans")
# plans: [(id, name, product_id), ...]
gplan = lambda i: plans[min(i, len(plans)-1)]  # returns (id, name, product_id)

def insert_app(app_id, num, name, email, status, plan_idx, aml_status, aml_score, govt_status, premium, cover, sponsor, occ, employer, marital, existing_health, diplomatic, breakdown, days):
    plan = gplan(plan_idx)
    cur.execute("""
        INSERT INTO applications (id, tenant_id, application_number, customer_name, customer_email,
            status, plan_id, aml_status, aml_risk_score, govt_check_status, total_premium, cover_amount,
            sponsor_type, occupation, employer_name, marital_status, existing_health_insurance,
            is_diplomatic_passport, premium_breakdown, member_count, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s,%s)
        ON CONFLICT (id) DO NOTHING
    """, (app_id, TENANT_ID, num, name, email, status, plan[0],
          aml_status, aml_score, govt_status, premium, cover, sponsor,
          occ, employer, marital, existing_health, diplomatic,
          json.dumps(breakdown) if breakdown else None, ago(days), ago(days)))

def insert_member(app_id, fname, lname, dob, gender, rel, nat, eid, passport, visa, height, weight, diplomatic=False):
    cur.execute("""
        INSERT INTO members (id, tenant_id, application_id, first_name, last_name, date_of_birth,
            gender, relationship, nationality, emirates_id, passport_number, visa_type,
            height_cm, weight_kg, is_diplomatic_passport, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO NOTHING
    """, (uid(), TENANT_ID, app_id, fname, lname, dob, gender, rel, nat, eid, passport, visa,
          height, weight, diplomatic, ago(45), ago(0)))

def insert_policy(pol_id, app_id, pol_num, name, email, premium, eff_days, exp_days, issued_days):
    plan_id = None
    cur.execute("SELECT plan_id FROM applications WHERE id = %s", (app_id,))
    row = cur.fetchone()
    if row: plan_id = row[0]
    cur.execute("SELECT product_id FROM plans WHERE id = %s", (plan_id,))
    row = cur.fetchone()
    product_id = row[0] if row else None
    cur.execute("""
        INSERT INTO policies (id, tenant_id, application_id, plan_id, product_id,
            policy_number, customer_name, customer_email, member_count, total_premium,
            status, effective_date, expiry_date, issued_by, issued_at, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1,%s,'active',%s,%s,%s,%s,%s,%s)
        ON CONFLICT ON CONSTRAINT uq_policies_tenant_number DO NOTHING
    """, (pol_id, TENANT_ID, app_id, plan_id, product_id, pol_num, name, email, premium,
          ago(eff_days), future(365-eff_days), ADMIN_USER, ago(issued_days), ago(issued_days), ago(0)))

def insert_payment(pol_id, amount, method, ref, days, pay_num=None):
    pnum = pay_num or ref
    cur.execute("""
        INSERT INTO payments (id, tenant_id, payment_number, policy_id, amount, method, status, reference, paid_at, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,'success',%s,%s,%s,%s)
        ON CONFLICT (id) DO NOTHING
    """, (uid(), TENANT_ID, pnum, pol_id, amount, method, ref, ago(days), ago(days), ago(0)))

def insert_aml(app_id, member_id, status, score, factors, pep_match):
    cur.execute("""
        INSERT INTO aml_records (id, tenant_id, application_id, member_id, check_type, status,
            risk_score, raw_response, checked_at, created_at, updated_at)
        VALUES (%s,%s,%s,%s,'risk_score',%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO NOTHING
    """, (uid(), TENANT_ID, app_id, member_id, status, score,
          json.dumps({"factors": factors, "pep_match": pep_match}),
          ago(7), ago(7), ago(0)))

def insert_notification(ntype, title, body, etype, eid, is_read, days):
    cur.execute("""
        INSERT INTO notification_records (id, tenant_id, recipient_user_id, notification_type,
            title, body, related_entity_type, related_entity_id, is_read, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO NOTHING
    """, (uid(), TENANT_ID, ADMIN_USER, ntype, title, body, etype, eid, is_read, ago(days), ago(0)))

def insert_loading(app_id, member_id, ltype, amount, notes, days):
    cur.execute("""
        INSERT INTO premium_loadings (id, tenant_id, application_id, member_id, loading_type,
            amount, applied_by, applied_at, notes, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO NOTHING
    """, (uid(), TENANT_ID, app_id, member_id, ltype, amount, ADMIN_USER,
          ago(days), notes, ago(days), ago(0)))

def insert_govt_check(app_id, member_id, ctype, status, days):
    cur.execute("""
        INSERT INTO govt_verification_records (id, tenant_id, application_id, member_id, check_type, status,
            request_payload, response_payload, triggered_at, resolved_at, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO NOTHING
    """, (uid(), TENANT_ID, app_id, member_id, ctype, status,
          json.dumps({"name": "test", "dob": "1970-01-01"}),
          json.dumps({"matched": False, "status": status}),
          ago(days), ago(days), ago(days), ago(0)))

# ── Application 1: Issued, 3 members ─────────────────────────────────────────
a1 = uid()
insert_app(a1,'APP-2026-0001','Mohammed Al-Rashid','m.alrashid@techcorp.ae',
    'issued',2,'clear',12.50,'verified',8750.00,500000.00,'corporate',
    'Senior IT Manager','TechCorp FZE Dubai','married','expired_gt30',False,
    {"gross_premium_excl_tax":8333.33,"vat_amount":416.67,"psp_fee":24.00,"amount_payable":8750.00},45)

m1_id = uid()
cur.execute("""INSERT INTO members (id,tenant_id,application_id,first_name,last_name,date_of_birth,gender,relationship,nationality,emirates_id,passport_number,visa_type,height_cm,weight_kg,created_at,updated_at) VALUES (%s,%s,%s,'Mohammed','Al-Rashid','1982-03-15','male','self','AE','784-1982-1234567-1','AE123456','employment',178.0,82.0,%s,%s) ON CONFLICT (id) DO NOTHING""",
    (m1_id,TENANT_ID,a1,ago(45),ago(0)))
cur.execute("""INSERT INTO members (id,tenant_id,application_id,first_name,last_name,date_of_birth,gender,relationship,nationality,emirates_id,visa_type,height_cm,weight_kg,created_at,updated_at) VALUES (%s,%s,%s,'Fatima','Al-Rashid','1985-07-22','female','spouse','AE','784-1985-7654321-2','employment',162.0,58.0,%s,%s) ON CONFLICT (id) DO NOTHING""",
    (uid(),TENANT_ID,a1,ago(45),ago(0)))
cur.execute("""INSERT INTO members (id,tenant_id,application_id,first_name,last_name,date_of_birth,gender,relationship,nationality,created_at,updated_at) VALUES (%s,%s,%s,'Omar','Al-Rashid','2010-11-05','male','child','AE',%s,%s) ON CONFLICT (id) DO NOTHING""",
    (uid(),TENANT_ID,a1,ago(45),ago(0)))
p1 = uid()
insert_policy(p1,a1,'POL-2026-00001','Mohammed Al-Rashid','m.alrashid@techcorp.ae',8750.00,30,335,30)
insert_payment(p1,8750.00,'card','PAY-2026-00001',30)

# ── Application 2: Submitted, AML MEDIUM ─────────────────────────────────────
a2 = uid()
insert_app(a2,'APP-2026-0002','Rajesh Sharma','r.sharma@globaltrading.ae',
    'submitted',4,'flagged',38.75,'verified',12400.00,1000000.00,'corporate',
    'Import/Export Trader','Global Trading LLC','married','active_policy',False,None,12)
m2_id = uid()
cur.execute("""INSERT INTO members (id,tenant_id,application_id,first_name,last_name,date_of_birth,gender,relationship,nationality,passport_number,visa_type,height_cm,weight_kg,created_at,updated_at) VALUES (%s,%s,%s,'Rajesh','Sharma','1978-09-20','male','self','IN','K1234567','employment',172.0,88.0,%s,%s) ON CONFLICT (id) DO NOTHING""",
    (m2_id,TENANT_ID,a2,ago(12),ago(0)))
cur.execute("""INSERT INTO members (id,tenant_id,application_id,first_name,last_name,date_of_birth,gender,relationship,nationality,visa_type,height_cm,weight_kg,created_at,updated_at) VALUES (%s,%s,%s,'Priya','Sharma','1981-04-10','female','spouse','IN','employment',158.0,62.0,%s,%s) ON CONFLICT (id) DO NOTHING""",
    (uid(),TENANT_ID,a2,ago(12),ago(0)))
insert_aml(a2,m2_id,'flagged',38.75,{"fatf_nationality":15,"premium_threshold":10,"occupation_risk":8,"income_inconsistency":5},False)
insert_loading(a2,m2_id,'underwriter',800.00,'High-risk occupation loading — import/export with FATF nationality',10)

# ── Application 3: AML HOLD - Diplomatic/PEP ────────────────────────────────
a3 = uid()
insert_app(a3,'APP-2026-0003','Ibrahim Hassan Al-Nasser','ibrahim@nassercorp.ae',
    'aml_hold',7,'hold',67.50,'verified',45200.00,5000000.00,'individual',
    'Government Official','UAE Federal Authority','married','none',True,None,8)
m3_id = uid()
cur.execute("""INSERT INTO members (id,tenant_id,application_id,first_name,last_name,date_of_birth,gender,relationship,nationality,emirates_id,visa_type,height_cm,weight_kg,created_at,updated_at) VALUES (%s,%s,%s,'Ibrahim','Al-Nasser','1970-05-12','male','self','AE','784-1970-9876543-3','citizen',180.0,92.0,%s,%s) ON CONFLICT (id) DO NOTHING""",
    (m3_id,TENANT_ID,a3,ago(8),ago(0)))
insert_aml(a3,m3_id,'hold',67.50,{"diplomatic_passport":5,"pep_status_self":25,"premium_threshold":10,"occupation_risk":5,"income_inconsistency":10,"prior_aml_flag":12},True)
for ct in ['icp','ofac','un_sanctions']:
    insert_govt_check(a3,m3_id,ct,'verified',7)

# ── Application 4: Approved, Awaiting Payment ─────────────────────────────────
a4 = uid()
insert_app(a4,'APP-2026-0004','Sarah Johnson','s.johnson@emirates.com',
    'approved',8,'clear',8.00,'verified',6200.00,500000.00,'corporate',
    'Senior Analyst','Emirates NBD','single','expired_lt30',False,None,5)
cur.execute("""INSERT INTO members (id,tenant_id,application_id,first_name,last_name,date_of_birth,gender,relationship,nationality,passport_number,visa_type,height_cm,weight_kg,created_at,updated_at) VALUES (%s,%s,%s,'Sarah','Johnson','1990-08-14','female','self','GB','GBP987654','employment',167.0,65.0,%s,%s) ON CONFLICT (id) DO NOTHING""",
    (uid(),TENANT_ID,a4,ago(5),ago(0)))

# ── Application 5: Draft ──────────────────────────────────────────────────────
a5 = uid()
insert_app(a5,'APP-2026-0005','Ahmed Khalil','a.khalil@newco.ae',
    'draft',0,'clear',None,'pending',3200.00,150000.00,'individual',
    'Consultant',None,'married',None,False,None,2)
cur.execute("""INSERT INTO members (id,tenant_id,application_id,first_name,last_name,date_of_birth,gender,relationship,nationality,passport_number,visa_type,created_at,updated_at) VALUES (%s,%s,%s,'Ahmed','Khalil','1988-01-30','male','self','EG','EG567890','employment',%s,%s) ON CONFLICT (id) DO NOTHING""",
    (uid(),TENANT_ID,a5,ago(2),ago(0)))

# ── Application 6: Issued Policy #2 ──────────────────────────────────────────
a6 = uid()
insert_app(a6,'APP-2026-0006','Zara Malik','z.malik@dubaifin.ae',
    'issued',6,'clear',5.00,'verified',4850.00,150000.00,'corporate',
    'Finance Manager','Dubai Financial Services LLC','single','none',False,None,60)
cur.execute("""INSERT INTO members (id,tenant_id,application_id,first_name,last_name,date_of_birth,gender,relationship,nationality,passport_number,visa_type,height_cm,weight_kg,created_at,updated_at) VALUES (%s,%s,%s,'Zara','Malik','1992-06-18','female','self','PK','PK234567','employment',165.0,58.0,%s,%s) ON CONFLICT (id) DO NOTHING""",
    (uid(),TENANT_ID,a6,ago(60),ago(0)))
p2 = uid()
insert_policy(p2,a6,'POL-2026-00002','Zara Malik','z.malik@dubaifin.ae',4850.00,55,310,55)
insert_payment(p2,4850.00,'bank_transfer','PAY-2026-00002',55)

# ── Application 7: Expiring in 25 days ───────────────────────────────────────
a7 = uid()
insert_app(a7,'APP-2025-0099','Ali Hassan Abbasi','ali.abbasi@construction.ae',
    'issued',1,'clear',None,'verified',2950.00,150000.00,'corporate',
    'Civil Engineer','Gulf Construction LLC','married',None,False,None,370)
cur.execute("""INSERT INTO members (id,tenant_id,application_id,first_name,last_name,date_of_birth,gender,relationship,nationality,passport_number,visa_type,created_at,updated_at) VALUES (%s,%s,%s,'Ali Hassan','Abbasi','1980-03-08','male','self','PK','PK111222','employment',%s,%s) ON CONFLICT (id) DO NOTHING""",
    (uid(),TENANT_ID,a7,ago(370),ago(0)))
p3 = uid()
# For this policy: expiry_date = 25 days from now
cur.execute("""SELECT plan_id FROM applications WHERE id = %s""", (a7,))
app7_plan = cur.fetchone()[0]
cur.execute("""SELECT product_id FROM plans WHERE id = %s""", (app7_plan,))
app7_prod = cur.fetchone()[0]
cur.execute("""
    INSERT INTO policies (id,tenant_id,application_id,plan_id,product_id,policy_number,customer_name,customer_email,member_count,total_premium,status,effective_date,expiry_date,issued_by,issued_at,created_at,updated_at)
    VALUES (%s,%s,%s,%s,%s,'POL-2025-00099','Ali Hassan Abbasi','ali.abbasi@construction.ae',1,2950.00,'active',
        NOW() - INTERVAL '340 days', NOW() + INTERVAL '25 days',%s,NOW() - INTERVAL '340 days',NOW() - INTERVAL '340 days',NOW())
    ON CONFLICT ON CONSTRAINT uq_policies_tenant_number DO NOTHING
""", (p3,TENANT_ID,a7,app7_plan,app7_prod,ADMIN_USER))
insert_payment(p3,2950.00,'cheque','PAY-2025-00099',340)

# ── Notifications ─────────────────────────────────────────────────────────────
insert_notification("aml_alert","AML Alert — APP-2026-0003","Application APP-2026-0003 (Ibrahim Al-Nasser) flagged HIGH risk. Score: 67.5. Diplomatic passport + PEP match. Manual review required.","application",a3,False,0)
insert_notification("application_submitted","New Application — APP-2026-0002","APP-2026-0002 from Rajesh Sharma submitted for underwriting. AML score 38.75 (MEDIUM) — CO notified.","application",a2,False,0)
insert_notification("aml_medium","AML Medium Risk — APP-2026-0002","Application APP-2026-0002 has AML risk score 38.75 (MEDIUM). Enhanced Due Diligence initiated.","application",a2,False,1)
insert_notification("application_approved","Application Approved — APP-2026-0004","APP-2026-0004 (Sarah Johnson) approved. Awaiting payment of AED 6,200.","application",a4,True,5)
insert_notification("policy_issued","Policy Issued — POL-2026-00001","Policy POL-2026-00001 issued for Mohammed Al-Rashid. Premium: AED 8,750.","policy",p1,True,30)
insert_notification("policy_issued","Policy Issued — POL-2026-00002","Policy POL-2026-00002 issued for Zara Malik. Annual premium: AED 4,850.","policy",p2,True,55)
insert_notification("expiry_warning","Policy Expiring Soon — POL-2025-00099","Policy POL-2025-00099 (Ali Hassan Abbasi) expires in 25 days. Initiate renewal to avoid coverage gap.","policy",p3,False,0)

conn.commit()
conn.close()
print("\n✅ Demo data seeded successfully!")
print("   Applications: 7 (Draft/Submitted/Approved/Issued/AML Hold)")
print("   Policies: 3 active (2 standard + 1 expiring soon)")
print("   Payments: AED 16,550 total collected")
print("   AML: 1 MEDIUM flagged, 1 HIGH hold")
print("   Notifications: 7 (4 unread)")
