import json
import aiohttp

from Modules.db_control import read_from_guild_settings_db, write_to_guild_settings_db

bot_phrases = {}

async def get_guild_language(guild_id: int) -> str:
    param_name = "language"
    guild_id = f"{guild_id}"
    language = ''
    try:
        language = await read_from_guild_settings_db(guild_id, param_name)
    except:
        pass

    if language:
        return language[0]
    else:
        default_language = "en" # default
        await write_to_guild_settings_db(guild_id, param_name, default_language)
        return default_language


PHRASES_FILE = 'bot_phrases.json'

try:
    with open(PHRASES_FILE, 'r', encoding='utf-8') as f:
        bot_phrases.update(json.load(f))
except FileNotFoundError:
    pass

async def translate_text(text: str, target_language: str) -> str:
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "en",
        "tl": target_language,
        "dt": "t",
        "q": text,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                result = await response.json()
                return result[0][0][0]
            return text


async def get_phrase(phrase_key: str, guild: str) -> str:
    try:
        guild_id = guild.id
    except AttributeError:
        guild_id = guild
    language = await get_guild_language(guild_id)

    phrase_key_formatted = phrase_key.replace("_", " ")

    if phrase_key not in bot_phrases:
        ru_translation = await translate_text(phrase_key_formatted, 'ru')
        en_translation = phrase_key_formatted

        bot_phrases[phrase_key] = {
            'ru': ru_translation,
            'en': en_translation
        }

        with open(PHRASES_FILE, 'w', encoding='utf-8') as f:
            json.dump(bot_phrases, f, ensure_ascii=False, indent=4)

    return bot_phrases.get(phrase_key, {}).get(language, "text 404")