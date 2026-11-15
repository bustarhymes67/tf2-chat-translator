# TF2 Chat Translator

Translates TF2 chat to English while you play.

## How to set it up

**1. Download it**
Click the green **Code** button above, then **Download ZIP**. Right-click the ZIP and choose **Extract All**.

**2. Install Python**
Get it from [python.org/downloads](https://www.python.org/downloads/).
On the first screen of the installer, **tick "Add python.exe to PATH"**, then click **Install Now**.

**3. Run Setup (only once)**
Quit Steam completely: **Steam > Exit** in Steam's top-left menu.
Open **`Start Translator.bat`**, type **5** and press **Enter**.

**4. Play**
Start Steam and TF2. Open **`Start Translator.bat`** again and pick a mode:

| Type | What happens |
|---|---|
| **1** | Russian → English, only you see it |
| **2** | All languages → English, only you see it |
| **3** | Russian → English, said in chat for everyone |
| **4** | All languages → English, said in chat for everyone |

Keep the black window open while you play. Closing it stops the translator.

## Good to know

- Run TF2 in **Windowed** or **Fullscreen Windowed** mode, or you won't see the translations.
- Press **F8** in game to move the overlay. Press **F8** again to lock it.
- If Windows says *"Windows protected your PC"*, click **More info** and then **Run anyway**.

## Not working?

- **Nothing shows up:** restart TF2 after running Setup. English lines are never translated.
- **"Steam is running":** right-click the Steam icon next to the clock and choose **Exit**, then run Setup again.
- **"Python isn't installed":** install Python again and tick **Add python.exe to PATH**.
- **Modes 3 and 4 don't work:** quit Steam, run Setup (5) again, then start TF2.

<details>
<summary>More details (settings, removing it)</summary>

**What Setup changes:** it adds these to TF2's launch options and keeps the ones you already had:
`-condebug -usercon +ip 0.0.0.0 +rcon_password <random> +hostport 27069 +net_start`
The password is random and stays in `config.json` on your PC.

**If Setup can't find Steam** (it isn't in `C:\Program Files (x86)\Steam`): in Steam, right-click
**Team Fortress 2** > **Properties** > **Launch Options**, and add `-condebug`. That's enough for modes 1 and 2.

**Settings:** you can change these in `config.json` with Notepad, while the translator is closed:
`toggle_key` (F8), `font_size`, `max_lines`, `line_seconds`, `width`, and `log_path`
(only needed if TF2 is installed somewhere else).

**Removing it:** delete the folder, and remove the options above from TF2's launch options.

**Tests:** `python -m unittest discover tests`

</details>
