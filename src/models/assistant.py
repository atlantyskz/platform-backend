from enum import Enum
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.models import Base,TimestampMixin
from src.models.assigned_assistant import assigned_assistant

class Assistant(Base,TimestampMixin):

    __tablename__ = 'assistants'

    id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True,autoincrement=True,index=True)
    name: so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    description:so.Mapped[str] = so.mapped_column(sa.String,nullable=False)
    status:so.Mapped[str] = so.mapped_column(sa.String,nullable=True)
    type: so.Mapped[str] = so.mapped_column(sa.String,nullable=True)

    organizations = so.relationship(
        "Organization",
        secondary=assigned_assistant,
        back_populates="assistants",
        cascade="all"
    )
    sessions = so.relationship("AssistantSession", back_populates="assistant")


class AssistantEnum(Enum):
    HR_ASSISTANT = (
        'HR Assistant',
        'Handles HR-related tasks',
        'active',
        'ai-assistant'
    )
    PRODUCT_MANAGER_ASSISTANT = (
        'Product Manager Assistant',
        'Helps product managers analyze user feedback and prioritize feature improvements effectively.',
        'active',
        'ai-assistant'
    )
    SALES_AUTOMATION_BOT = (
        'Sales Automation Bot',
        'Automates sales outreach and follow-up tasks while generating insightful performance analytics.',
        'dev',
        'ai-solution'
    )
    MARKETING_INTELLIGENCE_ADVISOR = (
        'Marketing Intelligence Advisor',
        'Provides real-time market insights, competitor analysis, and strategic campaign optimization tips.',
        'fix',
        'ai-assistant'
    )
    CUSTOMER_INSIGHTS_ASSISTANT = (
        'Customer Insights Assistant',
        'Collects customer feedback from multiple channels and identifies key satisfaction metrics quickly.',
        'active',
        'ai-assistant'
    )
    SOFTWARE_DEVELOPMENT_COACH = (
        'Software Development Coach',
        'Guides engineering teams with best practices, code reviews, and automated testing suggestions.',
        'fix',
        'ai-solution'
    )
    FINANCIAL_PLANNING_COMPANION = (
        'Financial Planning Companion',
        'Offers budget tracking, expense forecasting, and proactive investment recommendations for teams.',
        'dev',
        'ai-assistant'
    )
    DATA_ANALYTICS_FACILITATOR = (
        'Data Analytics Facilitator',
        'Aggregates various datasets into structured reports and highlights significant performance trends.',
        'active',
        'ai-solution'
    )
    PROJECT_COORDINATION_HELPER = (
        'Project Coordination Helper',
        'Coordinates tasks, deadlines, and resources across multiple teams to ensure timely project delivery.',
        'fix',
        'ai-assistant'
    )
    CHATBOT_EXPERIENCE_DESIGNER = (
        'Chatbot Experience Designer',
        'Suggests conversational flows, user engagement strategies, and natural language enhancements.',
        'dev',
        'ai-solution'
    )
    TECHNICAL_SUPPORT_ORCHESTRATOR = (
        'Technical Support Orchestrator',
        'Streamlines troubleshooting processes by categorizing user issues and providing relevant solutions.',
        'active',
        'ai-assistant'
    )
    
    @property
    def display_name(self):
        return self.value[0]
    
    @property
    def description(self):
        return self.value[1]
    
    @property
    def status(self):
        return self.value[2]
    
    @property
    def type(self):
        return self.value[3]
