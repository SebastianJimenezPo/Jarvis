"""Absolute launcher usable by pythonw and Task Scheduler, independent of cwd."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jarvis.__main__ import main

raise SystemExit(main())
