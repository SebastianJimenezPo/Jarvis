import re
import unicodedata
from .catalog import APPLICATIONS,LIGHTS,SCENES,COLORS


def normalize(text):
    text=''.join(c for c in unicodedata.normalize('NFD',text.casefold()) if not unicodedata.combining(c))
    return ' '.join(re.sub(r'[^\w%\s,;+-]',' ',text).split())


def mentions(text,table):
    found=[]
    # Specific light names take precedence over the generic phrase 'la luz'.
    if table is LIGHTS and any(alias in text for alias in LIGHTS['desk_light']):return ['desk_light']
    for entity,aliases in table.items():
        if any(re.search(r'(?<!\w)'+re.escape(alias)+r'(?!\w)',text) for alias in aliases):found.append(entity)
    return found


def clause_kind(text):
    if re.search(r'\b(?:no lo hagas|olvidalo|olvida eso|cancela todo|espera[, ]+no)\b',text):return 'cancel'
    if re.match(r'^no (?:se (?:oye|escucha)|quiero que (?:suene|se escuche) (?:tan|muy) fuerte)',text):return None
    if re.search(r'\b(ignora (?:las |tus )?(?:restricciones|reglas)|powershell|ejecuta (?:un )?(?:comando|codigo)|cmd exe|borra archivos|formatea)\b',text):return 'unsupported'
    if re.search(r'\b(que pasaria|como si|si (?:pusiera|apagara|bajara|abriera)|hipoteticamente|suponiendo)\b',text):return 'hypothetical'
    if re.search(r'\b(cuando|manana|despues|al terminar|mas tarde|esta noche|dentro de|si\s+\w+|en (?:\d+|cinco|diez|veinte|treinta|una|dos) (?:minutos|horas|segundos))\b',text):return 'deferred_request'
    if re.search(r'^(?:yo )?(?:prefiero|me gusta|recuerda|mi preferencia|quisiera recordar)\b',text):return 'preference'
    if re.search(r'\b(ayer|el otro dia|mi (?:amigo|hermano) (?:dijo|siempre)|estaba pensando|dijeron que)\b',text):return 'conversation'
    if re.search(r'^(?:como (?:puedo|se)|que (?:es|significa)|por que|puedes (?:abrir programas|cerrar aplicaciones automaticamente)|sabes |es posible|podrias explicarme)\b',text):return 'conversation'
    if re.search(r'^(?:no (?:quiero que |debes |vayas a )?|nunca |jamas |evita )',text):return 'negated'
    return None


def split_clauses(text):
    return re.split(r'\s*(?:[,;]|\bpero\s+|\s+y\s+)\s*',text)


def number(text):
    match=re.search(r'(?<!\w)(-?\d{1,4})(?:\s*%|\b)',text)
    if match:return int(match[1])
    values={'cero':0,'diez':10,'veinte':20,'veinticinco':25,'treinta':30,'cuarenta':40,'cincuenta':50,
            'sesenta':60,'setenta':70,'ochenta':80,'noventa':90,'cien':100,'mitad':50}
    return next((v for k,v in values.items() if re.search(r'\b'+k+r'\b',text)),None)


def color(text):
    return next((v for k,v in COLORS.items() if re.search(r'\b'+k+r'\b',text)),None)


def explicit_request(text):
    return bool(re.match(r'^(?:(?:por favor|puedes|podrias|quiero que|necesito que|mejor) )?(?:abre|abrir|abrelo|cierra|cerrar|cierralo|cierrala|enfoca|enfocar|pon|poner|sube|subir|baja|bajale|bajales|bajar|reduce|disminuye|aumenta|silencia|quita|pausa|reproduce|busca|enciende|prende|apaga|apagalo|apagala|activa|cambia|muestra|dame|ajusta|dejalo|haz|pasa|vuelve|trae)\b',text))
