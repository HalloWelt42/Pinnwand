# Sicherheitsmodell

Pinnwand ist als lokale Einzelplatz-Anwendung gedacht. Dieses Dokument hält das
Bedrohungsmodell, die getroffenen Maßnahmen und die bewusst akzeptierten
Restrisiken fest. Es ist das Ergebnis mehrerer Audit-Runden.

## Bedrohungsmodell

- Standardbetrieb: Backend und Oberfläche laufen auf demselben Rechner, gebunden
  an 127.0.0.1. Wer lokalen Code ausführt, hat ohnehin direkten Zugriff auf die
  Datei pinnwand.db; die lokale Bindung ist daher die zentrale Vertrauensgrenze.
- Relevante Angreifer: eine fremde Webseite im Browser des Nutzers (Drive-by),
  ein bösartiges lokales Werkzeug und ein KI-Werkzeug mit eingeschränktem Token.

## Authentifizierung

- Die Kanban-Kern-API und die Sicherungs-API sind bewusst ohne Token nutzbar.
  Das entspricht dem lokalen Modell: Sie sind nur über die localhost-Bindung
  erreichbar und nicht stärker geschützt als die Datenbankdatei selbst.
- Die Agenten-API (/api/agent) ist authentifiziert: Bearer-Token je Werkzeug mit
  den Scopes read, write und admin. Token werden nur als SHA-256-Hash gespeichert
  (hohe Entropie, pw_ plus 32 Byte Zufall); der Klartext wird genau einmal bei
  der Erstellung angezeigt. Verwaltung (anlegen, auflisten, widerrufen) erfordert
  admin. Ein optionales Bootstrap-Token (PINNWAND_AGENT_TOKEN) gilt als admin und
  wird timing-sicher verglichen.
- Der MCP-Server ist opt-in (PINNWAND_MCP), läuft als fester Akteur mit read und
  write (nie admin) und folgt der localhost-Bindung.

## Maßnahmen

- localhost-Bindung: start.sh übergibt PINNWAND_BIND an uvicorn (--host). Standard
  ist 127.0.0.1. Die deklarierte Grenze ist damit auch die wirksame Grenze.
- CORS: nur die bekannte Oberfläche (localhost auf dem Frontend-Port) ist erlaubt,
  kein offenes Sternchen. Über PINNWAND_CORS_ORIGINS erweiterbar. Damit kann eine
  fremde Webseite die Antworten der lokalen API nicht auslesen.
- Sicherungen enthalten niemals echte Geheimnisse: nur die Vorlage .env.muster,
  nie die echte .env. Ein weitergegebener Snapshot leakt keine Token oder Schlüssel.
- Spracheingabe-Upload ist auf 25 MB begrenzt (413 statt unbegrenztem Einlesen).
- Idempotenz-Schlüssel sind an den Akteur gebunden; ein Akteur kann den Schlüssel
  eines anderen weder einsehen noch dessen Schreibaktion unterdrücken.
- SQL durchgängig parametrisiert; dynamische Spalten-/Tabellennamen stammen aus
  Whitelists bzw. aus sqlite_master, nie aus Eingaben.
- Datei-Downloads nutzen IDs ausschließlich als Datenbankschlüssel; Dateinamen
  werden serverseitig erzeugt. Beim Entpacken von Snapshots werden Einträge mit
  Path(name).name neutralisiert (kein Zip-Slip).
- Wiederherstellung prüft die entpackte Datenbank per integrity_check und sichert
  vorher automatisch den aktuellen Stand.
- Frontend: Markdown wird über Svelte-Text-Interpolation gerendert (rohes HTML
  wird escaped); Mermaid-SVG wird mit DOMPurify gesäubert, KaTeX läuft ohne Trust.
- Geheimnisse werden nicht geloggt; das Audit-Log speichert keine Klartext-Token.

## Akzeptierte Restrisiken (lokaler Betrieb)

- Jeder lokale Prozess kann die unauthentifizierte Kanban- und Sicherungs-API
  nutzen. Das ist im lokalen Modell gleichbedeutend mit dem direkten Dateizugriff
  und wird akzeptiert.
- Das Audit-Log liegt in derselben Datenbank und ist nicht manipulationssicher.

## Betrieb außerhalb von localhost

Wird das Backend bewusst an eine nicht-lokale Adresse gebunden (PINNWAND_BIND),
sind die Kanban- und Sicherungs-API ungeschützt im Netz erreichbar. Das ist nicht
vorgesehen. In diesem Fall muss zwingend ein vorgelagerter Reverse-Proxy mit
eigener Authentifizierung betrieben werden; die Anwendung selbst schützt diese
Endpunkte nicht.
