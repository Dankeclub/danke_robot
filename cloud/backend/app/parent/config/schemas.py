"""Parent learning config schemas — aligned with parent-openapi.yaml."""

from datetime import datetime

from pydantic import BaseModel, Field


class ConfigSnapshot(BaseModel):
    """Effective config values for one module."""
    difficulty: str | None = None
    difficulty_label: str | None = None
    category: str | None = None
    category_label: str | None = None
    batch_size: int = 10
    min_repeat_interval_seconds: int = 604800
    config_version: int = 1


class LearningConfigModule(BaseModel):
    """One module's config with label."""
    module: str
    module_label: str
    enabled: bool = True
    effective_config: ConfigSnapshot


class UpdateLearningConfigModule(BaseModel):
    """Request body for updating one module's config."""
    module: str = Field(
        ..., pattern=r"^(science|math|english|poems|music|quiz)$"
    )
    enabled: bool | None = None
    difficulty: str | None = None
    category: str | None = None
    batch_size: int | None = None
    min_repeat_interval_seconds: int | None = None


class UpdateLearningConfigRequest(BaseModel):
    """Request body for bulk updating learning config."""
    modules: list[UpdateLearningConfigModule] = Field(..., min_length=1, max_length=6)


class ConfigAuditEntry(BaseModel):
    """One config change audit entry."""
    audit_id: str
    module: str
    changed_by: str
    old_values: dict
    new_values: dict
    config_version: int
    created_at: datetime


class ConfigAuditList(BaseModel):
    """Paginated config audit list."""
    items: list[ConfigAuditEntry]
    has_more: bool
    next_cursor: str | None = None
