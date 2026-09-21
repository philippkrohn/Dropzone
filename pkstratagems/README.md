# PK Stratagems – Quiz-Training

Zusätzlicher Bereich unter `/quiz/` auf **pkstratagems.netlify.app**. Kein Ersatz der bestehenden Stratagem- oder Doubles-Anwendung und keine Änderung des PDFs.

## Struktur

- `quiz/index.html`, `quiz/style.css`, `quiz/app.mjs`: zugängliche generische Oberfläche.
- `quiz/core.mjs`: Datenprüfung, Suche, Auswertung und sichere Wiederaufnahme.
- `quiz/data/index.json`: Quizkatalog mit Filtern.
- `quiz/data/<quiz-id>.json`: jeweils ein Quiz, unabhängig von Spielernamen und Armeelistenkürzeln.
- `tools/update_catalog.mjs`: Katalog aus allen Quizdateien erzeugen.
- `tests/core.test.mjs`, `tests/browser.py`: Logik und Browserprüfung.

## Ein weiteres Quiz ergänzen

1. Quiz-JSON in `quiz/data/` hinzufügen. Dateiname = `id + '.json'`.
2. Stabile Frage-/Antwort-IDs, Fraktion, Detachment, Thema, Schwierigkeit und Regelstand angeben. `correctOptionId` muss auf genau eine vorhandene Antwort zeigen.
3. Jede Frage braucht Erklärung und gültige `sourceIds`. Quellenstände ausdrücklich nennen. Keine unbekannten FAQs durch Erinnerung ergänzen.
4. Bei inhaltlicher Änderung `revision` erhöhen. So werden alte Antworten nicht mit einer neuen Lösung vermischt.
5. `node tools/update_catalog.mjs` und `node --test tests/core.test.mjs` ausführen.
6. Vollständigen aktuellen Site-Bestand mit den zusätzlichen Quizdateien veröffentlichen, niemals nur das Quiz als Ersatz der ganzen Seite hochladen.

Es ist kein Umbau des Renderers nötig. Im Katalog erscheinen neue Fraktionen und Detachments automatisch. Der erste Umfang ist bewusst Single Choice (ein Punkt pro Frage).

## Datenspeicherung

Ausschließlich `localStorage` unter `pkstratagems:quiz:v1:<id>:<revision>`; keine Anmeldung, kein Analytics, keine Übertragung der Antworten. Der Link enthält nur die Quiz-ID. Bestehende Website- und Dropzone-Schlüssel werden nicht verändert. Bestleistungen/Versuche sind keine Cloud-Synchronisation.

## Regelbasis

Das Quiz überträgt das zuvor erarbeitete Training, verallgemeinert die personenbezogenen Fragen und nennt pro Lösung seine Quelle. Die ursprünglichen Stratagem-Daten bleiben bytegleich. Diese technische Erweiterung ist keine allgemeine Regel-Neuprüfung.

## Veröffentlichung / Erhaltung des bisherigen Standes

Der vorherige Netlify-Deploy wird als unveränderter Stand für noch nicht in den lokalen Quellbestand überführte Altrouten verwendet. Eine **nicht erzwungene** Fallback-Rewrite-Regel bedient diese Routen; neue statische Dateien haben Vorrang. Dadurch bleiben auch Altrouten erhalten, die nicht aus der Startseite erschlossen werden können. Der konkrete Vorgänger wird im Deploymentbericht dokumentiert. Nicht löschen, solange die vollständige Altdateisammlung nicht migriert ist.

Die Netlify-Veröffentlichung verwendet ausschließlich kurzlebige, durch das aktivierte Plugin autorisierte, sitespezifische Proxy-Berechtigungen. Geheimnisse liegen niemals im Quelltext. Für einen einmaligen Remote-Upload werden sie mit einem nur im laufenden Runner vorhandenen privaten Schlüssel verschlüsselt übertragen; der öffentliche Schlüssel und die verschlüsselte Transportdatei enthalten keine offen nutzbaren Zugangsdaten.
