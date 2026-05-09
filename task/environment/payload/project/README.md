## Mod Downloader

Download release archives for a target mod thread from a forum:

```bash
./bin/download-mods --forum-url "$FORUM_URL" --target "Skyforge Overhaul" --out downloads/
```

Arguments:

- `--forum-url` base URL for the forum
- `--target` thread title fragment for the target mod
- `--out` output directory for downloaded archives
