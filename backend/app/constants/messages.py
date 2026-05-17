"""Standard error and success messages."""

# Auth
AUTH_INVALID_CREDENTIALS = "Invalid email or password."
AUTH_TOKEN_EXPIRED = "Access token has expired."
AUTH_TOKEN_INVALID = "Access token is invalid."
AUTH_REFRESH_TOKEN_INVALID = "Refresh token is invalid or expired."
AUTH_INSUFFICIENT_PERMISSIONS = "You do not have permission to perform this action."
AUTH_TENANT_INACTIVE = "Your organization account is inactive. Please contact support."
AUTH_USER_INACTIVE = "Your account has been deactivated. Please contact your administrator."
AUTH_USER_LOCKED = "Your account has been locked due to too many failed attempts."

# Tenants
TENANT_NOT_FOUND = "Tenant not found."
TENANT_ALREADY_EXISTS = "A tenant with this code already exists."
TENANT_CREATED = "Tenant created successfully."
TENANT_UPDATED = "Tenant updated successfully."

# Users
USER_NOT_FOUND = "User not found."
USER_EMAIL_TAKEN = "A user with this email already exists in your organization."
USER_CREATED = "User created successfully."
USER_UPDATED = "User updated successfully."
USER_DELETED = "User deactivated successfully."

# Products
PRODUCT_NOT_FOUND = "Product not found."
PRODUCT_CODE_TAKEN = "A product with this code already exists."
PLAN_NOT_FOUND = "Plan not found."
RATE_CARD_NOT_FOUND = "Rate card not found."

# Quotations
QUOTE_NOT_FOUND = "Quotation not found."
QUOTE_EXPIRED = "This quotation has expired."
QUOTE_ALREADY_CONVERTED = "This quotation has already been converted to an application."
QUOTE_CREATED = "Quotation created successfully."
QUOTE_SENT = "Quotation sent to customer successfully."
QUOTE_CONVERTED = "Quotation converted to application successfully."

# Applications
APPLICATION_NOT_FOUND = "Application not found."
APPLICATION_ALREADY_SUBMITTED = "This application has already been submitted."
APPLICATION_CANNOT_APPROVE = "Application cannot be approved in its current state."
APPLICATION_APPROVED = "Application approved successfully."
APPLICATION_REJECTED = "Application rejected."
APPLICATION_SUBMITTED = "Application submitted successfully."

# Policies
POLICY_NOT_FOUND = "Policy not found."
POLICY_ALREADY_CANCELLED = "This policy is already cancelled."
POLICY_CANNOT_AMEND = "Policy cannot be amended in its current state."
POLICY_ISSUED = "Policy issued successfully."

# Members
MEMBER_NOT_FOUND = "Member not found."
MEMBER_CREATED = "Member added successfully."
MEMBER_UPDATED = "Member updated successfully."

# Payments
PAYMENT_NOT_FOUND = "Payment not found."
PAYMENT_FAILED = "Payment processing failed. Please try again."
PAYMENT_ALREADY_REFUNDED = "This payment has already been refunded."
PAYMENT_SUCCESS = "Payment processed successfully."
REFUND_SUCCESS = "Refund initiated successfully."

# Documents
DOCUMENT_NOT_FOUND = "Document not found."
DOCUMENT_GENERATED = "Document generated successfully."
TEMPLATE_NOT_FOUND = "Document template not found."

# Integrations
INTEGRATION_NOT_FOUND = "Integration not found."
INTEGRATION_AUTH_FAILED = "Integration authentication failed. Check credentials."
INTEGRATION_SYNC_STARTED = "Synchronization started."
INTEGRATION_SYNC_SUCCESS = "Synchronization completed successfully."
INTEGRATION_SYNC_FAILED = "Synchronization failed."

# Generic
VALIDATION_ERROR = "Validation error. Please check your input."
INTERNAL_ERROR = "An internal error occurred. Please try again later."
NOT_FOUND = "Resource not found."
FORBIDDEN = "Access denied."
CONFLICT = "Resource already exists."
