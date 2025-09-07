from accessible_output2 import outputs
from accessible_output2.outputs.base import Output


_output: Output | None = None


def create_speech_output(prefer_tts: bool = False) -> Output | None:
	"""Create and return a speech output handler."""
	if prefer_tts:
		engines = [("sapi5", "SAPI5"), ("voiceover", "VoiceOver"), ("e_speak", "ESpeak")]
		for module_name, class_name in engines:
			if hasattr(outputs, module_name):
				engine_module = getattr(outputs, module_name)
				if hasattr(engine_module, class_name):
					return getattr(engine_module, class_name)()
	return outputs.auto.Auto()


def speak(text: str, interrupt: bool = True, prefer_tts: bool = False) -> bool:
	"""Speak the provided text, optionally interrupting the current announcement.
	If an `Output` object does not exist, one will be initialized automatically.
	In practice, this is the only function one should need to support outputting to a screen reader or the system TTS engine.
	"""
	global _output
	if _output is None:
		_output = create_speech_output(prefer_tts)
	if _output:
		_output.output(text, interrupt=interrupt)
		return True
	return False
