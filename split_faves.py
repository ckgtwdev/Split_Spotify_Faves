"""
Split your Spotify Liked Songs into shuffled 100-track playlists.
The first PRIORITY_PLAYLISTS playlists favour tracks that are
Scandi pop, instrumental-ish, or added in the last 12 months.

Setup (once):
    pip install -U spotipy python-dotenv
    Copy .env.example to .env and fill in your Spotify app credentials
  Redirect URI in your Spotify app must be: http://127.0.0.1:8888/callback

Run with DRY_RUN = True first. It only prints what it would do.
"""
import random
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

CHUNK_SIZE = 100
PRIORITY_PLAYLISTS = 4
NAME_PREFIX = "Faves"
DRY_RUN = True

SCANDI_WORDS = ("swedish", "norwegian", "danish", "finnish", "icelandic", "scandi", "nordic")
INSTRUMENTAL_WORDS = ("instrumental", "ambient", "post-rock", "piano", "classical",
                      "soundtrack", "lo-fi", "lofi", "neoclassical", "downtempo")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-library-read playlist-modify-private playlist-modify-private",
))


def fetch_tracks():
    """Return every Liked Song with its added date and artist ids."""
    tracks, seen, offset = [], set(), 0
    while True:
        page = sp.current_user_saved_tracks(limit=50, offset=offset)
        for entry in page["items"]:
            t = entry.get("track") or entry.get("item")
            if not t or not t.get("uri", "").startswith("spotify:track:"):
                continue
            if t["uri"] in seen:
                continue
            seen.add(t["uri"])
            tracks.append({
                "uri": t["uri"],
                "added": datetime.fromisoformat(entry["added_at"].replace("Z", "+00:00")),
                "artists": [a["id"] for a in t["artists"] if a.get("id")],
            })
        if not page.get("next"):
            return tracks
        offset += 50


genre_cache = {}


def fetch_artist_genres(artist_ids):
    unique_ids = list(set(artist_ids))
    for offset in range(0, len(unique_ids), 50):
        batch = unique_ids[offset:offset + 50]
        try:
            artists = sp.artists(batch).get("artists", [])
        except Exception as exc:
            print(f"Could not fetch artist genres for a batch: {exc}")
            artists = []
        for artist in artists:
            if artist:
                genre_cache[artist["id"]] = artist.get("genres", [])
        for artist_id in batch:
            genre_cache.setdefault(artist_id, [])


tracks = fetch_tracks()
print(f"Found {len(tracks)} unique Liked Songs")

fetch_artist_genres(a for t in tracks for a in t["artists"])

cutoff = datetime.now(timezone.utc) - timedelta(days=365)
for t in tracks:
    genres = [g for a in t["artists"] for g in genre_cache[a]]
    scandi = any("pop" in g and any(w in g for w in SCANDI_WORDS) for g in genres)
    instrumental = any(w in g for g in genres for w in INSTRUMENTAL_WORDS)
    recent = t["added"] >= cutoff
    t["score"] = int(scandi) + int(instrumental) + int(recent)

# Shuffle first, then a stable sort by score: ties stay random.
random.shuffle(tracks)
tracks.sort(key=lambda t: -t["score"])

chunks = [tracks[i:i + CHUNK_SIZE] for i in range(0, len(tracks), CHUNK_SIZE)]
for chunk in chunks:
    random.shuffle(chunk)  # shuffle order within each playlist too

for n, chunk in enumerate(chunks, start=1):
    avg = sum(t["score"] for t in chunk) / len(chunk)
    name = f"{NAME_PREFIX} {n:02d}"
    print(f"{name}: {len(chunk)} tracks, average score {avg:.2f}")
    if DRY_RUN:
        continue
    new = sp.current_user_playlist_create(name, public=False)
    sp.playlist_add_items(new["id"], [t["uri"] for t in chunk])

print("Dry run only. Set DRY_RUN = False to create the playlists." if DRY_RUN else "Done.")
