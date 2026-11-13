"""Punto de entrada de ``python3 -m control_center`` (§13: validar|compilar)."""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
