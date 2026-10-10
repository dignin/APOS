# APOS-Handbuch für Gäste und Mitglieder

[Dokumentationsübersicht](../README.md) · [English](../en/GUEST.md) · [Personalhandbuch](STAFF.md)

Für Gäste und Mitglieder, die ihren eigenen Bon in APOS 0.6 aufrufen. Ein Personalkonto ist nicht erforderlich. Die verfügbaren Funktionen hängen von den Vereinseinstellungen und dem Status Ihres Bons ab.

## Ihren Bon öffnen

Bitten Sie das Personal, Ihren Bon zu öffnen und den QR-Code zu zeigen. Scannen Sie ihn mit der Kamera Ihres Telefons oder öffnen Sie den übergebenen privaten Link. Alternativ öffnen Sie die APOS-Adresse Ihres Vereins mit `/view` und geben den privaten Zugangscode ein. Neue Codes bestehen aus vier Wörtern; Leerzeichen sowie unterschiedliche Groß-/Kleinschreibung werden akzeptiert.

Verwenden Sie die tatsächliche Vereinsadresse, nicht die öffentliche APOS-Projektwebsite. Möglicherweise müssen Sie mit dem Vereins-WLAN verbunden sein. Bei Verbindungsproblemen bitten Sie das Personal, Netzwerk und Server zu prüfen.

Behandeln Sie Link und Code vertraulich. Jeder mit dem Code kann Ihren Bon aufrufen und die dafür freigeschalteten Gastfunktionen nutzen. Teilen Sie keine Bildschirmfotos mit sichtbarem Zugangscode.

### Mit einem Member- oder Guest-Passwortkonto

Melden Sie sich mit den von der Administration erhaltenen Zugangsdaten an. APOS öffnet den neuesten noch zugänglichen Bon Ihres verknüpften Profils. Der Profilcode ist kein Passwort. Ein Gastbon mit QR-Code erzeugt nicht automatisch ein Passwortkonto. Ein Konto verlängert die Bonfrist nicht und stellt den Zugang nach E-Mail-Versand nicht wieder her. Ist kein Bon verfügbar, fragen Sie das Personal.

Wählen Sie **Persönliches Menü → Sprache → Deutsch → Anwenden** für die deutsche Oberfläche. Angemeldete Kontoinhaber können sich über **Persönliches Menü → Abmelden** abmelden. Bei Zugang nur über einen Code schließen Sie die Seite und schützen den Link; das Schließen widerruft den Link nicht.

## Beträge verstehen

- **Bestellsumme**: Wert der aktuellen, nicht stornierten Bestellungen.
- **Bisher bezahlt**: vom Personal erfasste Zahlungen.
- **Offener Betrag**: noch zu zahlender Rest.

Die Positionen zeigen Produkt, Menge, Einzelpreis, Zwischensumme und Bestellzeit in UTC. Aktualisieren Sie die Seite, um neue Einträge zu sehen; sie aktualisiert sich nicht automatisch. Ein früherer Zahlungsbeleg kann einen früheren Stand zeigen.

Bei falschen Bestellungen oder Zahlungen wenden Sie sich an das Personal. Sie können keine Positionen entfernen, Preise ändern, Zahlungen erfassen oder beglichene Bons wieder öffnen.

## Selbst bestellen, falls freigeschaltet

1. Suchen Sie den Bereich zum Hinzufügen von Produkten zum Bon. Fehlt er, sind Gastbestellungen deaktiviert, der Bon ist beglichen oder ein E-Mail-Versand läuft. Bestellen Sie dann beim Personal.
2. Wählen Sie ein verfügbares Produkt und eine ganze Menge von 1 bis 999.
3. Prüfen Sie Produkt, Einzelpreis, Menge und daraus entstehenden Betrag vor **Zahlungspflichtig bestellen**. Das Absenden fügt eine zahlungspflichtige Bestellung hinzu; eine Karte wird dadurch nicht belastet.
4. Warten Sie auf die Bestätigung und prüfen Sie die neue Position, bevor Sie erneut bestellen.

Es erscheinen nur aktive, vorrätige Produkte ohne Alkoholkennzeichnung. Fragen Sie beim Personal nach Alkohol und Lebensmittel-/Allergeninformationen. Verfügbarkeit kann sich zwischenzeitlich ändern; aktualisieren Sie nach einer Ablehnung die Seite. Melden Sie Fehlbestellungen umgehend. Gäste können nicht stornieren; nach einer Zahlung kann auch das Personal Positionen nicht mehr stornieren.

## Name und freiwilliges Profilfoto

Bei aktiven Gastprofilen ohne Mitgliedschaft können Sie unter **Ihr Gastname** den erzeugten Namen ändern: 1–120 Zeichen in einer Zeile eingeben und **Name speichern** wählen. Gastnummer und privater Code bleiben gleich. Mitgliedsnamen ändert Admin.

Falls der Fotobereich verfügbar ist, laden Sie JPEG, PNG oder WebP hoch oder verwenden die Kameraoption eines unterstützten Telefons. Wählen Sie anschließend **Foto speichern**. Die Eingabe darf höchstens 3 MiB und 20 Megapixel haben. APOS beschneidet das Bild und wandelt es in ein 256×256-JPEG ohne Bildmetadaten um. Ein Foto ist freiwillig; ohne Foto werden Initialen angezeigt.

Zum Entfernen wählen Sie **Profilfoto entfernen** und speichern, ohne gleichzeitig ein neues Bild hochzuladen. Das Foto kann auf Personalbildschirmen, gespeicherten/gedruckten Bons und E-Mail-Kopien erscheinen. Diese Kopien lassen sich durch Entfernen des Fotos nicht nachträglich löschen. Lesen Sie die **Datenschutzhinweise** Ihres Vereins; richten Sie spätere Datenanfragen an den Verein.

## Bon bezahlen

Bezahlen Sie beim Personal bar oder am separaten Kartenterminal. APOS verarbeitet keine Kartenzahlung. Eine Teilzahlung lässt den Bon offen; vollständige Zahlung schließt ihn. Aktualisieren Sie die Seite und prüfen Sie den erfassten Betrag. Fragen Sie bei Bedarf nach einer gedruckten Zahlungszusammenfassung. Diese ist kein zertifizierter Fiskalbeleg.

Der private Zugang gilt normalerweise während des offenen Bons und **24 Stunden nach vollständiger Begleichung**. Die angezeigte Ablaufzeit ist UTC. Bei stornierten Bons endet er sofort. Gäste können die Frist nicht verlängern.

## Beglichenen Bon per E-Mail erhalten

Diese Funktion erscheint nur bei vollständig bezahltem, geschlossenem Bon, noch gültigem Link und vom Verein aktiviertem E-Mail-Versand.

1. Prüfen Sie Bon und Empfängeradresse sorgfältig.
2. Entfernen Sie vor dem Versand Ihr aktuelles Profilfoto, falls es nicht mitgesendet werden soll.
3. Geben Sie Ihre E-Mail-Adresse ein und wählen Sie einmal **Bon senden und Gastzugang beenden**.
4. Warten Sie auf die Bestätigungsseite. Prüfen Sie Posteingang und Spamordner auf die Nachricht mit dem druckbaren Anhang `bon.html`.

Sobald der Mailserver die Nachricht angenommen hat, wird der private Link sofort ungültig — auch bei verzögerter Zustellung oder falscher Adresse. Über diesen Link ist dann kein erneuter Versand möglich. Die Annahme durch den Mailserver garantiert keine Zustellung im Posteingang. Meldet APOS einen Versandfehler, bleibt der Link bis zum normalen Ablauf nutzbar; versuchen Sie es erneut oder fragen Sie das Personal.

Erfolgreicher Versand entfernt das aktuelle Foto eines Gastes ohne Mitgliedschaft aus der aktiven Datenbank. Andernfalls werden solche Fotos im Bereinigungslauf des laufenden Servers entfernt, sobald kein gültiger Bonlink mehr besteht. Mitgliedsfotos bleiben erhalten. Finanzaufzeichnungen bleiben beim Personal; frühere Ausdrucke, E-Mails und Sicherungen werden durch Ablauf oder Fotobereinigung nicht gelöscht.

## Hilfe

| Anzeige/Problem | Vorgehen |
| --- | --- |
| Link nicht verfügbar/abgelaufen | Code prüfen; Personal nach Fristablauf, Bonstorno oder E-Mail-Versand fragen. |
| Keine Bestellfunktion/Produkte | Personal ansprechen; Gastbestellung ist optional, Alkohol nur über Personal. |
| Veraltete Beträge | Seite aktualisieren; bei Abweichungen dem Personal die Position/Zahlung zeigen. |
| Foto abgewiesen | Unterstütztes Format und Größen-/Auflösungsgrenzen einhalten; nur eine Bildquelle wählen. |
| Formular abgelaufen | Neu laden und vor Wiederholung prüfen, ob die vorherige Aktion erfolgreich war. |
| E-Mail nach Bestätigung fehlt | Spamordner prüfen und Personal fragen. Nach Mailserverannahme ist der Link bereits beendet. |
