import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import eventfully.database as db
from eventfully.logger import log


def get_zuerichunbezahlbar() -> list[db.RawEvent]:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    browser = webdriver.Chrome(chrome_options)

    events = _unbezahlbar(browser)

    browser.quit()

    return events


def _unbezahlbar(browser: webdriver.Chrome) -> list[db.RawEvent]:
    browser.get("https://www.zuerichunbezahlbar.ch/events/")

    events = []

    for _ in range(1):
        browser_events = _get_elements(browser, By.CSS_SELECTOR, ".poster__title-span.poster__title-span-text")
        for event in browser_events:
            try:
                event.click()
            except selenium.common.exceptions.ElementClickInterceptedException:
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
                continue

            log.debug(f"Got event '{title}'")

            _get_element(browser, By.CSS_SELECTOR, ".close-reveal-modal").click()

            event = db.RawEvent(
                raw=description + info,
                title=title,
                description=description + info,
                link=link,
                start_date=time,
                end_date=time,
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
