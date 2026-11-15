"""Conservative review vetoes, not semantic authorization or a Spanish parser."""
import re
import unicodedata
from .direct import direct_decision


_QUOTES = re.compile(r'"([^"\n]+)"|\x27([^\x27\n]+)\x27|«([^»\n]+)»|“([^”\n]+)”|‘([^’\n]+)’')
_PREFIX = re.compile(r'^(?:cuando|en cuanto|despues de|al terminar)\b')
_TIME = re.compile(r'\b(?:manana|pasado manana|esta (?:noche|tarde|madrugada)|en \d+ (?:minutos?|horas?))\b')


def blocked_scope(text, context):
    # Only a complete known command inside paired quotes triggers this veto.
    # Quoted entity names remain usable; unrecognized paraphrases are not covered.
    for match in _QUOTES.finditer(text):
        fragment = next(group for group in match.groups() if group is not None)
        if direct_decision(fragment, context) is not None:
            return 'quoted_command'
    normalized = ''.join(c for c in unicodedata.normalize('NFD', text.casefold())
                         if not unicodedata.combining(c))
    normalized = ' '.join(normalized.split())
    if _PREFIX.search(normalized) or _TIME.search(normalized):
        return 'deferred_time'
    return None
