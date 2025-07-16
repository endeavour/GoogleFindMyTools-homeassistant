# GoogleFindMyTools (Raspberry) Home Assistant

Dies ist ein fork of https://github.com/endeavour/GoogleFindMyTools-homeassistant

Dieser Fork von GoogleFindMyTools ist für den Betrieb auf Raspberry OS gedacht, da es dort ansonsten Probleme mit Chromeium und dem login in Chrome gibt. Die Kommunikation findet über Mqqt zu Home Assistant (Mqqt Brocker) statt, welches auf einem anderen Gerät läuft. 

Da Google Find my Device entweder einen Standort in Koordinatenform oder einen String "home" bzw. "zuhause", wurde die publish_mqqt.py angepasst. Falls google nun den string zuhause sendet, ersetzt der Raspbbery diesen durch Koordinaten für die Home Zone.
Der Aufruf zum aktualisieren des Standortes erfolgt über Home Assisant via mqtt. In diesem sind die Kooardinaten für die Homezone (Koordinaten + Radius) enthalten.

Da der Chrome Browser auf dem Raspberry beim "requstest url was not found on this server" meldet, kann man sich dort nicht einloggen. Man muss daher GoogleFindMyTools auf einem Windows PC installieren, sich einloggen und die secrets.json mit den Zugangsdaten von dem PC auf den Raspberry kopieren. Daher ist die Anleitung in drei Schritte aufgeteilt: Installation auf dem  Windows PC, installation auf dem Raspberry OS und anschließend die Mqqt Verbindung zu Home Assistant.

## Installation Windows PC:

git installieren:  https://git-scm.com/download/win <br>
Python installieren: https://www.python.org/downloads/windows/

Im Chromebrowser mit dem Nutzkonto einloggen. Wichtig: hiermit ist nicht die website von google.com gemeint, sondern das Chrome Desktop Programm!

PowerShell als Admin ausführen und GoogleFindMyTools von leonboe1 installieren
```
git clone https://github.com/leonboe1/GoogleFindMyTools
```
```
python -m venv venv
```
falls dass nicht geht ```& "C:\Users\[USER]\AppData\Local\Programs\Python\Python313\python.exe" -m venv venv``` 
hier bei muss [USER] durch den PC User ersetzt werden bzw. wo auch immer wurde 
```
venv\Scripts\activate
```
alternativ ```.\venv\Scripts\Activate.ps1```
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```
```
cd GoogleFindMyTools
```
```
pip install -r requirements.txt
```
```
python main.py```
```
<br>
<br>
<br>
<br>
Es könnte nun der Fehler "undetected_chromedriver" kommen. In diesem Fall muss der Chromedriver separat installiert werden

Zuerst muss man die Chrome Version herausfinden: Öffne Chrome  und gib  chrome://settings/help in die Adresszeile ein. Notiere die Version, z.B. 114.0.5735.199 
Nun muss man den passenden ChromeDriver herunterladen: https://googlechromelabs.github.io/chrome-for-testing/. Wenn die erste Zahl z.B. 144 der Versionnummer übereinstimmt, reicht das.

Entpacke die datei chromedriver.exe nach C:\Tools\chromedriver\<br>
Nun müssen wir noch den dateipfad anpassen, damit GoogleFindMyTools weiß wo dieser liegt. 

Gehe unter C:\WINDOWS\system32\GoogleFindMyTools\chrome_driver.py und öffne die Datei als Admin


wir müssen folgenden Block
```
def create_driver():
    """Create a Chrome WebDriver with undetected_chromedriver."""

    try:
        chrome_options = get_options()
        driver = uc.Chrome(options=chrome_options)
        print("[ChromeDriver] Installed and browser started.")
        return driver
    except Exception:
        print("[ChromeDriver] Default ChromeDriver creation failed. Trying alternative paths...")

        chrome_path = find_chrome()
        if chrome_path:
            chrome_options = get_options()
            chrome_options.binary_location = chrome_path
            try:
                driver = uc.Chrome(options=chrome_options)
                print(f"[ChromeDriver] ChromeDriver started using {chrome_path}")
                return driver
            except Exception as e:
                print(f"[ChromeDriver] ChromeDriver failed using path {chrome_path}: {e}")
        else:
            print("[ChromeDriver] No Chrome executable found in known paths.")

        raise Exception(
            "[ChromeDriver] Failed to install ChromeDriver. A current version of Chrome was not detected on your system.\n"
            "If you know that Chrome is installed, update Chrome to the latest version. If the script is still not working, "
            "set the path to your Chrome executable manually inside the script."
        )
```

durch diesen ersetzten

```
def create_driver():
    """Create a Chrome WebDriver with undetected_chromedriver."""

    try:
        chrome_options = get_options()
        driver = uc.Chrome(options=chrome_options)
        print("[ChromeDriver] Installed and browser started.")
        return driver
    except Exception:
        print("[ChromeDriver] Default ChromeDriver creation failed. Trying alternative paths...")

        chrome_path = find_chrome()
        if chrome_path:
            chrome_options = get_options()
            #chrome_options.binary_location = chrome_path
            chrome_options.debugger_address = "127.0.0.1:9222"
            try:
                #driver = uc.Chrome(options=chrome_options)
                driver = uc.Chrome(
                    options=chrome_options,
                    driver_executable_path="C:\\Tools\\chromedriver\\chromedriver.exe",
                    use_subprocess=False
                )
                print(f"[ChromeDriver] ChromeDriver started using {chrome_path}")
                return driver
            except Exception as e:
                print(f"[ChromeDriver] ChromeDriver failed using path {chrome_path}: {e}")
        else:
            print("[ChromeDriver] No Chrome executable found in known paths.")

        raise Exception(
            "[ChromeDriver] Failed to install ChromeDriver. A current version of Chrome was not detected on your system.\n"
            "If you know that Chrome is installed, update Chrome to the latest version. If the script is still not working, "
            "set the path to your Chrome executable manually inside the script."
        )
```

Hierdurch wird unser neuer Chromedriver verwendet und Chrome in Debug modus geöffnet. Melde dich dort im Chorme mit deinem Google Profil noch einmal an (wichtig: nicht die Website sondern im Chrome). Schließe alle Browser Fenster 

gebe nun 
```
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\ChromeDebugTemp"
```
in powershell ein und führe 
```
python main.py```
```
noch einmal aus. Nun sollte es funktionieren




