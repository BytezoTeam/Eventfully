from beartype import beartype
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


@beartype
def get_element(browser: webdriver.Chrome, selector_type: str, selector: str, timeout: int = 5):
    return WebDriverWait(browser, timeout).until(
        EC.presence_of_element_located((selector_type, selector)))


@beartype
def get_elements(browser: webdriver.Chrome, selector_type: str, selector: str, timeout: int = 5):
    return WebDriverWait(browser, timeout).until(
        EC.presence_of_all_elements_located((selector_type, selector)))
