# APOS-Administrationshandbuch

[Dokumentationsübersicht](../README.md) · [English](../en/ADMIN.md) · [Personalhandbuch](STAFF.md) · [Gästehandbuch](GUEST.md)

Für Betreiber und Konten mit der Rolle **Admin**, Stand APOS 0.6. Der Thekenbetrieb ist im Personalhandbuch beschrieben. Dieses Handbuch behandelt Installation, Einstellungen, Konten, Profile, Produkte und Wiederherstellung.

## 1. Installation vorbereiten

APOS benötigt Python ab 3.10; getestet ist Python 3.12. Laden oder klonen Sie das Projekt, öffnen Sie ein Terminal im Projektordner und führen Sie aus:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python main.py
```

Öffnen Sie `http://127.0.0.1:5000`. Terminal und Rechner müssen laufen. Mit Strg+C stoppen Sie den Server. Gespeicherte Daten bleiben bei Neustarts erhalten. Unter Windows ersetzen Sie `.venv/bin/python` durch `.venv\Scripts\python.exe`.

In einem zweiten Terminal im selben Ordner zeigen Sie das anfängliche Wiederherstellungspasswort an:

```sh
.venv/bin/python main.py password
```

Melden Sie sich als **admin** an. Nach der Migration einer älteren Installation gilt das bisherige gemeinsame Passwort für diesen Benutzernamen. Ändern Sie es und legen Sie vor dem Betrieb persönliche Staff-Konten an. Ein selbst vergebenes Passwort kann `password` nicht anzeigen.

Zum lokalen Setzen/Zurücksetzen von Wiederherstellungspasswort und Gastadresse:

```sh
.venv/bin/python main.py setup
```

Geben Sie ein Passwort mit 12–256 Zeichen zweimal und die Gastadresse ein. Der Befehl aktiviert das feste Konto `admin` wieder, stellt dessen Admin-Rolle her und macht bestehende Sitzungen ungültig. Beschränken Sie den Zugang zum Serverterminal.

## 2. Allgemeine Einstellungen und Netzwerk

Öffnen Sie **Admin → Allgemeine Einstellungen**. Setzen Sie bei Bedarf den **APOS-Untertitel** (eine Zeile, höchstens 120 Zeichen), die **Währung** und die Gastadresse/FQDN. Speichern Sie. Die Währung gilt nur für neue Mitglieder- und Gastbons; bestehende Bons und Belege behalten ihre Währung. EUR- und USD-Preise werden unabhängig gepflegt und nicht automatisch umgerechnet.

Verwenden Sie einen erreichbaren Ursprung wie `https://apos.example.org` (Platzhalter ersetzen), ohne Pfad/Abfrage. Ein bloßer Hostname bedeutet HTTPS. Ein leeres Feld verwendet den Ursprung der aktuellen Anfrage; bei Personalzugriff über localhost können dadurch unerreichbare Gastlinks entstehen. Die Einstellung verändert erzeugte Links/QR-Codes, richtet aber weder DNS, HTTPS noch Firewall/WLAN ein.

Für einen Test mit Wegwerfdaten im lokalen Netz starten Sie den Server für erreichbare Verbindungen:

```sh
.venv/bin/python main.py --host 0.0.0.0 --port 5000
```

Setzen Sie als Gastadresse die tatsächliche LAN-Adresse des Rechners mit `http://` und Port `5000`. Telefone müssen diesen Rechner erreichen können. Öffnen Sie den Port nur im vorgesehenen Netz und testen Sie den QR-Code mit einem Telefon. Diese HTTP-Testkonfiguration ist keine Anleitung zur öffentlichen Bereitstellung. Für echten Gastzugriff richten Sie HTTPS separat ein und setzen `APOS_SECURE_COOKIES=1`. Secure-Cookies funktionieren nicht über unverschlüsseltes HTTP. APOS hat keine Anmelderatenbegrenzung; veröffentlichen Sie es nicht unverändert per Portweiterleitung. Lassen Sie den Rechner laufen, solange Gastzugänge benötigt werden.

**Passwort ändern** in den allgemeinen Einstellungen ändert das Passwort des aktuell angemeldeten Admins. Erforderlich sind dessen aktuelles Passwort und zwei übereinstimmende neue Eingaben. Leere Felder erhalten das Passwort. Diese Änderung macht bestehende Sitzungen global ungültig. Ein Zurücksetzen unter Konten und Rollen betrifft dagegen die Sitzungen des bearbeiteten Kontos.

## 3. Konten und Berechtigungen

Öffnen Sie **Admin → Konten und Rollen**. Tragen Sie Benutzername, Passwort, Rolle, gegebenenfalls verknüpftes Profil und Aktivstatus ein und wählen Sie **Konto speichern**. Benutzernamen erlauben 1–80 Zeichen aus A–Z/a–z, Ziffern und `. _ @ -`; Passwörter benötigen 12–256 Zeichen.

| Rolle | Zugriff und erforderliches Profil |
| --- | --- |
| Admin | Thekenbetrieb und sämtliche Administration; kein Profil erforderlich. |
| Staff | Bons, neue Gäste ohne Mitgliedschaft, Bestellungen/Stornos, Zahlungen, Belege und Berichte; keine Administration. |
| Member | Eigener verfügbarer Bon; aktives Mitgliedsprofil erforderlich. |
| Guest | Eigener verfügbarer Bon; aktives Gastprofil ohne Mitgliedschaft erforderlich. |

Legen Sie für Member/Guest zunächst das passende Profil an und verknüpfen Sie es. Die Konten erlauben keinen Zugriff auf fremde Bons. Profilcodes und QR-Links sind keine Benutzernamen/Passwörter. Gastanlage und Mitgliederimport erzeugen keine Konten.

Über **Bearbeiten** setzen Sie Passwörter zurück, ändern Rolle/Profilverknüpfung oder deaktivieren Konten. Ein leeres Passwortfeld erhält das Passwort. Das Speichern eines bearbeiteten Kontos beendet dessen bestehende Sitzungen. Der letzte aktive Admin kann nicht deaktiviert oder herabgestuft werden; der Wiederherstellungsname `admin` ist unveränderlich. Persönliche Personalkonten sorgen für nachvollziehbare Zuordnung neuer Stornos.

## 4. Mitglieder, Gäste und Fotos

Unter **Admin → Mitglieder** tragen Sie Anzeigename und eindeutige Mitgliedsnummer ein, fügen optional ein Foto hinzu und legen das Mitglied an. Namen/Codes sind auf 120 Zeichen begrenzt. Änderungen erfolgen über **Bearbeiten**. Profile und Anmeldekonten sind getrennt.

Das Personal erzeugt Gastprofile über **Gast hinzufügen** unter Offene Bons. Admin verwaltet sie unter **Gastprofile**. Die dauerhafte Gastnummer unterscheidet gleiche/geänderte Namen. Gäste mit gültigem Link dürfen ihren eigenen Nichtmitgliedsnamen ändern, jedoch weder Mitgliedsnamen noch Gastnummer/Code.

Fotos dürfen JPEG/PNG/WebP mit höchstens 3 MiB und 20 Megapixeln sein. Sie werden als beschnittenes 256×256-JPEG ohne Bildmetadaten in SQLite gespeichert. Sie erscheinen auf aktuellen Bons/Belegen und können Bestandteil von Gast-E-Mails sein. Informieren Sie darüber in den tatsächlichen Datenschutzhinweisen. Das Entfernen eines aktuellen Fotos löscht keine Ausdrucke, E-Mail-Kopien oder Sicherungen.

Vor dem Entfernen/Archivieren deaktivieren Sie verknüpfte aktive Konten und begleichen oder stornieren offene Bons. Wählen Sie **Entfernen**, prüfen Sie die Bestätigungsseite und bestätigen Sie. Das Profil verschwindet aus aktiven Listen, das Foto wird entfernt; Finanzhistorie bleibt erhalten. Archivierte Codes dürfen nicht erneut verwendet werden. Eine automatische vollständige Profillöschung oder Aufbewahrungsfrist gibt es nicht.

### Mitglieder importieren

Wählen Sie **Mitglieder-CSV hochladen**, laden Sie die Vorlage herunter und erstellen Sie UTF-8-CSV mit `name,code` und optional `active`:

```csv
name,code,active
Alex Taylor,M001,true
Robin Lee,M002,true
```

Komma/Semikolon und UTF-8-BOM werden unterstützt. Statuswerte akzeptieren true/false, 1/0, yes/no oder ja/nein; ohne `active` gilt true. Grenzen: 500 Profile und 512 KiB. Codes müssen in der Datei unabhängig von Groß-/Kleinschreibung eindeutig sein und dürfen mit keinem vorhandenen Mitglieder-/Gastcode kollidieren, auch nicht mit archivierten.

Laden Sie hoch, prüfen Sie die Vorschau und bestätigen Sie. Die Vorschau gehört zur Browsersitzung, gilt 24 Stunden und ist einmalig nutzbar. Neue Konflikte nach der Vorschau verhindern den gesamten Import. Importiert werden nur Profile: keine Passwörter, Rollen, Fotos, Aktualisierungen bestehender Profile oder Löschungen ausgelassener Profile. Inaktive Importe bleiben gespeichert, können aber bis zur Aktivierung keine Bons/Konten erhalten.

## 5. Produkte und Verfügbarkeit

Legen Sie unter **Sortiment** Produktnamen sowie getrennte positive EUR-/USD-Preise an. Über **Bearbeiten** ändern Sie Namen/Preise und setzen die Alkoholkennzeichnung. Bestehende Positionen und Belegstände behalten ursprüngliche Produktnamen und Preise.

Kennzeichnen Sie jedes Alkoholprodukt vor Freigabe der Gastbestellung, auch neue CSV-/Demoprodukte. Neue Produkte sind zunächst nicht als Alkohol markiert. Markierte Produkte sind für Gäste nicht bestellbar, auch nicht durch direkte Formularanfragen. Das Personal muss das Alter vor dem Ausschank weiterhin prüfen.

**Deaktivieren** sperrt neue Bestellungen. **Als ausverkauft markieren** sperrt sie ebenfalls, ist aber ein eigenständiger Status. Vorrätig setzen aktiviert kein deaktiviertes Produkt. Die Kennzeichen werden manuell gepflegt und sind keine automatische Mengenverwaltung. Bestehende Bestellungen und Belege bleiben erhalten.

### Sortiment importieren oder synchronisieren

Wählen Sie **Sortiment-CSV hochladen**. Pflichtspalten: `name,price_eur,price_usd`; optional: `in_stock,active` (Standard true). Beide Währungspreise sind erforderlich:

```csv
name,price_eur,price_usd,in_stock,active
Sprudelwasser,2.50,3.00,true,true
Brezel,2.00,2.50,false,true
```

UTF-8/BOM, Komma/Semikolon und dieselben Wahrheitswerte wie beim Mitgliederimport werden unterstützt. Dezimalkommas erfordern Semikolon als Trennzeichen. Grenzen: 500 Produkte und 512 KiB. Ungültige Preise/Zeilen und doppelte Namen in der Datei verhindern den Import.

Der Standardimport ergänzt neue Produkte und weist vorhandene Namen ab. **Aufgeführte Produkte aktualisieren und fehlende Produkte als ausverkauft markieren** ordnet Namen unabhängig von Groß-/Kleinschreibung zu, aktualisiert Preise/Status, ergänzt neue Produkte und markiert ausgelassene Produkte als ausverkauft, ohne sie zu löschen. Prüfen Sie jede Vorschauaktion, besonders ausgelassene Produkte. Zwischenzeitliche Sortimentsänderungen verhindern eine veraltete Synchronisierung. Vorschauen sind sitzungsgebunden, gelten 24 Stunden und können nicht erneut verwendet werden. Bestehende Alkoholkennzeichen bleiben erhalten; neue Produkte müssen manuell klassifiziert werden.

Für Tests mit Wegwerfdaten ergänzt `main.py demo-stock` acht Beispielprodukte und überspringt vorhandene Namen. Deaktivieren Sie die Beispiele anschließend und prüfen Sie Alkoholkennzeichen vor Gastbestellungen.

## 6. Gastbestellung und E-Mail

Gastbestellungen sind standardmäßig aus. Aktivieren Sie **Gästen erlauben, ihrem eigenen Bon Produkte hinzuzufügen** erst nach Prüfung von Sortiment, Alkoholklassifikation, Bedienabläufen und Verbraucherinformationen. Deaktivieren weist auch bereits geöffnete Formulare ab. Erforderlich sind gültiger Link und offener Bon. Gäste können weder Positionen stornieren noch Alkohol bestellen.

Unter **Admin → Postausgangskonto** tragen Sie SMTP-Hostname, Port, Sicherheitsmodus, Absender und erforderliche Zugangsdaten Ihres Anbieters ein. Verwenden Sie dessen Vorgaben für STARTTLS oder implizites TLS/SSL. Unverschlüsselt ist nur für ein geeignetes lokales Relay gedacht. Aktivieren und speichern Sie ausdrücklich; unvollständige aktivierte Konfigurationen werden abgewiesen. Testen Sie mit Wegwerfdaten und einer von Ihnen kontrollierten Adresse.

Das SMTP-Passwort wird mit dem Anwendungsschlüssel verschlüsselt gespeichert. Ein leeres Feld erhält es bei gleichem Host/Benutzernamen; deren Änderung entfernt es, sofern kein neues Passwort eingegeben wird. Sichern Sie den Schlüssel passend zur Datenbank. Nach Schlüsseländerung muss das SMTP-Passwort neu eingegeben werden. Gespeicherte Passwörter werden nicht angezeigt.

Nur vollständig bezahlte, geschlossene Bons mit gültigem Link können versendet werden. Die Nachricht enthält Bestell-/Zahlungssummen und den druckbaren Anhang `bon.html`, gegebenenfalls mit aktuellem Profilfoto. Mailserverannahme beendet den Gastzugang sofort und entfernt das aktuelle Foto eines Nichtmitgliedsgastes. Buchungsdaten bleiben erhalten. Ein Versandfehler lässt den Link bis zum normalen Ablauf nutzbar. Die Annahme garantiert keine Posteingangszustellung.

Bleibt nach einem Absturz der Status `sending`, muss die zuständige technische Person vor einem Zurücksetzen die SMTP-Protokolle abgleichen. Es gibt dafür keine Admin-Schaltfläche. Nicht blind erneut senden oder improvisierte Datenbankänderungen vornehmen. Deaktivierter E-Mail-Versand verbirgt die Funktion und verhindert neue Sendungen.

## 7. Impressum, Datenschutz und Betriebsgrenzen

Öffnen Sie in Admin **Impressum** oder **Datenschutzhinweise → Vollbild bearbeiten**. Bearbeiten Sie Deutsch und Englisch getrennt, verwenden Sie Beispiele nur als Entwurf, ersetzen Sie alle Platzhalter, prüfen Sie die Vorschau und speichern Sie. Beispiele werden nicht automatisch veröffentlicht. Fehlende Übersetzungen fallen auf Englisch zurück. Der Untertitel ersetzt weder Betreiberidentität noch Pflichtangaben. Erfinden Sie keine Identität, Steuerstellung, Rechtsgrundlage oder Aufbewahrungsfrist.

Lesen Sie vor dem Betrieb die [Compliance-Bewertung](../COMPLIANCE.md). APOS ist nicht TSE-zertifiziert und nicht als eigenständige deutsche Fiskalkasse einsatzbereit. Lücken bei Zahlungserfassung, Belegen, Verbraucherbestellungen und Aufbewahrung bestehen weiterhin. Gast-QR-Codes sind keine Fiskal-QR-Codes. Finanzaufzeichnungen bleiben nach Gastablauf und Profilarchivierung erhalten. Legen Sie für den tatsächlichen Verein geeignete Zugangs-, Sicherungs-, Aufbewahrungs-, Lebensmittel-/Alkoholausschank- und Datenschutzabläufe fest. Dieses Handbuch begründet keine Rechtskonformität.

## 8. Sicherung und Wiederherstellung

Verwenden Sie einen neuen Dateinamen in einem vorhandenen geschützten Sicherungsordner:

```sh
.venv/bin/python main.py backup --output /pfad/zu/privaten-sicherungen/apos-veranstaltung.sqlite3
```

Ersetzen Sie den Beispielpfad. Die SQLite-Sicherungsfunktion funktioniert bei laufendem APOS; vorhandene Dateien werden nicht überschrieben. Kopieren Sie die Sicherung auf getrennten kontrollierten Speicher und prüfen Sie sie durch eine Wiederherstellung mit Wegwerfdaten. Die Datenbank enthält Profile/Fotos, Konten, private Codes, Bestellungen, Belege, Einstellungen und verschlüsselte Mailzugangsdaten. Sichern Sie den tatsächlich verwendeten Schlüssel (`instance/secret.key` oder sicher verwahrtes `APOS_SECRET_KEY`) getrennt und vertraulich. Bewahren Sie `instance/staff.key` auf, falls das erzeugte Wiederherstellungspasswort benötigt wird. Nichts davon gehört in Git.

Wiederherstellung:

1. APOS stoppen und die aktuelle Datenbank als Rückfallkopie erhalten.
2. Sicherung prüfen und mit privaten Dateirechten nach `instance/apos.sqlite3` beziehungsweise zum konfigurierten `APOS_DATABASE`-Pfad kopieren.
3. Gegebenenfalls passenden Schlüssel wiederherstellen und neu starten.
4. Spätere reale Zahlungen/Bestellungen vor dem Betrieb abgleichen. Auch Kontoänderungen und Gastablauf/-widerruf werden zurückgesetzt; alte Zugänge können wieder gültig werden.
5. Anmeldung, Beträge, Gastzugriff und Mailkonfiguration prüfen. Beim Wiederherstellungstest keine echten E-Mails versenden.

Überschreiben Sie nie eine laufende Datenbank. Automatische Sicherungsplanung sowie integrierte Erstattungs-/Zahlungsstornowiederherstellung sind nicht vorhanden.

## 9. Konfigurationsreferenz

| Variable | Zweck |
| --- | --- |
| `APOS_DATABASE` | SQLite-Pfad; Standard `instance/apos.sqlite3`; übergeordneter Ordner muss existieren. |
| `APOS_SECRET_KEY` | Dauerhafter Signatur-/Verschlüsselungsschlüssel; andernfalls `instance/secret.key`. |
| `APOS_STAFF_PASSWORD` | Anfängliches Wiederherstellungspasswort einer neuen Datenbank; ersetzt kein gespeichertes Passwort. |
| `APOS_PATRON_BASE_URL` | Anfängliche Gastadresse einer neuen Datenbank; spätere Änderungen über Admin/setup. |
| `APOS_SECURE_COOKIES` | Bei HTTPS auf `1` setzen; standardmäßig aus. |

Befehle: `serve` (Standard), `setup`, `password`, `demo-stock`, `backup --output PATH`; Serveroptionen: `--host`, `--port`. Verwenden Sie einen Serverprozess und eine synchronisierte Systemzeit. Der unterstützte Starter bereinigt abgelaufene Nichtmitgliedsgastfotos alle 30 Sekunden sowie beim Start/bei Anfragen. Eigene WSGI-Bereitstellungen benötigen einen geplanten Bereinigungsaufruf.

## 10. Abnahme und Fehlerbehebung

Sichern Sie vor Veranstaltungen und Updates. Prüfen Sie mit Wegwerfdaten: getrennte Admin-/Staff-Anmeldung und verweigerten Adminzugriff für Staff; Mitglieder-/Gastbons; Telefon-QR; Bestellung und begründetes Storno; Teil-/Vollzahlung mit Bar/Karte; Belegdruck; Berichte; konfigurierten Versand mit sofortigem Linkwiderruf; Sicherung/Wiederherstellung. Nach Softwareupdates führen Sie die Regressionstests aus:

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Vergessene Wiederherstellungsdaten setzen Sie lokal mit `main.py setup` zurück. Bei fehlenden Mitgliedern/Produkten prüfen Sie Profilstatus und beide Verfügbarkeitskennzeichen. Bei QR-Problemen prüfen Sie Serverbindung, echte Gastadresse, DNS/TLS, Firewall und WLAN-Isolation. Bei SMTP-Fehlern prüfen Sie Anbieterwerte, tatsächlichen Schlüssel und Protokolle, ohne Zugangsdaten offenzulegen. Bei Speicher-/Datenbankfehlern stoppen Sie weitere Zahlungserfassungen und untersuchen den Fehler, ohne Finanzhistorie zu löschen. Falsche Zahlungen werden nach Vereinsverfahren abgestimmt; APOS kann sie nicht rückgängig machen.
