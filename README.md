# TF2 Chat Translator

This program translates the TF2 chat into English during the game.

## Procedure: Install the translator

1. On this page, click the green **Code** button.
2. Click **Download ZIP**.
3. Right-click the ZIP file.
4. Click **Extract All**.
5. Go to [python.org/downloads](https://www.python.org/downloads/).
6. Download Python.
7. Start the Python installer.
8. On the first screen, select the check box **Add python.exe to PATH**.
9. Click **Install Now**.

## Procedure: Set TF2 for the translator (one time only)

1. In Steam, click **Steam > Exit**.
2. Make sure that Steam is fully closed.
3. Open the file **`Start Translator.bat`**.
4. Type **5**.
5. Push **Enter**.
6. Close the window.

## Procedure: Use the translator

1. Start Steam.
2. Start TF2.
3. Open the file **`Start Translator.bat`**.
4. Type the number of the mode. Refer to the table.
5. Push **Enter**.
6. Keep the black window open during the game.

| Number | Mode |
|---|---|
| **1** | The translator translates Russian into English. Only you see the translation. |
| **2** | The translator translates all languages into English. Only you see the translation. |
| **3** | The translator translates Russian into English. All players see the translation in the chat. |
| **4** | The translator translates all languages into English. All players see the translation in the chat. |

To stop the translator, close the black window.

## What option 5 (setup) does

The setup procedure changes only the TF2 launch options in Steam. It does not change TF2 files. It does not install software. It does not use the internet. You can read all of the code in the file `setup_tf2.py`.

The setup procedure does these steps:

1. It makes a random password. The file `config.json` on your computer keeps the password.
2. It makes sure that Steam is closed. Steam deletes changes to its settings when Steam closes.
3. It makes a backup copy of the Steam settings file (`localconfig.vdf`).
4. It adds the options in the table to the TF2 launch options. It keeps your other launch options.

| Option | Function |
|---|---|
| `-condebug` | TF2 writes the chat into the file `console.log`. The translator reads the chat from this file. All modes use this option. |
| `-usercon` | TF2 accepts commands from other programs (RCON). Mode 3 and mode 4 use this option to send the translations to the chat. |
| `+rcon_password <random>` | TF2 accepts commands only from a program that has this password. |
| `+hostport 27069` | The translator connects to TF2 on this port. |
| `+ip 0.0.0.0` and `+net_start` | These options start the network function of TF2 that RCON uses. |

NOTE: With `+ip 0.0.0.0`, computers on your home network can connect to RCON. They must have the random password. Windows Firewall usually blocks connections from outside your home network.

NOTE: The translator sends the chat text to Google Translate and MyMemory for the translation. It does not send other data.

To see the changes, right-click **Team Fortress 2** in Steam. Click **Properties**. Look at **Launch Options**.

## Notes

NOTE: Set TF2 to **Windowed** or **Fullscreen Windowed** mode. If you do not do this, you do not see the translations.

NOTE: To move the translations on the screen, push **F8**. Move the translations with the mouse. Push **F8** again.

NOTE: If Windows shows the message "Windows protected your PC", click **More info**. Then click **Run anyway**.

NOTE: The translator does not translate English text.

## Troubleshooting

| Problem | Action |
|---|---|
| You do not see translations. | Stop TF2. Start TF2 again. |
| The message "Steam is running" shows. | Right-click the Steam icon near the clock. Click **Exit**. Do the setup procedure again. |
| The message "Python isn't installed" shows. | Install Python again. Make sure that you select **Add python.exe to PATH**. |
| Mode 3 or mode 4 does not operate. | Close Steam. Do the setup procedure again. Start TF2. |

<details>
<summary>More information</summary>

**If the setup procedure cannot find Steam:**
1. In Steam, right-click **Team Fortress 2**.
2. Click **Properties**.
3. In **Launch Options**, type `-condebug`.

This option is sufficient for mode 1 and mode 2.

**Settings:**
Close the translator. Then change these settings in the file `config.json` with Notepad:
`toggle_key` (F8), `font_size`, `max_lines`, `line_seconds`, `width`, `log_path`.
Change `log_path` only if TF2 is in a different folder.

**Removal:**
1. Delete the folder of the translator.
2. Remove the options above from the TF2 launch options.

**Tests:** `python -m unittest discover tests`

</details>
