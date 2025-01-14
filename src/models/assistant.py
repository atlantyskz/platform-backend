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
        'ИИ Рекрутер',
        'Помогает автоматизировать подбор сотрудников: создает вакансии, анализирует резюме и проводит первичный отбор.',
        'active',
        'ai-assistant'
    )
    ACCOUNTING_ASSISTANT = (
        'ИИ Бухгалтер',
        'Упрощает финансовые задачи: расчет зарплат, создание отчетов и управление бюджетом.',
        'dev',
        'ai-assistant'
    )
    MANAGER_ASSISTANT = (
        'ИИ Менеджер',
        'Обеспечивает взаимодействие с клиентами: отвечает на запросы, консультирует и помогает улучшить сервис.',
        'dev',
        'ai-assistant'
    )
    MARKETING_ASSISTANT = (
        'ИИ Маркетолог',
        'Оптимизирует маркетинг: анализирует рынок, разрабатывает стратегии и помогает запускать успешные кампании.',
        'dev',
        'ai-assistant'
    )
    CLONE_AI = (
        'ИИ Клон',
        'Создайте своего виртуального клона: аватар, который выглядит и говорит, как вы. Идеальное решение для презентаций, обучения или общения.',
        'dev',
        'ai-solution'
    )
    AVATAR_AI = (
        'ИИ Аватар',
        'Используйте готовые виртуальные аватары для создания контента: рекламы, видео или взаимодействия с аудиторией. Простое и удобное решение для любых задач.',
        'dev',
        'ai-solution'
    )
    PODCAST_AI = (
        'ИИ Подкаст',
        'Создавайте подкасты с реалистичными голосами или добавляйте свой голос для уникального звучания. Делитесь идеями и обсуждениями в удобном аудиоформате.',
        'dev',
        'ai-solution'
    )
    CHATBOT_AI = (
        'ИИ Бот',
        'Умный чат-бот для автоматизации общения с клиентами: отвечает на вопросы, обрабатывает запросы и помогает с задачами.',
        'dev',
        'ai-solution'
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
