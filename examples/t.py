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
    print(education)
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

# Пример использования:
if __name__ == "__main__":
    import json
    # Предположим, sample_resume_json — это полный JSON одного resume
    sample_resume_json = {
        "last_name": "Дуйсенбеков",
        "first_name": "Бакдаулет",
        "middle_name": None,
        "title": "Full stack Developer",
        "created_at": "2024-05-16T14:45:33+0300",
        "updated_at": "2025-01-27T13:04:15+0300",
        "area": {"id": "160", "name": "Алматы", "url": "https://api.hh.ru/areas/160"},
        "age": 21,
        "gender": {"id": "male", "name": "Мужской"},
        "salary": {"amount": 600000, "currency": "KZT"},
        "photo": {
            "small": "https://img.hhcdn.ru/photo/761573000.jpeg?t=1739517736&h=YLaOscV_3wnL_WOjqNF4Ag",
            "medium": "https://img.hhcdn.ru/photo/761573001.jpeg?t=1739517736&h=_-5oyYagtESsUlpOl4NBRQ",
            "40": "https://img.hhcdn.ru/photo/761572999.jpeg?t=1739517736&h=RtaqrlLP7cIiXDnrT4bGJw",
            "100": "https://img.hhcdn.ru/photo/761573000.jpeg?t=1739517736&h=YLaOscV_3wnL_WOjqNF4Ag",
            "500": "https://img.hhcdn.ru/photo/761573001.jpeg?t=1739517736&h=_-5oyYagtESsUlpOl4NBRQ"
        },
        "total_experience": {"months": 26},
        "certificate": [],
        "owner": {"id": "81278212", "comments": {"url": "https://api.hh.ru/applicant_comments/81278212", "counters": {"total": 0}}},
        "can_view_full_info": True,
        "negotiations_history": {"url": "https://api.hh.ru/resumes/76798ae0000d30747100ae6f584e36354d4557/negotiations_history"},
        "hidden_fields": [],
        "actions": {
            "download": {
                "pdf": {"url": "https://api.hh.ru/resumes/76798ae0000d30747100ae6f584e36354d4557/download/Дуйсенбеков%20Бакдаулет.pdf?type=pdf"},
                "rtf": {"url": "https://api.hh.ru/resumes/76798ae0000d30747100ae6f584e36354d4557/download/Дуйсенбеков%20Бакдаулет.rtf?type=rtf"}
            }
        },
        "alternate_url": "https://hh.ru/resume/76798ae0000d30747100ae6f584e36354d4557",
        "id": "76798ae0000d30747100ae6f584e36354d4557",
        "download": {
            "pdf": {"url": "https://api.hh.ru/resumes/76798ae0000d30747100ae6f584e36354d4557/download/Дуйсенбеков%20Бакдаулет.pdf?type=pdf"},
            "rtf": {"url": "https://api.hh.ru/resumes/76798ae0000d30747100ae6f584e36354d4557/download/Дуйсенбеков%20Бакдаулет.rtf?type=rtf"}
        },
        "platform": {"id": "headhunter"},
        "resume_locale": {"id": "RU", "name": "Русский"},
        "skills": "Мои хобби включают в себя верховую езду, сноубординг, чтение книг и хайкинг...",
        "citizenship": [{"id": "40", "name": "Казахстан", "url": "https://api.hh.ru/areas/40"}],
        "work_ticket": [{"id": "40", "name": "Казахстан", "url": "https://api.hh.ru/areas/40"}],
        "birth_date": "2003-07-24",
        "contact": [
            {
                "value": {"country": "7", "city": "747", "number": "4398279", "formatted": "+7 (747) 439-82-79"},
                "type": {"id": "cell", "name": "Мобильный телефон"},
                "preferred": True,
                "comment": None,
                "need_verification": False,
                "verified": True
            },
            {
                "type": {"id": "email", "name": "Эл. почта"},
                "value": "duisenbekov07@gmail.com",
                "preferred": False
            }
        ],
        "education": {
            "level": {"id": "bachelor", "name": "Бакалавр"},
            "primary": [
                {
                    "id": "352986318",
                    "name": "Университет имени Сулеймана Демиреля, Алматы",
                    "organization": "Information Systems",
                    "result": "Information Technology",
                    "year": 2024,
                    "university_acronym": "УСД (СДУ)",
                    "name_id": "47415",
                    "organization_id": None,
                    "result_id": None,
                    "education_level": {"id": "bachelor", "name": "Бакалавр"}
                },
                {
                    "id": "352986372",
                    "name": "Astana Hub",
                    "organization": "Software developer",
                    "result": None,
                    "year": 2024,
                    "university_acronym": None,
                    "name_id": None,
                    "organization_id": None,
                    "result_id": None,
                    "education_level": {"id": "bachelor", "name": "Бакалавр"}
                }
            ],
            "additional": [
                {
                    "id": "98667260",
                    "name": "Software Engineering",
                    "organization": "Astana Hub",
                    "result": "IT",
                    "year": 2024
                }
            ],
            "attestation": [],
            "elementary": []
        },
        "employment": {"id": "full", "name": "Полная занятость"},
        "employments": [
            {"id": "full", "name": "Полная занятость"},
            {"id": "part", "name": "Частичная занятость"}
        ],
        "experience": [
            {
                "start": "2024-08-01",
                "end": None,
                "company": "PCA Group",
                "company_id": "1944533",
                "industry": None,
                "industries": [
                    {"id": "388.510", "name": "Дорожно-строительная техника, сельскохозяйственная и другая спец.техника, оборудование, лифты, погрузочно-разгрузочное, складское оборудование (продвижение, оптовая торговля)"},
                    {"id": "15.547", "name": "Автозапчасти, шины (розничная торговля)"},
                    {"id": "15.546", "name": "Автокомпоненты, запчасти, шины (продвижение, оптовая торговля)"}
                ],
                "area": {"id": "160", "name": "Алматы", "url": "https://api.hh.ru/areas/160"},
                "company_url": None,
                "employer": {
                    "id": "1242382",
                    "name": "PCA Group",
                    "url": "https://api.hh.ru/employers/1242382",
                    "alternate_url": "https://hh.ru/employer/1242382",
                    "logo_urls": {
                        "90": "https://img.hhcdn.ru/employer-logo/3147936.jpeg",
                        "240": "https://img.hhcdn.ru/employer-logo/3147937.jpeg",
                        "original": "https://img.hhcdn.ru/employer-logo-original/676701.jpg"
                    }
                },
                "position": "Fullstack-разработчик",
                "description": "Разработка платформы для диллеров. Стек Vue3, Tailwind, Rest API, PostgreSQL, Redis, Vuex, FileZilla. На платформе доступны несколько ролей, как суперадмин, админ и клиент. Бизнес решение, решает боль клиента и компании, объединяет и ускоряет процесс покупки/продажи товаров."
            },
            {
                "start": "2023-09-01",
                "end": "2024-05-01",
                "company": "RoLab",
                "company_id": None,
                "industry": None,
                "industries": [],
                "area": None,
                "company_url": None,
                "employer": None,
                "position": "Robotics",
                "description": "В компании Rolab я занимался сборкой роботов на базе платформы Arduino. В мои обязанности входила разработка программного обеспечения для этих роботов с использованием языка программирования C++. Я создавал и тестировал коды, обеспечивающие работу различных компонентов роботов, таких как датчики, двигатели и модули связи, а также интегрировал их в общую систему управления."
            },
            {
                "start": "2024-01-01",
                "end": "2024-03-01",
                "company": "Elefanto Group",
                "company_id": None,
                "industry": None,
                "industries": [{"id": "7.540", "name": "Разработка программного обеспечения"}],
                "area": {"id": "160", "name": "Алматы", "url": "https://api.hh.ru/areas/160"},
                "company_url": "https://elefanto.kz/",
                "employer": None,
                "position": "Разработчик ",
                "description": "В компании Elefanto.kz я работал на позиции project manager в течение трех месяцев. В мои обязанности входило управление проектами, координация работы команды, планирование и контроль сроков выполнения задач. Я также занимался взаимодействием с клиентами для уточнения их требований и обеспечения их удовлетворенности результатами работы. Моя роль включала мониторинг прогресса проектов и решение возникающих проблем, что способствовало успешной реализации проектов в установленные сроки."
            },
            {
                "start": "2022-08-01",
                "end": "2023-05-01",
                "company": "Университет имени Сулеймана Демиреля",
                "company_id": "1879614",
                "industry": None,
                "industries": [{"id": "39.442", "name": "Вуз, ссуз колледж, ПТУ"}],
                "area": None,
                "company_url": None,
                "employer": {
                    "id": "963723",
                    "name": "Университет имени Сулеймана Демиреля",
                    "url": "https://api.hh.ru/employers/963723",
                    "alternate_url": "https://hh.ru/employer/963723",
                    "logo_urls": {
                        "240": "https://img.hhcdn.ru/employer-logo/6327747.png",
                        "original": "https://img.hhcdn.ru/employer-logo-original/1176830.png",
                        "90": "https://img.hhcdn.ru/employer-logo/6327746.png"
                    }
                },
                "position": "Teacher Assistant",
                "description": "Проведение лекций факультету Information Systems. Планирование метода и оценка обучающихся."
            }
        ],
        "language": [
            {"id": "kaz", "name": "Казахский", "level": {"id": "l1", "name": "Родной"}},
            {"id": "eng", "name": "Английский", "level": {"id": "c1", "name": "C1 — Продвинутый"}},
            {"id": "rus", "name": "Русский", "level": {"id": "c2", "name": "C2 — В совершенстве"}},
            {"id": "tur", "name": "Турецкий", "level": {"id": "b1", "name": "B1 — Средний"}}
        ],
        "metro": None,
        "recommendation": [
            {"name": "Алмас Заурбеков", "organization": "Netflix", "position": "Software Developer at Netflix, ex Software Developer at Microsoft", "contact": ""}
        ],
        "relocation": {
            "type": {"id": "relocation_possible", "name": "могу переехать"},
            "area": [],
            "district": []
        },
        "schedule": {"id": "fullDay", "name": "Полный день"},
        "schedules": [
            {"id": "fullDay", "name": "Полный день"},
            {"id": "shift", "name": "Сменный график"},
            {"id": "flexible", "name": "Гибкий график"},
            {"id": "remote", "name": "Удаленная работа"}
        ],
        "site": [],
        "travel_time": {"id": "any", "name": "Не имеет значения"},
        "business_trip_readiness": {"id": "ready", "name": "готов к командировкам"},
        "paid_services": [],
        "portfolio": [
            {"small": "https://img.hhcdn.ru/photo/754843868.png?t=1739517736&h=L4YCxVPiASBTRRS5AUcJag",
             "medium": "https://img.hhcdn.ru/photo/754843869.png?t=1739517736&h=0Ad3DNvEecS9UYqedsGGRQ",
             "description": None},
            {"small": "https://img.hhcdn.ru/photo/754843864.png?t=1739517736&h=vjpmCsdmJHVnc6objlq3ZQ",
             "medium": "https://img.hhcdn.ru/photo/754843865.png?t=1739517736&h=gkBzThV240WRgtiN30JdvA",
             "description": None},
            {"small": "https://img.hhcdn.ru/photo/754843856.png?t=1739517736&h=tHjXVqSh1UEiSH-Fcb4_Zw",
             "medium": "https://img.hhcdn.ru/photo/754843857.png?t=1739517736&h=CH72Fi9Mn89QQPhJj9MntQ",
             "description": None},
            {"small": "https://img.hhcdn.ru/photo/754843844.png?t=1739517736&h=jc7CRM4dScFa7b8TlL-Xuw",
             "medium": "https://img.hhcdn.ru/photo/754843845.png?t=1739517736&h=mcdGXFOKovI4OILrbEuWdA",
             "description": None}
        ],
        "skill_set": [
            "Python", "HTML", "MySQL", "Git", "Английский язык", "CSS", "Bootstrap", "jQuery", "Ajax",
            "Code review", "Разработка мобильных приложений", "Программирование", "Тестирование",
            "Базы данных", "Scrum", "Обучение и развитие", "Искусственный интеллект", "Математика",
            "Коммуникативная компетентность", "VueJS", "Django Rest Framework", "SOLID", "ООП", "Java",
            "Умение аналитически мысли", "Математическая статистика", "Tailwind", "REST API", "PostgreSQL", "CI/CD"
        ],
        "favorited": False,
        "has_vehicle": None,
        "driver_license_types": [],
        "view_without_contacts_reason": None,
        "specialization": [],
        "professional_roles": [
            {"id": "10", "name": "Аналитик"},
            {"id": "96", "name": "Программист, разработчик"},
            {"id": "124", "name": "Тестировщик"}
        ],
        "tags": []
    }

    candidate_info = extract_full_candidate_info(sample_resume_json)
    summary = assemble_candidate_summary(candidate_info)
    print(summary)
