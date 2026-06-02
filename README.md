# Zendure SmartFlow

Home-Assistant-Custom-Integration fuer eine PV-Ueberschussladung mit drei Zendure SolarFlow 2400 Pro und einem Shelly EM3.

## Regelprinzip

Zendure SmartFlow liest die Shelly-Netzleistung aus Home Assistant und steuert die drei Zendure-Geraete direkt ueber die lokale ZenSDK-HTTP-API.

- Status lesen: `GET http://<ip>/properties/report`
- Werte setzen: `POST http://<ip>/properties/write`
- Ohne PV-Ueberschuss: `acMode=2`, `outputLimit=0`, `inputLimit=0`
- Mit PV-Ueberschuss: `acMode=1`, `outputLimit=0`, `inputLimit=<Ueberschussanteil>`
- `smartMode=1` wird bei Schreibbefehlen gesetzt, damit haeufige Regelbefehle nicht unnoetig dauerhaft gespeichert werden.

Die Shelly-Netzleistung muss positiv bei Netzbezug und negativ bei Einspeisung sein.

## Installation

Kopiere den Ordner `custom_components/zendure_smartflow` in den Home-Assistant-Konfigurationsordner und starte Home Assistant neu.

Danach unter **Einstellungen > Geraete & Dienste > Integration hinzufuegen** nach `Zendure SmartFlow` suchen.

## Benoetigte Daten

1. Shelly EM3 Netzleistung als Sensor, z. B. `sensor.shelly_em3_total_power`.
2. IP-Adresse und Seriennummer jedes Zendure SolarFlow 2400 Pro.

Die drei Zendure-Geraete werden in der UI zeilenweise im Format `IP,SERIENNUMMER` eingetragen:

```text
192.168.1.41,WOB123456789
192.168.1.42,WOB123456790
192.168.1.43,WOB123456791
```

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
