"""
app/api/routes/resume_versions.py
─────────────────────────────────
API endpoints for managing multiple resume versions (STEP 6).

Routes:
- POST   /candidates/resumes              - Upload new resume version
- GET    /candidates/resumes              - List candidate's resumes
- GET    /candidates/resumes/{id}         - Get specific resume
- PUT    /candidates/resumes/{id}         - Update resume
- DELETE /candidates/resumes/{id}         - Delete resume
- PUT    /candidates/resumes/{id}/primary - Set as primary resume
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.models import User, ResumeVersion
from app.db.session import get_db
from app.schemas.resume_version import (
    ResumeVersionCreate,
    ResumeVersionUpdate,
    ResumeVersionResponse,
    ResumeVersionListResponse,
    SetPrimaryResumeRequest,
)
from app.services.auth_service import decode_access_token, get_user_by_id
from app.core.exceptions import InvalidTokenError
from app.core.logging import get_logger

router = APIRouter(prefix="/candidates/resumes", tags=["Resume Management"])
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


def _require_authenticated(current_user: Optional[User] = Depends(_get_current_user)) -> User:
    """Require user to be authenticated."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return current_user


@router.post(
    "",
    response_model=ResumeVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload new resume version",
    description="Upload a new resume version for the authenticated candidate.",
)
async def upload_resume(
    data: ResumeVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_authenticated),
) -> ResumeVersion:
    """
    Upload a new resume version.

    **Requirements:**
    - User must be authenticated
    - User must be a candidate

    If this is the candidate's first resume, it will be set as primary automatically.
    """
    # Check if candidate
    if current_user.role != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can upload resumes"
        )

    # Check if this is the first resume
    existing_resumes = db.query(ResumeVersion).filter_by(candidate_id=current_user.id).all()
    is_first_resume = len(existing_resumes) == 0

    # Create resume version
    resume = ResumeVersion(
        candidate_id=current_user.id,
        title=data.title,
        resume_text=data.resume_text,
        file_url=data.file_url,
        is_primary=is_first_resume,  # First resume is primary by default
        is_active=True
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    logger.info(f"Candidate {current_user.id} uploaded resume version: {resume.title}")
    return resume


@router.get(
    "",
    response_model=List[ResumeVersionListResponse],
    status_code=status.HTTP_200_OK,
    summary="List candidate's resume versions",
    description="Get all resume versions for the authenticated candidate.",
)
async def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_authenticated),
) -> List[ResumeVersion]:
    """
    Get all resume versions for the authenticated candidate.

    **Requirements:**
    - User must be authenticated
    - User must be a candidate
    """
    if current_user.role != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can view resumes"
        )

    resumes = db.query(ResumeVersion).filter_by(candidate_id=current_user.id).order_by(
        ResumeVersion.is_primary.desc(),
        ResumeVersion.created_at.desc()
    ).all()

    logger.info(f"Candidate {current_user.id} retrieved {len(resumes)} resume versions")
    return resumes


@router.get(
    "/{resume_id}",
    response_model=ResumeVersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specific resume version",
    description="Get a specific resume version by ID.",
)
async def get_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_authenticated),
) -> ResumeVersion:
    """
    Get a specific resume version.

    **Requirements:**
    - User must be authenticated
    - User must own the resume
    """
    resume = db.query(ResumeVersion).filter_by(id=resume_id).first()

    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # Check ownership (allow candidates to view their own, recruiters can't view)
    if current_user.role == "candidate" and resume.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own resumes"
        )

    return resume


@router.put(
    "/{resume_id}",
    response_model=ResumeVersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update resume version",
    description="Update a resume version. Only the owner can update.",
)
async def update_resume(
    resume_id: int,
    data: ResumeVersionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_authenticated),
) -> ResumeVersion:
    """
    Update a resume version.

    **Requirements:**
    - User must be authenticated and be a candidate
    - User must own the resume
    """
    resume = db.query(ResumeVersion).filter_by(id=resume_id).first()

    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # Check ownership
    if resume.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own resumes"
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(resume, field, value)

    db.commit()
    db.refresh(resume)

    logger.info(f"Candidate {current_user.id} updated resume {resume_id}")
    return resume


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete resume version",
    description="Delete a resume version. Only the owner can delete.",
)
async def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_authenticated),
) -> None:
    """
    Delete a resume version.

    **Requirements:**
    - User must be authenticated and be a candidate
    - User must own the resume
    - Cannot delete if it's the only active resume
    """
    resume = db.query(ResumeVersion).filter_by(id=resume_id).first()

    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # Check ownership
    if resume.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own resumes"
        )

    # Check if this is the only active resume
    active_resumes = db.query(ResumeVersion).filter(
        ResumeVersion.candidate_id == current_user.id,
        ResumeVersion.is_active == True
    ).count()

    if active_resumes <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete your only active resume. Upload a new one first."
        )

    # Soft delete (mark as inactive)
    resume.is_active = False
    if resume.is_primary:
        # Set another active resume as primary
        other_resume = db.query(ResumeVersion).filter(
            ResumeVersion.candidate_id == current_user.id,
            ResumeVersion.id != resume_id,
            ResumeVersion.is_active == True
        ).order_by(ResumeVersion.created_at.desc()).first()

        if other_resume:
            other_resume.is_primary = True

    db.commit()
    logger.info(f"Candidate {current_user.id} deleted resume {resume_id}")


@router.put(
    "/{resume_id}/primary",
    response_model=ResumeVersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Set resume as primary",
    description="Set a resume version as the primary resume for job matching.",
)
async def set_primary_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_authenticated),
) -> ResumeVersion:
    """
    Set a resume as the primary resume.

    Primary resume is used for auto-matching and default scoring.

    **Requirements:**
    - User must be authenticated and be a candidate
    - User must own the resume
    """
    resume = db.query(ResumeVersion).filter_by(id=resume_id).first()

    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # Check ownership
    if resume.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only set your own resumes as primary"
        )

    # Unset current primary
    current_primary = db.query(ResumeVersion).filter(
        ResumeVersion.candidate_id == current_user.id,
        ResumeVersion.is_primary == True
    ).first()

    if current_primary:
        current_primary.is_primary = False

    # Set new primary
    resume.is_primary = True

    db.commit()
    db.refresh(resume)

    logger.info(f"Candidate {current_user.id} set resume {resume_id} as primary")
    return resume


@router.get(
    "/primary/current",
    response_model=Optional[ResumeVersionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get primary resume",
    description="Get the candidate's primary resume used for job matching.",
)
async def get_primary_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_authenticated),
) -> Optional[ResumeVersion]:
    """
    Get the candidate's primary resume.

    Returns the primary resume or the most recent if no primary is set.

    **Requirements:**
    - User must be authenticated and be a candidate
    """
    if current_user.role != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only candidates can view resumes"
        )

    # Try to get primary resume
    primary = db.query(ResumeVersion).filter(
        ResumeVersion.candidate_id == current_user.id,
        ResumeVersion.is_primary == True,
        ResumeVersion.is_active == True
    ).first()

    if primary:
        return primary

    # Fallback: get most recent active resume
    return db.query(ResumeVersion).filter(
        ResumeVersion.candidate_id == current_user.id,
        ResumeVersion.is_active == True
    ).order_by(ResumeVersion.created_at.desc()).first()
