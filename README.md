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
sudo apt install systemd-networkd-wait-online
```
```
sudo systemctl enable systemd-networkd-wait-online.service
```

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
python main.py
```
noch einmal aus. Nun sollte es funktionieren. 


PowerShell lassen wir geöffnet und richten nun den Raspberry ein.



## Installation Raspberry:
Für einen Aufbau habe ich einen Raspberry 2 b verwendet und dort Raspberry OS Bookworm verwendet. Die Verbindung kann man mit Putty (Port 22) von Windows zum Raspberry herstellen. Anschließend mit User und Passwort anmelden. 

```
sudo apt install chromium-browser
```
```
sudo apt install chromium-browser
```
Es es klappt kann man sich über die UI im Chromebrowser anmelden. Falls nicht  "requstest url was not found on this server", muss man die  secrets.json von windows später zum Raspberry kopieren


Installieren wir nun GoogleFindMyTools
```
git clone https://github.com/xHecktor/GoogleFindMyTools-homeassistant.git ~/GoogleFindMyTools
```
```
cd ~/GoogleFindMyTools
```
```
python3 -m venv venv
```
```
source venv/bin/activate
```
```
pip install -r requirements.txt
```
```
python3 main.py
```
oder ```python main.py```


hier wird nun ein Fehler wegen der Zugangsdaten von Chrome Browser kommen. Daher gehen wir wieder in Powershell und übertragen nun die Zugangsdaten von Windows zum Raspberry.
In PowerShell folgenes eintrippen:
```
scp Auth\secrets.json admin@raspberrypi.local:~/GoogleFindMyTools/Auth/
```
ggf. muss hier admin durch den User und raspberry durch den Gerätenamen im oben link ersetzt werden.


<br><br>
nun müssen wir die Daten vom Mqtt Brocker eintragen. Daher wieder in Putty die publish_mqtt.py auf dem Raspberry öffenen
```
nano publish_mqtt.py
```
und folgende Felder anpassten:

```
MQTT_BROKER = "192.168.1.100"  # Ändere die IP zu der von Home Assistant
MQTT_PORT = 1883
MQTT_USERNAME = "mqttuser"  # Ändere einen Usernamen
MQTT_PASSWORD = "password"  # Ändere dein Passwort
```
Drücke STG+X, dann Y und Enter

Nun richten wir einen Autstart ein
```
cd /home/admin
```
```
nano update_location.sh
```
und dort folgendes einfügen:
```
#!/bin/bash
cd /home/admin/GoogleFindMyTools
source venv/bin/activate
python3 publish_mqtt.py
```
Drücke STG+X, dann Y und Enter
```
chmod +x update_location.sh
```
Ausführung testen: 
```
./update_location.sh
```

<br><br><br>
Nun erstellen wir noch einen Listener, um die Trigger von Home Assistant zu empfangen:
```
nano mqtt_listener.py
```
hier müssen auch wieder die Zugangsdaten des Mqtt Brockers angepasst werden

```
import paho.mqtt.client as mqtt
import subprocess
import datetime
import json

MQTT_BROKER = "192.168.100"
MQTT_PORT = 1883
MQTT_TOPIC = "googlefindmytools/trigger/update"
MQTT_USER = "mqttuser"
MQTT_PASS = "password"

def on_connect(client, userdata, flags, rc, properties=None):
        print("Connected with result code " + str(rc))
        client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    print(f"Received trigger: {msg.payload.decode()}")

    try:
        # JSON laden
        payload = json.loads(msg.payload.decode())

        # Optional: Nur ausführen, wenn bestimmte Keys vorhanden sind
        if "lat_home" in payload and "lon_home" in payload and "home_radius" in payload:
            print("→ Konfiguration aus Trigger empfangen, sende retained an googlefindmytools/config")

            # An config-Topic weiterleiten (retain!)
            client.publish("googlefindmytools/config", json.dumps(payload), retain=True)

        else:
            print("→ Kein gültiger Konfigurations-Payload – wird ignoriert.")

    except json.JSONDecodeError:
        print("→ Kein JSON – evtl. nur 'start' ohne Konfiguration")

    # Skript immer starten, egal ob mit oder ohne Konfiguration
    print("Running update_location.sh...")

    try:
        result = subprocess.run(
            ["/home/admin/update_location.sh"],
            capture_output=True,
            text=True,
            timeout=120
        )
        print(" STDOUT:\n", result.stdout)
        print(" STDERR:\n", result.stderr)

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if result.returncode == 0:
            status_msg = f" Standortdaten erfolgreich aktualisiert um {now}."
        else:
            status_msg = f" Fehler bei der Standortaktualisierung ({result.returncode}) um {now}.\n{result.stderr}"
    except Exception as e:
        import traceback
        status_msg = f" Ausnahmefehler: {e}\n{traceback.format_exc()}"

    client.publish("googlefindmytools/status", status_msg)



client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.on_connect = on_connect
client.on_message = on_message


client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()

```

Drücke STG+X, dann Y und Enter

```
chmod +x mqtt_listener.py
```
hiermit kann man den listener testen
```
python3 ~/mqtt_listener.py
```

<br><br><br>
Abschließend müssen wir noch den Listener Service erstellen
```
sudo nano /etc/systemd/system/mqtt_listener.service
```
hier muss folgendes hineinkopiert werden:
```

[Unit]
Description=MQTT Listener for Google Find My Tools
Wants=network-online.target
After=network.target
#After=network-online.target


[Service]
ExecStart=/home/admin/GoogleFindMyTools/venv/bin/python /home/admin/mqtt_listener.py
WorkingDirectory=/home/admin
StandardOutput=journal
StandardError=journal
Restart=always
User=admin
Environment="PATH=/home/admin/GoogleFindMyTools/venv/bin"

[Install]
WantedBy=multi-user.target
```
Drücke STG+X, dann Y und Enter
```
sudo systemctl daemon-reexec
```
```
sudo systemctl daemon-reload
```
```
sudo systemctl enable mqtt_listener.service
```
```
sudo systemctl start mqtt_listener.service
```
listener Service testen:
```
sudo systemctl status mqtt_listener.service
```
```
journalctl -u mqtt_listener.service -f
```
<br><br><br><br>
wenn man sich später die kommunikation mit HA anschauen möchte:
```
cd /home/admin
source ~/GoogleFindMyTools/venv/bin/activate
python3 ~/mqtt_listener.py
```
Str + c zum beenden


# Home Assistant
Abschnließend müssen wir noch den Broker in Home Assistant installieren

In der configuration.yaml
```
mqtt:
```
hinzufügen

Als nächstes müssen wir einen neuen User zu HA hinzufügen. <br>
Einstellungen/Personen/Benutzer hinzufügen<br>
Dieser Username und Passwort muss mit dem übereinstimmen, was wir oben im Raspberry bereits hinterlegt haben.<br>


Nun installieren wir den Mqqt Broker:<br>
In Home Assistant Einstellungen/ Geräte&Dienste Integration hinzufügen drücken und nach Mqtt suchen und installieren und das offizielle Mqqt auswählen (nicht das manuelle mit den Benutzerdetails) <br>

Nun richten wir den Broker ein:<br>
Einstellungen/ Geräte&Dienste / MQTT<br><br>

Dort gibt es nun einen Integrationseintrag: "Mosquitto Mqtt Broker". Dort gehen wir auf die drei Punkte und wählen "Neu konfigueren" aus.<br>
Folgendes geben wir ein:<br>
Server: core-mosquitto<br>
Port: 1883<br>
Benutzername: Dein User den du beim Raspberry verwendet hast in der mqtt_listener.py und in der publish_mqtt.py<br>
Passwort: Dein Passwort das du beim Raspberry verwendet hast in der mqtt_listener.py und in der publish_mqtt.py<br>

<br><br><br><br>
Nun erstellen wir den Aufruf zum Orten der Google Tags
Einstellungen/Automatisierungen&Szenen/Skripte/ Neues Skript hinzufügen


Hier kannst du die Koordinaten und den Umkreis von deinem Zuhause definieren. Wenn nun der Google Tag anstatt von Koordinaten nur "Zuhause" meldet, wird dieses in Koordinaten umgewandelt, damit Home Assisant den Tracker anzeigen kann. 
```
alias: Google Tracker aktualisieren
sequence:
  - data:
      topic: googlefindmytools/trigger/update
      payload: "{ \"lat_home\": 31.8909528, \"lon_home\": 7.1904316, \"home_radius\": 500 }"
    action: mqtt.publish
```
speichern und ausführen. Die Google Tags sollten nun in Home Assistan angezeigt werden. 

Zuletzt legen wir noch eine Automatisierung ab, um den Standort alle 15 min zu aktualisieren:
Einstellungen/Automatisierungen&Szenen/ Automatisierung erstellen

```
alias: Google_Airtag
description: ""
triggers:
  - trigger: time_pattern
    minutes: /15
conditions: []
actions:
  - action: script.update_google_locations
    metadata: {}
    data: {}
mode: single
```
speichern



So fertig sind wir





