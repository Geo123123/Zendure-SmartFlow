# Zendure SmartFlow

Home-Assistant-Custom-Integration fuer eine PV-Regelung mit drei Zendure SolarFlow 2400 Pro und einem Shelly EM3.

## Regelprinzip

Zendure SmartFlow liest die Shelly-Netzleistung und setzt drei Zendure-`number`-Entities fuer die Ausgangsleistung.

- Positive Shelly-Leistung bedeutet Netzbezug.
- Negative Shelly-Leistung bedeutet Einspeisung.
- Zielwert ist standardmaessig `30 W` Netzbezug.
- Im Totband wird nichts geaendert, damit die Regelung nicht pendelt.
- Optional beruecksichtigt SmartFlow je Zendure einen SOC-Sensor und stoppt Geraete unterhalb der Reserve.

## Installation

Kopiere den Ordner `custom_components/zendure_smartflow` in den Home-Assistant-Konfigurationsordner und starte Home Assistant neu.

Danach unter **Einstellungen > Geraete & Dienste > Integration hinzufuegen** nach `Zendure SmartFlow` suchen.

## Benoetigte Entities

1. Shelly EM3 Netzleistung als Sensor, z. B. `sensor.shelly_em3_total_power`.
2. Drei Zendure Ausgangsleistungs-Entities als `number`, je eine pro SolarFlow 2400 Pro.
3. Optional drei Zendure SOC-Sensoren, je einer pro SolarFlow 2400 Pro.

Die drei Zendure-Entities werden in der UI zeilenweise oder kommasepariert eingetragen.

## Wichtige Parameter

- `Ziel-Netzleistung`: positiver Zielwert fuer leichten Netzbezug.
- `Totband`: Bereich, in dem keine Anpassung erfolgt.
- `Maximale Ausgangsleistung je Zendure`: Sicherheitslimit pro SolarFlow.
- `Mindest-Aenderung`: verhindert staendige kleine Setzbefehle.
- `Reaktionsfaktor`: hoeher reagiert schneller, niedriger ruhiger.
- `SOC-Reserve`: unterhalb dieser Reserve wird ein Geraet nicht entladen.

## Services

`zendure_smartflow.force_update`

Fuehrt sofort einen Regelzyklus aus.

`zendure_smartflow.set_enabled`

Aktiviert oder pausiert die Regelung.
