# Zendure SmartFlow

Home-Assistant-Custom-Integration fuer eine PV-Ueberschussladung mit drei Zendure SolarFlow 2400 Pro und einem Shelly EM3.

## Regelprinzip

Zendure SmartFlow liest die Shelly-Netzleistung aus Home Assistant und regelt drei Zendure-Geraete auf Ueberschussladung.

- Status lesen: `GET http://<ip>/properties/report`
- Stellbefehle: wahlweise lokal per HTTP oder ueber Home-Assistant-MQTT
- Ohne PV-Ueberschuss: `acMode=2`, `outputLimit=0`, `inputLimit=0`
- Mit PV-Ueberschuss: `acMode=1`, `outputLimit=0`, `inputLimit=<Ueberschussanteil>`
- `smartMode=0` wird gesetzt, wenn beide Limits `0` sind.
- `smartMode=1` wird gesetzt, sobald geladen wird.

Die Shelly-Netzleistung muss positiv bei Netzbezug und negativ bei Einspeisung sein.

## Steuerwege

### HTTP

HTTP schreibt direkt an die lokale ZenSDK-API:

```text
POST http://<ip>/properties/write
```

Geraeteformat:

```text
192.168.1.41,WOB123456789
192.168.1.42,WOB123456790
192.168.1.43,WOB123456791
```

### MQTT

MQTT nutzt den Home-Assistant-MQTT-Dienst `mqtt.publish` und die Zendure-HA Topic-Struktur:

```text
iot/<productKey>/<deviceId>/properties/write
```

Geraeteformat:

```text
192.168.1.41,WOB123456789,PRODUCTKEY1,DEVICEID1
192.168.1.42,WOB123456790,PRODUCTKEY2,DEVICEID2
192.168.1.43,WOB123456791,PRODUCTKEY3,DEVICEID3
```

Auch im MQTT-Modus wird die IP gebraucht, weil SmartFlow den aktuellen Status per lokaler ZenSDK-HTTP-API liest.

## Installation

Kopiere den Ordner `custom_components/zendure_smartflow` in den Home-Assistant-Konfigurationsordner und starte Home Assistant neu.

Danach unter **Einstellungen > Geraete & Dienste > Integration hinzufuegen** nach `Zendure SmartFlow` suchen.

## Benoetigte Daten

1. Shelly EM3 Netzleistung als Sensor, z. B. `sensor.shelly_em3_total_power`.
2. IP-Adresse und Seriennummer jedes Zendure SolarFlow 2400 Pro.
3. Fuer MQTT zusaetzlich `productKey` und `deviceId` je Geraet.

## Wichtige Parameter

- `Ziel-Netzleistung`: positiver Zielwert fuer leichten Netzbezug.
- `Totband`: erst bei Einspeisung unterhalb `-Totband` wird geladen.
- `Maximale Ladeleistung je Zendure`: Sicherheitslimit pro SolarFlow.
- `Mindest-Aenderung`: verhindert staendige kleine Setzbefehle.
- `Reaktionsfaktor`: hoeher reagiert schneller, niedriger ruhiger.
- `SOC-Reserve`: Stoppt Ladung oberhalb von `100 - SOC-Reserve`.

## Services

`zendure_smartflow.force_update`

Fuehrt sofort einen Regelzyklus aus.

`zendure_smartflow.set_enabled`

Aktiviert oder pausiert die Regelung.
