# GoogleFindMyTools (Raspberry) Home Assistant

Dies ist ein fork of https://github.com/endeavour/GoogleFindMyTools-homeassistant

Dieser Fork von GoogleFindMyTools ist für den Betrieb auf Raspberry OS gedacht, da es dort ansonsten Probleme mit Chromeium und dem login in Chrome gibt. Die Kommunikation findet über Mqqt zu Home Assistant (Mqqt Brocker) statt, welches auf einem anderen Gerät läuft. 

Da Google Find my Device entweder einen Standort in Koordinatenform oder einen String "home" bzw. "zuhause", wurde die publish_mqqt.py angepasst. Falls google nun den string zuhause sendet, ersetzt der Raspbbery diesen durch Koordinaten für die Home Zone.
Der Aufruf zum aktualisieren des Standortes erfolgt über Home Assisant via mqtt. In diesem sind die Kooardinaten für die Homezone (Koordinaten + Radius) enthalten.

Die Home Zone (Koordinaten + Umkreis) sind nötig, da Home Assistant immer einen Status zur Übermittlung der Attribute (Koordinaten) benötigt. Vorher hat die publisch_mqtt.py immer unkown als Status gesendet und die Koordinaten als Attribute. Die folge war, das home assistent den tracker bei jeder Standort aktualisierung auf unkown gesetzt hat und dann die Attribute ausliest, um dann wieder "home" als status zu setzten. Mit dieser Änderung wird direkt der richtige status an home Assistent gesendet. 

Da der Chrome Browser auf dem Raspberry beim "requstest url was not found on this server" meldet, kann man sich dort nicht einloggen. Man muss daher GoogleFindMyTools auf einem Windows PC installieren, sich einloggen und die secrets.json mit den Zugangsdaten von dem PC auf den Raspberry kopieren. Daher ist die Anleitung in drei Schritte aufgeteilt: Installation auf dem  Windows PC, installation auf dem Raspberry OS und anschließend die Mqqt Verbindung zu Home Assistant.

## Installation Windows PC:

git installieren:  https://git-scm.com/download/win <br>
Python installieren: https://www.python.org/downloads/windows/

Im Chromebrowser mit dem Nutzkonto einloggen. Wichtig: hiermit ist nicht die website von google.com gemeint, sondern das Chrome Desktop Programm!

PowerShell als Admin ausführen und GoogleFindMyTools **<ins> von leonboe1 </ins>** installieren


```
git clone https://github.com/leonboe1/GoogleFindMyTools
```
```
cd GoogleFindMyTools
```
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
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
cd GoogleFindMyTools
```
```
pip install -r requirements.txt
```
```
python main.py
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
sudo apt install chromium-chromedriver
```
Es es klappt kann man sich über die UI im Chromebrowser anmelden. Falls nicht  "requstest url was not found on this server", muss man die  secrets.json von windows später zum Raspberry kopieren

```
sudo apt install systemd-networkd-wait-online
```
```
sudo systemctl enable systemd-networkd-wait-online.service
```

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
MQTT_USERNAME = "DeinMqttUser"  # Ändere einen Usernamen
MQTT_PASSWORD = "DeinMqttPasswort"  # Ändere dein Passwort
```
Drücke STG+X, dann Y und Enter

<br><br><br>
Auch die Zugangsdaten vom LIstener anpassen, um die Trigger von Home Assistant zu empfangen:
```
nano mqtt_listener.py
```
hier müssen auch wieder die Zugangsdaten des Mqtt Brockers angepasst werden

```
MQTT_BROKER = "192.168.100"
MQTT_PORT = 1883
MQTT_TOPIC = "googlefindmytools/trigger/update"
MQTT_USER = "DeinMqqtUser"
MQTT_PASS = "DeinMqttPasswort"

```

Drücke STG+X, dann Y und Enter

```
chmod +x mqtt_listener.py
```


<br><br><br>
Abschließend müssen wir noch den Listener Service erstellen
```
sudo nano /etc/systemd/system/mqtt_listener.service
```
hier muss folgendes hineinkopiert werden (Achtung User Verzeichnis anpassen, hier admin):
```

[Unit]
Description=MQTT Listener for Google Find My Tools
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=60
StartLimitBurst=5


[Service]
#Type=simple
User=admin
WorkingDirectory=/home/admin/GoogleFindMyTools
Environment="PATH=/home/admin/GoogleFindMyTools/venv/bin"
#ExecStart=/home/admin/GoogleFindMyTools/venv/bin/python mqtt_listener.py
ExecStart=/home/admin/GoogleFindMyTools/venv/bin/python /home/admin/GoogleFindMyTools/mqtt_listener.py

# stderr ins Nichts leiten, stdout bleibt im Journal
#StandardError=null
StandardOutput=journal
StandardError=journal

# 🧹 Alte Subprozesse (z. B. nbe_list_devices.py) aufräumen
ExecStopPost=/usr/bin/pkill -f nbe_list_devices.py

# → Watchdog einschalten
Type=notify
WatchdogSec=30
NotifyAccess=all

# Fallback‑Restart, falls das Skript wirklich abstürzt
Restart=on-failure
RestartSec=5


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
Nun müssen wir noch einen Watchdog erstellen. Dies ist leider nur eine behälfsmäßige Lösung. Ich habe die Erfahrung gemacht, dass sich der update Service gerne aufhängt. Der Watchdoog schaut, ob der Updateprozess innnerhalb von 400 Sekunden fertig gemeldet hat. Ist es nicht der Fall, killt alles und startet es neu. 400s habe ich deshalb eingestellt, da Home Assistant alle 5 min einen Trigger schickt. Wenn Home Assistant seltener die Trigger sendet, sollte auch der Watchdog angepasst werden.

Um den Watchdog zu starten
```
sudo apt install watchdog
```
```
sudo systemctl enable watchdog
```
```
sudo systemctl start watchdog
```
```
sudo nano /etc/watchdog.conf
```
Aktiviere folgende Zeilen, indem du die Raute davor entfernst. Falls nicht vorhanden füge diese einfach hinzu.
```
watchdog-device = /dev/watchdog
max-load-1 = 24
temperature-device = /sys/class/thermal/thermal_zone0/temp
max-temperature = 75000

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
journalctl -u mqtt_listener.service -f

```
Str + c zum beenden

wenn man später die kommunikation mit HA sehen möchte, einfach ein zweites Puttyfenster aufmachen und folgendes eingeben:
user ip und password müssen natürlich die von deinem Broker (Home Assistant) sein
```
mosquitto_sub -h 192.168.1.100 -u DeinMqttUser -P DeinMqttPassword -v -t "homeassistant/#"
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
Dieser DeinMqqtUser und DeinMqqtPasswort muss mit dem übereinstimmen, was wir oben im Raspberry bereits hinterlegt haben.<br>


Nun installieren wir den Mqqt Broker:<br>
In Home Assistant Einstellungen/ Geräte&Dienste Integration hinzufügen drücken und nach Mqtt suchen und installieren und das offizielle Mqqt auswählen (nicht das manuelle mit den Benutzerdetails) <br>

Nun richten wir den Broker ein:<br>
Einstellungen/ Geräte&Dienste / MQTT<br><br>

Dort gibt es nun einen Integrationseintrag: "Mosquitto Mqtt Broker". Dort gehen wir auf die drei Punkte und wählen "Neu konfigueren" aus.<br>
Folgendes geben wir ein:<br>
Server: core-mosquitto<br>
Port: 1883<br>
Benutzername: DeinMqqtUser den du beim Raspberry verwendet hast in der mqtt_listener.py und in der publish_mqtt.py<br>
Passwort: DeinMqttPasswort das du beim Raspberry verwendet hast in der mqtt_listener.py und in der publish_mqtt.py<br>

<br><br><br><br>
Nun erstellen wir den Aufruf zum Orten der Google Tags<br>
Einstellungen/Automatisierungen&Szenen/Skripte/   hier auf den Button "+Skript erstellen" klicken und "Neues Skipt erstellen im Dialog auswählen<br>
nun sind wir im Editor der GUI geführt ist. Um es uns leichter zu machen, klick oben rechts aud ie drei Punkt und wähle "in YAML bearbeiten" aus<br>


Hier kannst du die Koordinaten und den Umkreis von deinem Zuhause definieren. Wenn nun der Google Tag anstatt von Koordinaten nur "Zuhause" meldet, wird dieses in Koordinaten umgewandelt, damit Home Assisant den Tracker anzeigen kann.<br>
Kopiere das Skript in den Editor 

```
alias: Google Tracker aktualisieren
sequence:
  - data:
      topic: googlefindmytools/trigger/update
      payload: "{ \"lat_home\": 31.8909428, \"lon_home\": 7.1704316, \"home_radius\": 500 }"
    action: mqtt.publish
```
speichern und ausführen. Die Google Tags sollten nun in Home Assistan angezeigt werden (Einstellungen/Geräte und Dienste/MQTT). 

Zuletzt legen wir noch eine Automatisierung ab, um den Standort alle 5 min zu aktualisieren: <br>
Einstellungen/Automatisierungen&Szenen/ auf den Button "+Automatisierung erstellen" klicken und "Neue Automation erstellen" auswählen<br>
nun sind wir im Editor der GUI geführt ist. Um es uns leichter zu machen, klick oben rechts aud ie drei Punkt und wähle "in YAML bearbeiten" aus<br>
Kopiere das Skript in den Editor <br>
```
alias: Google_Airtag
description: ""
triggers:
  - trigger: time_pattern
    minutes: /5
conditions: []
actions:
  - action: script.update_google_locations
    metadata: {}
    data: {}
mode: single
```
speichern



**So fertig sind wir**


**kleines Extra:**
Wer es noch brauchen kann hier sind drei Karten für das dashboard<br>
Einfach in das Dashboard gehen, eine irgendeine neue Karte hinzufügen und auf "im Code Editor anzeigen" gehen.<br>
Anschleißend folgenden code hinein kopieren und die Trackernamen (Airtag_1) anpassen<br>

Hier eine Karte
```
type: map
entities:
  - device_tracker.Airtag_1
  - device_tracker.Airtag_2
  - device_tracker.Airtag_3
default_zoom: 16
hours_to_show: 1
theme_mode: auto
```

Hier die Personen
```
type: tile
features_position: bottom
vertical: true
entity: device_tracker.Airtag_1
state_content:
  - state
  - last_changed
  - semantic_location
grid_options:
  rows: 2
  columns: 6
```

Hier als Markdown
```
type: markdown
title: Google Airtag Status
content: >
  **Status:**    {{ states('device_tracker.Airtag_1') }}

  **Letzter Wechsel:**  {% if states.device_tracker.naomi.last_changed %}{{
  as_timestamp(states.device_tracker.naomi.last_changed)|
  timestamp_custom('%Y-%m-%d %H:%M:%S') }}{% else %}–

  {% endif %}

  **Semantic Location:**    {{ state_attr('device_tracker.naomi',
  'semantic_location') or '–' }}

  **Letztes GPS‑Update:**    {{ state_attr('device_tracker.naomi',
  'last_updated') or '–' }}
grid_options:
  columns: 9
  rows: auto
```
```show_name: true
show_icon: true
type: button
entity: automation.google_airtag
tap_action:
  action: perform-action
  perform_action: automation.trigger
  target:
    entity_id: automation.google_airtag
  data:
    skip_condition: true
```


Viel Spaß damit 
