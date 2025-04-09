import re
from typing import Dict, Any, List


def format_experience(experiences: List[Dict[str, Any]]) -> str:
    if not experiences:
        return "Опыт работы не указан."
    exp_lines = []
    for exp in experiences:
        start = exp.get("start", "не указано")
        end = exp.get("end", "по настоящее время")
        company = exp.get("company", "не указана")
        position = exp.get("position", "не указана")
        description = exp.get("description", "").strip()
        industries = exp.get("industries", [])
        industries_names = ", ".join(ind.get("name", "") for ind in industries) if industries else ""
        line = f"Период: {start} - {end}. Компания: {company}. Должность: {position}."
        if industries_names:
            line += f" Отрасли: {industries_names}."
        if description:
            line += f" Описание: {description}"
        exp_lines.append(line)
    return "\n".join(exp_lines)


def format_education(education: Dict[str, Any]) -> str:
    if not education:
        return "Образование не указано."
    level = education.get("level", {})
    if level:
        level = level.get("name", "не указан")
    primary = education.get("primary", [])
    lines = [f"Уровень: {level}."]
    if primary:
        for edu in primary:
            name = edu.get("name", "не указано")
            organization = edu.get("organization", "")
            result = edu.get("result", "")
            year = edu.get("year", "не указан")
            line = f"Учебное заведение: {name}"
            if organization:
                line += f", {organization}"
            line += f". Специальность/результат: {result}. Год: {year}."
            lines.append(line)
    # Дополнительное образование
    additional = education.get("additional", [])
    if additional:
        for edu in additional:
            name = edu.get("name", "не указано")
            organization = edu.get("organization", "")
            result = edu.get("result", "")
            year = edu.get("year", "не указан")
            line = f"Дополнительное образование: {name}"
            if organization:
                line += f", {organization}"
            line += f". Результат: {result}. Год: {year}."
            lines.append(line)
    return "\n".join(lines)


def format_languages(languages: List[Dict[str, Any]]) -> str:
    if not languages:
        return "Языковые навыки не указаны."
    lang_lines = []
    for lang in languages:
        name = lang.get("name", "не указано")
        level = lang.get("level", {}).get("name", "не указан")
        lang_lines.append(f"{name} ({level})")
    return ", ".join(lang_lines)


def format_portfolio(portfolio: List[Dict[str, Any]]) -> str:
    if not portfolio:
        return "Портфолио не указано."
    lines = []
    for idx, item in enumerate(portfolio, start=1):
        url = item.get("medium") or item.get("small") or ""
        description = item.get("description") or ""
        line = f"Проект {idx}: URL: {url}"
        if description:
            line += f". Описание: {description}"
        lines.append(line)
    return "\n".join(lines)


def format_recommendations(recommendations: List[Dict[str, Any]]) -> str:
    if not recommendations:
        return "Рекомендации не указаны."
    rec_lines = []
    for rec in recommendations:
        name = rec.get("name", "не указано")
        organization = rec.get("organization", "не указана")
        position = rec.get("position", "не указана")
        rec_lines.append(f"{name} из {organization} - {position}")
    return ", ".join(rec_lines)


def assemble_candidate_summary(candidate: Dict[str, Any]) -> str:
    # Полное имя
    first = candidate.get("first_name", "")
    middle = candidate.get("middle_name") or ""
    last = candidate.get("last_name", "")
    full_name = " ".join(filter(None, [first, middle, last])) or "Не указано"

    title = candidate.get("title", "Не указано")
    area = candidate.get("area", {}).get("name", "Не указано")
    age = candidate.get("age", "Не указано")
    gender = candidate.get("gender", {}).get("name", "Не указано")
    salary = candidate.get("salary")
    salary_text = f"{salary.get('amount')} {salary.get('currency')}" if salary else "Не указана"

    experience_text = format_experience(candidate.get("experience", []))
    education_text = format_education(candidate.get("education", {}))

    # Если навыки хранятся в fields "skills" (текст) или "skill_set" (список)
    skills = candidate.get("skill_set")
    if not skills:
        skills = ", ".join(candidate.get("skill_set", []))

    contacts = candidate.get("contact", [])
    contacts_text = ", ".join(f"{c.get('type', {}).get('name')}: {c.get('value')}" for c in contacts) or "Не указаны"

    languages = format_languages(candidate.get("language", []))
    portfolio = format_portfolio(candidate.get("portfolio", []))
    recommendations = format_recommendations(candidate.get("recommendation", []))

    # Готовность к переезду и командировкам
    relocation = candidate.get("relocation", {})
    relocation_type = relocation.get("type", {}).get("name", "Не указано")
    business_trip = candidate.get("business_trip_readiness", {}).get("name", "Не указано")

    summary = (
        f"ФИО: {full_name}\n"
        f"Должность: {title}\n"
        f"Местоположение: {area}\n"
        f"Возраст: {age}\n"
        f"Пол: {gender}\n"
        f"Ожидаемая зарплата: {salary_text}\n"
        f"Опыт работы:\n{experience_text}\n\n"
        f"Образование:\n{education_text}\n\n"
        f"Навыки: {skills}\n\n"
        f"Контактные данные: {contacts_text}\n\n"
        f"Языковые навыки: {languages}\n\n"
        f"Портфолио и проекты:\n{portfolio}\n\n"
        f"Рекомендации и отзывы: {recommendations}\n\n"
        f"Готовность к переезду: {relocation_type}\n"
        f"Готовность к командировкам: {business_trip}\n"
    )
    return summary


# Пример извлечения кандидата из полного JSON-резюме (resume)
def extract_full_candidate_info(resume: Dict[str, Any]) -> Dict[str, Any]:
    candidate_info = resume.copy()
    # Добавляем удобное поле full_name
    first = resume.get("first_name", "")
    middle = resume.get("middle_name") or ""
    last = resume.get("last_name", "")
    candidate_info["full_name"] = " ".join(filter(None, [first, middle, last])) or "Не указано"
    return candidate_info


def extract_candidates_from_response(response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = response_data.get("items", [])
    candidates = []
    for item in items:
        resume = item.get("resume", {})
        candidate = extract_full_candidate_info(resume)
        candidates.append(candidate)
    return candidates


def strip_html_tags(text: str) -> str:
    """Удаляет HTML-теги из текста."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text).strip()


def extract_vacancy_summary(vacancy: Dict[str, Any]) -> str:
    """
    Извлекает основные поля вакансии и формирует краткий summary.
    Поля: название, область, зарплата, описание (без HTML-тегов), ключевые навыки,
    а также, при необходимости, опыт работы (если указан) и другие критерии.
    """
    name = vacancy.get("name", "Не указано")
    area = vacancy.get("area", {}).get("name", "Не указано")
    salary = vacancy.get("salary")
    if salary:
        # Пример: "400000-450000 KZT" (если указаны оба значения)
        salary_from = salary.get("from")
        salary_to = salary.get("to")
        currency = salary.get("currency", "")
        if salary_from and salary_to:
            salary_text = f"{salary_from} - {salary_to} {currency}"
        elif salary_from:
            salary_text = f"От {salary_from} {currency}"
        elif salary_to:
            salary_text = f"До {salary_to} {currency}"
        else:
            salary_text = "Не указана"
    else:
        salary_text = "Не указана"

    raw_description = vacancy.get("description", "")
    description = strip_html_tags(raw_description)

    key_skills_list = vacancy.get("key_skills", [])
    key_skills = ", ".join(skill.get("name", "") for skill in key_skills_list) if key_skills_list else "Не указаны"

    schedule = vacancy.get("schedule", {}).get("name", "Не указано")
    employment = vacancy.get("employment", {}).get("name", "Не указано")

    summary = (
        f"Название вакансии: {name}\n"
        f"Местоположение: {area}\n"
        f"Зарплата: {salary_text}\n"
        f"Тип занятости: {employment}\n"
        f"График работы: {schedule}\n"
        f"Описание: {description}\n"
        f"Ключевые навыки: {key_skills}\n"
    )
    return summary
