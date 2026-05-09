from __future__ import annotations

from copy import deepcopy


def attachment(filename: str, mod: str, version: str, badge: str | None = None) -> dict[str, str | None]:
    return {"filename": filename, "mod": mod, "version": version, "badge": badge}


def post(author: str, posted: str, body_html: str, kind: str = "reply", attachments: list[dict] | None = None) -> dict:
    return {
        "author": author,
        "posted": posted,
        "kind": kind,
        "body_html": body_html.strip(),
        "attachments": attachments or [],
    }


def fixture_default() -> dict:
    return {
        "name": "default",
        "threads": [
            {
                "slug": "corelib",
                "title": "CoreLib — shared utilities for the Skyforge ecosystem",
                "posts": [
                    post(
                        "corelib_maintainer",
                        "2026-03-22",
                        """
                        <p>CoreLib provides shared utilities used across several mods. Each CoreLib release in the 1.x line is built against <strong>ScriptBridge v5.1 exactly</strong> — older or newer ScriptBridge will not link. Pick the latest stable 1.x patch unless a downstream mod tells you otherwise.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("corelib-1.2.0.zip", "corelib", "1.2.0"),
                            attachment("corelib-1.3.5.zip", "corelib", "1.3.5"),
                            attachment("corelib-1.4.0.zip", "corelib", "1.4.0"),
                            attachment("corelib-1.4.5.zip", "corelib", "1.4.5", "latest 1.x"),
                            attachment("corelib-1.5.0-beta2.zip", "corelib", "1.5.0-beta2", "Beta, not for production"),
                        ],
                    ),
                    post(
                        "toolsmith_ray",
                        "2026-03-24",
                        "<p>1.4 tightened up a few utility wrappers for us. Thanks for keeping the API tidy.</p>",
                    ),
                ],
            },
            {
                "slug": "frostbite-tweaks",
                "title": "Frostbite Tweaks 1.9.0",
                "posts": [
                    post(
                        "icestorm_mods",
                        "2026-03-27",
                        """
                        <p>Frostbite Tweaks bundles a colder palette and a few combat pacing changes for northern maps. I tested this with CoreLib 1.3 and it seems fine, but it is not a requirement and I am not shipping integration for Skyforge.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("frostbite-tweaks-1.9.0.zip", "frostbite-tweaks", "1.9.0"),
                            attachment("frostbite-tweaks-2.0.0-beta1.zip", "frostbite-tweaks", "2.0.0-beta1", "Beta"),
                            attachment("frostbite-wallpaper-pack.zip", "frostbite-wallpaper-pack", "art-pack", "Screenshots"),
                        ],
                    ),
                ],
            },
            {
                "slug": "modding-roundtable",
                "title": "Modding Roundtable: spring thread",
                "posts": [
                    post(
                        "forum_admin",
                        "2026-04-01",
                        """
                        <p>General discussion thread for WIP projects, testing notes, and screenshots. Someone asked whether TerrainKit 2.1 was worth trying; consensus was that the stable branch is still the safer option for people who just want to play.</p>
                        """,
                        kind="op",
                    ),
                ],
            },
            {
                "slug": "scriptbridge",
                "title": "ScriptBridge — scripting runtime",
                "posts": [
                    post(
                        "scriptbridge_dev",
                        "2026-03-25",
                        """
                        <p>ScriptBridge is the scripting runtime. The 5.1 line is feature-frozen and stable. The 5.2 line introduces a breaking ABI change — do not mix 5.1 consumers with 5.2 runtimes.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("scriptbridge-5.0.4.zip", "scriptbridge", "5.0.4"),
                            attachment("scriptbridge-5.1.0.zip", "scriptbridge", "5.1.0"),
                            attachment("scriptbridge-5.1.2.zip", "scriptbridge", "5.1.2", "stable, recommended"),
                            attachment("scriptbridge-5.1.5.zip", "scriptbridge", "5.1.5", "latest 5.1.x"),
                            attachment("scriptbridge-5.2.0-rc1.zip", "scriptbridge", "5.2.0-rc1"),
                            attachment("scriptbridge-5.2.0.zip", "scriptbridge", "5.2.0"),
                        ],
                    ),
                    post(
                        "scriptbridge_dev",
                        "2026-03-29",
                        """
                        <p>Heads up: 5.1.5 is broken on Linux due to a packaging mistake — pin to 5.1.2 if you're on Linux. Will be fixed in 5.1.6 when we cut it.</p>
                        """,
                    ),
                ],
            },
            {
                "slug": "skyforge-overhaul",
                "title": "Skyforge Overhaul 3.4.1 — Stable Release",
                "posts": [
                    post(
                        "mod_author_kira",
                        "2026-04-09",
                        """
                        <p>Skyforge Overhaul 3.4.1 is the current stable release. To install, you'll also need:</p>
                        <ul>
                          <li><strong>CoreLib v1.2+</strong> (the shared library)</li>
                          <li><strong>TerrainKit 2.0.x only</strong> — do not use TerrainKit 2.1, the API changed and Skyforge will fail to load.</li>
                        </ul>
                        <p>Recommended companion mods (not required): Skyforge HD Texture Pack, Skyforge Ambient Music Pack. These are nice but you do not need them to play.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("skyforge-overhaul-3.4.1.zip", "skyforge-overhaul", "3.4.1"),
                            attachment("skyforge-overhaul-3.5.0-rc1.zip", "skyforge-overhaul", "3.5.0-rc1", "Preview build, do not use for stable profiles"),
                            attachment("skyforge-overhaul-3.3.0.zip", "skyforge-overhaul", "3.3.0", "Previous stable, kept for reference"),
                            attachment("skyforge-hd-textures-1.0.zip", "skyforge-hd-textures", "1.0", "Optional companion"),
                            attachment("skyforge-music-pack-2.1.zip", "skyforge-music-pack", "2.1", "Optional companion"),
                            attachment("skyforge-overhaul-3.4.1-source.zip", "skyforge-overhaul", "3.4.1-source", "Source archive for modders"),
                            attachment("skyforge-screenshots.zip", "skyforge-screenshots", "press-kit", "Screenshots and press kit"),
                        ],
                    ),
                    post(
                        "mod_author_kira",
                        "2026-04-11",
                        """
                        <p>PINNED — Important update for 3.4.1: due to a regression in CoreLib's entity loader, <strong>CoreLib must be exactly 1.4.0</strong>. Versions 1.4.1 through 1.4.5 contain a memory leak that corrupts save files in long sessions. The OP still says v1.2+ because I haven't edited it yet — if you're installing fresh, treat the requirement as CoreLib 1.4.0 specifically until a fixed CoreLib release lands.</p>
                        """,
                        kind="pinned",
                    ),
                    post("ember_glade", "2026-04-12", "<p>Installed cleanly after I stopped trying the preview build. Great release.</p>"),
                    post("talonforge", "2026-04-13", "<p>Works great here. The terrain transitions look much better than 3.3.</p>"),
                ],
            },
            {
                "slug": "skyforge-overhaul-legacy-mirror",
                "title": "Skyforge Overhaul 3.3 mirror",
                "title_html": "<s>Skyforge Overhaul 3.3 mirror</s> <span class=\"badge\">Superseded — use main thread</span>",
                "posts": [
                    post(
                        "vault_keeper",
                        "2026-02-16",
                        """
                        <p><s>Mirror for people who needed the old 3.3 package while the main post was briefly offline.</s> Use the main thread now.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("vaultcopy-330.zip", "vaultcopy", "3.3.0", "Superseded — use main thread"),
                        ],
                    ),
                ],
            },
            {
                "slug": "terrainkit",
                "title": "TerrainKit — terrain generation toolkit",
                "posts": [
                    post(
                        "terrainkit_team",
                        "2026-03-20",
                        """
                        <p>TerrainKit handles terrain generation. Requires <strong>WeatherHooks &gt;=0.9.5, &lt;1.0</strong> — the 1.0 line broke our integration and we have not migrated yet. The 2.0.x line of TerrainKit is the maintained branch; 2.1.0 was an experimental rewrite that was abandoned and is not recommended.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("terrainkit-1.9.2.zip", "terrainkit", "1.9.2"),
                            attachment("terrainkit-2.0.3.zip", "terrainkit", "2.0.3"),
                            attachment("terrainkit-2.0.5.zip", "terrainkit", "2.0.5", "latest 2.0.x"),
                            attachment("terrainkit-2.1.0.zip", "terrainkit", "2.1.0", "Experimental, abandoned"),
                            attachment("terrainkit-2.2.0-dev.zip", "terrainkit", "2.2.0-dev", "Dev preview"),
                        ],
                    ),
                ],
            },
            {
                "slug": "weatherhooks",
                "title": "WeatherHooks — environmental hooks",
                "posts": [
                    post(
                        "weatherhooks_dev",
                        "2026-03-18",
                        """
                        <p>WeatherHooks provides environmental callbacks. The 0.9.x line is stable. The 1.0 line is a rewrite using a different callback model and is not source-compatible with 0.9.x consumers.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("weatherhooks-0.9.4.zip", "weatherhooks", "0.9.4"),
                            attachment("weatherhooks-0.9.5.zip", "weatherhooks", "0.9.5"),
                            attachment("weatherhooks-0.9.8.zip", "weatherhooks", "0.9.8", "latest 0.9.x"),
                            attachment("weatherhooks-1.0.0.zip", "weatherhooks", "1.0.0"),
                            attachment("weatherhooks-1.0.1-rc1.zip", "weatherhooks", "1.0.1-rc1"),
                        ],
                    ),
                ],
            },
            {
                "slug": "wildlands-photo-pack",
                "title": "Wildlands Photo Pack",
                "posts": [
                    post(
                        "lensflare",
                        "2026-03-30",
                        """
                        <p>Collection of promotional screenshots and loading-screen captures. No gameplay assets are included.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("wildlands-photo-pack-2026.zip", "wildlands-photo-pack", "2026"),
                        ],
                    ),
                ],
            },
        ],
    }


def fixture_hidden() -> dict:
    return {
        "name": "hidden",
        "threads": [
            {
                "slug": "corelib",
                "title": "CoreLib — shared utilities for the Skyforge ecosystem",
                "posts": [
                    post(
                        "corelib_maintainer",
                        "2026-03-22",
                        """
                        <p>CoreLib provides shared utilities used across several mods. Each CoreLib release in the 2.x line is built against <strong>ScriptBridge v6.4 exactly</strong> — older or newer ScriptBridge will not link. Pick the latest stable 2.x patch unless a downstream mod tells you otherwise.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("corelib-2.0.4.zip", "corelib", "2.0.4"),
                            attachment("corelib-2.1.3.zip", "corelib", "2.1.3"),
                            attachment("corelib-2.2.1.zip", "corelib", "2.2.1"),
                            attachment("corelib-2.2.4.zip", "corelib", "2.2.4", "latest 2.x"),
                            attachment("corelib-2.3.0-beta1.zip", "corelib", "2.3.0-beta1", "Beta, not for production"),
                        ],
                    ),
                ],
            },
            {
                "slug": "frostbite-tweaks",
                "title": "Frostbite Tweaks 2.4.0",
                "posts": [
                    post(
                        "icestorm_mods",
                        "2026-04-01",
                        """
                        <p>Frostbite Tweaks now has a harder survival profile. I tried it next to CoreLib 2.1 during testing, but that was just a side experiment and not a requirement.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("frostbite-tweaks-2.4.0.zip", "frostbite-tweaks", "2.4.0"),
                            attachment("frostbite-tweaks-2.5.0-rc1.zip", "frostbite-tweaks", "2.5.0-rc1", "Preview"),
                        ],
                    ),
                ],
            },
            {
                "slug": "modding-roundtable",
                "title": "Modding Roundtable: summer thread",
                "posts": [
                    post(
                        "forum_admin",
                        "2026-04-03",
                        """
                        <p>General discussion thread for works in progress, screenshots, and casual testing chatter. One post mentioned TerrainKit 3.4 out of curiosity, but nobody was treating it as a dependency baseline.</p>
                        """,
                        kind="op",
                    ),
                ],
            },
            {
                "slug": "scriptbridge",
                "title": "ScriptBridge — scripting runtime",
                "posts": [
                    post(
                        "scriptbridge_dev",
                        "2026-03-25",
                        """
                        <p>ScriptBridge is the scripting runtime. The 6.4 line is feature-frozen and stable. The 6.5 line introduces a breaking ABI change — do not mix 6.4 consumers with 6.5 runtimes.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("scriptbridge-6.3.9.zip", "scriptbridge", "6.3.9"),
                            attachment("scriptbridge-6.4.0.zip", "scriptbridge", "6.4.0"),
                            attachment("scriptbridge-6.4.1.zip", "scriptbridge", "6.4.1", "stable, recommended"),
                            attachment("scriptbridge-6.4.3.zip", "scriptbridge", "6.4.3", "latest 6.4.x"),
                            attachment("scriptbridge-6.5.0-rc1.zip", "scriptbridge", "6.5.0-rc1"),
                            attachment("scriptbridge-6.5.0.zip", "scriptbridge", "6.5.0"),
                        ],
                    ),
                    post(
                        "scriptbridge_dev",
                        "2026-03-31",
                        """
                        <p>Heads up: 6.4.3 is broken on Linux due to a packaging mistake — pin to 6.4.1 if you're on Linux. Will be fixed in 6.4.4 when we cut it.</p>
                        """,
                    ),
                ],
            },
            {
                "slug": "skyforge-overhaul",
                "title": "Skyforge Overhaul 4.0.2 — Stable Release",
                "posts": [
                    post(
                        "mod_author_kira",
                        "2026-04-09",
                        """
                        <p>Skyforge Overhaul 4.0.2 is the current stable release. To install, you'll also need:</p>
                        <ul>
                          <li><strong>CoreLib v2.0+</strong> (the shared library)</li>
                          <li><strong>TerrainKit 3.3.x only</strong> — do not use TerrainKit 3.4, the API changed and Skyforge will fail to load.</li>
                        </ul>
                        <p>Recommended companion mods (not required): Skyforge HD Texture Pack, Skyforge Soundscape Pack. These are nice but you do not need them to play.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("skyforge-overhaul-4.0.2.zip", "skyforge-overhaul", "4.0.2"),
                            attachment("skyforge-overhaul-4.1.0-rc2.zip", "skyforge-overhaul", "4.1.0-rc2", "Preview build, do not use for stable profiles"),
                            attachment("skyforge-overhaul-3.9.8.zip", "skyforge-overhaul", "3.9.8", "Previous stable, kept for reference"),
                            attachment("skyforge-hd-textures-1.4.zip", "skyforge-hd-textures", "1.4", "Optional companion"),
                            attachment("skyforge-soundscape-pack-3.0.zip", "skyforge-soundscape-pack", "3.0", "Optional companion"),
                            attachment("skyforge-overhaul-4.0.2-source.zip", "skyforge-overhaul", "4.0.2-source", "Source archive for modders"),
                            attachment("skyforge-gallery.zip", "skyforge-gallery", "press-kit", "Screenshots and press kit"),
                        ],
                    ),
                    post(
                        "mod_author_kira",
                        "2026-04-11",
                        """
                        <p>PINNED — Important update for 4.0.2: due to a regression in CoreLib's entity loader, <strong>CoreLib must be exactly 2.2.1</strong>. Versions 2.2.2 through 2.2.4 contain a memory leak that corrupts save files in long sessions. The OP still says v2.0+ because I haven't edited it yet — if you're installing fresh, treat the requirement as CoreLib 2.2.1 specifically until a fixed CoreLib release lands.</p>
                        """,
                        kind="pinned",
                    ),
                    post("ember_glade", "2026-04-12", "<p>Installed cleanly after I stopped trying the preview build. Great release.</p>"),
                ],
            },
            {
                "slug": "skyforge-overhaul-legacy-mirror",
                "title": "Skyforge Overhaul 3.9 mirror",
                "title_html": "<s>Skyforge Overhaul 3.9 mirror</s> <span class=\"badge\">Superseded — use main thread</span>",
                "posts": [
                    post(
                        "vault_keeper",
                        "2026-02-16",
                        """
                        <p><s>Mirror for people who needed the old 3.9 package while the main post was briefly offline.</s> Use the main thread now.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("vaultcopy-398.zip", "vaultcopy", "3.9.8", "Superseded — use main thread"),
                        ],
                    ),
                ],
            },
            {
                "slug": "terrainkit",
                "title": "TerrainKit — terrain generation toolkit",
                "posts": [
                    post(
                        "terrainkit_team",
                        "2026-03-20",
                        """
                        <p>TerrainKit handles terrain generation. Requires <strong>WeatherHooks &gt;=1.8.2, &lt;2.0</strong> — the 2.0 line broke our integration and we have not migrated yet. The 3.3.x line of TerrainKit is the maintained branch; 3.4.0 was an experimental rewrite that was abandoned and is not recommended.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("terrainkit-3.2.9.zip", "terrainkit", "3.2.9"),
                            attachment("terrainkit-3.3.4.zip", "terrainkit", "3.3.4"),
                            attachment("terrainkit-3.3.7.zip", "terrainkit", "3.3.7", "latest 3.3.x"),
                            attachment("terrainkit-3.4.0.zip", "terrainkit", "3.4.0", "Experimental, abandoned"),
                            attachment("terrainkit-3.5.0-dev.zip", "terrainkit", "3.5.0-dev", "Dev preview"),
                        ],
                    ),
                ],
            },
            {
                "slug": "weatherhooks",
                "title": "WeatherHooks — environmental hooks",
                "posts": [
                    post(
                        "weatherhooks_dev",
                        "2026-03-18",
                        """
                        <p>WeatherHooks provides environmental callbacks. The 1.8.x line is stable. The 2.0 line is a rewrite using a different callback model and is not source-compatible with 1.8.x consumers.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("weatherhooks-1.8.1.zip", "weatherhooks", "1.8.1"),
                            attachment("weatherhooks-1.8.2.zip", "weatherhooks", "1.8.2"),
                            attachment("weatherhooks-1.8.6.zip", "weatherhooks", "1.8.6", "latest 1.8.x"),
                            attachment("weatherhooks-2.0.0.zip", "weatherhooks", "2.0.0"),
                            attachment("weatherhooks-2.0.1-rc1.zip", "weatherhooks", "2.0.1-rc1"),
                        ],
                    ),
                ],
            },
            {
                "slug": "wildlands-photo-pack",
                "title": "Wildlands Photo Pack",
                "posts": [
                    post(
                        "lensflare",
                        "2026-03-30",
                        """
                        <p>Collection of promotional screenshots and loading-screen captures. No gameplay assets are included.</p>
                        """,
                        kind="op",
                        attachments=[
                            attachment("wildlands-photo-pack-2027.zip", "wildlands-photo-pack", "2027"),
                        ],
                    ),
                ],
            },
        ],
    }


def get_fixtures() -> dict[str, dict]:
    return {
        "default": deepcopy(fixture_default()),
        "hidden": deepcopy(fixture_hidden()),
    }
