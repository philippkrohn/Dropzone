# PK Stratagems · Training & Fraktionskatalog v2.0

Stand der Umsetzung: 22.09.2026. Veröffentlichung erst nach grünem Releasebericht.

## Öffentliche Routen
- `/`: vertrauter Stratagembrowser mit erweitertem Matched-Play-Katalog, 24 Fraktionen und 270 Detachments; vorhandene `pk_active_v2`- und `pk_cp`-Werte bleiben erhalten.
- `/quiz/`: zehn unterschiedliche Konzepte pro Durchlauf; drei echte Schwierigkeitsstufen; Regeln, Taktik oder Mischung. Fehlertraining ergänzt bis auf zehn Fragen. Allgemeine Inhalte sind als fraktionsübergreifend bezeichnet.
- `/fraktionen/`: Fraktionsregeln zusätzlich zu Detachment-Regeln, Aufwertungen und Datasheet-Links.
- `/doubles/` und sonstige frühere Dateien: unveränderte Weiterleitung auf den vorherigen unveränderlichen Netlify-Deploy.

## Quellen und Inhaltsqualität
Der Wahapedia-CSV-Export hat den Stand 13.09.2026; die Fraktionsseiten wurden am22.09.2026 abgerufen. Der Quellenabruf ist keine Garantie, dass der Drittanbieter alle jüngsten Originaländerungen umgesetzt hat. Der EN-Wortlaut wird als solcher gekennzeichnet, Lore entfernt. `library/provenance.json` führt Quellen und Hashes. Boarding Actions, Crusade, Legends und Unbound Adversaries sind ausgeschlossen. Supplements stehen unter Space Marines. Nicht bestätigte Alt-Detachments bleiben als Archiv sichtbar, nicht im aktuellen Quiz.

Der Fragenpool enthält quellengebundene Varianten, nicht Tausende manuell verfasster Taktiksituationen. Taktikfragen sind eigenständig redaktionell; alle Alternativen sind laut Aufgabe zulässig, die Zielgröße ist ausdrücklich genannt. Rechenfragen sind vereinfachte Modelle ohne unausgesprochene Datasheet-Fähigkeiten.

Antwortvarianten sind in Form und Umfang vergleichbar; bei neuen Versuchen werden Fragen und Antwortpositionen gemischt. Richtige Werte sind nicht systematisch der Mittelwert der Zahlenoptionen. Quellen und Erklärungen erscheinen nach der Auswertung. `tests/catalog_v2.py` und `tests/training.test.mjs` prüfen Grenzen und Verteilungen, ersetzen aber keine kontinuierliche fachliche Prüfung.

## Speichern und Erweitern
Neuer Trainingsspeicher: `pkstratagems:training:v2`. Alte Quizdaten und übrige Website-Daten werden nicht gelöscht. Keine Cloud-Synchronisierung. Eine sehr enge Themenauswahl startet nur bei mindestens zehn verschiedenen Konzepten; keine erfundenen Ersatzfragen.

Neue redaktionelle Fragen: `tools/author_questions.py`; generische Source-Varianten: `tools/generate_bank.py`. Stabile IDs und conceptId verwenden. Nach Quellenänderungen Datenversion erhöhen. Die sicheren Generatoren werden für einen bewussten Release auf eingefrorene, protokollierte Inputs angewendet, nicht automatisch auf wechselnde Internettexte.

## Betrieb
Die Arbeit liegt auf `update/training-catalog-2026-09` im Repository philippkrohn/Dropzone, unter `pkstratagems/`. Die separate GitHub-Pages-Anwendung auf main und das ursprüngliche PDF bleiben unverändert.

Rollback vor v2: Netlify-Deploy `6ab1939ae68f1a942996df56`. Die Auslieferung und das Update der lokalen Auswahl müssen bei jeder Veröffentlichung getestet werden. Keine Zugangsdaten im Code. Der Release erhält seine Netlify-Proxyberechtigung ausschließlich als verschlüsselten, an Runner/Build-Hash gebundenen Umschlag.
