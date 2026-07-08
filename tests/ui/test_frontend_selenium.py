import os
import time

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

pytestmark = pytest.mark.ui


@pytest.fixture(scope="module")
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")

    try:
        service = Service(ChromeDriverManager().install())
        drv = webdriver.Chrome(service=service, options=options)
    except Exception as exc:
        pytest.skip(f"Chrome/chromedriver indisponible : {exc}")
        return

    drv.implicitly_wait(2)
    yield drv
    drv.quit()


def wait_visible(driver, locator, timeout=10):
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))


def wait_present(driver, locator, timeout=10):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))


def set_date_value(driver, element, iso_date):
    driver.execute_script("arguments[0].value = arguments[1];", element, iso_date)


def test_homepage_loads_with_title(driver):
    driver.get(FRONTEND_URL)
    wait_present(driver, (By.CSS_SELECTOR, ".sidebar .logo"))
    assert "FutureKawa" in driver.title
    assert "FutureKawa" in driver.find_element(By.CSS_SELECTOR, ".sidebar .logo").text


def test_country_selector_has_three_countries(driver):
    driver.get(FRONTEND_URL)
    wait_present(driver, (By.CSS_SELECTOR, "#country-select option"))

    options = driver.find_elements(By.CSS_SELECTOR, "#country-select option")
    values = {opt.get_attribute("value") for opt in options}

    assert values == {"equateur", "bresil", "colombie"}


def test_switching_country_reloads_lots_for_that_country(driver):
    driver.get(FRONTEND_URL)
    wait_present(driver, (By.CSS_SELECTOR, "#lots-tbody tr.lot-row"))

    from selenium.webdriver.support.ui import Select
    Select(driver.find_element(By.ID, "country-select")).select_by_value("bresil")

    WebDriverWait(driver, 10).until(
        lambda d: "LOT-BR-" in d.find_element(By.ID, "lots-tbody").text
    )

    table_text = driver.find_element(By.ID, "lots-tbody").text
    assert "LOT-BR-" in table_text
    assert "LOT-EQ-" not in table_text


def test_lots_view_has_at_least_six_rows(driver):
    driver.get(FRONTEND_URL)
    wait_present(driver, (By.CSS_SELECTOR, "#lots-tbody tr.lot-row"))

    rows = driver.find_elements(By.CSS_SELECTOR, "#lots-tbody tr.lot-row")
    assert len(rows) >= 6


def test_first_lot_is_oldest_fifo(driver):
    driver.get(FRONTEND_URL)
    wait_present(driver, (By.CSS_SELECTOR, "#lots-tbody tr.lot-row"))

    rows = driver.find_elements(By.CSS_SELECTOR, "#lots-tbody tr.lot-row")
    dates_text = [row.find_elements(By.TAG_NAME, "td")[3].text for row in rows]
    parsed = [tuple(reversed(d.split("/"))) for d in dates_text]

    assert parsed == sorted(parsed)


def test_clicking_lot_opens_detail_with_charts(driver):
    driver.get(FRONTEND_URL)
    row = wait_present(driver, (By.CSS_SELECTOR, "#lots-tbody tr.lot-row"))
    row.click()

    wait_visible(driver, (By.CSS_SELECTOR, "#view-lot-detail.active"))
    assert driver.find_element(By.ID, "chart-temperature").is_displayed()
    assert driver.find_element(By.ID, "chart-humidity").is_displayed()


def test_alerts_view_displayed(driver):
    driver.get(FRONTEND_URL)
    nav = wait_present(driver, (By.CSS_SELECTOR, ".nav-link[data-view='alerts']"))
    nav.click()

    wait_visible(driver, (By.CSS_SELECTOR, "#view-alerts.active"))
    assert driver.find_element(By.ID, "alerts-table").is_displayed()


def test_create_lot_via_form_appears_in_list(driver):
    driver.get(FRONTEND_URL)
    nav = wait_present(driver, (By.CSS_SELECTOR, ".nav-link[data-view='new-lot']"))
    nav.click()
    wait_visible(driver, (By.CSS_SELECTOR, "#view-new-lot.active"))

    lot_code = f"LOT-SEL-{int(time.time())}"
    driver.find_element(By.NAME, "lot_code").send_keys(lot_code)
    driver.find_element(By.NAME, "farm").send_keys("Ferme Selenium")
    set_date_value(driver, driver.find_element(By.NAME, "storage_date"), "2025-01-01")
    driver.find_element(By.CSS_SELECTOR, "#new-lot-form button[type='submit']").click()

    wait_visible(driver, (By.CSS_SELECTOR, "#view-lots.active"), timeout=10)
    wait_present(driver, (By.CSS_SELECTOR, "#lots-tbody tr.lot-row"))

    table_text = driver.find_element(By.ID, "lots-tbody").text
    assert lot_code in table_text
