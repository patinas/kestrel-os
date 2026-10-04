# Optional launchers

The guarded VM-only installer defaults to no game launchers. Set `KESTREL_GAME_LAUNCHERS=lutris`, `steam`, or `both`, or use `KESTREL_INTERACTIVE=yes` for a prompt. Steam needs explicit local `KESTREL_STEAM_TERMS_ACCEPTED=yes`; review https://store.steampowered.com/subscriber_agreement/ first. No Steam proprietary binary is bundled in the live ISO. Desktop mode remains available without Steam; gaming mode is unavailable without Steam. Selected launcher package names and the installed package inventory are recorded under /usr/share/kestrel.

Lutris: official Arch extra, GPL-3.0-only, https://archlinux.org/packages/extra/any/lutris/. Steam: official Arch multilib, proprietary subscriber agreement, https://archlinux.org/packages/multilib/x86_64/steam/. Heroic and Bottles have GPL-3.0 AUR entries but no reviewed install route here: https://aur.archlinux.org/packages/heroic-games-launcher-bin and https://aur.archlinux.org/packages/bottles?all_deps=1. They are not offered as working options.

CI verification is pending for both no-games and Lutris installation. Selecting Steam does not buy games or sign into a Valve account.
