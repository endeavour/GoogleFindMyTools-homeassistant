from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def create_driver():
	chrome_options = Options()
	chrome_options.add_argument("--no-sandbox")
	chrome_options.add_argument("--disable-dev-shm-usage")
	chrome_options.add_argument("--headless=new")
	chrome_options.add_argument("--disable-gpu")
	chrome_options.add_argument("--window-size=1920,1080")

	# Manueller Pfad zu chromedriver (überprüft mit `which chromedriver`)
	service = Service(executable_path="/usr/bin/chromedriver")

	try:
		driver = webdriver.Chrome(service=service, options=chrome_options)
		print("[ChromeDriver] ChromeDriver gestartet.")
		return driver
	except Exception as e:
		raise Exception(f"[ChromeDriver] Fehler beim Start von ChromeDriver: {e}")
