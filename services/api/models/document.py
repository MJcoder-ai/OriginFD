"""
Database models for ODL-SD documents.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from .base import Base, TenantMixin, TimestampMixin, UUIDMixin


class Document(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Main document table for ODL-SD documents.
    Stores metadata and current version content.
    """

    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_tenant_project", "tenant_id", "project_name"),
        Index("ix_documents_domain_scale", "domain", "scale"),
        # Note: PostgreSQL partitioning will be handled via migration scripts
    )

    # Document metadata
    project_name = Column(String(255), nullable=False)
    portfolio_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    domain = Column(String(50), nullable=False)  # PV, BESS, HYBRID, etc.
    scale = Column(String(50), nullable=False)  # RESIDENTIAL, COMMERCIAL, etc.

    # Current version info
    current_version = Column(Integer, nullable=False, default=1)
    content_hash = Column(String(71), nullable=False)  # sha256:hash
    document_data = Column(JSONB, nullable=False)  # Full ODL-SD document

    # Status and access
    is_active = Column(Boolean, nullable=False, default=True)
    is_locked = Column(Boolean, nullable=False, default=False)
    locked_by = Column(UUID(as_uuid=True), nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    versions = relationship("DocumentVersion", back_populates="document")
    access_controls = relationship("DocumentAccess", back_populates="document")

    def __repr__(self):
        return f"<Document(id={self.id}, project={self.project_name}, version={self.current_version})>"


class DocumentVersion(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Version history for documents.
    Stores snapshots of document changes.
    """

    __tablename__ = "document_versions"
    __table_args__ = (
        Index("ix_doc_versions_document_version", "document_id", "version_number"),
    )

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)

    # Version metadata
    content_hash = Column(String(71), nullable=False)
    previous_hash = Column(String(71), nullable=True)
    change_summary = Column(Text, nullable=True)

    # Patch information
    patch_operations = Column(JSONB, nullable=True)  # JSON-Patch operations
    evidence_uris = Column(JSONB, nullable=True)  # Evidence for changes

    # Actor information
    created_by = Column(UUID(as_uuid=True), nullable=False)
    actor_type = Column(String(50), nullable=False, default="user")  # user, system, api

    # Version data
    document_data = Column(JSONB, nullable=False)  # Full document at this version

    # Relationships
    document = relationship("Document", back_populates="versions")

    def __repr__(self):
        return f"<DocumentVersion(document_id={self.document_id}, version={self.version_number})>"


class DocumentAccess(Base, UUIDMixin, TimestampMixin, TenantMixin):
    """
    Access control for documents.
    Manages who can read/write specific documents.
    """

    __tablename__ = "document_access"
    __table_args__ = (
        Index("ix_doc_access_document_user", "document_id", "user_id"),
        Index("ix_doc_access_role_permissions", "role", "permissions"),
    )

    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Specific user
    role = Column(String(100), nullable=True)  # Or role-based

    # Permission flags
    permissions = Column(
        JSONB, nullable=False
    )  # {"read": true, "write": false, "approve": false}

    # Access constraints
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # Granted by
    granted_by = Column(UUID(as_uuid=True), nullable=False)
    grant_reason = Column(Text, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="access_controls")

    def __repr__(self):
        return f"<DocumentAccess(document_id={self.document_id}, user_id={self.user_id}, role={self.role})>"


# Row Level Security (RLS) policies - applied at database level
RLS_POLICIES = [
    """
    CREATE POLICY documents_tenant_policy ON documents
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);
    """,
    """
    CREATE POLICY document_versions_tenant_policy ON document_versions
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);
    """,
    """
    CREATE POLICY document_access_tenant_policy ON document_access
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid);
    """,
]
