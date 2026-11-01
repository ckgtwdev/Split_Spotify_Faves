# Split Spotify Faves

Split your Spotify Liked Songs into shuffled playlists of up to 100 tracks. Tracks are ranked so playlists created earlier favour songs added in the last year, Scandi pop, and instrumental-related genres.

## Requirements

- Python 3.9 or later
- A Spotify account and a Spotify Developer application

## Setup

Install the project dependencies:

```powershell
python -m pip install -r requirements.txt
```

In your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), create or select an app and set its Redirect URI to:

```text
http://127.0.0.1:8888/callback
```

Copy the example environment file and enter the app's client ID and client secret in `.env`:

```powershell
Copy-Item .env.example .env
```

Edit `.env` with your credentials. It is excluded by `.gitignore`, so your secrets won't be committed. Keep `.env.example` as the template; do not put real credentials in it.

## Run

```powershell
python .\split_faves.py
```

The first run opens a browser so you can authorize access. The script reads your Liked Songs and artist genres, prints the playlist sizes and average scores, and by default runs in dry-run mode without creating playlists.

Review the output first. To create playlists, change `DRY_RUN = True` to `DRY_RUN = False` near the top of `split_faves.py`, then run it again. It creates new private playlists named `Faves 01`, `Faves 02`, and so on; it does not update or remove playlists from earlier runs.

## Run for another user

You can run the script on your computer for someone else. If your Spotify app is in Development Mode, add their Spotify account as an allowed user in the Spotify Developer Dashboard. They must sign in to their own Spotify account in the browser and approve access; do not ask them to share their password. The script reads their Liked Songs and creates playlists in their account; it does not change their Liked Songs.

Spotipy saves the authorized account's token in `.cache`. Before switching to another user, remove the cache so the script prompts them to authorize their own account:

```powershell
if (Test-Path .cache) { Remove-Item .cache }
```

Deleting `.cache` does not sign the browser out of Spotify. Before running the script for another user, also sign out of Spotify in the browser that opens (or switch to a browser profile signed into their account). Check that the authorization page shows their account before approving access.

The cache contains account access tokens. Keep it private and remove it when you are finished. `.cache` is excluded by `.gitignore`.

## How ranking works

Each track receives one point for each matching condition:

- Added to your Liked Songs in the last 365 days
- An artist genre includes a Scandi/Nordic country or region and `pop`
- An artist genre includes a listed instrumental-related term, such as `ambient`, `classical`, or `soundtrack`

Tracks are sorted by score, with randomized ordering among ties. Each group contains at most 100 tracks and is shuffled before it is added to a playlist. Artist genre data may be unavailable; those tracks are still included and simply do not receive genre-based points.

The script requests permission to read your library and create public or private playlists. It creates private playlists. `PRIORITY_PLAYLISTS` is currently defined in the script but does not affect the ranking or playlist creation.