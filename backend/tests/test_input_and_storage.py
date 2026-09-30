import pytest
import io
from fastapi import status


class TestInputValidationAndUploadSecurity:
    def test_upload_valid_pdf_attachment(self, client, owner1_headers, test_application):
        file_content = b"%PDF-1.4 test document stream"
        files = {
            "file": ("invoice.pdf", io.BytesIO(file_content), "application/pdf")
        }
        response = client.post(
            f"/api/v1/applications/{test_application.id}/attachments",
            headers=owner1_headers,
            files=files,
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["filename"] == "invoice.pdf"
        assert data["media_type"] == "application/pdf"

    def test_upload_invalid_mime_type_rejected(self, client, owner1_headers, test_application):
        file_content = b"<script>alert('xss')</script>"
        files = {
            "file": ("malicious.html", io.BytesIO(file_content), "text/html")
        }
        response = client.post(
            f"/api/v1/applications/{test_application.id}/attachments",
            headers=owner1_headers,
            files=files,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upload_by_unauthorized_user_forbidden(self, client, owner2_headers, test_application):
        file_content = b"%PDF-1.4 test document stream"
        files = {
            "file": ("invoice.pdf", io.BytesIO(file_content), "application/pdf")
        }
        # owner2 is not the applicant for test_application
        response = client.post(
            f"/api/v1/applications/{test_application.id}/attachments",
            headers=owner2_headers,
            files=files,
        )
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
