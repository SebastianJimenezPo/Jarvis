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
        # Addressing Jarvis in a known test phrase is optional. Do not modify STT text.
        addressed=re.sub(r'\bjarvis\b','',normalized)
        addressed=' '.join(addressed.split())
        if addressed in ('hola','hola como estas'):
            return DialogueReply('Hola')
        if re.fullmatch(r'(?:hola )?(?:si )?me escuchas(?: bien)?(?: o no)?',addressed):
            return DialogueReply('Sí, te escucho')
        if normalized=='como estas':
            return DialogueReply('Estoy funcionando correctamente')
        if normalized in ('gracias','gracias jarvis'):
            return DialogueReply('Con gusto')
        if normalized in ('perfecto','listo'):
            return DialogueReply('Listo')
        if re.match(r'^(?:por favor )?(?:abre|abrir|cierra|cerrar|pon|reproduce|apaga|enciende|sube|baja)\b',addressed):
            return DialogueReply('Te escuché, pero el control de aplicaciones todavía no está habilitado.')
        return DialogueReply('No reconocí una frase de prueba. ¿Puedes repetirla?')


class DialogueBridge:
    def __init__(self,provider=None):
        self.provider=provider or Phase2ResponseProvider()

    def respond(self,utterance,diagnostic_echo=False):
        return self.provider.respond(utterance,diagnostic_echo)


def activation_only_candidate(text,first_turn):
    """Conservative response gate, not a rewrite or claim about the spoken word.

    Wake acoustics are present in pre-roll and STT can spell the name differently.
    An unknown isolated token on the first turn is ambiguous: keep listening.
    Known one-word test phrases and all multiword utterances remain available.
    """
    clean=strip_wake_prefix(text)
    tokens=re.findall(r'\w+',clean.casefold())
    known={'hola','gracias','adiós','adios','chao','perfecto','listo',
           'cancela','cancelar','cancélalo','cancelalo','cancélala','cancelala','cancéleme','cancelame'}
    return first_turn and (not tokens or (len(tokens)==1 and tokens[0] not in known))
