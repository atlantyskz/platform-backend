import requests
import json
from urllib3.exceptions import InsecureRequestWarning
import urllib3

course_code = input("COURSE_NAME: ")

def cb_SearchCourse(response):
    if response.status_code == 200:
        content = response.content.decode('utf-8-sig')
        resAr = json.loads(content)
        response_data = resAr.get("DATA2", [])
        sections = response_data[0]
        labs = response_data[1]

        try:
            for section_id, section in sections.items():
                if section['COURSE_TYPE'] == 'N':
                    teacher = section['TEACHER']
                    print("---------------------------------------------")
                    print(f'LECTURE {teacher} quota {section["QUOTA"]} ({section["SCHEDULE"]})')
                    pracitse_time = section["PRACTICE"].split(",")
                    try:
                        for time in pracitse_time:
                            print(f'PRACTICE {labs[time]["TEACHER"]} | quota {labs[time]["QUOTA"]} ({labs[time]["SCHEDULE"]})')
                    except:
                        print("без практики")
        except:
            print("не открыт лох")

    else:
        print(f"Request failed with status code {response.status_code}")

def search_course():
    urllib3.disable_warnings(InsecureRequestWarning)
    login_url = 'https://my.sdu.edu.kz/loginAuth.php'
    search_url = f'https://my.sdu.edu.kz/index.php?ajx=1&mod=course_reg&action=ShowSectionsByDersKod&dk={course_code}&dy=2026'
    login_payload = {
        "username": "210107112",
        "password": "7c1R6rz~X2a'",
        "modstring": "",
        "LogIn": "Log in"
    }
    session = requests.Session()
    login_response = session.post(login_url, data=login_payload, verify=False)
    if login_response.status_code != 200:
        print(f"Login failed with status code {login_response.status_code}")
        return

    search_payload = {
        "ajx": "1",
        "mod": "course_reg",
        "action": "ShowSectionsByDersKod",
        "dk": course_code,
        "dy": 2024,
        "1722587282300": ""
    }

    response = session.post(search_url, data=search_payload, verify=False)
    cb_SearchCourse(response)

search_course()
