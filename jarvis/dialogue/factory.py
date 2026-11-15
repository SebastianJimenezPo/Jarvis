"""Exactly one dialogue architecture per voice worker, selected lazily."""
def make_provider(root,config,cancel):
    if config.dialogue_profile == 'next':
        from .next_bridge import NextVoiceBridge
        return NextVoiceBridge(config,cancel)
    from jarvis.intelligence.provider import make_provider as legacy
    return legacy(root,cancel)
