# APOS-Handbuch für das Thekenpersonal

[Dokumentationsübersicht](../README.md) · [English](../en/STAFF.md) · [Gästehandbuch](GUEST.md) · [Administrationshandbuch](ADMIN.md)

Für Konten mit der Rolle **Staff** oder **Admin**, Stand APOS 0.6. APOS erfasst Zahlungen; das Geld wird separat entgegengenommen. APOS verarbeitet keine Kartenzahlungen, erstellt keine zertifizierten Fiskalbelege und unterstützt keine Erstattungen oder Zahlungsstornos. Beachten Sie die vereinbarten Vereinsabläufe und die [dokumentierten Einschränkungen](../COMPLIANCE.md).

## 1. Schicht beginnen

1. Öffnen Sie die von der Administration mitgeteilte APOS-Adresse. Die öffentliche Projektwebsite ist keine Kasseninstanz Ihres Vereins.
2. Melden Sie sich mit Ihrem persönlichen Benutzernamen und Passwort an. Mitgliedsnummern und private Gastcodes sind keine Zugangsdaten für das Personal.
3. Wählen Sie bei Bedarf **Persönliches Menü → Sprache → Deutsch → Anwenden**.
4. Prüfen Sie unter **Offene Bons** die Währung. Lassen Sie diese vor neuen Bons durch Admin korrigieren. Bestehende Bons behalten ihre Währung.
5. Prüfen Sie das Sortiment und testen Sie einen Gastlink mit einem Telefon. Melden Sie fehlende Produkte an Admin; Staff kann das Sortiment nicht ändern.

Staff darf Bons öffnen/fortsetzen, Gäste ohne Mitgliedschaft anlegen, Bestellungen aufnehmen, zulässige Positionen stornieren, Zahlungen erfassen sowie Zahlungsbelege und Berichte ansehen. Konten, Profilverwaltung, Sortiment und Einstellungen sind Admin vorbehalten.

## 2. Den richtigen Bon öffnen

**Mitglied:** Suchen Sie unter **Offene Bons → Mitglied suchen** nach Name oder Mitgliedsnummer. Wählen Sie das Mitglied und **Bon öffnen**. Ein bereits offener Bon dieses Mitglieds wird fortgesetzt. Fehlende Mitglieder legt Admin an.

**Gast ohne Mitgliedschaft:** Wählen Sie **Gast hinzufügen**. APOS erzeugt sofort ein Profil mit zufälligem Namen, eindeutiger dauerhafter Gastnummer und einem neuen Bon. Merken Sie sich die Gastnummer: Namen können mehrfach vorkommen oder geändert werden. Ein echter Name ist nicht erforderlich. Ein Passwortkonto wird dadurch nicht erstellt.

**Vorhandener Bon:** Nutzen Sie **Bon suchen** und öffnen Sie die passende Karte. Prüfen Sie Name, Mitglieds- oder Gastnummer und Währung. Der Kartenbetrag ist die Bestellsumme und nicht zwingend die Restschuld. Prüfen Sie im Bon den **Offenen Betrag**.

## 3. Bestellung aufnehmen

1. Öffnen Sie den Bon des richtigen Gastes.
2. Nutzen Sie bei Bedarf **Produkt suchen**, stellen Sie die Menge ein und tippen Sie das Produkt an. Mengen müssen ganze Zahlen von 1 bis 999 sein.
3. Prüfen Sie die Positionen sowie **Bestellsumme**, **Bisher bezahlt** und **Offener Betrag**.
4. Prüfen Sie vor der Ausgabe von Alkohol das Alter. Die Produktkennzeichnung ersetzt keine Altersprüfung. Beachten Sie die vereinsinternen Abläufe für Lebensmittel, Allergene und Ausschank.

Bestellbar sind nur aktive und vorrätige Produkte. Verschwindet ein Produkt oder wird die Bestellung abgewiesen, aktualisieren Sie die Seite und lassen Sie die Verfügbarkeit prüfen. Spätere Preisänderungen verändern bereits bestellte Positionen nicht.

### Fehler korrigieren

Vor der ersten Zahlung öffnen Sie **Entfernen**, tragen einen nachvollziehbaren **Stornogrund** ein und wählen **Position stornieren**. Die ursprüngliche Position und das Storno bleiben erhalten. Stornierte Positionen werden nicht mehr in den offenen Betrag eingerechnet.

Nach der ersten Zahlung sind Positionsstornos gesperrt, auch wenn der Bon offen bleibt. Weitere Bestellungen sind möglich. Bei falschen Zahlungen oder Korrekturen nach einer Zahlung beteiligen Sie die Administration gemäß dem Abstimmungsverfahren des Vereins. APOS bietet keine Erstattung und keinen Zahlungsstorno. Löschen oder ändern Sie keine Datenbankeinträge, um Beträge passend zu machen.

**Leeren Bon stornieren** ist nur möglich, wenn keine unstornierten Positionen vorhanden sind. Der Gastzugang endet sofort. Bei einem unbezahlten, nicht leeren Bon müssen zuerst alle Positionen mit Begründung storniert werden.

## 4. Privaten Gastzugang übergeben

Öffnen Sie im Bon den Abschnitt für den Gastzugang mit QR-Code. Lassen Sie den Gast den Code scannen oder übergeben Sie den privaten Link/Code. Unter `/view` an der Vereinsadresse lässt sich der Code auch eingeben. Neue Vier-Wort-Codes akzeptieren Leerzeichen und unterschiedliche Groß-/Kleinschreibung.

Jeder mit diesem Code kann den Bon aufrufen und freigeschaltete Gastfunktionen nutzen. Geben Sie ihn nur dem richtigen Gast; das gilt auch für Ausdrucke. Der Zugang gilt während des offenen Bons und 24 Stunden nach vollständiger Begleichung, sofern er nicht zuvor durch erfolgreichen E-Mail-Versand oder Stornierung endet. Das Einklappen des QR-Bereichs ist kein Zugriffsschutz.

Gäste müssen ihre Seite aktualisieren, um neue Bestellungen und Zahlungen zu sehen. Admin steuert die optionale Gastbestellung. Gäste können weder Positionen stornieren noch Zahlungen erfassen. Alkohol wird über das Personal bestellt.

## 5. Zahlung entgegennehmen und erfassen

1. Prüfen Sie Gast und **Offenen Betrag**.
2. Nehmen Sie Bargeld entgegen oder schließen Sie die Zahlung am separaten Kartenterminal ab.
3. Wählen Sie unter **Zahlung** die tatsächlich verwendete Zahlungsart: **Bar** oder **Karte** (externes Terminal).
4. Tragen Sie den tatsächlich auf den Bon gezahlten Betrag ein. **Gesamter Restbetrag** übernimmt die ganze Restschuld; für einen kleineren Betrag nutzen Sie die Teilzahlung. Prüfen Sie das Betragsfeld vor dem Absenden.
5. Wählen Sie **Zahlung erfassen**. Warten Sie auf den Beleg und prüfen Sie Betrag, Zahlungsart und Restschuld.

Beispiel: Bei €18,00 Bestellsumme erhält das Personal €10,00. Erfassen Sie diese einmal; €8,00 bleiben offen. Nach Eingang der restlichen €8,00 erfassen Sie diese. Die vollständige Begleichung schließt den Bon und startet die 24-stündige Gastzugangsfrist.

Beträge über der Restschuld werden abgewiesen. Erfassen Sie den auf den Bon angerechneten Betrag, nicht das übergebene Bargeld vor Rückgeld. Die Betragsschaltflächen ziehen kein Geld ein. Bei einer Zeitüberschreitung nicht erneut kassieren: Prüfen Sie zuerst **Zahlungsbelege** und Bon. APOS schützt vor Wiederholung desselben Zahlungsformulars; ein frisch geladenes Formular ist ein neuer Zahlungsauftrag.

## 6. Zahlungsbelege und Schichtende

Unter **Zahlungsbelege** finden Sie gespeicherte Zahlungsvorgänge. Drucken oder speichern Sie den Beleg über die Druckfunktion des Browsers als PDF. Jeder Beleg zeigt den Stand zum Zahlungszeitpunkt. Ein früher Teilzahlungsbeleg kann deshalb vom späteren Bon abweichen. Das aktuelle Profilfoto kann angezeigt werden. Ein noch gültiger privater QR-Code/Link kann auf dem Beleg stehen; behandeln Sie Ausdrucke entsprechend vertraulich. Diese Zusammenfassungen sind keine zertifizierten Fiskalbelege.

Wählen Sie unter **Berichte** das UTC-Start- und Enddatum und anschließend die Berichtsanzeige oder den CSV-Download. Beide gewählten Kalendertage sind enthalten. Bestellsummen umfassen unbezahlte Bestellungen und schließen stornierte Positionen aus. Zahlungssummen erfassen die im Zeitraum eingetragenen Zahlungen einschließlich Teilzahlungen; EUR und USD bleiben getrennt. UTC-Tage können vom lokalen Geschäftstag abweichen. CSV-Geldspalten mit `_cents` enthalten ganze Centbeträge. Exporte enthalten keine Mitgliedsnamen, Bon-IDs oder Gastcodes; kleine Gruppen oder Produktnamen können dennoch Rückschlüsse ermöglichen.

Übergeben Sie offene Beträge und ungeklärte Fehler, veranlassen Sie eine Sicherung durch die zuständige Person und wählen Sie **Persönliches Menü → Abmelden**. Schalten Sie den Rechner nicht ab, solange Gastzugänge noch benötigt werden.

## Probleme im Betrieb

| Problem | Vorgehen |
| --- | --- |
| Mitglied/Bon nicht gefunden | Suche leeren, Mitglieds- oder Gastnummer prüfen; fehlende Profile mit Admin klären. |
| Produkt nicht verfügbar | Seite aktualisieren; Admin prüft Aktivierung und Vorratsstatus. |
| Sitzung/Formular abgelaufen | Gegebenenfalls neu anmelden, Seite neu laden und vor Wiederholung den bisherigen Erfolg prüfen. |
| Telefon kann QR nicht öffnen | Admin prüft Gastadresse, Netzwerk, HTTPS und Server. Localhost auf dem Telefon bezeichnet das Telefon selbst. |
| Gastlink beendet | Begleichung, Ablaufzeit und E-Mail-Versand prüfen. Personalbelege bleiben erhalten. |
| Falsche Zahlung erfasst | Aufzeichnungen erhalten und eskalieren; kein Erstattungs-/Zahlungsstornoverfahren in APOS. |
| Speicher-/Datenbankfehler | Weitere Zahlungserfassung stoppen und zuständige Person informieren. Datenbank nicht löschen. |
