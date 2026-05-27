"""
app/services/company_service.py
───────────────────────────────
Business logic for company profile management.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.db.models import CompanyProfile, User
from app.schemas.company import CompanyProfileCreate, CompanyProfileUpdate
from app.core.logging import get_logger

logger = get_logger(__name__)


class CompanyService:
    """Service for managing company profiles."""

    @staticmethod
    def create_company_profile(
        db: Session,
        recruiter_id: int,
        data: CompanyProfileCreate
    ) -> CompanyProfile:
        """
        Create a new company profile for a recruiter.

        Args:
            db: Database session
            recruiter_id: ID of the recruiter (must be verified recruiter role)
            data: Company profile creation data

        Returns:
            Created CompanyProfile instance

        Raises:
            ValueError: If recruiter already has a company profile
        """
        # Check if recruiter already has a company profile
        existing = db.query(CompanyProfile).filter_by(recruiter_id=recruiter_id).first()
        if existing:
            raise ValueError(f"Recruiter {recruiter_id} already has a company profile")

        company = CompanyProfile(
            recruiter_id=recruiter_id,
            company_name=data.company_name,
            description=data.description,
            logo_url=str(data.logo_url) if data.logo_url else None,
            website=str(data.website) if data.website else None,
            location=data.location,
            industry=data.industry,
            company_size=data.company_size,
        )

        db.add(company)
        db.commit()
        db.refresh(company)

        logger.info(f"Created company profile for recruiter {recruiter_id}: {company.company_name}")
        return company

    @staticmethod
    def get_company_by_id(db: Session, company_id: int) -> Optional[CompanyProfile]:
        """
        Get a company profile by ID.

        Args:
            db: Database session
            company_id: Company profile ID

        Returns:
            CompanyProfile instance or None if not found
        """
        return db.query(CompanyProfile).filter_by(id=company_id).first()

    @staticmethod
    def get_recruiter_company(db: Session, recruiter_id: int) -> Optional[CompanyProfile]:
        """
        Get a recruiter's company profile.

        Args:
            db: Database session
            recruiter_id: Recruiter's user ID

        Returns:
            CompanyProfile instance or None if not found
        """
        return db.query(CompanyProfile).filter_by(recruiter_id=recruiter_id).first()

    @staticmethod
    def update_company_profile(
        db: Session,
        company_id: int,
        data: CompanyProfileUpdate
    ) -> CompanyProfile:
        """
        Update a company profile.

        Args:
            db: Database session
            company_id: Company profile ID
            data: Update data

        Returns:
            Updated CompanyProfile instance

        Raises:
            ValueError: If company not found
        """
        company = db.query(CompanyProfile).filter_by(id=company_id).first()
        if not company:
            raise ValueError(f"Company profile {company_id} not found")

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                if field in ["logo_url", "website"]:
                    # Convert HttpUrl to string
                    setattr(company, field, str(value))
                else:
                    setattr(company, field, value)

        db.commit()
        db.refresh(company)

        logger.info(f"Updated company profile {company_id}: {company.company_name}")
        return company

    @staticmethod
    def delete_company_profile(db: Session, company_id: int) -> bool:
        """
        Delete a company profile.

        Args:
            db: Database session
            company_id: Company profile ID

        Returns:
            True if deleted, False if not found
        """
        company = db.query(CompanyProfile).filter_by(id=company_id).first()
        if not company:
            return False

        db.delete(company)
        db.commit()

        logger.info(f"Deleted company profile {company_id}")
        return True

    @staticmethod
    def get_all_companies(db: Session, skip: int = 0, limit: int = 10):
        """
        Get all company profiles (for browse/search).

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of CompanyProfile instances
        """
        return db.query(CompanyProfile).offset(skip).limit(limit).all()

    @staticmethod
    def search_companies(db: Session, search_query: str, skip: int = 0, limit: int = 10):
        """
        Search companies by name, location, or industry.

        Args:
            db: Database session
            search_query: Search term
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of matching CompanyProfile instances
        """
        query = db.query(CompanyProfile).filter(
            (CompanyProfile.company_name.ilike(f"%{search_query}%")) |
            (CompanyProfile.location.ilike(f"%{search_query}%")) |
            (CompanyProfile.industry.ilike(f"%{search_query}%"))
        )
        return query.offset(skip).limit(limit).all()
