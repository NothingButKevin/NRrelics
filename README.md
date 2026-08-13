# NRrelics Deck CLI

An SSH-first Steam Deck port of [NRrelics](https://github.com/limbic07/NRrelics) for *Elden Ring Nightreign*.

This fork deliberately has no desktop window. Run it from a Mac terminal after connecting to the Deck with SSH. It manages Nightreign saves and the same `presets.json` schema used by the upstream tool, so existing preset rules can be reused without conversion.

## What Works

- Detects the SteamOS Proton save location for Nightreign (`2622380`)
- Lists, creates, and restores local save backups; restore makes a safety copy first
- Creates and edits general/dedicated normal or Deepnight preset rules
- Maintains Deepnight blacklist rules
- Searches the bundled Chinese affix vocabulary
- Runs entirely through an SSH terminal; no Deck desktop window, mouse, or keyboard is required

The original OCR, vocabulary correction, shop loop, and repository loop are retained. The Deck CLI swaps only their Windows capture/input/window dependencies for SteamOS-compatible adapters, then launches the unchanged original loops from SSH.

## Install On Deck

From the cloned repository on the Deck:

```bash
chmod +x scripts/install-deck.sh
./scripts/install-deck.sh
cd ~/Applications/NRrelics-Deck-CLI
```

The installer only copies this repository into `~/Applications/NRrelics-Deck-CLI` and creates `~/.local/bin/nrrelics`. It does not modify SteamOS or install system packages.

Reconnect with SSH, then run:

```bash
nrrelics status
nrrelics saves backup --name before-relic-cleanup
nrrelics shell
```

If `~/.local/bin` is not in the SSH session's `PATH`, run `~/Applications/NRrelics-Deck-CLI/nrrelics.py` instead.

For the existing Deck offline OCR setup, run the included wrapper instead. It reuses `~/Mods/NRrelics-Deck/py312` and its already-downloaded OCR models:

```bash
~/Mods/NRrelics-Deck-CLI/scripts/run-deck-cli.sh doctor
```

## Commands

```bash
# Detect the real SteamOS Proton path and current save
nrrelics status
nrrelics doctor
nrrelics screen
nrrelics input f

# Back up, inspect, and restore a save
nrrelics saves list
nrrelics saves backup --name before-shopping
nrrelics saves restore before-shopping --yes

# Search the Chinese affix vocabulary, then add it to the normal general preset
nrrelics presets normal search 攻击
nrrelics presets normal add "攻击力提升"
nrrelics presets normal list

# Create a dedicated build preset and add a rule to it
nrrelics presets normal create Tank
nrrelics presets normal add "生命力提升" --preset PASTE_THE_PRINTED_ID
nrrelics presets normal disable PASTE_THE_PRINTED_ID

# Manage Deepnight exclusions
nrrelics presets deepnight blacklist-add "受到伤害增加"
nrrelics presets deepnight blacklist-list

# Run the original automatic purchase/filter loop from SSH
nrrelics shop normal --stop-currency 5000

# Run the original automatic repository sell loop from SSH
nrrelics repo sell normal --count 100 --yes
```

`nrrelics shell` accepts the same commands without repeating `nrrelics`; use `exit` when finished.

`screen` writes a screenshot from the currently visible Deck session. `input` sends one named key to the current focused window through `xdotool` or `ydotool`; it does not create a window or move focus. Steam Deck's game mode uses the existing `ffmpeg + xdotool` XWayland path; `grim + ydotool` is a fallback. Run `nrrelics doctor` first to see which helper is available.

## Save Location

On Steam Deck, the detected path is:

```text
~/.local/share/Steam/steamapps/compatdata/2622380/pfx/drive_c/users/steamuser/AppData/Roaming/Nightreign/<SteamID64>/NR0000.sl2
```

The CLI's own data is stored under `~/.local/share/nrrelics-deck/`. Set `NRRELICS_STEAM_ROOT` or `NRRELICS_DATA_DIR` only when testing or using a nonstandard Steam installation.

## Development

The default CLI requires only Python 3.10+. Run its checks with:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall nrrelics_deck
```

## License

This fork retains the upstream MIT license. See [LICENSE](LICENSE).
