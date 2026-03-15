from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, EmailStr, Field


DriverState = Literal[
    "draft",
    "submitted",
    "docs_pending",
    "background_pending",
    "review_pending",
    "approved",
    "rejected",
    "suspended",
    "reactivation_review",
]

DriverTier = Literal["Casual", "Professional", "Pro+", "Elite"]

IncidentType = Literal[
    "ACCIDENT",
    "VEHICLE_BREAKDOWN",
    "CUSTOMER_DISPUTE",
    "SAFETY_THREAT",
    "FRAUD_ATTEMPT",
    "DELIVERY_ISSUE",
    "OTHER",
]

IncidentStatus = Literal[
    "reported",
    "verification_pending",
    "verified",
    "assistance_requested",
    "drug_test_pending",
    "drug_test_submitted",
    "under_review",
    "assistance_approved",
    "assistance_denied",
    "closed",
    "escalated",
]

DrugTestComplianceLevel = Literal[
    "ideal",
    "acceptable",
    "non_compliant",
    "pending",
]


class VehicleProfile(BaseModel):
    make: str
    model: str
    year: int
    color: str
    plate_number: str
    vehicle_type: str


class DriverDocuments(BaseModel):
    license_number_full: Optional[str] = None
    license_number_masked: Optional[str] = None
    license_expiration: Optional[str] = None
    license_status: str = "pending"

    insurance_carrier: Optional[str] = None
    insurance_policy_full: Optional[str] = None
    insurance_policy_masked: Optional[str] = None
    insurance_expiration: Optional[str] = None
    insurance_status: str = "pending"


class BackgroundCheck(BaseModel):
    status: str = "pending"
    provider: Optional[str] = None
    report_id: Optional[str] = None
    completed_at: Optional[str] = None


class MotorVehicleRecord(BaseModel):
    status: str = "pending"
    provider: Optional[str] = None
    report_id: Optional[str] = None
    completed_at: Optional[str] = None


class DriverApplicationCreate(BaseModel):
    full_name: str
    phone: str
    email: EmailStr
    home_zone: str
    preferred_zones: List[str] = Field(default_factory=list)
    vehicle: VehicleProfile
    documents: DriverDocuments = Field(default_factory=DriverDocuments)
    consent_background_check: bool = False
    consent_terms: bool = False


class DriverApplicationRecord(BaseModel):
    application_id: str
    created_at: datetime
    updated_at: datetime

    full_name: str
    phone: str
    email: EmailStr
    home_zone: str
    preferred_zones: List[str] = Field(default_factory=list)

    vehicle: VehicleProfile
    documents: DriverDocuments = Field(default_factory=DriverDocuments)
    background_check: BackgroundCheck = Field(default_factory=BackgroundCheck)
    mvr_check: MotorVehicleRecord = Field(default_factory=MotorVehicleRecord)

    consent_background_check: bool = False
    consent_terms: bool = False
    state: DriverState = "submitted"
    notes: Optional[str] = None


class DriverProfile(BaseModel):
    driver_id: str
    application_id: str
    created_at: datetime
    updated_at: datetime

    full_name: str
    phone: str
    email: EmailStr
    home_zone: str
    preferred_zones: List[str] = Field(default_factory=list)

    vehicle: VehicleProfile
    documents: DriverDocuments = Field(default_factory=DriverDocuments)

    state: DriverState = "approved"
    tier: DriverTier = "Casual"
    rolling_30_day_miles: float = 0.0
    completed_deliveries: int = 0
    total_tips: float = 0.0
    total_base_pay: float = 0.0
    is_dispatch_active: bool = False
    last_active: Optional[str] = None


class ApplicationStateUpdate(BaseModel):
    state: DriverState
    notes: Optional[str] = None


class DriverActivationUpdate(BaseModel):
    is_dispatch_active: bool = True


class ComplianceDocumentsUpdate(BaseModel):
    license_number_full: Optional[str] = None
    license_expiration: Optional[str] = None
    license_status: Optional[str] = None

    insurance_carrier: Optional[str] = None
    insurance_policy_full: Optional[str] = None
    insurance_expiration: Optional[str] = None
    insurance_status: Optional[str] = None


class BackgroundStatusUpdate(BaseModel):
    background_check_status: Optional[str] = None
    background_provider: Optional[str] = None
    background_report_id: Optional[str] = None
    background_completed_at: Optional[str] = None

    mvr_check_status: Optional[str] = None
    mvr_provider: Optional[str] = None
    mvr_report_id: Optional[str] = None
    mvr_completed_at: Optional[str] = None


class DriverGovernancePolicy(BaseModel):
    tip_policy: str
    tier_system: dict
    recovery_policy: dict


class DriverIncidentCreate(BaseModel):
    driver_id: str
    order_id: Optional[str] = None
    incident_type: IncidentType
    location: str
    description: str
    gps_location: Optional[str] = None
    vehicle_plate_number: Optional[str] = None
    photos: List[str] = Field(default_factory=list)
    video_verification_link: Optional[str] = None
    vehicle_damage: bool = False
    injuries_reported: bool = False
    police_report_number: Optional[str] = None
    police_report_uploaded: bool = False


class IncidentEvidenceUpdate(BaseModel):
    location: Optional[str] = None
    gps_location: Optional[str] = None
    vehicle_plate_number: Optional[str] = None
    photos: Optional[List[str]] = None
    video_verification_link: Optional[str] = None
    police_report_number: Optional[str] = None
    police_report_uploaded: Optional[bool] = None
    description: Optional[str] = None
    vehicle_damage: Optional[bool] = None
    injuries_reported: Optional[bool] = None


class IncidentAssistanceRequest(BaseModel):
    assistance_requested: bool = True


class IncidentDrugTestSubmission(BaseModel):
    provider: str
    test_taken_at: str
    document_url: Optional[str] = None
    result_status: str = "submitted"


class DriverIncidentStatusUpdate(BaseModel):
    status: IncidentStatus
    review_notes: Optional[str] = None


class DriverIncidentRecord(BaseModel):
    incident_id: str
    driver_id: str
    order_id: Optional[str] = None

    incident_type: IncidentType
    status: IncidentStatus = "reported"

    created_at: datetime
    updated_at: datetime
    incident_time: datetime

    location: str
    gps_location: Optional[str] = None
    vehicle_plate_number: Optional[str] = None
    description: str

    photos: List[str] = Field(default_factory=list)
    video_verification_link: Optional[str] = None

    vehicle_damage: bool = False
    injuries_reported: bool = False

    police_report_number: Optional[str] = None
    police_report_uploaded: bool = False

    assistance_requested: bool = False
    assistance_status: str = "not_requested"

    drug_test_required: bool = False
    drug_test_target_deadline: Optional[str] = None
    drug_test_final_deadline: Optional[str] = None
    drug_test_status: str = "not_required"
    drug_test_provider: Optional[str] = None
    drug_test_taken_at: Optional[str] = None
    drug_test_document_url: Optional[str] = None
    drug_test_compliance_level: DrugTestComplianceLevel = "pending"

    review_notes: Optional[str] = None


class AdminQueueSummary(BaseModel):
    pending_applications: List[dict]
    pending_incidents: List[dict]
    suspended_drivers: List[dict]
    reactivation_review_drivers: List[dict]