"""
Simulator Repositories - Interview, incident, and simulator event operations.

Cortez46: Extracted from repositories.py (5,134 lines)

SPRINT 6:
- HU-EST-011: Enfrentar Entrevista Técnica Simulada (IT-IA)
- HU-EST-012: Responder Incidente en Producción (IR-IA)
- FIX 3.2: SimulatorEventRepository
"""
from typing import List, Optional
from uuid import uuid4
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.constants import utc_now
from ..models import InterviewSessionDB, IncidentSimulationDB, SimulatorEventDB
from .base import BaseRepository

logger = logging.getLogger(__name__)


class InterviewSessionRepository(BaseRepository):
    """
    Repository for interview session operations.

    SPRINT 6 - HU-EST-011: Enfrentar Entrevista Técnica Simulada (IT-IA)
    """

    def create(
        self,
        session_id: str,
        student_id: str,
        interview_type: str,
        activity_id: Optional[str] = None,
        difficulty_level: str = "MEDIUM",
        questions_asked: Optional[List[dict]] = None,
    ) -> InterviewSessionDB:
        """
        Create a new interview session.

        Args:
            session_id: Session ID
            student_id: Student ID
            interview_type: Type of interview (CONCEPTUAL, ALGORITHMIC, DESIGN, BEHAVIORAL)
            activity_id: Optional activity ID
            difficulty_level: Difficulty (EASY, MEDIUM, HARD)
            questions_asked: Initial questions

        Returns:
            Created InterviewSessionDB instance
        """
        interview = InterviewSessionDB(
            id=str(uuid4()),
            session_id=session_id,
            student_id=student_id,
            activity_id=activity_id,
            interview_type=interview_type,
            difficulty_level=difficulty_level,
            questions_asked=questions_asked or [],
            responses=[],
        )
        self.db.add(interview)
        self.db.commit()
        self.db.refresh(interview)

        logger.info(
            "Interview session created: %s for session %s",
            interview.id,
            session_id,
            extra={
                "interview_id": interview.id,
                "session_id": session_id,
                "interview_type": interview_type,
            },
        )
        return interview

    def get_by_id(self, interview_id: str) -> Optional[InterviewSessionDB]:
        """Get interview by ID."""
        return (
            self.db.query(InterviewSessionDB)
            .filter(InterviewSessionDB.id == interview_id)
            .first()
        )

    def add_question(
        self, interview_id: str, question: dict
    ) -> Optional[InterviewSessionDB]:
        """Add a question to an interview."""
        interview = self.get_by_id(interview_id)
        if not interview:
            return None

        interview.questions_asked = interview.questions_asked + [question]
        interview.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def add_response(
        self, interview_id: str, response: dict
    ) -> Optional[InterviewSessionDB]:
        """Add a student response to an interview."""
        interview = self.get_by_id(interview_id)
        if not interview:
            return None

        interview.responses = interview.responses + [response]
        interview.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def complete_interview(
        self,
        interview_id: str,
        evaluation_score: float,
        evaluation_breakdown: dict,
        feedback: str,
        duration_minutes: int,
    ) -> Optional[InterviewSessionDB]:
        """Complete an interview with final evaluation."""
        interview = self.get_by_id(interview_id)
        if not interview:
            return None

        interview.evaluation_score = evaluation_score
        interview.evaluation_breakdown = evaluation_breakdown
        interview.feedback = feedback
        interview.duration_minutes = duration_minutes
        interview.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(interview)

        logger.info(
            "Interview completed: %s with score %.2f",
            interview.id,
            evaluation_score,
            extra={
                "interview_id": interview.id,
                "evaluation_score": evaluation_score,
            },
        )
        return interview

    def get_by_session(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[InterviewSessionDB]:
        """
        Get all interviews for a session.

        FIX 3.1 Cortez5: Added limit/offset to prevent unbounded queries
        """
        return (
            self.db.query(InterviewSessionDB)
            .filter(InterviewSessionDB.session_id == session_id)
            .order_by(InterviewSessionDB.created_at)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_student(
        self, student_id: str, limit: Optional[int] = None
    ) -> List[InterviewSessionDB]:
        """Get interviews by student."""
        query = (
            self.db.query(InterviewSessionDB)
            .filter(InterviewSessionDB.student_id == student_id)
            .order_by(desc(InterviewSessionDB.created_at))
        )
        if limit:
            query = query.limit(limit)
        return query.all()


class IncidentSimulationRepository(BaseRepository):
    """
    Repository for incident simulation operations.

    SPRINT 6 - HU-EST-012: Responder Incidente en Producción (IR-IA)
    """

    def create(
        self,
        session_id: str,
        student_id: str,
        incident_type: str,
        incident_description: str,
        activity_id: Optional[str] = None,
        severity: str = "HIGH",
        simulated_logs: Optional[str] = None,
        simulated_metrics: Optional[dict] = None,
    ) -> IncidentSimulationDB:
        """
        Create a new incident simulation.

        Args:
            session_id: Session ID
            student_id: Student ID
            incident_type: Type (API_ERROR, PERFORMANCE, SECURITY, DATABASE, DEPLOYMENT)
            incident_description: Description of the simulated incident
            activity_id: Optional activity ID
            severity: Severity (LOW, MEDIUM, HIGH, CRITICAL)
            simulated_logs: Simulated error logs
            simulated_metrics: Simulated monitoring metrics

        Returns:
            Created IncidentSimulationDB instance
        """
        incident = IncidentSimulationDB(
            id=str(uuid4()),
            session_id=session_id,
            student_id=student_id,
            activity_id=activity_id,
            incident_type=incident_type,
            severity=severity,
            incident_description=incident_description,
            simulated_logs=simulated_logs,
            simulated_metrics=simulated_metrics or {},
            diagnosis_process=[],
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)

        logger.info(
            "Incident simulation created: %s (%s, %s)",
            incident.id,
            incident_type,
            severity,
            extra={
                "incident_id": incident.id,
                "session_id": session_id,
                "incident_type": incident_type,
                "severity": severity,
            },
        )
        return incident

    def get_by_id(self, incident_id: str) -> Optional[IncidentSimulationDB]:
        """Get incident by ID."""
        return (
            self.db.query(IncidentSimulationDB)
            .filter(IncidentSimulationDB.id == incident_id)
            .first()
        )

    def add_diagnosis_step(
        self, incident_id: str, diagnosis_step: dict
    ) -> Optional[IncidentSimulationDB]:
        """Add a diagnosis step to the incident."""
        incident = self.get_by_id(incident_id)
        if not incident:
            return None

        incident.diagnosis_process = incident.diagnosis_process + [diagnosis_step]
        incident.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def complete_incident(
        self,
        incident_id: str,
        solution_proposed: str,
        root_cause_identified: str,
        time_to_diagnose_minutes: int,
        time_to_resolve_minutes: int,
        post_mortem: str,
        evaluation: dict,
    ) -> Optional[IncidentSimulationDB]:
        """Complete an incident with solution and evaluation."""
        incident = self.get_by_id(incident_id)
        if not incident:
            return None

        incident.solution_proposed = solution_proposed
        incident.root_cause_identified = root_cause_identified
        incident.time_to_diagnose_minutes = time_to_diagnose_minutes
        incident.time_to_resolve_minutes = time_to_resolve_minutes
        incident.post_mortem = post_mortem
        incident.evaluation = evaluation
        incident.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(incident)

        logger.info(
            "Incident simulation completed: %s in %d minutes",
            incident.id,
            time_to_resolve_minutes,
            extra={
                "incident_id": incident.id,
                "time_to_resolve": time_to_resolve_minutes,
            },
        )
        return incident

    def get_by_session(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[IncidentSimulationDB]:
        """
        Get all incidents for a session.

        FIX 3.1 Cortez5: Added limit/offset to prevent unbounded queries
        """
        return (
            self.db.query(IncidentSimulationDB)
            .filter(IncidentSimulationDB.session_id == session_id)
            .order_by(IncidentSimulationDB.created_at)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_student(
        self, student_id: str, limit: Optional[int] = None
    ) -> List[IncidentSimulationDB]:
        """Get incidents by student."""
        query = (
            self.db.query(IncidentSimulationDB)
            .filter(IncidentSimulationDB.student_id == student_id)
            .order_by(desc(IncidentSimulationDB.created_at))
        )
        if limit:
            query = query.limit(limit)
        return query.all()


class SimulatorEventRepository(BaseRepository):
    """
    Repository for simulator events (S-IA-X).

    Provides access to SimulatorEventDB records without direct queries in routers.
    FIX 3.2: Added to avoid direct queries in routers.
    """

    def create(
        self,
        session_id: str,
        student_id: str,
        simulator_type: str,
        event_type: str,
        event_data: dict,
        activity_id: Optional[str] = None,
    ) -> SimulatorEventDB:
        """
        Create a new simulator event.

        Args:
            session_id: Session ID
            student_id: Student ID
            simulator_type: Type of simulator (product_owner, scrum_master, etc.)
            event_type: Type of event (challenge, response, feedback, etc.)
            event_data: Event data dict
            activity_id: Optional activity ID

        Returns:
            Created SimulatorEventDB instance
        """
        event = SimulatorEventDB(
            id=str(uuid4()),
            session_id=session_id,
            student_id=student_id,
            activity_id=activity_id,
            simulator_type=simulator_type,
            event_type=event_type,
            event_data=event_data,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        logger.debug(
            "Simulator event created: %s (%s/%s)",
            event.id,
            simulator_type,
            event_type,
        )
        return event

    def get_by_id(self, event_id: str) -> Optional[SimulatorEventDB]:
        """Get event by ID."""
        return (
            self.db.query(SimulatorEventDB)
            .filter(SimulatorEventDB.id == event_id)
            .first()
        )

    def get_by_session(
        self,
        session_id: str,
        simulator_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SimulatorEventDB]:
        """
        Get events for a session, optionally filtered by simulator type.

        FIX 3.1 Cortez5: Added limit/offset to prevent unbounded queries
        """
        query = self.db.query(SimulatorEventDB).filter(
            SimulatorEventDB.session_id == session_id
        )
        if simulator_type:
            query = query.filter(SimulatorEventDB.simulator_type == simulator_type)
        return (
            query.order_by(SimulatorEventDB.created_at)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_student(
        self,
        student_id: str,
        simulator_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SimulatorEventDB]:
        """Get events for a student, optionally filtered by simulator type."""
        query = self.db.query(SimulatorEventDB).filter(
            SimulatorEventDB.student_id == student_id
        )
        if simulator_type:
            query = query.filter(SimulatorEventDB.simulator_type == simulator_type)
        return (
            query.order_by(desc(SimulatorEventDB.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count_by_session(
        self, session_id: str, simulator_type: Optional[str] = None
    ) -> int:
        """Count events for a session."""
        query = self.db.query(SimulatorEventDB).filter(
            SimulatorEventDB.session_id == session_id
        )
        if simulator_type:
            query = query.filter(SimulatorEventDB.simulator_type == simulator_type)
        return query.count()
