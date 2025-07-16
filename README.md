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

Es könnte nun der Fehler "undetected_chromedriver" kommen. In diesem Fall muss der Chromedriver separat installiert werden

Zuerst muss man die Chrome Version herausfinden: Öffne Chrome  und gib  chrome://settings/help in die Adresszeile ein. Notiere die Version, z.B. 114.0.5735.199 
Nun muss man den passenden ChromeDriver herunterladen: https://googlechromelabs.github.io/chrome-for-testing/. Wenn die erste Zahl z.B. 144 der Versionnummer übereinstimmt, reicht das.

Entpacke die datei chromedriver.exe nach C:\Tools\chromedriver\<br>
Nun müssen wir noch den dateipfad anpassen, damit GoogleFindMyTools weiß wo dieser liegt. 

