"""Phase handlers for the event-driven workflow router."""

# Individual handler classes (kept for direct imports in tests and other modules).
from .architecting import ArchitectingHandler
from .completing import CompletingHandler
from .designing import DesigningHandler
from .failed import FailedHandler
from .fixing import FixingHandler
from .implementing import ImplementingHandler
from .planning import PlanningHandler
from .product_management import ProductManagementHandler
from .reviewing import ReviewingHandler

# Build the handler mapping locally to avoid circular import with phase_registry.
# phase_registry imports these handler classes, so it cannot be the source of
# PHASE_HANDLERS without creating a cycle when handlers/__init__.py is loaded
# as part of the package initialization.
PHASE_HANDLERS = {
    "product_management": ProductManagementHandler(),
    "architecting": ArchitectingHandler(),
    "planning": PlanningHandler(),
    "designing": DesigningHandler(),
    "implementing": ImplementingHandler(),
    "reviewing": ReviewingHandler(),
    "fixing": FixingHandler(),
    "completing": CompletingHandler(),
    "failed": FailedHandler(),
}

__all__ = [
    "PHASE_HANDLERS",
    "ArchitectingHandler",
    "ProductManagementHandler",
    "PlanningHandler",
    "DesigningHandler",
    "ImplementingHandler",
    "ReviewingHandler",
    "FixingHandler",
    "CompletingHandler",
    "FailedHandler",
]
