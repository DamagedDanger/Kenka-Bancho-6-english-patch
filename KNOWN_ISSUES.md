# Known issues — 0.9.0-beta

## Not translated (cannot be changed with this kind of patch, or not done yet)

* **Opening movie.** The title art (喧嘩番長6 logo, katakana subtitle) and a few comic sound-effect letters are baked into the video file.
  The movie has no spoken-text subtitles to translate.
* **The game logo** on the title screen and the logo shown on the bottom screen during cutscenes are still the Japanese artwork.
* **Scenery and world textures**: shop signs, posters, banners and other text drawn on 3D objects in the town and school are still in Japanese.
* **Name filter word list** (`menu/cmn/Glob`) is intentionally left alone.
* A few **counters in the executable** keep Japanese units where there was no room for English: `計%d点`, `全%d問`, `%s組`, and some exam wording.

## Things that may look off

* **Text overflow.** Balloons were wrapped by measuring the new font, and menus were fitted by hand, but only the first scenes have been seen running.
  If something overflows a box or balloon, please report it with a screenshot and where it happens.
* **Comic sound effects** are romanised syllables (DO + N = "DON"). They are upright letters; the game rotates and slants them, so some look rougher than the originals.
* **Letters everywhere changed.** The Latin letters of the game's font were redrawn (proportional serif). Digits are fixed-width so number columns line up.
  Japanese characters are untouched.
* **Names.** Character names follow family-name-first order. A few readings of rare kanji (mainly in the staff roll) are best guesses.
* **Image text** was redrawn with a different font than the original lettering; a few shapes (fish cards, comic stamps) may show small remnants of the old marks.

## Platform notes

* **Real 3DS:** not tested on hardware yet. The optional `exheader.bin` (New 3DS speed flags) is untested; delete it if you see crashes.
* **Emulators:** tested only in the first scenes with Azahar (software renderer). The optional per-game settings file needs a real GPU.
* **Saves:** the patch does not touch save data and should work with existing saves, but back them up before trying.

## Reporting a problem

Please include: the screen or scene, a screenshot, whether you use an emulator (which one and version) or a real 3DS, and the text of any error from `kb6_patcher.py`.
