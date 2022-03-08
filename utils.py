import csv
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Tuple
from typing import Iterable

HEADER_ROW = ('Track', 'Artist', 'Album', 'Added by', 'Date added', 'Duration')


def item_to_track(item: Dict) -> Tuple[str, ...]:
    track_name = item['track']['name']
    artist = ', '.join([record['name'] for record in item['track']['artists']])
    album = item['track']['album']['name']
    added_by = item['added_by']['id']
    added_at = str(datetime.fromisoformat(item['added_at'].rstrip('Z')))
    duration_ms = timedelta(milliseconds=item['track']['duration_ms'])
    duration = f'{duration_ms.seconds // 60}:{duration_ms.seconds % 60}'

    return track_name, artist, album, added_by, added_at, duration


def save_playlist_as_csv(header_row: Iterable[str], items: Iterable) -> str:
    with tempfile.NamedTemporaryFile(mode='wt', delete=False) as fh:
        writer = csv.writer(fh)
        writer.writerow(header_row)

        for item in items:
            track = item_to_track(item)
            writer.writerow(track)

        return fh.name


def delete_temp_file(path: str):
    if os.path.exists(path):
        os.remove(path)
