from DataBase.db_control import read_from_guild_settings_db, write_to_guild_settings_db

bot_phrases = {
    'language_changed': {
        'ru': 'Язык изменен на русский',
        'en': 'Language changed to English'
    },
    'channels for party search created': {
        'ru': 'Текстовый и голосовой каналы для поиска пати созданы',
        'en': 'Text and voice channels for party search created'
    },
    'Text Channel': {
        'ru': 'Текстовый канал',
        'en': 'Text Channel'
    },
    'Voice Channel': {
        'ru': 'Голосовой канал',
        'en': 'Voice Channel'
    },
    'looking for a company': {
        'ru': 'ищет компанию в голосовом канале',
        'en': 'looking for a company in the voice channel'
    },
    'Join Voice Channel': {
        'ru': 'Присоединиться',
        'en': 'Join Voice Channel'
    },
    'Click here to join': {
        'ru': 'Нажми чтобы присоединиться',
        'en': 'Click here to join'
    },
    'Time': {
        'ru': 'Время',
        'en': 'Time'
    },
    'Number of unique players': {
        'ru': 'Количество уникальных игроков',
        'en': 'Number of unique players'
    },
    'Top games activity on': {
        'ru': 'Топ игровых активносей на',
        'en': 'Top games activity on'
    },
    'Top': {
        'ru': 'Топ',
        'en': 'Top'
    },
    'Games Activity': {
        'ru': 'Игровых Активностей',
        'en': 'Games Activity'
    },
    'Data for the last': {
        'ru': 'Данные за последние',
        'en': 'Data for the last'
    },
    'days with granularity': {
        'ru': 'дней с гранулярностью',
        'en': 'days with granularity'
    },
    'unique players': {
        'ru': 'уникальных игроков',
        'en': 'unique players'
    },
    'popularity chart for the last': {
        'ru': 'чарт популярности за последние',
        'en': 'popularity chart for the last'
    },
    'Activity': {
        'ru': 'Активность',
        'en': 'Activity'
    }
}

def get_guild_language(guild_id: int) -> str:
    param_name = "language"
    guild_id = f"{guild_id}"
    language = ''
    try:
        language = read_from_guild_settings_db(guild_id, param_name)
    except:
        pass

    if language:
        return language[0]
    else:
        default_language = "en" # default
        write_to_guild_settings_db(guild_id, param_name, default_language)
        return default_language


def get_phrase(phrase_key: str, guild: str) -> str:
    language = get_guild_language(guild.id)

    return bot_phrases.get(phrase_key, {}).get(language, "text 404")
