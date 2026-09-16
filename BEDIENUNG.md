# Dropzone · Philipp & Norman

Eigenständige statische Spielhilfe für das Dice Dropzone Tournament XII am 10.10.2026. Die bestehende PK-Stratagems-Seite bei Netlify wird nicht geändert.

## Benutzung

- **Am Tisch:** Spiel, gegnerische Disposition, Seitenrolle und unabhängig davon Zugfolge wählen. Spiel 3 verlangt die vom Gegner zugewiesene eigene Disposition.
- **Fünf Runden:** gleicher Missionsfall, getrennte und aufeinander abgestimmte Aufgaben für Norman und Philipp.
- **Armeen & Regeln:** Einheitenlegende und die neun Vorbereitungskapitel des Dossiers.
- **Missionen:** 5×5-Matrix und die 25 bereitgestellten Primärmissionswortlaute.
- **Tisch-Notizen:** automatische lokale Speicherung je Spiel/Szenario. Kein Cloud-Abgleich. Export/Import zum Übertragen; zurücksetzen fragt nach.

Karten lassen sich vergrößern. Zahlen sind Bereitstellungsanker, keine maßstäblichen Bases. Die acht Nummern erklären 12 Aufstellvorgänge der empfohlenen Standardformation; B2/T2 sind in dieser Empfehlung in Reserve, S1 im Rhino. Captains starten separat. Am Tisch alle Abstände und Modelle prüfen.

**Offline:** Bei Verbindung unten „Offlinepaket speichern“ wählen und auf die Erfolgsmeldung warten. Danach dieselbe Adresse auf demselben Gerät verwenden. Browser können gespeicherte Daten später entfernen; vor dem Turnier im Flugmodus testen. Externe Quellenlinks funktionieren nicht offline.

**Drucken:** „Karte & Plan drucken“ enthält das ausgewählte Szenario und seinen vollständigen Fünf-Runden-Plan. Unter Armeen & Regeln lässt sich das gesamte Web-Dossier drucken bzw. mit der Browserfunktion als PDF speichern. Dies ist eine Web-Druckfassung, nicht das unveränderte ursprüngliche PDF.

## Inhalt und Grenzen

Taktischer Stand: **16.09.2026 / Dossier v1.0**. Keine stille Regelaktualisierung oder neue taktische Bewertung. Regelstichtag 03.10.2026 bleibt später zu prüfen. Gegnerlisten und vollständige Sekundärmissionskarten waren nicht Teil der Vorlage. Team-Warlord noch offen, K1 nur Empfehlung. Die manuelle Punktetabelle berechnet Eingabesummen, keine Missionspunkte oder automatischen Regelentscheidungen.

Die Seite ist öffentlich. `noindex` ist eine Bitte an Suchmaschinen, kein Zugangsschutz. Lokale Notizen werden nicht hochgeladen und nicht in Szenariolinks aufgenommen. Keine Analytics, externen Schriftdateien oder serverseitigen Konten.

## Technik und Pflege

Ohne Build-Schritt: HTML, CSS und ES-Module. GitHub Pages veröffentlicht `main` / Root. Alle internen Pfade sind relativ und funktionieren unter `/Dropzone/`.

- `data/missions.json`: zehn unveränderte Missionspläne.
- `data/cases.json`: 20 Szenarien, je zwei unabhängige Ankersätze.
- `data/chapters.json`: neun unveränderte Vorbereitungskapitel.
- `data/reference.json`: Einheiten, Matrix, Quellen und Ressourcen.
- `data/words.json`: 25 englische Texte aus der bereitgestellten RTF-Datei.
- `tools/build_assets.py`: 19 Geländepläne aus der exakt per SHA-256 geprüften Original-PDF. Änderungen an der Quelle brechen ab, statt still andere Karten auszuliefern.
- `tests/`: kanonische Inhaltsprüfsummen, 134 Logiktests und Browser-Prüfungen.

Bei Inhaltsänderungen Quellenstand bewusst ändern, Prüfsummen nicht blind aktualisieren. Die ursprünglichen Texte stammen aus dem mit Philipp erarbeiteten Übergabepaket. Für die Webfassung wurde nur die technische Struktur angepasst.

Lokal: `python -m http.server 8765 --directory ..` aus dem Repository; dann `http://127.0.0.1:8765/Dropzone/` öffnen. Logik: `node --test tests/core.test.mjs`. Inhalt: `python tests/verify_content.py`. Browser: Playwright installieren und `python tests/browser_smoke.py` ausführen.

## Rücknahme

Vorheriger leerer Startstand: Commit `92d8fc6377309c91e16605f92ff22c41ef9f6d46`. Für Änderungen vorzugsweise neue Revert-Commits benutzen, nicht die Historie überschreiben. Netlify war nie Bestandteil dieser Veröffentlichung.

Inoffizielles persönliches Fanprojekt. Warhammer, Regeltexte, Namen und Geländeabbildungen gehören ihren jeweiligen Rechteinhabern. Keine Verbindung zu Games Workshop. Es wird keine pauschale Lizenz für fremde Inhalte vergeben.
