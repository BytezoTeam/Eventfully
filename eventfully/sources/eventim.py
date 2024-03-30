import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep

import eventfully.database as db
from eventfully.logger import log


# TODO: Documentation


def get_eventim() -> list[db.RawEvent]:
    events = scrape()

    return events


def scrape() -> list[db.RawEvent]:
    raw_events = []
    try:
        # 10 Pages = around 1325 Events
        for page in range(10):
            chrome_options = Options()
            # Start minimized
            browser = webdriver.Chrome(chrome_options)
            log.debug(f"Getting page {page + 1}")
            # Get the website
            log.debug("Initialize Browser")
            browser.get(f"https://www.eventim.de/events/kultur-2/?ticketDirect=true&page={page + 1}")
            log.debug('Waiting for Cookie Popup')
            try:
                WebDriverWait(browser, 5).until(
                    EC.presence_of_element_located((By.ID, 'cmpbntyestxt')),

                )
                browser.find_element(By.ID, 'cmpbntyestxt').click()
            except selenium.common.exceptions.TimeoutException:
                log.debug('No Cookie Popup')

            log.debug('Waiting for Main Events loaded')
            sleep(5)
            artists = browser.find_elements(By.CSS_SELECTOR, 'product-group-item[class="hydrated"]')
            log.debug(f"Found {len(artists)} Main Events")
            for count, artist in enumerate(artists):
                log.debug(f"[{count + 1}/{len(artists)}] Getting Artist")
                artist_name = artist.find_element(By.XPATH, f'//*[@id="listing-headline-{count}"]/span[1]').text
                events = artist.find_element(By.CSS_SELECTOR, 'div[class="nested-products"]').find_elements(
                    By.CSS_SELECTOR,
                    'product-item[class="hydrated"]')
                price = artist.find_element(By.XPATH,
                                            f'//*[@id="list-item-{count}"]/div[1]/listing-cta[1]/event-status[1]/div[1]/span[1]/span[1]').text

                for event_count, event in enumerate(events):
                    titles = event.find_elements(By.XPATH, f'//*[@id="list-item-{count}"]/div[1]/div[1]/div[2]/span[1]')
                    times = event.find_elements(By.XPATH, f'//*[@id="list-item-{count}"]/div[1]/div[1]/div[1]/span[1]')
                    links = event.find_elements(By.CLASS_NAME, 'btn.link.theme-link-color.theme-link-color-hover')
                    for link in links:
                        link = link.get_attribute("href")

                    title = titles[event_count].text
                    time = times[event_count].text

                    city, _, _ = time.split(",")

                    log.debug(f"Got event '{title}' from '{artist_name}'")

                    event = db.RawEvent(
                        raw="",
                        title=title,
                        description="/",
                        link=link,
                        price=price,
                        start_date=time,
                        end_date="/",
                        address="/",
                        city=city,
                    )
                    # Append the event to the list
                    raw_events.append(event)

            browser.quit()
        return raw_events
    except Exception as e:
        log.error(f"Error while scraping Eventim: Returning events so far!", exc_info=e)
        return raw_events


if __name__ == '__main__':
    events = get_eventim()
    print(len(events))
