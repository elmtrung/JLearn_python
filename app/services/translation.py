from googletrans import Translator
from asgiref.sync import async_to_sync

async def translate_japanese_to_vietnamese(text):
    """Translates Japanese text to Vietnamese."""
    translator = Translator()
    result = await translator.translate(text, src='ja', dest='vi')
    return result.text 