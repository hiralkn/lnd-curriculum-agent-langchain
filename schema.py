from typing import List
from pydantic import BaseModel, Field

class CurriculumModule(BaseModel):
    module_name: str = Field(description="The formal title of this learning module.")
    estimated_hours: int = Field(description="Approximate time required to finish this module.")
    topics_covered: List[str] = Field(description="Bullet points of specific core technologies, frameworks, or theoretical concepts covered.")
    practical_labs: List[str] = Field(description="Action-oriented hands-on assignments or coding exercises designed for the user.")

class CorporateSyllabus(BaseModel):
    curriculum_title: str = Field(description="Descriptive, industry-standard title for this specific enterprise upskilling path.")
    target_role: str = Field(description="The corporate designation or skill-level milestone this path targets.")
    total_duration_weeks: int = Field(description="Accumulated weeks required to cycle through the training curriculum.")
    modules: List[CurriculumModule] = Field(description="The progressive breakdown of chronological training modules.")
    capstone_project_details: str = Field(description="Comprehensive summary outlining a production-grade project integrating all modules.")
