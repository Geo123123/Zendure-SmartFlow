# Zendure SmartFlow

Home-Assistant-Custom-Integration fuer eine PV-Ueberschussladung mit drei Zendure SolarFlow 2400 Pro und einem Shelly EM3.

## Regelprinzip

Zendure SmartFlow liest die Shelly-Netzleistung und steuert pro Zendure zwei `number`-Entities:

- WR-Ausgang/Bypass: wird im Automatikbetrieb immer auf `0 W` gesetzt.
- Ladeleistung: wird nur bei PV-Ueberschuss gesetzt.

Damit gilt:

- Positive Shelly-Leistung bedeutet Netzbezug.
- Negative Shelly-Leistung bedeutet Einspeisung/PV-Ueberschuss.
- Wenn kein Ueberschuss vorhanden ist, bleibt der Wechselrichter auf Bypass bzw. `0 W`.
- Erst bei echter Einspeisung wird die Akku-Ladeleistung erhoeht.
- Zielwert ist standardmaessig `30 W` Netzbezug, damit die Regelung nicht dauerhaft einspeist.

## Installation

Kopiere den Ordner `custom_components/zendure_smartflow` in den Home-Assistant-Konfigurationsordner und starte Home Assistant neu.

Danach unter **Einstellungen > Geraete & Dienste > Integration hinzufuegen** nach `Zendure SmartFlow` suchen.

## Benoetigte Entities

1. Shelly EM3 Netzleistung als Sensor, z. B. `sensor.shelly_em3_total_power`.
2. Drei Zendure WR-Ausgang/Bypass-Entities als `number`, je eine pro SolarFlow 2400 Pro.
3. Drei Zendure Ladeleistungs-Entities als `number`, je eine pro SolarFlow 2400 Pro.
4. Optional drei Zendure SOC-Sensoren, je einer pro SolarFlow 2400 Pro.

Die drei Zendure-Entities werden in der UI zeilenweise oder kommasepariert eingetragen.

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
