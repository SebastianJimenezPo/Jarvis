from dataclasses import dataclass
import re
import unicodedata


def strip_wake_prefix(text):
    return re.sub(r'^\s*[¿¡]?\s*jarvis\b[\s,.:;!?¿¡-]*','',text,flags=re.IGNORECASE).strip()


@dataclass(frozen=True)
class UserUtterance:
    session_id: str
    turn_id: str
    text: str
    language: str
    timestamp: float


@dataclass(frozen=True)
class DialogueReply:
    text: str
    end_session: bool = False


class Phase2ResponseProvider:
    def respond(self,utterance,diagnostic_echo=False):
        text=strip_wake_prefix(utterance.text)
        normalized=''.join(c for c in unicodedata.normalize('NFD',text.lower()) if not unicodedata.combining(c))
        normalized=re.sub(r'[^\w\s]','',normalized).strip()
        if not normalized:
            return DialogueReply('')
        if diagnostic_echo:
            return DialogueReply('Escuché: '+text)
        if normalized in ('adios','hasta luego','chao','gracias jarvis adios'):
            return DialogueReply('Hasta luego',True)
        if normalized in ('hola','hola jarvis'):
            return DialogueReply('Hola')
        if normalized in ('me escuchas','me escuchas bien','hola me escuchas','hola me escuchas bien'):
            return DialogueReply('Sí, te escucho')
        if normalized=='como estas':
            return DialogueReply('Estoy funcionando correctamente')
        if normalized in ('gracias','gracias jarvis'):
            return DialogueReply('Con gusto')
        if normalized in ('perfecto','listo'):
            return DialogueReply('Listo')
        return DialogueReply('Te escuché. En esta fase puedo escuchar y hablar; el control de aplicaciones todavía no está habilitado.')


class DialogueBridge:
    def __init__(self,provider=None):
        self.provider=provider or Phase2ResponseProvider()

    def respond(self,utterance,diagnostic_echo=False):
        return self.provider.respond(utterance,diagnostic_echo)
