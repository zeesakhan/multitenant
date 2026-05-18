# Staff Portal (`/`)

The staff back-office is the primary management interface used by insurance company employees. It requires a staff JWT and RBAC permissions for every operation.

## Roles

| Role | Key Capabilities |
|------|-----------------|
| `super_admin` | Full access across all tenants |
| `tenant_admin` | Full access within own tenant |
| `agent` | Quotations, applications, policies, members |
| `broker` | Similar to agent |
| `underwriter` | Review and approve/reject applications |
| `claims_manager` | Review and adjudicate claims |

## Pages

| URL | Page | Description |
|-----|------|-------------|
| `/` | Dashboard | KPI summary, recent applications and payments |
| `/tenants` | Tenants | Manage tenants (super admin only) |
| `/users` | Users | Manage staff accounts and roles |
| `/products` | Products | Define products, plans, and coverages |
| `/quotations` | Quotations | Create and send quotes to prospects |
| `/applications` | Applications | Review and underwrite applications |
| `/policies` | Policies | Issued policy management |
| `/members` | Members | Cross-policy member search |
| `/claims` | Claims | Claims adjudication workflow |
| `/payments` | Payments | Premium payment tracking |
| `/reports` | Reports | KPI dashboards and exports |

## Application Lifecycle

```
Draft → Submitted → Under Review → Approved / Rejected
                                        ↓ (if Approved)
                                      Issued  →  Policy created
```

After **Issue**, a `Policy` record is created and the customer can register on the member portal.

## Self-Service Applications (from `/buy`)

Applications submitted through the purchase portal arrive with:
- `status: submitted`
- `additional_info.source: "self_service"`
- All members and coverage items already populated

Staff can find them in the Applications list, review them, and issue the policy exactly like manually created applications.

## API

All staff API endpoints are under `/api/v1/` and require:
- `Authorization: Bearer <staff-jwt>`
- `X-Tenant-ID: <tenant-uuid>`
- The appropriate RBAC permission for the operation

See the FastAPI docs at `/docs` (development only) for the full endpoint list.
