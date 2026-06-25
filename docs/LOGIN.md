# Anmeldung (Login mit Name und Passwort)

Echte Anmeldung mit Name oder Kürzel und Passwort. Optional: nur aktiv, wenn der
Schalter "Anmeldung erforderlich" gesetzt ist. Ohne ihn verhält sich Pinnwand wie
zuvor (passwortlose Personen-Auswahl, reines UI-Scoping).

## Bestandteile

- **Passwort je Person** (`module/auth/passwort.py`): pbkdf2-sha256 mit Zufalls-Salt,
  Format `pbkdf2_sha256$iterationen$salt$hash`, konstantzeitiger Vergleich. Nur der
  Hash wird gespeichert, nie das Passwort.
- **Sitzung** (`module/auth/persistence.py`): beim Login entsteht ein Zufalls-Token
  (`secrets.token_urlsafe`); in der DB liegt nur sein sha256-Hash mit Ablauf (30 Tage).
  Der Browser schickt ihn als Header `X-Pinnwand-Sitzung`.
- **Durchsetzung** (`app/main.py` -> `module/auth/dienst.py:zugriff_pruefen`): bei aktiver
  Anmeldung braucht jede `/api`-Anfrage eine gültige Sitzung (401 sonst). Sensible
  Bereiche sind echt admin-only (403 sonst): Datensicherung/Zurücksetzen (`/api/backup`),
  Verwaltung in der Planung (Schreibzugriffe inkl. Passwörter), Label-Verwaltung,
  Login-Modus. Die Agenten-API (`/api/agent`) hat ihre eigene Token-Prüfung.
- **Frontend**: Login-Sperre (`Login.svelte`), Abmelden-Knopf in der Seitenleiste; die
  Rolle kommt bei aktiver Anmeldung vom Server (autoritativ), nicht aus dem
  Personen-Dropdown.

## Einrichten

1. In der **Planung** je Person ein Passwort setzen (nur Admins). Mindestens eine
   Admin-Person braucht ein Passwort.
2. In den **Einstellungen** den Schalter **"Anmeldung erforderlich"** aktivieren. Das
   Aktivieren wird blockiert, solange kein Admin ein Passwort hat (Aussperr-Schutz).

## Anmelden / Abmelden

- Anmelden: Name oder Kürzel + Passwort auf der Login-Sperre.
- Abmelden: Knopf unten in der Seitenleiste ("... abmelden").

## Notausgang

Sollte die Anmeldung versehentlich aussperren, deaktiviert die Umgebungsvariable
`PINNWAND_LOGIN_AUS=1` die Anmeldepflicht (Recovery), bis ein Admin sie wieder
einrichtet.
