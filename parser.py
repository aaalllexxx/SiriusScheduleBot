import json
import time

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def parse(group):
    schedule = {}
    options = Options()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options)
    link = "https://schedule.siriusuniversity.ru/"

    driver.get(link)
    el = driver.find_element(By.XPATH, '//*[@id="searchListInput"]')
    el.send_keys(f"{group}")
    button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
        (By.XPATH, '/html/body/div/div/div[2]/div/div/div/div[2]/div[2]/div[1]/div[1]/div/ul/li')))
    button.click()
    frame = driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div/div/div[3]/div[2]/div[2]/table/tbody")
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "tr")))
    rows = frame.find_elements(By.CSS_SELECTOR, "tr")
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, row in enumerate(rows):
        data = row.find_elements(By.CSS_SELECTOR, "td")
        for j, el in enumerate(data):
            if not schedule.get(days[j]):
                schedule[days[j]] = []
            try:
                name = el.find_element(By.CSS_SELECTOR, ".rasp-grid-min-discipline").text
                teacher = el.find_element(By.CSS_SELECTOR, ".rasp-grid-min-teachers").text
                aud = el.find_elements(By.TAG_NAME, "span")[3].text
                tm = el.find_elements(By.TAG_NAME, "span")[0].text
                tp = el.find_element(By.CSS_SELECTOR, ".pb-2").text
                schedule[days[j]].append({
                    "name": name,
                    "teacher": teacher,
                    "time": tm,
                    "aud": aud,
                    "type": tp
                })
            except NoSuchElementException as e:
                schedule[days[j]].append({
                    "name": "Окно",
                    "teacher": "",
                    "time": "",
                    "aud": "",
                    "type": ""
                })
    driver.close()
    return schedule


if __name__ == "__main__":
    parse_data = parse("К0409-22")
    print(json.dumps(parse_data, indent=4, ensure_ascii=False))
