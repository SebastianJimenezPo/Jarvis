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
    negative=re.search(r'\bmenos\s+',text)
    if negative:
        value=number(text[negative.end():])
        return -value if value is not None else None
    if re.search(r'\bmil\b',text):return 1000
    values={'cero':0,'diez':10,'veinte':20,'veinticinco':25,'treinta':30,'cuarenta':40,'cincuenta':50,
            'sesenta':60,'setenta':70,'ochenta':80,'noventa':90,'cien':100,'mitad':50}
    values.update({'uno':1,'una':1,'dos':2,'tres':3,'cuatro':4,'cinco':5,'seis':6,'siete':7,'ocho':8,'nueve':9,
                   'once':11,'doce':12,'trece':13,'catorce':14,'quince':15,'dieciseis':16,'diecisiete':17,
                   'dieciocho':18,'diecinueve':19,'veintiuno':21,'veintidos':22,'veintitres':23,'veinticuatro':24,
                   'veintiseis':26,'veintisiete':27,'veintiocho':28,'veintinueve':29})
    # Do not interpret "ciento veinte" as a permitted value of twenty.
    hundred=re.search(r'\b(ciento|doscientos|trescientos|cuatrocientos|quinientos|seiscientos|setecientos|ochocientos|novecientos)\b',text)
    if hundred:
        base={'ciento':100,'doscientos':200,'trescientos':300,'cuatrocientos':400,'quinientos':500,
              'seiscientos':600,'setecientos':700,'ochocientos':800,'novecientos':900}[hundred[1]]
        return base+(number(text[hundred.end():]) or 0)
    match=re.search(r'(?<!\w)(-?\d{1,4})(?:\s*%|\b)',text)
    if match:return int(match[1])
    word=re.search(r'\b(?:'+'|'.join(values)+r')\b',text)
    if not word:return None
    value=values[word[0]]
    if 30<=value<=90 and value%10==0:
        units=re.match(r'\s+y\s+(uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve)\b',text[word.end():])
        if units:value+=values[units[1]]
    return value


def color(text):
    return next((v for k,v in COLORS.items() if re.search(r'\b'+k+r'\b',text)),None)


def explicit_request(text):
    return bool(re.match(r'^(?:(?:por favor|puedes|podrias|quiero que|necesito que|mejor) )?(?:abre|abrir|abrelo|cierra|cerrar|cierralo|cierrala|enfoca|enfocar|pon|poner|sube|subir|baja|bajale|bajales|bajar|reduce|disminuye|aumenta|silencia|quita|pausa|reproduce|busca|enciende|prende|apaga|apagalo|apagala|activa|cambia|muestra|dame|ajusta|dejalo|haz|pasa|vuelve|trae)\b',text))
