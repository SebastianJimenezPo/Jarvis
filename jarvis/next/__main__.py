"""Standalone textual prototype; no resident, microphone, models or network."""
import argparse
import json
from .engine import NextEngine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('text', nargs='+', help='One or more turns in the same temporary session')
    args = parser.parse_args()
    engine = NextEngine()
    engine.begin_session('cli')
    try:
        for index, text in enumerate(args.text, 1):
            result = engine.interpret(text, turn_id=str(index))
            print(json.dumps(result.model_dump(mode='json'), ensure_ascii=False))
    except ValueError:
        parser.error('Each turn must contain 1..1600 characters.')
    finally:
        engine.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
