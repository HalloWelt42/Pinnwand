#!/usr/bin/env bash
# Stoppt die gesamte Anwendung (Backend + Frontend).
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/start.sh" stop
