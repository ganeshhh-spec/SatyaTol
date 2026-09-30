import pytest
from fastapi import status
from app.models.user import User, UserRole
from app.models.application import Application, VerificationType, ApplicationStatus
from app.core.security import create_access_token


class TestAuthentication:
    def test_login_success(self, client, owner1_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "owner1_test@example.com", "password": "password123"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self, client, owner1_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "owner1_test@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "password123"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_without_token(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_invalid_token(self, client):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_inactive_user_rejected(self, client, db, owner1_user):
        owner1_user.is_active = False
        db.commit()
        token = create_access_token(data={"sub": str(owner1_user.id), "email": owner1_user.email})
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRoleBasedAccessControl:
    def test_owner_cannot_review_application(self, client, owner1_headers, test_application):
        response = client.post(
            f"/api/v1/applications/{test_application.id}/review",
            headers=owner1_headers,
            json={"action": "approve", "reason": "Self approving"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_owner_cannot_issue_certificate(self, client, owner1_headers, test_application):
        response = client.post(
            f"/api/v1/certificates/{test_application.id}/issue",
            headers=owner1_headers,
            json={"valid_from": "2026-01-01T00:00:00", "valid_until": "2027-01-01T00:00:00"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_data_isolation_owner_cannot_access_other_owner_application(
        self, client, owner2_headers, test_application
    ):
        response = client.get(
            f"/api/v1/applications/{test_application.id}",
            headers=owner2_headers,
        )
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_lmo_access_to_assigned_application(self, client, lmo_headers, test_application):
        response = client.get(
            f"/api/v1/applications/{test_application.id}",
            headers=lmo_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_application.id
