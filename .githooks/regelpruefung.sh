#!/usr/bin/env bash
# Regelpruefung fuer Commits und Pushes - blockiert Verstoesse gegen die Projektregeln.
# Aufruf: regelpruefung.sh <datei> [<datei> ...]
# Portabel (BSD- und GNU-grep), ASCII-only, das eigene Hook-Verzeichnis ist ausgenommen.
set -u

fehler=0
emdash=$(printf '\xe2\x80\x94'); endash=$(printf '\xe2\x80\x93')
lsq=$(printf '\xe2\x80\x98');     rsq=$(printf '\xe2\x80\x99')
ldq=$(printf '\xe2\x80\x9c');     rdq=$(printf '\xe2\x80\x9d')

# Haeufige falsche Umlaut-Ersetzungen (nur in Doku geprueft), als ganze Woerter.
UMLAUT='fuer|ueber|ueberblick|ueberschritten|koennen|koennte|muessen|moeglich|moechte'
UMLAUT="$UMLAUT|naechste|naechsten|spaeter|loeschen|schliessen|oeffnen|groesse|groesser"
UMLAUT="$UMLAUT|groesste|gross|grosse|strasse|massnahme|gemaess|waehrend|aenderung|aendern"
UMLAUT="$UMLAUT|zurueck|standardmaessig|unterstuetzen|schluessel|gebuendelt|ausfuehren"
UMLAUT="$UMLAUT|einfuehren|fuehren|fuehrt|ueblich|haeufig|taeglich|woechentlich|jaehrlich"
UMLAUT="$UMLAUT|erklaerung|erklaerungen|faellig|faelligkeit|zustaendig|vollstaendig"
UMLAUT="$UMLAUT|urspruenglich|naemlich|ungefaehr|verfuegbar|benoetigt|enthaelt|haengt"

melde() { echo "  [BLOCK] $1"; fehler=1; }
zeig()  { printf '%s\n' "$1" | sed 's/^/        /'; }

for f in "$@"; do
  [ -f "$f" ] || continue
  case "$f" in .githooks/*) continue ;; esac
  case "$f" in
    *.woff|*.woff2|*.ttf|*.otf|*.png|*.jpg|*.jpeg|*.gif|*.ico|*.webp|*.pdf|*.db|*.lock|*.map|*.min.js|*.min.css) continue ;;
  esac
  grep -Iq . "$f" 2>/dev/null || continue   # Binaerdateien ueberspringen

  base=$(basename "$f")
  case "$base" in
    .env.example|.env.muster|.env.sample|.env.template) : ;;  # Vorlagen mit Platzhaltern erlaubt
    .env|.env.*) melde "$f: echte .env-Datei darf nicht eingecheckt werden (nur .env.example/.env.muster mit Platzhaltern)" ;;
  esac
  case "$f" in *.pem|*.key|*.p12|*.keystore) melde "$f: Schluesseldatei darf nicht eingecheckt werden" ;; esac

  if out=$(grep -nIiE 'claude|anthropic|co-authored-by|generated with (claude|ai)' "$f" 2>/dev/null); then
    melde "$f: KI-/Claude-/Co-Authored-Referenz"; zeig "$out"
  fi
  if out=$(LC_ALL=C grep -nF -e "$emdash" -e "$endash" -e "$lsq" -e "$rsq" -e "$ldq" -e "$rdq" "$f" 2>/dev/null); then
    melde "$f: typografisches Sonderzeichen (Em-/En-Dash oder geschweiftes Anfuehrungszeichen)"; zeig "$out"
  fi
  if out=$(grep -nIE 'BEGIN (RSA |OPENSSH |EC |DSA |PGP )?PRIVATE KEY|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}' "$f" 2>/dev/null); then
    melde "$f: moegliches Geheimnis/Schluessel"; zeig "$out"
  fi
  case "$f" in
    *.md|*.markdown|*.txt)
      if out=$(grep -nIwiE "$UMLAUT" "$f" 2>/dev/null); then
        melde "$f: Umlaut-Ersatz (ae/oe/ue/ss) in Doku - echte Umlaute verwenden"; zeig "$out"
      fi
      ;;
  esac
done

[ "$fehler" -ne 0 ] && echo "Regelpruefung fehlgeschlagen. Bitte oben gelistete Stellen korrigieren."
exit $fehler
