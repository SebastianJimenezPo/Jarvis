"""Textual simulation pilot. Offline by default; Groq requires explicit opt-in."""
import argparse
import json
from .engine import NextEngine
from .conversation import NextConversation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('text', nargs='*', help='One or more turns in the same temporary session')
    parser.add_argument('--provider', choices=['offline', 'groq'], default='offline')
    parser.add_argument('--allow-remote', action='store_true', help='Allow current text and minimal context to Groq')
    parser.add_argument('--free-tier', action='store_true', help='Attest that you checked this Groq account is Free, not Developer')
    parser.add_argument('--review', action='store_true', help='Offer contextual drafts for explicit local simulation review')
    parser.add_argument('--interactive', action='store_true', help='Read turns; :confirm ID applies a reviewed simulation, :quit exits')
    parser.add_argument('--timeout', type=float, default=None)
    parser.add_argument('--model', choices=['openai/gpt-oss-20b', 'openai/gpt-oss-120b'], default='openai/gpt-oss-120b')
    parser.add_argument('--reasoning-effort', choices=['low', 'medium'], default='medium')
    args = parser.parse_args()
    if not args.text and not args.interactive:
        parser.error('Provide text or --interactive.')
    if args.provider == 'groq' and not (args.allow_remote and args.free_tier):
        parser.error('Groq requires --allow-remote and --free-tier after checking your account. No billing is enabled here.')
    provider = None
    if args.provider == 'groq':
        from .groq import GroqProvider
        provider = GroqProvider(enabled=True, free_tier_confirmed=True, model=args.model, reasoning_effort=args.reasoning_effort)
    timeout = args.timeout if args.timeout is not None else 4.0
    try:
        engine = NextConversation(NextEngine(provider, timeout=timeout, review_enabled=args.review))
    except ValueError:
        if provider:
            provider.close()
        parser.error('Invalid timeout: expected 0.01..30 seconds.')
    engine.begin_session('cli')
    try:
        for index, text in enumerate(args.text, 1):
            result = engine.interpret(text, turn_id=str(index))
            print(json.dumps(result.model_dump(mode='json'), ensure_ascii=False))
        if args.interactive:
            index = len(args.text)
            for line in __import__('sys').stdin:
                text = line.strip()
                if text == ':quit':
                    break
                if not text:
                    continue
                index += 1
                if text.startswith(':confirm '):
                    result = engine.confirm(text.removeprefix(':confirm ').strip(), turn_id=str(index))
                else:
                    result = engine.interpret(text, turn_id=str(index))
                print(json.dumps(result.model_dump(mode='json'), ensure_ascii=False), flush=True)
    except ValueError:
        parser.error('Each turn must contain 1..1600 characters.')
    finally:
        engine.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
