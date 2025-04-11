import asyncio
import aiohttp
import json
from typing import Dict, Any, List

# Фиктивные данные — замените на реальные
ACCESS_TOKEN = 'USERII4G57QOSRHGM7GFIO5LPD8BFA16LD3REJU0G7GI5C0OS3JPISDB6027H3J9'
CLIENT_ID = "PLRA71P98D6AKD214F3ILJMTV00P2525A1D17R2OH6DQIOV0O5BMHF279VPKV21O"
CLIENT_SECRET = "OE1MR221VJU5MTFNPNDT0K89OCFCGAR4AJJMKL1F4K4MBG8FD2OC1G7B3EC647FE"
import asyncio
import aiohttp
import json
from typing import Dict, Any, List


# Кэш для хранения полученных резюме по resume_id
resume_cache: Dict[str, Any] = {}

# Ограничитель одновременных запросов (throttling): максимум 5 параллельных запросов
concurrency_limit = 5
semaphore = asyncio.Semaphore(concurrency_limit)

# ----------------------------
# Асинхронные функции для работы с API
# ----------------------------
async def get_vacancy_responses(session: aiohttp.ClientSession, vacancy_id: str, page: int = 0, per_page: int = 20) -> Dict[str, Any]:
    url = "https://api.hh.ru/negotiations/response"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    params = {
        "vacancy_id": vacancy_id,
        "page": page,
        "per_page": per_page
    }
    async with session.get(url, headers=headers, params=params) as response:
        if response.status != 200:
            print(f"Ошибка запроса на странице {page}: {response.status}")
            return {}
        return await response.json()

async def collect_all_responses(session: aiohttp.ClientSession, vacancy_id: str) -> List[Dict[str, Any]]:
    responses = []
    page = 0
    per_page = 20
    while True:
        data = await get_vacancy_responses(session, vacancy_id, page, per_page)
        if not data:
            break
        items = data.get("items", [])
        if not items:
            break
        responses.extend(items)
        total_pages = data.get("pages", 1)
        if page >= total_pages - 1:
            break
        page += 1
    return responses

async def get_resume_details_with_retry(session: aiohttp.ClientSession, resume_id: str, max_retries: int = 5) -> Dict[str, Any]:
    # Если данные уже есть в кэше, возвращаем их
    if resume_id in resume_cache:
        return resume_cache[resume_id]
    
    url = f"https://api.hh.ru/resumes/{resume_id}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    retry_count = 0
    while retry_count < max_retries:
        # Ограничиваем количество одновременных запросов
        async with semaphore:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    resume_cache[resume_id] = data  # сохраняем в кэш
                    return data
                elif response.status == 429:
                    retry_after = response.headers.get("Retry-After")
                    delay = int(retry_after) if retry_after and retry_after.isdigit() else (2 ** retry_count)
                    print(f"Ошибка 429 для {resume_id}. Ретрай через {delay} секунд (попытка {retry_count+1}/{max_retries})")
                    await asyncio.sleep(delay)
                    retry_count += 1
                else:
                    print(f"Ошибка получения резюме {resume_id}: {response.status}")
                    return {}
    print(f"Превышено число попыток для {resume_id}")
    return {}

# ----------------------------
# Синхронные функции для форматирования данных резюме
# ----------------------------
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
    level = education.get("level", {}).get("name", "не указан")
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
    
    skills = candidate.get("skill_set")
    if not skills:
        skills = candidate.get("skills", "")
    else:
        skills = ", ".join(skills) if isinstance(skills, list) else skills
    
    contacts = candidate.get("contact", [])
    contacts_text = ", ".join(f"{c.get('type', {}).get('name')}: {c.get('value')}" for c in contacts) or "Не указаны"
    
    languages = format_languages(candidate.get("language", []))
    recommendations = format_recommendations(candidate.get("recommendation", []))
    
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

def extract_full_candidate_info(resume: Dict[str, Any]) -> Dict[str, Any]:
    candidate_info = resume.copy()
    first = resume.get("first_name", "")
    middle = resume.get("middle_name") or ""
    last = resume.get("last_name", "")
    candidate_info["full_name"] = " ".join(filter(None, [first, middle, last])) or "Не указано"
    return candidate_info

# ----------------------------
# Асинхронный основной блок
# ----------------------------
async def main():
    vacancy_id = "110202595"  # Замените на нужный ID вакансии
    async with aiohttp.ClientSession() as session:
        print("Получаем отклики для вакансии...")
        responses = await collect_all_responses(session, vacancy_id)
        if not responses:
            print("Отклики не найдены или произошла ошибка.")
            return

        # Параллельное получение деталей резюме с использованием ретраев, семафора и кэширования
        tasks = []
        for index, response_item in enumerate(responses, start=1):
            resume_info = response_item.get("resume")
            if resume_info:
                resume_id = resume_info.get("id")
                if resume_id:
                    print(f"[{index}] Запрашиваем полное резюме для resume_id: {resume_id}")
                    tasks.append(get_resume_details_with_retry(session, resume_id))
        
        resume_details_list = await asyncio.gather(*tasks)

        candidate_summaries = []
        for index, resume_details in enumerate(resume_details_list, start=1):
            if resume_details:
                candidate = extract_full_candidate_info(resume_details)
                summary = assemble_candidate_summary(candidate)
                candidate_summaries.append(f"{index}.\n{summary}")

        output_txt = "candidates_summary_async.txt"
        with open(output_txt, "w", encoding="utf-8") as f:
            f.write("\n" + ("-" * 50) + "\n\n".join(candidate_summaries))
        
        print(f"Резюме кандидатов успешно сохранены в файл: {output_txt}")

if __name__ == "__main__":
    asyncio.run(main())
