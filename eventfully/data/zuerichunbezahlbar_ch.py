import selenium.common.exceptions
from result import Result, Ok, Err
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import eventfully.database as db


def get_zuerichunbezahlbar() -> Result[None, Exception]:
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        browser = webdriver.Chrome(chrome_options)

        events = _unbezahlbar(browser)

        browser.quit()

        db.add_events(events)
    except Exception as e:
        return Err(e)

    return Ok(None)


def _unbezahlbar(browser: webdriver.Chrome) -> list[db.Event]:
    browser.get("https://www.zuerichunbezahlbar.ch/events/")

    events = []

    for _ in range(6):
        browser_events = _get_elements(browser, By.CSS_SELECTOR, ".poster__title-span.poster__title-span-text")
        for event in browser_events:
            try:
                event.click()
            except selenium.common.exceptions.ElementClickInterceptedException:
                print("Problem")
                continue

            try:
                title = _get_element(browser, By.CSS_SELECTOR,
                                    ".reveal-modal.open .poster__title-span.poster__title-span-text").text
                time = _get_element(browser, By.CSS_SELECTOR, ".detailpost__date time").text
                info = _get_element(browser, By.CSS_SELECTOR, "div.detailpost__info").text
                address = _get_element(browser, By.CSS_SELECTOR, "address.detailpost__address").text
                description = _get_element(browser, By.CSS_SELECTOR, "div.detailpost__description").text
                link = _get_element(browser, By.CSS_SELECTOR, "a.detailpost__link").get_attribute("href")
            except (
                    selenium.common.exceptions.TimeoutException,
                    selenium.common.exceptions.ElementClickInterceptedException):
                print("Problem")
                continue

            print(title)

            _get_element(browser, By.CSS_SELECTOR, ".close-reveal-modal").click()

            event = db.Event(
                title=title,
                description=description,
                link=link,
                price="",
                tags="",
                start_date=time,
                end_date=time,
                age="",
                accessibility="",
                address=address,
                city="Zürich",
            )
            events.append(event)

        # get_element(By.CSS_SELECTOR, "span.step-links a").click()
        _get_element(browser, By.XPATH, "//a[text()='weiter »']").click()

    return events


def _get_element(browser: webdriver.Chrome, selector_type: str, selector: str):
    return WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((selector_type, selector)))


def _get_elements(browser: webdriver.Chrome, selector_type: str, selector: str):
    return WebDriverWait(browser, 5).until(
        EC.presence_of_all_elements_located((selector_type, selector)))


if __name__ == '__main__':
    get_zuerichunbezahlbar()
