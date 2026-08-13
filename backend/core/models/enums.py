"""Enums tightly coupled to stored domain values for the Whitfield WMS."""

from enum import Enum


class UserRole(str, Enum):
    """Roles allowed for warehouse staff users."""

    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"


class ShipmentStatus(str, Enum):
    """Lifecycle status for an inbound shipment."""

    DRAFT = "draft"
    RECEIVED = "received"


class OrderStatus(str, Enum):
    """Lifecycle status for an outbound order."""

    PENDING = "pending"
    PICKING = "picking"
    PACKED = "packed"
    LABELED = "labeled"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class DamageGrade(str, Enum):
    """Standardized four-level damage grading system."""

    A = "A"  # minor packaging damage, product fine
    B = "B"  # moderate damage, sellable at discount
    C = "C"  # severe, cannot sell
    D = "D"  # total loss, carrier claim


class ReturnCondition(str, Enum):
    """Condition of a returned item."""

    RESELLABLE = "resellable"
    DAMAGED = "damaged"
    UNSELLABLE = "unsellable"


class ReturnAction(str, Enum):
    """Disposition action taken on a returned item."""

    RESTOCKED_TO_GOOD = "restocked_to_good"
    PLACED_IN_DAMAGED = "placed_in_damaged"
    RETURNED_TO_SELLER = "returned_to_seller"
    DISPOSED = "disposed"


class ReturnStatus(str, Enum):
    """Lifecycle status for a return record."""

    PENDING = "pending"
    COMPLETED = "completed"
    AWAITING_SELLER = "awaiting_seller"
    DISPOSED = "disposed"


class AuditMethod(str, Enum):
    """Source method of a recorded action."""

    MANUAL_ENTRY = "manual_entry"
    BARCODE_SCAN = "barcode_scan"
    VOICE_INPUT = "voice_input"
    AI_AGENT = "ai_agent"
    API_SCRIPT = "api_script"
    SYSTEM_AUTO = "system_auto"


class NotificationChannel(str, Enum):
    """Delivery channel for a notification."""

    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PUSH = "push"


class RecipientType(str, Enum):
    """Type of notification recipient."""

    USER = "user"
    SELLER = "seller"


class NotificationType(str, Enum):
    """Category of notification."""

    LOW_STOCK_ALERT = "low_stock_alert"
    SHIPMENT_RECEIVED = "shipment_received"
    ORDER_SHIPPED = "order_shipped"
    RETURN_PROCESSED = "return_processed"
    INVOICE_READY = "invoice_ready"
    DAILY_SUMMARY = "daily_summary"
    STALE_ORDER = "stale_order"
    DAMAGE_REPORT = "damage_report"
    ANOMALY = "anomaly"


class InvoiceStatus(str, Enum):
    """Lifecycle status for an invoice."""

    DRAFT = "draft"
    SENT = "sent"


class ConfidenceLevel(str, Enum):
    """Forecast confidence indicator."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
