from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os

class SeleniumExtractor:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = self.configurar_driver()

    def configurar_driver(self):
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')  # Executar sem interface gráfica
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')

        # Caminho absoluto corrigido para o ChromeDriver
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        chrome_driver_path = os.path.join(base_dir, "drivers", "chromedriver.exe")
        service = Service(chrome_driver_path)

        return webdriver.Chrome(service=service, options=chrome_options)

    def extrair_com_selenium(self, url, seletor):
        try:
            self.driver.get(url)
            self.driver.implicitly_wait(5)
            elementos = self.driver.find_elements(By.CSS_SELECTOR, seletor)
            return [el.text for el in elementos]
        finally:
            self.driver.quit()
