import pytest
from app.models.audit import AuditEvent
from app.services.audit import create_audit_event, verify_audit_chain


class TestAuditHashChainAndIntegrity:
    def test_audit_event_creation_and_hash_calculation(self, db, lmo_user):
        event = create_audit_event(
            db,
            actor_id=lmo_user.id,
            action="verify_test",
            entity_type="application",
            entity_id=101,
            previous_status="submitted",
            new_status="under_scrutiny",
            reason="Document checks initiated",
        )
        assert event.id is not None
        assert event.event_hash is not None
        assert len(event.event_hash) == 64  # SHA-256 hex string

    def test_audit_chain_links_events(self, db, lmo_user):
        event1 = create_audit_event(
            db,
            actor_id=lmo_user.id,
            action="action_1",
            entity_type="instrument",
            entity_id=1,
        )
        event2 = create_audit_event(
            db,
            actor_id=lmo_user.id,
            action="action_2",
            entity_type="instrument",
            entity_id=1,
        )
        assert event2.previous_hash == event1.event_hash

        is_valid, errors = verify_audit_chain(db)
        assert is_valid is True
        assert len(errors) == 0

    def test_tamper_detection_in_audit_chain(self, db, lmo_user):
        event1 = create_audit_event(
            db,
            actor_id=lmo_user.id,
            action="clean_action_1",
            entity_type="certificate",
            entity_id=5,
        )
        event2 = create_audit_event(
            db,
            actor_id=lmo_user.id,
            action="clean_action_2",
            entity_type="certificate",
            entity_id=5,
        )

        # Intentionally tamper with event1 data without recomputing hash
        event1.action = "tampered_action_name"
        db.commit()

        is_valid, errors = verify_audit_chain(db)
        assert is_valid is False
        assert len(errors) >= 1
        assert errors[0]["event_id"] == event1.id

    def test_database_rollback_on_failed_transaction(self, db, lmo_user):
        initial_count = db.query(AuditEvent).count()
        try:
            with db.begin_nested():
                bad_event = AuditEvent(
                    actor_id=lmo_user.id,
                    action=None,  # Not nullable in schema
                    entity_type="test",
                    entity_id=1,
                )
                db.add(bad_event)
                db.flush()
        except Exception:
            pass  # Expected rollback

        after_count = db.query(AuditEvent).count()
        assert after_count == initial_count
