"""Minimal stub factory classes for integration test imports."""

class UserFactory:  # pragma: no cover - placeholder for compatibility
    """Stub factory returning static user payloads."""

    @staticmethod
    def build(**overrides):
        payload = {
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Test User",
            "role": "engineer",
        }
        payload.update(overrides)
        return payload


class ProjectFactory:  # pragma: no cover - placeholder for compatibility
    """Stub factory returning static project payloads."""

    @staticmethod
    def build(**overrides):
        payload = {
            "name": "Sample Project",
            "description": "A sample project",
            "domain": "PV",
            "scale": "COMMERCIAL",
        }
        payload.update(overrides)
        return payload


class ComponentFactory:  # pragma: no cover - placeholder for compatibility
    """Stub factory returning static component payloads."""

    @staticmethod
    def build(**overrides):
        payload = {
            "component_id": "CMP-001",
            "brand": "OriginFD",
            "part_number": "PART-001",
            "rating_w": 100.0,
        }
        payload.update(overrides)
        return payload
