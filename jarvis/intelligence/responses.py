import re
from .contracts import Kind

LABELS={'open_application':'abrir','close_application':'cerrar','focus_application':'enfocar',
    'turn_on_light':'encender','turn_off_light':'apagar','set_light_color':'cambiar el color de',
    'set_light_brightness':'ajustar el brillo de','set_volume':'ajustar el volumen',
    'increase_volume':'subir el volumen','decrease_volume':'bajar el volumen','mute_audio':'silenciar el audio',
    'unmute_audio':'quitar el silencio','play_music':'reproducir música','pause_music':'pausar la música',
    'next_track':'pasar a la siguiente canción','previous_track':'volver a la canción anterior',
    'search_music':'buscar música','activate_scene':'activar el modo','get_system_status':'consultar el estado del sistema'}
NAMES={'main_light':'la luz principal','desk_light':'la luz del escritorio','system_audio':'',
       'music_player':'','system':'','gaming':'jugar','movie':'película','study':'estudio'}
COLORS={'red':'rojo','blue':'azul','green':'verde','white':'blanco','purple':'morado','yellow':'amarillo','orange':'naranja','pink':'rosa'}


class ResponseComposer:
    def compose(self,result):
        if result.kind==Kind.ACTION_PROPOSAL:
            parts=[]
            for a in result.actions:
                phrase=LABELS[a.intent]+(' '+NAMES.get(a.target,a.target) if NAMES.get(a.target,a.target) else '')
                if 'color' in a.parameters:phrase+=' a '+COLORS[a.parameters['color']]
                if 'value' in a.parameters:phrase+=' al '+str(a.parameters['value'])+' por ciento'
                if 'query' in a.parameters:phrase+=': '+a.parameters['query']
                if 'delta' in a.parameters:phrase+=' '+('bajándolo' if a.parameters['delta']<0 else 'subiéndolo')
                parts.append(phrase)
            return 'En simulación: '+', y '.join(parts)+'. No he ejecutado ninguna acción.'
        if result.kind==Kind.CLARIFICATION:return result.clarification_question or '¿Puedes aclarar qué quieres?'
        if result.kind==Kind.CANCEL:return self.clean(result.response) if result.response else 'Descarté la propuesta pendiente. No había ejecutado ninguna acción.'
        if result.kind==Kind.NEGATED:return 'Entendido, no propondré esa acción.'
        if result.kind==Kind.DEFERRED_REQUEST:return 'Es una solicitud para después o bajo una condición. Todavía no puedo programarla.'
        if result.kind==Kind.PREFERENCE:return 'Lo tendré presente en esta conversación; todavía no lo guardaré como preferencia permanente.'
        if result.kind==Kind.UNSUPPORTED:return 'Esa capacidad no está habilitada. No he ejecutado ninguna acción.'
        return self.clean(result.response or 'Entendido.')

    def clean(self,text):
        text=re.sub(r'<think>.*?</think>','',text,flags=re.S).strip()
        # Free text must never be allowed to assert execution or unprovided online access.
        if re.search(r'\b(?:he abierto|he cerrado|he cambiado|ya encendi|ya apague|ya abr[ií]|he ejecutado|he consultado internet|busqu[eé] en internet|acabo de buscar)\b',text,re.I) or re.match(r'^(?:hecho|ya est[aá])\b',text,re.I):
            return 'Estoy en modo de simulación y no tengo acceso automático a internet.'
        return text[:600].rsplit(' ',1)[0]+'…' if len(text)>600 else text
