# Kenka Bancho 6: Soul & Blood — English Patch

**Version 0.9.0-beta** · fan translation · 3DS (Japanese version, title ID `00040000000F4F00`, product code `CTR-P-BC6J`)

This patch turns the Japanese 3DS game *Kenka Bancho 6: Soul & Blood* (喧嘩番長6 ソウル&ブラッド) into an English game.
It works on the **Azahar / Citra-style emulators** and on a **real 3DS running Luma3DS**.

> **This is a beta.** Almost everything has been checked in image previews and in the first scenes of the game, but not played through.
> Please read [KNOWN_ISSUES.md](KNOWN_ISSUES.md) and report anything that overflows, looks wrong or is still in Japanese.

![balloon](screenshots/balloon_1.png)

## What is translated

* All story dialogue, cutscenes, and speech balloons (auto-wrapped to fit, in a rebuilt serif font in the same weight as the original)
* Menus, items, clothing, skills, missions, phone messages, shops, hideout and the memo book
* Most text that is part of images: pause menu and screen titles, tutorials, minigame rules and results, ranking battle, game-over screen,
  stamps, fish guide, comic sound effects (romanised), and the staff roll
* Hard-coded prompts such as "Skip this scene? Yes / No"

What is **not** translated is listed in [KNOWN_ISSUES.md](KNOWN_ISSUES.md) (the opening movie, the title logo, and signs on the town scenery).

## What you need

1. **Your own copy of the Japanese game.** This package contains **no game files**, only the differences (see "How it works"). You must supply a dump of a game you own.
   It must be the original, unmodified **Japanese version** and **decrypted**:
   a `.3ds` / `.cci` / `.cxi` / `.cia` file, **or** a folder with the extracted RomFS
   (in Azahar: right-click the game in the list and choose *Dump RomFS*; the menu wording may differ between versions).
2. **Python 3.8 or newer** (free, from python.org). On Windows tick *"Add python.exe to PATH"* when installing. Only the standard library is used.
3. An emulator (**[Azahar](https://azahar-emu.org)** recommended; Citra-based forks use the same folders) **or** a 3DS with Luma3DS.

## Step 1 — create the English files

**Windows:** unzip the package, then drag your game file (or the RomFS folder) onto **`Apply patch (Windows).bat`**.

**macOS / Linux:** open Terminal in the unzipped folder and run

```
python3 kb6_patcher.py "/path/to/your/game.3ds"
```

The tool checks that the game is the right version, builds the English files and puts them in a new folder called **`KB6_English_Output`**.
(Run `python3 kb6_patcher.py --help` for options, e.g. `--target azahar` or `--target luma`.)

If it complains, see *Troubleshooting* below. Your original dump is never modified.

## Step 2 — install

### Azahar / Citra (PC, Mac, Linux)

1. Start Azahar and choose **File → Open Azahar Folder** (this is the emulator's *user folder*).
2. Copy **`KB6_English_Output/azahar_or_citra/load`** into that folder (merge if asked). You should end up with
   `load/mods/00040000000F4F00/romfs/...` and `load/mods/00040000000F4F00/exefs/code.ips`.
3. **Restart the game** (mods are read when the game starts).
4. Optional but recommended: copy **`KB6_English_Output/azahar_or_citra/config`** into the same user folder.
   It adds per-game settings: 3x internal resolution, CPU clock 300% (about New 3DS speed, fewer slowdowns) and custom textures on.
   It needs a real GPU; delete `config/custom/00040000000F4F00.ini` to go back to your normal settings.

### Real 3DS (Luma3DS)

1. Copy **`KB6_English_Output/luma3ds/luma`** to the **root of your SD card**, merging with the existing `luma` folder.
   You get `luma/titles/00040000000F4F00/romfs/...`, `code.ips` and an optional `exheader.bin`.
2. Hold **SELECT** while the console boots to open the Luma3DS configuration and turn on **"Enable game patching"**.
3. Start the game as usual (from the cartridge or an installed copy of the Japanese game).

`exheader.bin` only matters on **New 3DS / New 2DS XL**: it asks the system for the faster CPU speed. It is untested on hardware; **delete it if the game ever crashes**.

## Troubleshooting

* **"python is not recognized" / nothing happens:** install Python (see above) and make sure it is on PATH; on Windows the launcher also tries `py -3`.
* **"the game data looks ENCRYPTED":** use a decrypted dump, or dump the RomFS in Azahar and pass that folder to the patcher instead.
* **"differs from the expected Japanese version" / "executable does not match":** your dump is a different version, region or has been modified.
  This patch only supports the original Japanese release. Forcing it with `--force` is not recommended and can break the game.
* **The game is still in Japanese:** the `load` folder is in the wrong place (it must be inside the emulator's *user folder*), the game was not restarted,
  or the folder name is not exactly `00040000000F4F00`. Check that a file like `load/mods/00040000000F4F00/romfs/text/text.zdp` exists.
* **Real 3DS:** make sure *Enable game patching* is switched on in the Luma3DS menu.
* **Slow in the emulator:** use the Vulkan renderer on a machine with a real GPU. The built-in software renderer is far too slow to play.

## How it works

`kb6_patch.dat` contains, for each changed game file, a compact delta (new English text, redrawn image areas, the rebuilt font).
`kb6_patcher.py` reads the matching file from **your** dump, verifies it against a checksum, applies the delta, and verifies the result.
The package does not contain any complete game file. Checksums of the package are in `checksums.sha256`.

## Credits and legal

* Translation, image editing, font and tools: **[Luke Nelson]**
* Machine-assisted translation (Claude by Anthropic) with human direction; proofreading and corrections from the community are very welcome.
* *Kenka Bancho* is © Spike Chunsoft. This is an unofficial, free fan project, not affiliated with or endorsed by the publisher.
  Please support the official release. **Do not ask for, or share, game files.**
