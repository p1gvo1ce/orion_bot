from Modules.db_control import read_from_guild_settings_db, write_to_guild_settings_db

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
    },
    'Add Info': {
        'ru': 'Добавить инфо',
        'en': 'Add Info'
    },
    'Additional Information': {
        'ru': 'Дополнительная информация',
        'en': 'Additional Information'
    },
    'Enter any additional details here...': {
        'ru': 'Введи дополнительные детали тут...',
        'en': 'Enter any additional details here...'
    },
    'Information successfully added.': {
        'ru': 'Дополнительная информация добавлена',
        'en': 'Information successfully added.'
    },
    'Who is playing?': {
        'ru': 'Кто в игре?',
        'en': 'Who is playing?'
    },
    'Close': {
        'ru': 'Закрыть',
        'en': 'Close'
    },
    'Currently in game': {
        'ru': 'Сейчас в игре',
        'en': 'Currently in game'
    },
    'Only the channel creator can add info.': {
        'ru': 'Добавлять информацию может только создатель поиска',
        'en': 'Only the channel creator can add info.'
    },
    'Only the channel creator can close the search.': {
        'ru': 'Только инициатор поиска может его закрыть.',
        'en': 'Only the channel creator can close the search.'
    },
    'Search message closed.': {
        'ru': 'Поиск закрыт.',
        'en': 'Search message closed.'
    },
    'No one else is currently playing this game.': {
        'ru': 'В эту игру больше никто не играет.',
        'en': 'No one else is currently playing this game.'
    },
    'Currently playing': {
        'ru': 'Сейчас в игре',
        'en': 'Currently playing'
    },
    'Data based on': {
        'ru': 'Основано на данных',
        'en': 'Data based on'
    },
    'unique players over all time': {
        'ru': 'уникальных игроков за период',
        'en': 'unique players over all time'
    },
    'You need to specify the on/off mode': {
        'ru': 'Нужно указать режим on/off',
        'en': 'You need to specify the on/off mode'
    },
    'Automatic greeting deletion enabled': {
        'ru': 'Включено автоматическое удаление приветствий',
        'en': 'Automatic greeting deletion enabled'
    },
    'Delay': {
        'ru': 'Задержка',
        'en': 'Delay'
    },
    'Automatic greeting deletion disabled': {
        'ru': 'Выключено автоматическое удаление приветствий',
        'en': 'Automatic greeting deletion disabled'
    },
    'seconds': {
        'ru': 'секунд',
        'en': 'seconds'
    },
    'Create a party search': {
        'ru': 'Создание поиска пати',
        'en': 'Create a party search'
    },
    'How to search': {
        'ru': 'Как искать',
        'en': 'How to search'
    },
    'how_to_search_instruction': {
        'ru': '''Чтобы начать поиск тебе нужно:

```
1. Присоединиться к любому доступному голосовому каналу
2. Нажать кнопку "Создать поиск"
3. Заполнить информацию об активности для которой ты ищешь людей и указать дополнительную информацию
```
Поиск будет существовать до тех пор, пока ты остаёшься в голосовом канале или пока не нажмешь кнопку завершения поиска
Если на сервере есть роль соответствующая твоей активности (строгое соответствие названия), то эта роль будет упомянута в сообщении.

Если ты хочешь создать роль для поиска, то нужно:
```
1. Включить в Дискорд синхронизацию со Стим или с другим источником активности (в твоем профиле должно отображаться "играет в..."
2. Зайти в канал для поиска пати
```
Если это невозможно для какой-то активности, то необходимо обратиться к владельцам (администраторам) сервера для создания роли активности вручную
''',
        'en': '''To start a search you need to:

```
1. Join any available voice channel
2. Click the "Create search" button
3. Fill in the information about the activity for which you are searching for people and specify additional information
```
The search will exist as long as you remain in the voice channel or until you click the end search button
If there is a role on the server that matches your activity (strict match of the name), then this role will be mentioned in the message.

If you want to create a role for searching, you need to:
```
1. Enable syncing with Steam or another source of activity in Discord (your profile should display "plays in..."
2. Go to the channel to search for a party
```
If this is not possible for some activity, then you need to contact the owners (administrators) of the server to create the activity role manually.
'''
    },
    'create_find': {
        'ru': 'Создать поиск',
        'en': 'Create a search'
    },
    'You must be in the voice channel.': {
        'ru': 'Ты должен быть в голосовом канале.',
        'en': 'You must be in the voice channel.'
    },
    'Activity name': {
        'ru': 'Название активности',
        'en': 'Activity name'
    },
    'Enter the activity name here': {
        'ru': 'Укажи название активности здесь',
        'en': 'Enter the activity name here'
    },
    'You cannot run more than 1 search per person.': {
        'ru': 'Нельзя запустить более 1 поиска на человека.',
        'en': 'You cannot run more than 1 search per person.'
    },
    'No one has been seen playing this game lately.': {
        'ru': 'В последнее время никто не замечен в этой игре.',
        'en': 'No one has been seen playing this game lately.'
    },
    'There is no information on this activity.': {
        'ru': 'По этой активности нет информации.',
        'en': 'There is no information on this activity.'
    },
    'Roles for top games have been created': {
        'ru': 'Роли для топ %s игр успешно созданы и назначены.',
        'en': 'Roles for top %s games have been successfully created and assigned.'
    },
    'Name_personal_voice_set': {
        'ru': 'Задано название для личных голосовых каналов.',
        'en': 'The name for personal voice channels has been set.'
    },
    'Game Roles Update Enabled': {
        'ru': 'Включено обновление игровых ролей',
        'en': 'Game Roles Update Enabled'
    },
    'Game role Update disabled': {
        'ru': 'Выключено обновление игровых ролей',
        'en': 'Game role Update disabled'
    },
    'New Message': {
        'ru': 'Новое сообщение',
        'en': 'New Message'
    },
    'Author': {
        'ru': 'Автор',
        'en': 'Author'
    },
    'Content': {
        'ru': 'Содержание',
        'en': 'Content'
    },
    'Channel': {
        'ru': 'Канал',
        'en': 'Channel'
    },
    'Created At': {
        'ru': 'Создано',
        'en': 'Created At'
    },
    'Deleted Message': {
        'ru': 'Удалено сообщение',
        'en': 'Deleted Message'
    },
    'Deleted At': {
        'ru': 'Удалено',
        'en': 'Deleted At'
    },
    'Message Edited': {
        'ru': 'Сообщение отредактировано',
        'en': 'Message Edited'
    },
    'Content Before': {
        'ru': 'Содержание До',
        'en': 'Content Before'
    },
    'Content After': {
        'ru': 'Содержание После',
        'en': 'Content After'
    },
    'Event Type': {
        'ru': 'Событие',
        'en': 'Event Type'
    },
    'Logged At': {
        'ru': 'Время записи',
        'en': 'Logged At'
    },
    'Data': {
        'ru': 'Данные',
        'en': 'Data'
    },
    'Category': {
        'ru': 'Категория',
        'en': 'Category'
    },
    'Edited At': {
        'ru': 'Отредактировано',
        'en': 'Edited At'
    },
    'No logs found for the specified filters': {
        'ru': 'Нет логов с указанными фильтрами',
        'en': 'No logs found for the specified filters'
    },
    'start time': {
        'ru': 'начало периода',
        'en': 'start time'
    },
    'end time': {
        'ru': 'конец периода',
        'en': 'end time'
    },
    'search': {
        'ru': 'поиск',
        'en': 'search'
    },
    'Fetching logs': {
        'ru': 'Извлечение логов',
        'en': 'Fetching logs'
    },
    'Vars': {
        'ru': 'Переменные',
        'en': 'Vars'
    },
    'event type': {
        'ru': 'тип события',
        'en': 'event type'
    },
    'operator': {
        'ru': 'оператор',
        'en': 'operator'
    },
    'input': {
        'ru': 'ввод',
        'en': 'input'
    },
    'New Member Joined': {
        'ru': 'Участник присоединился',
        'en': 'New Member Joined'
    },
    'Member': {
        'ru': 'Участникк',
        'en': 'Member'
    },
    'Invited by': {
        'ru': 'Пригласил',
        'en': 'Invited by'
    },
    'Invite Code': {
        'ru': 'Код приглашения',
        'en': 'Invite Code'
    },
    'Joined At': {
        'ru': 'Присоединился',
        'en': 'Joined At'
    },
    'Member Left': {
        'ru': 'Участник ушел',
        'en': 'Member Left'
    },
    'Name': {
        'ru': 'Имя',
        'en': 'Name'
    },
    'Left At': {
        'ru': 'Ушел',
        'en': 'Left At'
    },
    'Member Muted': {
        'ru': 'Участник получил mute',
        'en': 'Member Muted'
    },
    'Muted At': {
        'ru': 'Лишен голоса',
        'en': 'Muted At'
    },
    'Reason': {
        'ru': 'Причина',
        'en': 'Reason'
    },
    'Duration': {
        'ru': 'Длительность',
        'en': 'Duration'
    },
    'Member Unmuted': {
        'ru': 'С участника снят mute',
        'en': 'Member Unmuted'
    },
    'Unmuted At': {
        'ru': 'Mute снят',
        'en': 'Unmuted At'
    },
    'Member Banned': {
        'ru': 'Участник забанен',
        'en': 'Member Banned'
    },
    'Banned At': {
        'ru': 'Забанен',
        'en': 'Banned At'
    },
    'Joined Voice Channel': {
        'ru': 'Подключение к голосовому каналу',
        'en': 'Joined Voice Channel'
    },
    'Left Voice Channel': {
        'ru': 'Отключение от голосового канала',
        'en': 'Left Voice Channel'
    },
    'Switched Voice Channels': {
        'ru': 'Смена голосового канала',
        'en': 'Switched Voice Channels'
    },
    'Muted Microphone': {
        'ru': 'Выключение микрофона',
        'en': 'Muted Microphone'
    },
    'Unmuted Microphone': {
        'ru': 'Включение микрофона',
        'en': 'Unmuted Microphone'
    },
    'Deafened': {
        'ru': 'Выключение звука',
        'en': 'Deafened'
    },
    'Undeafened': {
        'ru': 'Включение звука',
        'en': 'Undeafened'
    },
    'Voice Channel': {
        'ru': 'Голосовой канал',
        'en': 'Voice Channel'
    },
    'Occurred At': {
        'ru': 'Время события',
        'en': 'Occurred At'
    },
    'Role Created': {
        'ru': 'Создана роль',
        'en': 'Role Created'
    },
    'Role Name': {
        'ru': 'Название роли',
        'en': 'Role Name'
    },
    'Role ID': {
        'ru': 'ID роли',
        'en': 'Role ID'
    },
    'Role Updated': {
        'ru': 'Роль обновлена',
        'en': 'Role Updated'
    },
    'Before': {
        'ru': 'До',
        'en': 'Before'
    },
    'After': {
        'ru': 'После',
        'en': 'After'
    },
    'Updated At': {
        'ru': 'Время обновления',
        'en': 'Updated At'
    },
    'Role Deleted': {
        'ru': 'Роль удалена',
        'en': 'Role Deleted'
    },
    'Channel Created': {
        'ru': 'Создан канал',
        'en': 'Channel Created'
    },
    'Channel Name': {
        'ru': 'Название канала',
        'en': 'Channel Name'
    },
    'Channel ID': {
        'ru': 'ID канала',
        'en': 'Channel ID'
    },
    'Channel Updated': {
        'ru': 'Канал обновлен',
        'en': 'Channel Updated'
    },
    'Channel Deleted': {
        'ru': 'Канал удален',
        'en': 'Channel Deleted'
    },
    'Command error': {
        'ru': 'Произошла ошибка, либо недостаточно прав для выполнения команды',
        'en': 'An error occurred or you do not have sufficient rights to execute the command.'
    }
}

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


async def get_phrase(phrase_key: str, guild: str) -> str:
    try:
        guild_id = guild.id
    except:
        guild_id = guild
    language = await get_guild_language(guild_id)

    return bot_phrases.get(phrase_key, {}).get(language, "text 404")