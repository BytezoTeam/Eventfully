import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import eventfully.utils as utils
import eventfully.database as db


def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    browser = webdriver.Chrome(chrome_options)

    unbezahlbar(browser)

    browser.quit()


def unbezahlbar(browser: webdriver.Chrome):
    browser.get("https://www.zuerichunbezahlbar.ch/events/")

    for _ in range(6):
        browser_events = get_elements(browser, By.CSS_SELECTOR, ".poster__title-span.poster__title-span-text")
        for event in browser_events:
            try:
                event.click()
            except selenium.common.exceptions.ElementClickInterceptedException:
                print("Problem")
                continue

            try:
                title = get_element(browser, By.CSS_SELECTOR,
                                    ".reveal-modal.open .poster__title-span.poster__title-span-text").text
                time = get_element(browser, By.CSS_SELECTOR, ".detailpost__date time").text
                info = get_element(browser, By.CSS_SELECTOR, "div.detailpost__info").text
                address = get_element(browser, By.CSS_SELECTOR, "address.detailpost__address").text
                description = get_element(browser, By.CSS_SELECTOR, "div.detailpost__description").text
                link = get_element(browser, By.CSS_SELECTOR, "a.detailpost__link").get_attribute("href")
            except (
                    selenium.common.exceptions.TimeoutException,
                    selenium.common.exceptions.ElementClickInterceptedException):
                print("Problem")
                continue

            print(title)

            get_element(browser, By.CSS_SELECTOR, ".close-reveal-modal").click()

            content_hash = utils.get_hash_string(title + time)
            if db.EMailContent.select().where(db.EMailContent.subject == content_hash).exists():
                continue
            db.EMailContent.create(subject=content_hash,
                                   content=f"title: {title}\ntime_date: {time}\n info: {info}\naddress: {address}\ndescription: {description}\nlink: {link}\naddress: {address}\ncity: Zürich")

        # get_element(By.CSS_SELECTOR, "span.step-links a").click()
        get_element(browser, By.XPATH, "//a[text()='weiter »']").click()


def get_element(browser: webdriver.Chrome, selector_type: str, selector: str):
    return WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((selector_type, selector)))


def get_elements(browser: webdriver.Chrome, selector_type: str, selector: str):
    return WebDriverWait(browser, 5).until(
        EC.presence_of_all_elements_located((selector_type, selector)))


if __name__ == '__main__':
    main()
