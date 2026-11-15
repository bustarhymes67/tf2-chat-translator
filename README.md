# TF2 Chat Translator

Translates Team Fortress 2 chat to English while you play. Only Python's standard library, no
accounts or API keys: it uses Google Translate's free web address (and MyMemory as a backup).

## Start

1. Install [Python](https://www.python.org/downloads/) (tick "Add python.exe to PATH").
2. Open `Start Translator.bat` and pick **5. Setup** once, with Steam fully closed. It adds
   these to TF2's launch options (your own options are kept, and Steam's file is backed up):
   `-condebug -usercon +ip 0.0.0.0 +rcon_password <random> +hostport 27069 +net_start`
3. Start TF2, open `Start Translator.bat` and pick a mode:

| | Mode | Who sees it |
|---|---|---|
| 1 | Russian to English | you (overlay) |
| 2 | All languages to English | you (overlay) |
| 3 | Russian to English | everyone (TF2 chat) |
| 4 | All languages to English | everyone (TF2 chat) |

Overlay-only modes need just `-condebug`. The chat modes say each translation as
`name: translation` (team chat stays in team chat) over RCON, at the pace TF2's spam limit
allows; when lines pile up they're joined into one: `A: x | B: y`.

## The overlay

Press **F8** in game to unlock it: drag to move, click a line to copy the translation,
right-click to copy the original, and switch between *Russian only* and *All languages*.
Press F8 again to lock it, so clicks go through to the game.

Settings are in `config.json` (made on first run): `toggle_key`, `font_size`, `max_lines`,
`line_seconds`, `width`, and `log_path` if TF2 isn't in the default Steam folder.

## Tests

```
python -m unittest discover tests
```
