# Steam Datagram Relay rule-set

Репозиторий ежедневно получает актуальные адреса Steam Datagram Relay для
Counter-Strike 2 из [Steam API](https://api.steampowered.com/ISteamApps/GetSDRConfig/v1?appid=730)
и генерирует [`steam-ip.json`](steam-ip.json) в формате source rule-set для
[sing-box](https://sing-box.sagernet.org/configuration/rule-set/source-format/).
В файл попадают только адреса, явно перечисленные API; соседние адреса
объединяются в CIDR без расширения фактического диапазона.

Прямая ссылка на актуальный rule-set:

```text
https://raw.githubusercontent.com/mrvokintos/steam-datagram-relay/main/steam-ip.json
```

## Локальный запуск

Требуется Python 3.10 или новее. Сторонние пакеты не нужны.

```bash
python3 scripts/generate_steam_ip.py
```

Для проверки парсера без обращения к сети можно передать сохранённый ответ API:

```bash
python3 scripts/generate_steam_ip.py --input sdr-config.json --output steam-ip.json
```

Тесты запускаются командой:

```bash
python3 -m unittest discover -s tests -v
```

Workflow `.github/workflows/update-steam-ip.yml` запускается каждый день в
03:17 UTC, а также вручную через `workflow_dispatch`. Если список сетей
изменился, GitHub Actions коммитит обновлённый `steam-ip.json` в текущую ветку.
