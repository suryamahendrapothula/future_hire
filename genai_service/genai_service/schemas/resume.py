"""Resume-related Pydantic schemas."""

from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    role: str = ""
    highlights: list[str] = Field(default_factory=list)


class ExperienceInfo(BaseModel):
    company: str = ""
    title: str = ""
    duration: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class EducationInfo(BaseModel):
    institution: str = ""
    degree: str = ""
    field: str = ""
    year: str = ""
    highlights: list[str] = Field(default_factory=list)


class CertificateInfo(BaseModel):
    name: str = ""
    issuer: str = ""
    year: str = ""


class ParsedResume(BaseModel):
    """Structured extraction from a candidate resume."""

    candidate_name: str = ""
    email: str = ""
    phone: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    projects: list[ProjectInfo] = Field(default_factory=list)
    experience: list[ExperienceInfo] = Field(default_factory=list)
    education: list[EducationInfo] = Field(default_factory=list)
    certificates: list[CertificateInfo] = Field(default_factory=list)
    internships: list[ExperienceInfo] = Field(default_factory=list)
    github: str = ""
    linkedin: str = ""
    achievements: list[str] = Field(default_factory=list)
    raw_text: str = ""
    years_of_experience: float = 0.0
    primary_domains: list[str] = Field(default_factory=list)


class UploadResumeResponse(BaseModel):
    candidate_id: str
    candidate_name: str
    skills: list[str]
    primary_domains: list[str]
    years_of_experience: float
    message: str = "Resume parsed successfully"
