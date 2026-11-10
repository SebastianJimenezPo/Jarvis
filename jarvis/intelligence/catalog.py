"""Finite simulation catalog. Entity IDs are test data, not discovered hardware."""
from .contracts import ActionProposal

APPLICATIONS={'chrome':['chrome','crom','google chrome'],'spotify':['spotify','espoti','espotify'],
              'steam':['steam','esteam'],'discord':['discord'],'edge':['edge','microsoft edge'],
              'vscode':['visual studio code','vscode']}
LIGHTS={'main_light':['luz principal','luces','la luz','iluminacion'],
        'desk_light':['luz del escritorio','luz de escritorio','lampara del escritorio']}
SCENES={'gaming':['modo jugar','modo juego','modo gaming'],'movie':['modo pelicula','modo cine'],'study':['modo estudio']}
COLORS={'rojo':'red','rojas':'red','rojos':'red','roja':'red','azul':'blue','azules':'blue',
        'verde':'green','verdes':'green','blanco':'white','blancas':'white','morada':'purple','moradas':'purple',
        'morado':'purple','amarillas':'yellow','amarillo':'yellow','naranja':'orange','rosadas':'pink','rosa':'pink'}
CATALOG={
 'open_application':('Abrir aplicación simulada','application',{},'none'),
 'close_application':('Cerrar aplicación simulada','application',{},'confirm_if_unsaved'),
 'focus_application':('Enfocar aplicación simulada','application',{},'none'),
 'set_volume':('Volumen absoluto','audio',{'value':'int:0..100'},'none'),
 'increase_volume':('Aumentar volumen','audio',{'amount':'int:-100..100'},'none'),
 'decrease_volume':('Disminuir volumen','audio',{'amount':'int:-100..100'},'none'),
 'mute_audio':('Silenciar','audio',{},'none'),'unmute_audio':('Quitar silencio','audio',{},'none'),
 'play_music':('Solicitar música','music',{'query':'optional_text'},'none'),
 'pause_music':('Pausar música','music',{},'none'),'next_track':('Siguiente pista','music',{},'none'),
 'previous_track':('Pista anterior','music',{},'none'),'search_music':('Buscar música','music',{'query':'text'},'none'),
 'turn_on_light':('Encender luz simulada','light',{},'none'),'turn_off_light':('Apagar luz simulada','light',{},'none'),
 'set_light_color':('Color de luz simulada','light',{'color':'color'},'none'),
 'set_light_brightness':('Brillo simulado','light',{'value':'optional_int:0..100','delta':'optional_int:-100..100'},'none'),
 'activate_scene':('Modo simulado','scene',{},'confirm_multi_action'),
 'get_system_status':('Estado simulado','system',{},'none')}


def entity_type(intent):
    return CATALOG[intent][1]


def catalog_spec():
    examples=dict(zip(CATALOG,[
        'Abre Chrome','Cierra Chrome','Enfoca Chrome','Pon el volumen al 50','Sube el volumen','Baja el volumen',
        'Silencia el audio','Quita el silencio','Reproduce música','Pausa la música','Pasa a la siguiente canción',
        'Vuelve a la canción anterior','Busca Hotel California','Enciende la luz principal','Apaga la luz principal',
        'Pon las luces azules','Pon el brillo al 50','Activa el modo jugar','Dame el estado del sistema']))
    return {name:{'description':row[0],'entity_type':row[1],'parameters':row[2],
                  'future_confirmation_policy':row[3],
                  'context_required':'Un objetivo explícito o un referente único del tipo compatible',
                  'restrictions':['Simulación obligatoria','Sin ejecución real','Validar polaridad, temporalidad y parámetros'],
                  'positive_examples':[examples[name]],
                  'negative_examples':['No '+examples[name].lower(),'Mañana '+examples[name].lower()]}
            for name,row in CATALOG.items()}


def validate_action(action:ActionProposal):
    _,group,params,_=CATALOG[action.intent]
    targets={'application':APPLICATIONS,'light':LIGHTS,'scene':SCENES,
             'audio':{'system_audio':[]},'music':{'music_player':[]},'system':{'system':[]}}[group]
    if action.target not in targets:
        raise ValueError('Unknown target')
    if set(action.parameters)-set(params):
        raise ValueError('Unknown parameter')
    for key,rule in params.items():
        value=action.parameters.get(key)
        if value is None:
            if rule.startswith('optional_'):continue
            raise ValueError(f'Missing parameter: {key}')
        rule=rule.removeprefix('optional_')
        if rule.startswith('int:'):
            low,high=map(int,rule[4:].split('..'))
            if type(value) is not int or not low<=value<=high:
                raise ValueError(f'Invalid parameter: {key}')
        elif rule=='color':
            if value not in set(COLORS.values()):raise ValueError('Unknown color')
        elif rule=='text':
            if not isinstance(value,str) or not 1<=len(value)<=160:raise ValueError('Invalid text')
    if action.intent=='set_light_brightness' and len(action.parameters)!=1:
        raise ValueError('Brightness requires exactly one of value or delta')
    if action.intent in ('increase_volume','decrease_volume') and action.parameters['amount']<=0:
        raise ValueError('Volume change amount must be positive')
    return action


class DryRunExecutor:
    def __init__(self):self.records=[]
    def propose(self,actions):
        validated=[validate_action(action) for action in actions]
        record={'simulated':True,'executed':False,'actions':[a.model_dump() for a in validated]}
        self.records.append(record);self.records=self.records[-20:]
        return record
