# TF2 Chat Translator

Translates Team Fortress 2 chat to English while you play. You can show the translations in an
overlay only you can see, or have them said in TF2's chat for everyone.

It uses only Python's standard library: no accounts and no API keys. Translations come from
Google Translate's free web address, with MyMemory as a backup.

## The four modes

| | Mode | Who sees it |
|---|---|---|
| 1 | Russian to English | only you (overlay) |
| 2 | All languages to English | only you (overlay) |
| 3 | Russian to English | everyone (TF2 chat) |
| 4 | All languages to English | everyone (TF2 chat) |

---

## Step-by-step setup

### Step 1: Download the translator

1. At the top of this page, click the green **Code** button, then **Download ZIP**.
2. Right-click the downloaded ZIP and choose **Extract All...**.
3. Pick a folder you'll find again, for example `Documents\TF2 Chat Translator`.

Don't run it from inside the ZIP: its settings can't be saved there.

### Step 2: Install Python (once)

1. Go to <https://www.python.org/downloads/> and click the big **Download Python** button.
2. Run the installer. **On the first screen, tick "Add python.exe to PATH"** at the bottom.
3. Click **Install Now** and wait until it says the setup was successful.

To check it worked, open the Start menu, type `cmd`, press Enter, then type `python --version`.
It should print something like `Python 3.13.1`. If it says Python wasn't found, run the
installer again and tick "Add python.exe to PATH".

### Step 3: Set TF2's launch options (once)

The translator reads TF2's chat from a log file, and the chat modes send lines to TF2. Both
need some launch options in TF2. The Setup step adds them for you.

1. Close TF2.
2. **Quit Steam completely**: in Steam's top-left menu choose **Steam > Exit**. Closing the
   window isn't enough, because Steam keeps running in the system tray.
3. Open the translator folder and double-click **`Start Translator.bat`**.
   - If Windows says *"Windows protected your PC"*, click **More info**, then **Run anyway**.
4. Type **`5`** and press **Enter**.
5. It should say `TF2 launch options updated`. Press any key to go back to the menu, then close
   the window.

Setup keeps any launch options you already had, and saves a backup of Steam's config file next
to the original. It adds:

```
-condebug -usercon +ip 0.0.0.0 +rcon_password <random> +hostport 27069 +net_start
```

The random password is kept only in `config.json` in the translator's folder, on your PC.

### Step 4: Start TF2

1. Start Steam and launch TF2 as usual.
2. To check the launch options: in your Steam library, right-click **Team Fortress 2** >
   **Properties** > **General**. The **Launch Options** box should contain `-condebug`.

### Step 5: Start the translator

1. With TF2 running, double-click **`Start Translator.bat`**.
2. Type **`1`**, **`2`**, **`3`** or **`4`** (see the table above) and press **Enter**.
3. Leave the black window open while you play. Closing it stops the translator.

Run TF2 in **Windowed** or **Fullscreen Windowed** (Options > Video). The overlay can't show on
top of exclusive fullscreen.

### Step 6: Use the overlay

Translations appear at the bottom-left of the screen and fade after 15 seconds.

Press **F8** (also in game) to unlock the overlay. While it's unlocked you can:

- **Drag** it to move it. The spot is saved when you lock it again.
- **Click** a line to copy its translation.
- **Right-click** a line to copy the original message.
- Click **Russian only** or **All languages** to switch without restarting.

Press **F8** again to lock it, so clicks go through to the game.

### Chat modes (3 and 4)

Each translation is said in chat as `name: translation`. Team chat is answered in team chat.

TF2 blocks players who send too many lines, so the translator only sends as fast as TF2
allows. When several translations are waiting, they're joined into one line: `A: x | B: y`.

When it connects, the black window says `Connected to TF2: translations go to chat`.

---

## Something not working?

**Nothing gets translated.**
- Check that `-condebug` is in TF2's launch options (Step 4), and restart TF2 after adding it.
- English lines are skipped on purpose. In modes 1 and 3, only lines in the Russian alphabet
  are translated.
- If TF2 isn't installed in the default Steam folder, open `config.json` with Notepad and set
  `log_path` to your `...\Team Fortress 2\tf\console.log`. Use double backslashes: `D:\\Games\\...`.

**Setup says "Steam is running".**
Steam is still in the system tray. Right-click its icon near the clock and choose **Exit**.

**Setup says Steam's config wasn't found.**
Setup looks in `C:\Program Files (x86)\Steam`. If Steam is somewhere else, add the options by hand:
1. Run the translator once and pick any mode, so `config.json` is created. Then close it.
2. Open `config.json` with Notepad and copy the `rcon_password` value. If it's empty, type a
   random word there and save.
3. In Steam: right-click **Team Fortress 2** > **Properties** > **Launch Options**, and add:
   `-condebug -usercon +ip 0.0.0.0 +rcon_password YOURPASSWORD +hostport 27069 +net_start`

For overlay-only modes (1 and 2), `-condebug` alone is enough.

**Chat modes say "TF2 refused the RCON password".**
The password in TF2's launch options doesn't match `config.json`. Quit Steam and run Setup
(option 5) again, then restart TF2.

**The black window says "Python isn't installed".**
Install Python again (Step 2) and make sure **Add python.exe to PATH** is ticked.

**"Already running in another window".**
The translator is already open. Close the other black window first.

**F8 does nothing.**
Another program may already use F8. Open `config.json` and change `toggle_key` to something
else, for example `"F7"` or `"INSERT"`.

## Settings

`config.json` is created the first time you run the translator. Close the translator before
editing it.

| Setting | What it does | Default |
|---|---|---|
| `toggle_key` | key that unlocks and locks the overlay | `F8` |
| `font_size` | text size | `13` |
| `max_lines` | lines shown at once | `6` |
| `line_seconds` | seconds before a line fades | `15` |
| `width` | overlay width in pixels | `620` |
| `log_path` | where TF2's `console.log` is | the default Steam folder |

## Removing it

1. Delete the translator folder.
2. In Steam: right-click **Team Fortress 2** > **Properties** > **Launch Options**, and remove
   the options from Step 3.

## Tests

```
python -m unittest discover tests
```
