"""
app/api/routes/companies.py
───────────────────────────
API endpoints for company profile management.

Routes:
- POST   /companies                    - Create company profile (recruiter only)
- GET    /companies/{id}               - Get public company profile
- PUT    /companies/{id}               - Update company profile (recruiter only)
- GET    /recruiters/{recruiter_id}/company - Get recruiter's company
- GET    /companies                    - Browse all companies (with pagination)
- GET    /companies/search             - Search companies
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.models import User, UserRole, CompanyProfile
from app.db.session import get_db
from app.schemas.company import (
    CompanyProfileCreate,
    CompanyProfileUpdate,
    CompanyProfileResponse,
    CompanyPublicResponse,
)
from app.services.company_service import CompanyService
from app.services.auth_service import decode_access_token, get_user_by_id
from app.core.exceptions import InvalidTokenError
from app.core.logging import get_logger

router = APIRouter(prefix="/companies", tags=["Companies"])
logger = get_logger(__name__)

_bearer = HTTPBearer(auto_error=False)


def _get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Get current authenticated user."""
    if not credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        return get_user_by_id(db, int(payload["sub"]))
    except (InvalidTokenError, Exception):
        return None


def _require_recruiter(current_user: Optional[User] = Depends(_get_current_user)) -> User:
    """Require user to be authenticated and be a recruiter."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if current_user.role != UserRole.recruiter:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only recruiters can manage company profiles")
    return current_user


@router.post(
    "",
    response_model=CompanyProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create company profile",
    description="Create a new company profile. Only recruiters can create profiles.",
)
async def create_company(
    data: CompanyProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_recruiter),
) -> CompanyProfile:
    """
    Create a new company profile for the authenticated recruiter.
    
    **Requirements:**
    - User must be authenticated
    - User must have recruiter role
    - User must not already have a company profile
    """
    try:
        company = CompanyService.create_company_profile(
            db=db,
            recruiter_id=current_user.id,
            data=data
        )
        logger.info(f"Recruiter {current_user.id} created company profile: {company.company_name}")
        return company
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error creating company profile: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create company profile")


@router.get(
    "/{company_id}",
    response_model=CompanyPublicResponse,
    status_code=status.HTTP_200_OK,
    summary="Get public company profile",
    description="Get a company profile by ID. Public endpoint.",
)
async def get_company(
    company_id: int = ...,
    db: Session = Depends(get_db),
) -> CompanyProfile:
    """
    Get public company profile information.
    
    Anyone can view this endpoint (no authentication required).
    """
    company = CompanyService.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.put(
    "/{company_id}",
    response_model=CompanyProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update company profile",
    description="Update company profile. Only the recruiter who owns the profile can update it.",
)
async def update_company(
    company_id: int,
    data: CompanyProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_recruiter),
) -> CompanyProfile:
    """
    Update a company profile.
    
    **Requirements:**
    - User must be authenticated and be a recruiter
    - User must own the company profile
    """
    company = CompanyService.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Check ownership
    if company.recruiter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own company profile"
        )

    try:
        updated_company = CompanyService.update_company_profile(db, company_id, data)
        logger.info(f"Recruiter {current_user.id} updated company profile: {updated_company.company_name}")
        return updated_company
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error updating company profile: {exc}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update company profile")


@router.get(
    "",
    response_model=List[CompanyPublicResponse],
    status_code=status.HTTP_200_OK,
    summary="Browse all companies",
    description="Get paginated list of all company profiles.",
)
async def list_companies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum records to return"),
    db: Session = Depends(get_db),
) -> List[CompanyProfile]:
    """
    Get a paginated list of all company profiles.
    
    Public endpoint - anyone can browse companies.
    """
    companies = CompanyService.get_all_companies(db, skip=skip, limit=limit)
    return companies


@router.get(
    "/search",
    response_model=List[CompanyPublicResponse],
    status_code=status.HTTP_200_OK,
    summary="Search companies",
    description="Search companies by name, location, or industry.",
)
async def search_companies(
    q: str = Query(..., min_length=2, description="Search query (company name, location, or industry)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum records to return"),
    db: Session = Depends(get_db),
) -> List[CompanyProfile]:
    """
    Search for companies by name, location, or industry.
    
    Public endpoint - anyone can search companies.
    """
    companies = CompanyService.search_companies(db, search_query=q, skip=skip, limit=limit)
    logger.info(f"Company search: {q} returned {len(companies)} results")
    return companies


@router.get(
    "/recruiters/{recruiter_id}/company",
    response_model=Optional[CompanyPublicResponse],
    status_code=status.HTTP_200_OK,
    summary="Get recruiter's company",
    description="Get the company profile associated with a specific recruiter.",
)
async def get_recruiter_company(
    recruiter_id: int,
    db: Session = Depends(get_db),
) -> Optional[CompanyProfile]:
    """
    Get a recruiter's company profile.
    
    Public endpoint - returns company info associated with a recruiter.
    """
    company = CompanyService.get_recruiter_company(db, recruiter_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company profile not found for this recruiter")
    return company


@router.delete(
    "/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete company profile",
    description="Delete a company profile. Only the owner can delete.",
)
async def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_recruiter),
) -> None:
    """
    Delete a company profile.
    
    **Requirements:**
    - User must be authenticated and be a recruiter
    - User must own the company profile
    """
    company = CompanyService.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Check ownership
    if company.recruiter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own company profile"
        )

    if CompanyService.delete_company_profile(db, company_id):
        logger.info(f"Recruiter {current_user.id} deleted company profile: {company.company_name}")
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
