"""
Export Router - REST API endpoints for research data export

Endpoints:
- POST /api/v1/export/research-data - Export anonymized data for research
- GET /api/v1/export/history - View previous exports (admin only)
- GET /api/v1/export/{export_id} - Download specific export
- GET /api/v1/export/session/{session_id} - Export session data (Frontend compatibility)
- GET /api/v1/export/activity/{activity_id} - Export activity data (Frontend compatibility)

FIX Cortez52: Added authentication to research-data endpoint
"""

import logging
import uuid
import json
import csv
import io
from datetime import datetime
from typing import Dict, List, Optional, Literal

from fastapi import APIRouter, Depends, Query

# FIX Cortez91 LOW-03: Type-safe export format validation
ExportFormat = Literal["json", "csv"]

from backend.core.constants import utc_now
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...database import (
    get_db_session,
    CognitiveTraceDB,
    EvaluationDB,
    RiskDB,
    SessionDB,
    ActivityDB,
)
from ...export import (
    DataAnonymizer,
    AnonymizationConfig,
    ResearchDataExporter,
    ExportConfig,
    PrivacyValidator,
    GDPRCompliance,
)
from ..schemas.export import (
    ExportRequest,
    ExportResponse,
    ExportMetadata,
    ValidationReport,
    PrivacyMetrics,
)
from ..schemas.common import validate_uuid_format
# FIX Cortez53: Import custom exceptions
from ..exceptions import (
    AINativeAPIException,
    AuthorizationError,
    NoDataFoundError,
    PrivacyValidationError,
    ExportError,
    SessionNotFoundError,
    NoSessionsFoundError,
)
from ..deps import require_admin_role, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Data Export"])


def fetch_data_from_db(
    db: Session, request: ExportRequest
) -> Dict[str, List[Dict]]:
    """
    Fetch data from database based on export request filters

    Args:
        db: Database session
        request: Export request with filters

    Returns:
        Dictionary mapping data types to lists of records
    """
    data = {}

    # Build base query filters
    filters = []
    if request.start_date:
        filters.append(SessionDB.start_time >= request.start_date)
    if request.end_date:
        filters.append(SessionDB.start_time <= request.end_date)
    if request.activity_ids:
        filters.append(SessionDB.activity_id.in_(request.activity_ids))

    # Fetch sessions
    if request.include_sessions:
        sessions = db.query(SessionDB).filter(*filters).all()
        data["sessions"] = [
            {
                "id": s.id,
                "student_id": s.student_id,
                "activity_id": s.activity_id,
                "mode": s.mode,
                "status": s.status,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "created_at": s.created_at,
            }
            for s in sessions
        ]
        session_ids = [s.id for s in sessions]
    else:
        session_ids = [s.id for s in db.query(SessionDB.id).filter(*filters).all()]

    # Fetch traces
    if request.include_traces and session_ids:
        traces = (
            db.query(CognitiveTraceDB)
            .filter(CognitiveTraceDB.session_id.in_(session_ids))
            .all()
        )
        data["traces"] = [
            {
                "id": t.id,
                "session_id": t.session_id,
                "student_id": t.student_id,
                "activity_id": t.activity_id,
                "trace_level": t.trace_level,
                "interaction_type": t.interaction_type,
                "cognitive_state": t.cognitive_state,
                "cognitive_intent": t.cognitive_intent,
                "ai_involvement": t.ai_involvement,
                "content": t.content,
                "response": t.response,
                "created_at": t.created_at,
                "trace_metadata": t.trace_metadata,
            }
            for t in traces
        ]

    # Fetch evaluations
    if request.include_evaluations and session_ids:
        evaluations = (
            db.query(EvaluationDB)
            .filter(EvaluationDB.session_id.in_(session_ids))
            .all()
        )
        data["evaluations"] = [
            {
                "id": e.id,
                "session_id": e.session_id,
                "student_id": e.student_id,
                "activity_id": e.activity_id,
                "overall_competency_level": e.overall_competency_level,
                "overall_score": e.overall_score,
                "dimensions": e.dimensions,
                "key_strengths": e.key_strengths,
                "improvement_areas": e.improvement_areas,
                "created_at": e.created_at,
            }
            for e in evaluations
        ]

    # Fetch risks
    if request.include_risks and session_ids:
        risks = (
            db.query(RiskDB).filter(RiskDB.session_id.in_(session_ids)).all()
        )
        data["risks"] = [
            {
                "id": r.id,
                "session_id": r.session_id,
                "student_id": r.student_id,
                "activity_id": r.activity_id,
                "risk_type": r.risk_type,
                "risk_level": r.risk_level,
                "dimension": r.dimension,
                "description": r.description,
                "evidence": r.evidence,
                "recommendations": r.recommendations,
                "resolved": r.resolved,
                "created_at": r.created_at,
            }
            for r in risks
        ]

    return data


@router.post("/research-data", response_model=ExportResponse)
async def export_research_data(
    request: ExportRequest,
    _current_user: dict = Depends(require_admin_role),  # FIX Cortez52: Require admin auth
    db: Session = Depends(get_db_session),
) -> ExportResponse:
    """
    Export anonymized research data with privacy guarantees

    This endpoint implements HU-ADM-005: Exportación de datos para investigación institucional

    **Privacy Safeguards**:
    - k-anonymity (configurable, default k=5)
    - ID hashing (irreversible pseudonymization)
    - PII suppression (emails, names removed)
    - Timestamp generalization (week level)
    - Optional differential privacy noise
    - GDPR Article 89 compliance

    **Use Cases**:
    - Educational research
    - Learning analytics
    - Institutional improvement
    - Academic publications

    **Example Request**:
    ```json
    {
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": "2025-12-31T23:59:59Z",
        "activity_ids": ["prog2_tp1", "prog2_tp2"],
        "include_traces": true,
        "include_evaluations": true,
        "format": "json",
        "k_anonymity": 5
    }
    ```

    **Response**:
    - Returns export metadata and validation report
    - For large exports, provides download URL
    - For small exports (<10MB), includes data inline

    **Permissions**: Requires admin role (FIX Cortez52: Implemented)
    """
    export_id = str(uuid.uuid4())[:8]

    logger.info(
        "Starting research data export",
        extra={
            "export_id": export_id,
            "format": request.format,
            "k_anonymity": request.k_anonymity,
            "start_date": request.start_date,
            "end_date": request.end_date,
        },
    )

    try:
        # Step 1: Fetch data from database
        raw_data = fetch_data_from_db(db, request)

        total_records = sum(len(v) for v in raw_data.values())
        if total_records == 0:
            # FIX Cortez53: Use custom exception
            raise NoDataFoundError("the specified filters")

        logger.info(
            "Data fetched from database",
            extra={"total_records": total_records, "data_types": list(raw_data.keys())},
        )

        # Step 2: Anonymize data
        anon_config = AnonymizationConfig(
            k_anonymity=request.k_anonymity,
            suppress_pii=True,
            generalize_timestamps=True,
            add_noise_to_scores=request.add_noise,
            noise_epsilon=request.noise_epsilon,
        )
        anonymizer = DataAnonymizer(anon_config)

        anonymized_data = {}
        for data_type, records in raw_data.items():
            if data_type == "traces":
                anonymized_data[data_type] = [
                    anonymizer.anonymize_trace(r) for r in records
                ]
            elif data_type == "evaluations":
                anonymized_data[data_type] = [
                    anonymizer.anonymize_evaluation(r) for r in records
                ]
            elif data_type == "risks":
                anonymized_data[data_type] = [
                    anonymizer.anonymize_risk(r) for r in records
                ]
            elif data_type == "sessions":
                anonymized_data[data_type] = [
                    anonymizer.anonymize_session(r) for r in records
                ]

        logger.info("Data anonymization completed")

        # Step 3: Validate privacy
        validator = PrivacyValidator(min_k=request.k_anonymity)

        # Validate all records together for k-anonymity
        all_records = []
        for records in anonymized_data.values():
            all_records.extend(records)

        # Quasi-identifiers: fields that combined could identify someone
        quasi_identifiers = ["activity_id", "week"]

        validation_result = validator.validate(all_records, quasi_identifiers)

        # Check GDPR compliance
        gdpr_result = GDPRCompliance.check_article_89_compliance(
            anonymization_config=anon_config.model_dump(),
            validation_result=validation_result,
        )

        # Combine validation results
        validation_result.metrics.update(gdpr_result.metrics)
        validation_result.is_valid &= gdpr_result.is_valid
        validation_result.errors.extend(gdpr_result.errors)

        if not validation_result.is_valid:
            logger.error(
                "Privacy validation failed",
                extra={
                    "errors": validation_result.errors,
                    "metrics": validation_result.metrics,
                },
            )
            # FIX Cortez53: Use custom exception
            raise PrivacyValidationError(validation_result.errors, validation_result.metrics)

        logger.info("Privacy validation passed", extra=validation_result.metrics)

        # Step 4: Export to requested format
        export_config = ExportConfig(
            format=request.format,
            compress=request.compress,
            include_metadata=True,
        )
        exporter = ResearchDataExporter(export_config)

        # Export (returns string or bytes depending on format)
        exported_data = exporter.export(anonymized_data)

        # Calculate file size
        if isinstance(exported_data, str):
            file_size = len(exported_data.encode("utf-8"))
        else:
            file_size = len(exported_data)

        logger.info(
            "Export completed successfully",
            extra={
                "export_id": export_id,
                "format": request.format,
                "file_size_bytes": file_size,
                "total_records": total_records,
            },
        )

        # Build response
        metadata = ExportMetadata(
            export_timestamp=utc_now(),
            export_format=request.format,
            total_records=total_records,
            data_types=list(anonymized_data.keys()),
            anonymization_applied=True,
            privacy_standard="k-anonymity",
            date_range={
                "start": request.start_date,
                "end": request.end_date,
            }
            if request.start_date or request.end_date
            else None,
        )

        privacy_metrics = PrivacyMetrics(**validation_result.metrics)

        validation_report = ValidationReport(
            is_valid=validation_result.is_valid,
            errors=validation_result.errors,
            warnings=validation_result.warnings,
            metrics=privacy_metrics,
            gdpr_article_89_compliant=validation_result.metrics.get(
                "gdpr_article_89_compliance", False
            ),
        )

        # For now, return data inline (future: upload to S3 and provide download URL)
        # TODO: For production, save to file storage and provide download URL
        download_url = None  # f"/api/v1/export/download/{export_id}"

        return ExportResponse(
            success=True,
            message=f"Export completed successfully. {total_records} records anonymized with k={request.k_anonymity}.",
            metadata=metadata,
            validation_report=validation_report,
            download_url=download_url,
            file_size_bytes=file_size,
            export_id=export_id,
        )

    except AINativeAPIException:
        raise
    except Exception as e:
        logger.error(
            "Export failed with exception",
            exc_info=True,
            extra={"export_id": export_id},
        )
        # FIX Cortez53: Use custom exception
        raise ExportError(str(e), request.format)


# =============================================================================
# FRONTEND COMPATIBILITY ENDPOINTS
# These endpoints were missing and are required by the frontend
# =============================================================================


def _serialize_datetime(obj):
    """Helper to serialize datetime objects for JSON export"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def _build_session_export_data(
    db: Session,
    session_ids: List[str],
) -> Dict[str, List[Dict]]:
    """Build export data for given session IDs"""
    data = {}

    # Fetch sessions
    sessions = db.query(SessionDB).filter(SessionDB.id.in_(session_ids)).all()
    data["sessions"] = [
        {
            "id": s.id,
            "student_id": s.student_id,
            "activity_id": s.activity_id,
            "mode": s.mode,
            "status": s.status,
            "start_time": _serialize_datetime(s.start_time),
            "end_time": _serialize_datetime(s.end_time),
            "created_at": _serialize_datetime(s.created_at),
        }
        for s in sessions
    ]

    # Fetch traces
    traces = db.query(CognitiveTraceDB).filter(
        CognitiveTraceDB.session_id.in_(session_ids)
    ).all()
    data["traces"] = [
        {
            "id": t.id,
            "session_id": t.session_id,
            "student_id": t.student_id,
            "activity_id": t.activity_id,
            "trace_level": t.trace_level,
            "interaction_type": t.interaction_type,
            "cognitive_state": t.cognitive_state,
            "cognitive_intent": t.cognitive_intent,
            "ai_involvement": t.ai_involvement,
            "content": t.content,
            "response": t.response,
            "created_at": _serialize_datetime(t.created_at),
        }
        for t in traces
    ]

    # Fetch evaluations
    evaluations = db.query(EvaluationDB).filter(
        EvaluationDB.session_id.in_(session_ids)
    ).all()
    data["evaluations"] = [
        {
            "id": e.id,
            "session_id": e.session_id,
            "student_id": e.student_id,
            "activity_id": e.activity_id,
            "overall_competency_level": e.overall_competency_level,
            "overall_score": e.overall_score,
            "dimensions": e.dimensions,
            "key_strengths": e.key_strengths,
            "improvement_areas": e.improvement_areas,
            "created_at": _serialize_datetime(e.created_at),
        }
        for e in evaluations
    ]

    # Fetch risks
    risks = db.query(RiskDB).filter(RiskDB.session_id.in_(session_ids)).all()
    data["risks"] = [
        {
            "id": r.id,
            "session_id": r.session_id,
            "student_id": r.student_id,
            "activity_id": r.activity_id,
            "risk_type": r.risk_type,
            "risk_level": r.risk_level,
            "dimension": r.dimension,
            "description": r.description,
            "evidence": r.evidence,
            "recommendations": r.recommendations,
            "resolved": r.resolved,
            "created_at": _serialize_datetime(r.created_at),
        }
        for r in risks
    ]

    return data


def _convert_to_csv(data: Dict[str, List[Dict]]) -> str:
    """Convert export data to CSV format"""
    output = io.StringIO()

    for data_type, records in data.items():
        if not records:
            continue

        # Write section header
        output.write(f"\n# {data_type.upper()}\n")

        # Get all unique keys from records
        all_keys = set()
        for record in records:
            all_keys.update(record.keys())
        fieldnames = sorted(all_keys)

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            # Convert complex types to strings
            row = {}
            for key, value in record.items():
                if isinstance(value, (list, dict)):
                    row[key] = json.dumps(value)
                else:
                    row[key] = value
            writer.writerow(row)

    return output.getvalue()


@router.get(
    "/session/{session_id}",
    summary="Export session data",
    description="Export all data for a specific session (Frontend compatibility)",
)
async def export_session_data(
    session_id: str,
    # FIX Cortez91 LOW-03: Use Literal type for format validation
    format: ExportFormat = Query(default="json", description="Export format: json or csv"),
    current_user: dict = Depends(get_current_user),  # FIX Cortez91 CRIT-R01: Add authentication
    db: Session = Depends(get_db_session),
) -> StreamingResponse:
    """
    Export all data for a specific session.

    Returns session info, traces, evaluations, and risks in the specified format.
    """
    # FIX Cortez54: Validate UUID format before DB access
    session_id = validate_uuid_format(session_id, "session_id")

    try:
        # Verify session exists
        session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
        if not session:
            # FIX Cortez53: Use custom exception
            raise SessionNotFoundError(session_id)

        # Build export data
        data = _build_session_export_data(db, [session_id])

        # Add metadata
        export_data = {
            "export_info": {
                "export_type": "session",
                "session_id": session_id,
                "exported_at": utc_now().isoformat(),
                "format": format,
            },
            **data,
        }

        logger.info(
            "Session data exported",
            extra={
                "session_id": session_id,
                "format": format,
                "traces_count": len(data.get("traces", [])),
            },
        )

        if format == "csv":
            content = _convert_to_csv(data)
            media_type = "text/csv"
            filename = f"session_{session_id}_export.csv"
        else:
            content = json.dumps(export_data, indent=2, default=str)
            media_type = "application/json"
            filename = f"session_{session_id}_export.json"

        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )

    except AINativeAPIException:
        raise
    except Exception as e:
        logger.error(
            "Session export failed",
            exc_info=True,
            extra={"session_id": session_id},
        )
        # FIX Cortez53: Use custom exception
        raise ExportError(str(e))


@router.get(
    "/activity/{activity_id}",
    summary="Export activity data",
    description="Export all data for a specific activity (Frontend compatibility)",
)
async def export_activity_data(
    activity_id: str,
    # FIX Cortez91 LOW-03: Use Literal type for format validation
    format: ExportFormat = Query(default="json", description="Export format: json or csv"),
    current_user: dict = Depends(get_current_user),  # FIX Cortez91 CRIT-R01: Add authentication
    db: Session = Depends(get_db_session),
) -> StreamingResponse:
    """
    Export all data for a specific activity.

    Returns all sessions, traces, evaluations, and risks for the activity.
    """
    # FIX Cortez54: Validate UUID format before DB access
    activity_id = validate_uuid_format(activity_id, "activity_id")

    try:
        # Get all sessions for this activity
        sessions = db.query(SessionDB).filter(
            SessionDB.activity_id == activity_id
        ).all()

        if not sessions:
            # FIX Cortez53: Use custom exception
            raise NoSessionsFoundError(activity_id=activity_id)

        session_ids = [s.id for s in sessions]

        # Build export data
        data = _build_session_export_data(db, session_ids)

        # Get activity info
        activity = db.query(ActivityDB).filter(ActivityDB.id == activity_id).first()
        activity_info = {
            "id": activity_id,
            "title": activity.title if activity else activity_id,
            "description": activity.description if activity else None,
        }

        # Add metadata
        export_data = {
            "export_info": {
                "export_type": "activity",
                "activity_id": activity_id,
                "activity_title": activity_info.get("title"),
                "total_sessions": len(sessions),
                "exported_at": utc_now().isoformat(),
                "format": format,
            },
            "activity": activity_info,
            **data,
        }

        logger.info(
            "Activity data exported",
            extra={
                "activity_id": activity_id,
                "format": format,
                "sessions_count": len(sessions),
                "traces_count": len(data.get("traces", [])),
            },
        )

        if format == "csv":
            content = _convert_to_csv(data)
            media_type = "text/csv"
            filename = f"activity_{activity_id}_export.csv"
        else:
            content = json.dumps(export_data, indent=2, default=str)
            media_type = "application/json"
            filename = f"activity_{activity_id}_export.json"

        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )

    except AINativeAPIException:
        raise
    except Exception as e:
        logger.error(
            "Activity export failed",
            exc_info=True,
            extra={"activity_id": activity_id},
        )
        # FIX Cortez53: Use custom exception
        raise ExportError(str(e))
