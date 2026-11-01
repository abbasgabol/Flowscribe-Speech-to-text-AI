"""Shared decoding options for the app and its integration checks."""
DECODING = {
    'language': 'en',
    'beam_size': 5,
    'vad_filter': True,
    'condition_on_previous_text': False,
    # Whisper uses transcript-style context, not chat-style instructions.
    'initial_prompt': "Hello. How are you? I'm doing well, thank you.",
}
