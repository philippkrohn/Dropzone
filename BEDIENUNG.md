# Dropzone · Philipp & Norman

Eigenständige statische Spielhilfe für das Dice Dropzone Tournament XII am 10.10.2026. Die bestehende PK-Stratagems-Seite bei Netlify wird nicht geändert.

## Benutzung

- **Am Tisch:** Spiel, gegnerische Disposition, Seitenrolle und unabhängig davon Zugfolge wählen. Spiel 3 verlangt die vom Gegner zugewiesene eigene Disposition.
- **Fünf Runden:** gleicher Missionsfall, getrennte und aufeinander abgestimmte Aufgaben für Norman und Philipp.
- **Armeen & Regeln:** Einheitenlegende und die neun Vorbereitungskapitel des Dossiers.
- **Missionen:** 5×5-Matrix und die 25 bereitgestellten Primärmissionswortlaute.
- **Tisch-Notizen:** automatische lokale Speicherung je Spiel/Szenario. Kein Cloud-Abgleich. Export/Import zum Übertragen; zurücksetzen fragt nach.

Karten lassen sich vergrößern. Zahlen sind Bereitstellungsanker, keine maßstäblichen Bases. Die acht Nummern erklären zehn Aufstellvorgänge der empfohlenen Standardformation; B2/T2 sind in Reserve, S1 im Rhino. K1 führt V1 und K2 führt V2 ab Spielbeginn: Anker 7/8 stehen jeweils für eine Vierer-Einheit mit 355 Punkten. T1/T2 tragen je drei Guardian Spears ohne Vexilla. Am Tisch alle Abstände und Modelle prüfen.

**Offline:** Nach dem Listenupdate die Seite bei bestehender Verbindung neu laden. Unten „Offlinepaket speichern / aktualisieren“ wählen und auf die Erfolgsmeldung warten. Danach dieselbe Adresse auf demselben Gerät verwenden. Browser können gespeicherte Daten später entfernen; vor dem Turnier im Flugmodus testen. Externe Quellenlinks funktionieren nicht offline.

**Drucken:** „Karte & Plan drucken“ enthält das ausgewählte Szenario und seinen vollständigen Fünf-Runden-Plan. Unter Armeen & Regeln lässt sich das gesamte Web-Dossier drucken bzw. mit der Browserfunktion als PDF speichern. Dies ist eine Web-Druckfassung, nicht das unveränderte ursprüngliche PDF.

## Inhalt und Grenzen

Taktischer Stand: **18.09.2026 / Web v1.1**, angepasst an Philipps neue Custodes-Liste. Regel- und Missionsbasis weiterhin 16.09.2026; keine allgemeine Regelaktualisierung. Das ursprüngliche PDF bleibt unverändert auf v1.0. Regelstichtag 03.10.2026 bleibt später zu prüfen. Gegnerlisten und vollständige Sekundärmissionskarten waren nicht Teil der Vorlage. K1 ist Warlord laut neuem Custodes-Export; die Team-Warlord-Festlegung mit Norman abgleichen. Die manuelle Punktetabelle berechnet Eingabesummen, keine Missionspunkte oder automatischen Regelentscheidungen.

Die Seite ist öffentlich. `noindex` ist eine Bitte an Suchmaschinen, kein Zugangsschutz. Lokale Notizen werden nicht hochgeladen und nicht in Szenariolinks aufgenommen. Keine Analytics, externen Schriftdateien oder serverseitigen Konten.

## Technik und Pflege

Ohne Build-Schritt: HTML, CSS und ES-Module. GitHub Pages veröffentlicht `main` / Root. Alle internen Pfade sind relativ und funktionieren unter `/Dropzone/`.

- `data/missions.json`: zehn auf die neue Formation angepasste Missionspläne.
- `data/cases.json`: 20 Szenarien, je zwei unabhängige Ankersätze.
- `data/chapters.json`: neun aktualisierte Vorbereitungskapitel.
- `data/reference.json`: Einheiten, Matrix, Quellen und Ressourcen.
- `data/words.json`: 25 englische Texte aus der bereitgestellten RTF-Datei.
- `tools/build_assets.py`: 19 Geländepläne aus der exakt per SHA-256 geprüften Original-PDF. Änderungen an der Quelle brechen ab, statt still andere Karten auszuliefern.
- `tests/`: kanonische Inhaltsprüfsummen, 134 Logiktests und Browser-Prüfungen.

Bei Inhaltsänderungen Quellenstand bewusst ändern, Prüfsummen nicht blind aktualisieren. Die ursprünglichen Texte stammen aus dem mit Philipp erarbeiteten Übergabepaket. v1.1 ändert ausdrücklich die vom Listenwechsel betroffenen Strategien und Formationen. Missionswortlaute, Wertungsbedingungen und Punktegrenzen bleiben unverändert.

Lokal: `python -m http.server 8765 --directory ..` aus dem Repository; dann `http://127.0.0.1:8765/Dropzone/` öffnen. Logik: `node --test tests/core.test.mjs`. Inhalt: `python tests/verify_content.py`. Browser: Playwright installieren und `python tests/browser_smoke.py` ausführen.

## Rücknahme

Vorheriger leerer Startstand: Commit `92d8fc6377309c91e16605f92ff22c41ef9f6d46`. Für Änderungen vorzugsweise neue Revert-Commits benutzen, nicht die Historie überschreiben. Netlify war nie Bestandteil dieser Veröffentlichung.

Inoffizielles persönliches Fanprojekt. Warhammer, Regeltexte, Namen und Geländeabbildungen gehören ihren jeweiligen Rechteinhabern. Keine Verbindung zu Games Workshop. Es wird keine pauschale Lizenz für fremde Inhalte vergeben.

## Listenrevision v1.1

Beide Captains sind Start-Leader; für den Startanschluss keine CP einplanen. Eine Bike-Formation (355) plus Allarus (165) wären 520 Punkte Reserve und überschreiten die 500-Punkte-Spielergrenze. Priorität: Philipp entfernt wertungsrelevante Gegner, Norman stellt Aktionshelfer und Halter. Custodes übernehmen erforderliche Missionsarbeit, wenn nur sie die entscheidenden Punkte erreichen können.

Lokale Notizschlüssel und Ressourcen-Reihenfolge sind unverändert. Beim Service-Worker-Update werden nur unveränderte Karten übernommen, keine alten Regeln oder Strategiedaten. Bestehende eigene Notizen auf überholte Solo-Captain-Pläne prüfen; die Website löscht sie nicht.

Rollback-Ausgang für diese Revision: `ebb70f4320c295ecd4821d65c2692b73b68d8733`. Eine Rücknahme als neuen Commit veröffentlichen und dabei die Offline-Cache-Version erneut erhöhen.
