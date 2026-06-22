from enum import Enum


class TenantStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class UserType(str, Enum):
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    AGENT = "agent"
    BROKER = "broker"
    CUSTOMER = "customer"
    UNDERWRITER = "underwriter"
    CLAIMS_MANAGER = "claims_manager"
    COMPLIANCE_OFFICER = "compliance_officer"
    FINANCE = "finance"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class ProductStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class PlanType(str, Enum):
    INDIVIDUAL = "individual"
    FAMILY = "family"
    GROUP = "group"
    SENIOR = "senior"


class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    EXPIRED = "expired"
    CONVERTED = "converted"
    DECLINED = "declined"


class ApplicationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    PENDING_DOCUMENTS = "pending_documents"
    PENDING_PAYMENT = "pending_payment"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ISSUED = "issued"
    AML_HOLD = "aml_hold"


class PolicyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    LAPSED = "lapsed"
    RENEWED = "renewed"


class MemberRelationship(str, Enum):
    SELF = "self"
    SPOUSE = "spouse"
    CHILD = "child"
    PARENT = "parent"
    SIBLING = "sibling"
    DEPENDENT = "dependent"


class MemberStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DECEASED = "deceased"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"
    WALLET = "wallet"
    CHEQUE = "cheque"
    CASH = "cash"
    NET_BANKING = "net_banking"


class PaymentFrequency(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    SINGLE = "single"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    PARTIALLY_PAID = "partially_paid"


class DocumentType(str, Enum):
    POLICY_DOCUMENT = "policy_document"
    QUOTE_DOCUMENT = "quote_document"
    APPLICATION_FORM = "application_form"
    INVOICE = "invoice"
    ENDORSEMENT = "endorsement"
    RENEWAL_NOTICE = "renewal_notice"
    CLAIMS_FORM = "claims_form"
    MEDICAL_REPORT = "medical_report"
    ID_PROOF = "id_proof"
    ADDRESS_PROOF = "address_proof"
    INCOME_PROOF = "income_proof"


class ClaimStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CLOSED = "closed"
    WITHDRAWN = "withdrawn"


class ClaimType(str, Enum):
    HOSPITALIZATION = "hospitalization"
    OUTPATIENT = "outpatient"
    PHARMACY = "pharmacy"
    DENTAL = "dental"
    VISION = "vision"
    MATERNITY = "maternity"
    EMERGENCY = "emergency"
    OTHER = "other"


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class WorkflowInstanceStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IntegrationType(str, Enum):
    TPA = "tpa"
    GOVERNMENT = "government"
    CORE_SYSTEM = "core_system"
    PAYMENT_GATEWAY = "payment_gateway"
    NOTIFICATION = "notification"
    WEBHOOK = "webhook"


class IntegrationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING_AUTH = "pending_auth"


class SyncDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class SyncStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    RETRYING = "retrying"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class AuditAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    APPROVE = "approve"
    REJECT = "reject"
    SUBMIT = "submit"
    CANCEL = "cancel"
    ISSUE = "issue"
    RENEW = "renew"
    EXPORT = "export"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class CoverageType(str, Enum):
    HOSPITALIZATION = "hospitalization"
    OUTPATIENT = "outpatient"
    DENTAL = "dental"
    VISION = "vision"
    MATERNITY = "maternity"
    MENTAL_HEALTH = "mental_health"
    PRESCRIPTION = "prescription"
    PREVENTIVE = "preventive"
    EMERGENCY = "emergency"
    WELLNESS = "wellness"


class AmlStatus(str, Enum):
    CLEAR = "clear"
    FLAGGED = "flagged"
    HOLD = "hold"
    CLEARED = "cleared"


class GovtCheckStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    OVERRIDDEN = "overridden"


class LoadingType(str, Enum):
    UNDERWRITER = "underwriter"
    BMI = "bmi"
    OTHER = "other"
    TPA = "tpa"
    BROKER = "broker"
    INSURER = "insurer"


class AmlCheckType(str, Enum):
    PEP = "pep"
    SANCTIONS = "sanctions"
    RISK_SCORE = "risk_score"
    TRANSACTION = "transaction"


class AmlRecordStatus(str, Enum):
    PENDING = "pending"
    CLEAR = "clear"
    FLAGGED = "flagged"
    HOLD = "hold"
    CLEARED = "cleared"


class GovtCheckType(str, Enum):
    ICP = "icp"
    DHA = "dha"
    DOH = "doh"
    OFAC = "ofac"
    UN_SANCTIONS = "un_sanctions"
    UAE_CABINET_74 = "uae_cabinet_74"


class GovtVerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    MISMATCH = "mismatch"
    NOT_FOUND = "not_found"
    FAILED = "failed"
    OVERRIDDEN = "overridden"


class SponsorType(str, Enum):
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"


class StrStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    FILED = "filed"
    CLOSED = "closed"


class ExistingHealthInsurance(str, Enum):
    ACTIVE_POLICY = "active_policy"
    EXPIRED_GT30 = "expired_gt30"
    EXPIRED_LT30 = "expired_lt30"
    NONE = "none"
