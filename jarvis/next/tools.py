"""Small capability registry; no OS adapters or executable callbacks."""
from dataclasses import dataclass
from types import MappingProxyType
from pydantic import Field, StrictBool, StrictInt
from .contracts import Capability, Record, ToolCall, ToolResult


class NoParameters(Record):
    pass


class VolumeParameters(Record):
    value: StrictInt = Field(ge=0, le=100)


class MuteParameters(Record):
    muted: StrictBool


@dataclass(frozen=True)
class ToolDefinition:
    capability: Capability
    parameters: type[Record]


class ToolRegistry:
    def __init__(self, definitions):
        rows = tuple(definitions)
        self._tools = MappingProxyType({row.capability.tool: row for row in rows})
        if len(self._tools) != len(rows):
            raise ValueError('Duplicate tool')

    def capabilities(self):
        return tuple(row.capability.model_copy(deep=True) for row in self._tools.values())

    def validate(self, call: ToolCall):
        definition = self._tools.get(call.tool)
        if definition is None or call.target not in definition.capability.targets:
            raise ValueError('Unknown tool or target')
        definition.parameters.model_validate(call.parameters, strict=True)

    def simulate(self, call: ToolCall):
        self.validate(call)
        return ToolResult(tool=call.tool, target=call.target,
                          status='unknown' if self._tools[call.tool].capability.access == 'read' else 'simulated')


def default_registry():
    rows = [
        ('applications.open', 'Abrir aplicación', ('steam', 'spotify', 'chrome', 'discord'), 'application', 'write', 'moderate', NoParameters),
        ('system_audio.set_volume', 'Ajustar volumen absoluto', ('system_audio',), 'audio', 'write', 'low', VolumeParameters),
        ('system_audio.set_mute', 'Establecer silencio', ('system_audio',), 'audio', 'write', 'low', MuteParameters),
        ('system_audio.get_volume', 'Consultar volumen', ('system_audio',), 'audio', 'read', 'low', NoParameters),
        ('media.pause', 'Pausar música', ('music_player',), 'media', 'write', 'low', NoParameters),
    ]
    return ToolRegistry(ToolDefinition(Capability(tool=tool, description=description, targets=targets,
        resource=resource, access=access, risk=risk, parameter_schema=params.model_json_schema()), params)
        for tool, description, targets, resource, access, risk, params in rows)
