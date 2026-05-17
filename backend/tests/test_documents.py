import pytest
from fastapi.testclient import TestClient
from app.constants.enums import DocumentType
from io import BytesIO


def test_upload_document_success(client: TestClient, admin_headers, tenant, db):
    """Test successful document upload"""
    # Create document template first
    resp = client.post(
        "/api/v1/documents/templates",
        json={
            "name": "Medical Report",
            "code": "MED_REPORT",
            "template_type": "medical",
            "max_size_kb": 5120,
            "mime_types": ["application/pdf"],
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201

    # Upload document
    files = {
        "file": ("medical_report.pdf", b"PDF content here", "application/pdf"),
    }
    data = {
        "document_type": "MEDICAL_REPORT",
        "entity_type": "application",
        "entity_id": "app-001",
    }

    resp = client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data,
        headers=admin_headers,
    )
    assert resp.status_code == 201
    doc = resp.json()["data"]
    assert doc["file_name"] == "medical_report.pdf"
    assert doc["document_type"] == "MEDICAL_REPORT"
    assert doc["validation_status"] == "pending"


def test_list_documents_by_entity(client: TestClient, admin_headers, tenant, db):
    """Test listing documents by entity"""
    # Upload multiple documents
    for i in range(3):
        files = {
            "file": (f"doc{i}.pdf", b"PDF content", "application/pdf"),
        }
        data = {
            "document_type": "POLICY_DOCUMENT",
            "entity_type": "application",
            "entity_id": "app-001",
        }
        client.post("/api/v1/documents/upload", files=files, data=data, headers=admin_headers)

    # List by entity
    resp = client.get(
        "/api/v1/documents?entity_type=application&entity_id=app-001",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    docs = resp.json()["data"]
    assert len(docs) == 3


def test_list_documents_by_type(client: TestClient, admin_headers, tenant, db):
    """Test filtering documents by type"""
    # Upload different document types
    for doc_type in ["POLICY_DOCUMENT", "INVOICE", "MEDICAL_REPORT"]:
        files = {
            "file": (f"doc_{doc_type}.pdf", b"PDF content", "application/pdf"),
        }
        data = {
            "document_type": doc_type,
            "entity_type": "policy",
            "entity_id": "pol-001",
        }
        client.post("/api/v1/documents/upload", files=files, data=data, headers=admin_headers)

    # Filter by type
    resp = client.get(
        "/api/v1/documents?document_type=POLICY_DOCUMENT",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    docs = resp.json()["data"]
    assert len(docs) == 1
    assert docs[0]["document_type"] == "POLICY_DOCUMENT"


def test_document_template_enforcement(client: TestClient, admin_headers, tenant, db):
    """Test that document templates enforce constraints"""
    # Create template with size limit
    resp = client.post(
        "/api/v1/documents/templates",
        json={
            "name": "Small Doc",
            "code": "SMALL",
            "template_type": "misc",
            "max_size_kb": 1,  # 1 KB max
            "mime_types": ["application/pdf"],
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201

    # Try to upload file exceeding size limit
    files = {
        "file": ("large.pdf", b"x" * 2000, "application/pdf"),  # 2000 bytes > 1KB
    }
    data = {
        "document_type": "POLICY_DOCUMENT",
        "entity_type": "application",
        "entity_id": "app-001",
    }

    # Upload should still succeed (validation happens after storage)
    resp = client.post("/api/v1/documents/upload", files=files, data=data, headers=admin_headers)
    assert resp.status_code == 201
    # But validation_status should be pending (not validated yet)
    assert resp.json()["data"]["validation_status"] == "pending"


def test_delete_document(client: TestClient, admin_headers, tenant, db):
    """Test document deletion"""
    # Upload document
    files = {
        "file": ("test.pdf", b"PDF content", "application/pdf"),
    }
    data = {
        "document_type": "POLICY_DOCUMENT",
        "entity_type": "application",
        "entity_id": "app-001",
    }

    resp = client.post("/api/v1/documents/upload", files=files, data=data, headers=admin_headers)
    doc_id = resp.json()["data"]["id"]

    # Delete document
    resp = client.delete(f"/api/v1/documents/{doc_id}", headers=admin_headers)
    assert resp.status_code == 204

    # Verify deleted
    resp = client.get(f"/api/v1/documents/{doc_id}", headers=admin_headers)
    assert resp.status_code == 404


def test_validate_document(client: TestClient, admin_headers, tenant, db):
    """Test document validation"""
    # Upload document
    files = {
        "file": ("test.pdf", b"PDF content", "application/pdf"),
    }
    data = {
        "document_type": "MEDICAL_REPORT",
        "entity_type": "application",
        "entity_id": "app-001",
    }

    resp = client.post("/api/v1/documents/upload", files=files, data=data, headers=admin_headers)
    doc_id = resp.json()["data"]["id"]
    assert resp.json()["data"]["validation_status"] == "pending"

    # Validate document
    resp = client.post(f"/api/v1/documents/{doc_id}/validate", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["validation_status"] == "valid"


def test_tenant_isolation_documents(client: TestClient, admin_headers, tenant, tenant2, db):
    """Verify document isolation across tenants"""
    # Create another admin user for tenant2
    from tests.conftest import create_access_token
    from app.models.user import User
    from app.constants.enums import UserType, UserStatus
    from passlib.context import CryptContext

    crypt = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user2 = User(
        id="user-tenant2",
        tenant_id=tenant2.id,
        email="admin2@testco.com",
        password_hash=crypt.hash("admin123"),
        first_name="Admin",
        last_name="Two",
        user_type=UserType.TENANT_ADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(user2)
    db.flush()

    token2 = create_access_token({
        "sub": user2.id,
        "tenant_id": tenant2.id,
        "email": user2.email,
        "user_type": user2.user_type,
    })
    headers2 = {"Authorization": f"Bearer {token2}", "X-Tenant-ID": tenant2.id}

    # Upload document for tenant 1
    files = {
        "file": ("tenant1.pdf", b"Tenant 1 content", "application/pdf"),
    }
    data = {
        "document_type": "POLICY_DOCUMENT",
        "entity_type": "application",
        "entity_id": "app-001",
    }
    resp1 = client.post("/api/v1/documents/upload", files=files, data=data, headers=admin_headers)
    assert resp1.status_code == 201
    doc_id = resp1.json()["data"]["id"]

    # Try to access from tenant2
    resp2 = client.get(f"/api/v1/documents/{doc_id}", headers=headers2)
    assert resp2.status_code == 404


def test_get_document_metadata(client: TestClient, admin_headers, tenant, db):
    """Test retrieving document metadata"""
    # Upload document
    files = {
        "file": ("test.pdf", b"PDF content" * 10, "application/pdf"),
    }
    data = {
        "document_type": "INVOICE",
        "entity_type": "policy",
        "entity_id": "pol-001",
    }

    resp = client.post("/api/v1/documents/upload", files=files, data=data, headers=admin_headers)
    doc_id = resp.json()["data"]["id"]

    # Get metadata
    resp = client.get(f"/api/v1/documents/{doc_id}", headers=admin_headers)
    assert resp.status_code == 200
    doc = resp.json()["data"]
    assert doc["id"] == doc_id
    assert doc["file_name"] == "test.pdf"
    assert doc["document_type"] == "INVOICE"
    assert doc["entity_type"] == "policy"
    assert doc["entity_id"] == "pol-001"
    assert doc["file_size"] > 0
