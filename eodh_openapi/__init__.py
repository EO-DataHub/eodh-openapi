from dataclasses import dataclass, field
from typing import Any, Optional, TypedDict


@dataclass(frozen=True)
class OpenAPISpec:
    class Info(TypedDict):
        title: str
        version: str
        description: Optional[str]

    class Components(TypedDict):
        schemas: dict[str, Any]
        securitySchemes: dict[str, Any]

    openapi: str
    info: Info
    tags: list[str] = field(default_factory=list)
    paths: dict[str, dict[str, Any]] = field(default_factory=dict)
    components: Components = field(
        default_factory=lambda: {
            "schemas": {},
            "securitySchemas": {},
        }
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the OpenAPISpec object to a dictionary."""
        return self.__dict__

    def merge(self, other: dict):
        """Merge another OpenAPISpec into this one."""
        # Paths
        self.paths.update(other.paths)

        # Components
        self.components.setdefault("schemas", {}).update(
            other.components.get("schemas", {}),
        )
        self.components.setdefault("securitySchemes", {}).update(
            other.components.get("securitySchemes", {}),
        )
