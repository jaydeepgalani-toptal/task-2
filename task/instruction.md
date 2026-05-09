I'm rebuilding an old modded game profile from a forum thread, and the download manager everyone used back then is dead. The target mod page still exists on the local forum, but it describes its dependencies only in normal forum post text. Some dependencies have their own release threads with their own dependency notes, and some newer-looking files are actually incompatible with this profile.

The workspace contains a downloader project with a fixed entrypoint and CLI. Running it against the Skyforge Overhaul thread today produces a downloads/ directory that has too many files and the wrong versions of some dependencies: required archives are missing, extras are present, and version selection does not match what the forum text says.

Diagnose what the downloader is doing wrong, fix it, and confirm that a clean rerun of its documented command produces only the required release archives for the target profile in downloads/.

The target mod is **Skyforge Overhaul**. The forum is reachable at http://localhost:8080, also exposed as FORUM_URL. The downloader's documented command is:

./bin/download-mods --forum-url "$FORUM_URL" --target "Skyforge Overhaul" --out downloads/
Treat the forum prose as the authoritative spec. The rules for what counts as a required dependency and which version satisfies a stated requirement are in the forum content itself. Read the forum pages carefully. “Newest” is not automatically correct.

You may repair parsing, traversal, constraint solving, or downloading logic in any way you prefer. The entrypoint name and CLI signature are fixed, but the implementation is yours. You may use raw HTTP, curl, wget, Python HTTP clients, or any installed tool. Do not modify forum data, attachment files, tests, package metadata, protected helper scripts, or server setup. Do not hardcode the final file list and do not fabricate zip files. The required archives must come from the local forum's attachment links.

The verifier reruns the documented command from a clean downloads/ directory, repeats it for determinism, and may also rerun it against a separate forum fixture with the same page structure but different version choices.