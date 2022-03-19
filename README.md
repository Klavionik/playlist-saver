# Spotify Playlist Saver

Сохранение плейлистов из Spotify в табличном виде. 

## История
Небольшой проект, который я сделал в дни перед уходом Spotify из России, чтобы забэкапить
свои плейлисты с ценной музыкой. Некоторое время хостил его в облаке, пока у меня не 
кончился триальный период. :)

Поигрался с новыми для себя инструментами: применил FastAPI и CSS-фреймворк Bulma, сделал 
деплой с помощью GitHub Actions и Ansible в Яндекс.Облако. Ради бесплатного HTTPS и 
мониторинга прикрутил Traefik.

## Локальный запуск
Для локального запуска понадобится аккаунт в [Spotify Developer](https://developer.spotify.com)
и тоннель [ngrok](https://ngrok.com).

1. Запустить тоннель командой `ngrok http 8030`
2. В дашборде Spotify:
   1. Создать новое приложение.
   2. В список Redirect URIs добавить URL вида **{http-адрес-тоннеля}/callback**

Затем склонировать репозиторий и запустить приложение:

`git clone git@github.com:Klavionik/spotify-playlist-saver.git`  
`cd spotify-playlist-saver`  
`cp .env.dev.example .env.dev`  
`Добавить CLIENT_ID и CLIENT_SECRET из дашборда Spotify Developer в .env.dev `  
`make dev`

Приложение будет доступно в браузере по адресу тоннеля.
