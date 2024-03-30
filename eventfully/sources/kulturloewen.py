import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from time import sleep

import eventfully.database as db
from eventfully.logger import log


def get_kulturloewen() -> list[db.RawEvent]:

    events = scrape()
    return events


def scrape() -> list[db.RawEvent]:
    # Make variables
    raw_events = []
    full_events = 0
    min_events = 0

    # Configure browser
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    browser = webdriver.Chrome(chrome_options)

    # Get the website
    browser.get("https://www.kulturloewen.de/veranstaltungen")

    # Get the event box
    event_box = browser.find_element(By.ID, "klive-kalenderbox")

    # Get the event ids
    log.debug("Getting event ids")
    ids = event_box.find_elements(By.XPATH, "//a[@name]")
    log.debug("Removing ids that are not numbers")
    event_ids = []

    # Remove ids that are not numbers
    for id in range(len(ids)):
        try:
            int(ids[id].get_attribute('name'))
            event_ids.append(ids[id])
        except ValueError:
            log.debug(f"Removing id '{ids[id].get_attribute('name')}'")

    # Get the events
    events = event_box.find_elements(By.CLASS_NAME, "klive-terminbox")
    count = 0
    log.debug("Beginning to scrape events")
    # Loop through the events
    for event in events:
        information = event.find_element(By.CLASS_NAME, "klive-kurzfassung")
        title_box = information.find_element(By.CLASS_NAME, "klive-titel")
        try:
            # Get the title
            title = title_box.find_element(By.CLASS_NAME, "klive-titel-titel").text
        except selenium.common.exceptions.NoSuchElementException:
            # Use the artist name if the title is not found
            title = title_box.find_element(By.CLASS_NAME, "klive-titel-artist").text
        found = False
        tries = 0
        while not found:
            try:
                # Try to get further information
                sleep(0.5)
                title_box.find_element(By.ID, f"a{event_ids[count].get_attribute('name')}").click()
                sleep(1)
                more_data = event.find_element(By.ID, f"termin{event_ids[count].get_attribute('name')}")
                further_information = more_data.find_element(By.ID, "klive-kalenderbox")
                found = True
            except selenium.common.exceptions.NoSuchElementException:
                tries += 1
                if tries > 2:
                    # If the information is not found, log an error
                    log.error("Could not find further information for this event")
                    break

        if found:
            # Get the description, start/end_time, and address
            body_slots = further_information.find_element(By.CLASS_NAME, "klive-langfassung").find_element(By.CLASS_NAME, "klive-langfassung-inhalt").find_element(By.CLASS_NAME,"klive-langfassung-fotoundtext").find_elements(By.CLASS_NAME, "bodySlots")
            description = body_slots[0].find_element(By.CLASS_NAME, "bText").text
            # Get the time
            date_information = information.find_element(By.CLASS_NAME, "klive-datumuhrzeit").find_element(By.CLASS_NAME, "klive-datum")
            time = f"{information.find_element(By.CLASS_NAME, 'klive-datumuhrzeit').find_element(By.CLASS_NAME, 'klive-tag').text}, {date_information.find_element(By.CLASS_NAME, 'klive-datum-tag').text}{date_information.find_element(By.CLASS_NAME, 'klive-datum-monat').text}24: {information.find_element(By.CLASS_NAME, 'klive-datumuhrzeit').find_element(By.CLASS_NAME, 'klive-zeit').text}"
            # Get the address
            address_unfiltered = further_information.find_element(By.CLASS_NAME, "klive-langfassung").find_element(By.CLASS_NAME, "klive-langfassung-inhalt").find_element(By.CLASS_NAME, "klive-langfassung-veranstaltungsort").text
            address = address_unfiltered.replace("VERANSTALTUNGSORT", "")
            log.debug(f"[{count +1}/{len(events)}] Got event '{title}' (ID: {event_ids[count].get_attribute('name')})")
            full_events += 1

            # Create the Raw DB event
            event = db.RawEvent(
                raw=description,
                title=title,
                description=description,
                link="https://www.kulturloewen.de/veranstaltungen",
                start_date=time,
                address=address,
                city="Velbert",
            )
            # Append the event to the list
            raw_events.append(event)
        else:
            # Append the event to the list with minimal information
            log.debug(f"[{count +1}/{len(events)}] Added event '{title}' (ID: {event_ids[count].get_attribute('name')}) without further information")
            min_events += 1

            # Create the Raw DB event
            event = db.RawEvent(
                raw="",
                title=title,
                link="https://www.kulturloewen.de/veranstaltungen",
                city="Velbert",
            )
            # Append the event to the list
            raw_events.append(event)

        # Increment the count
        count += 1

    # Give the user some feedback
    log.debug(f"Finished scraping events: Added {len(raw_events)} events to the list. {full_events} events have full "
             f"information, {min_events} events have minimal information")
    return raw_events


if __name__ == '__main__':
    get_kulturloewen()