from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional
import re

@dataclass
class Post:
    id: str
    topic_id: str
    author: str
    date: datetime
    content_original: str
    content_translated: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data['date'] = self.date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Post':
        # Handle date if it's a string
        if isinstance(data.get('date'), str):
            try:
                data['date'] = datetime.fromisoformat(data['date'])
            except ValueError:
                # Fallback if isoformat fails (should not happen if created via to_dict)
                pass
        return cls(**data)

    @staticmethod
    def parse_spanish_date(date_str: str) -> datetime:
        """
        Parses a Spanish date string into a datetime object.
        Handles:
        - ISO strings (from data attributes)
        - "Hoy a las HH:MM"
        - "Ayer a las HH:MM"
        - "DD de Month de YYYY"
        - "DD MMM YYYY"
        """
        if not date_str:
            return datetime.now()

        # Try ISO first (often found in <time> tags)
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            pass

        now = datetime.now()
        date_str_lower = date_str.lower().strip()

        # Relative dates
        if 'hoy' in date_str_lower:
            # Extract time
            time_match = re.search(r'(\d{1,2})[:\.](\d{2})', date_str_lower)
            if time_match:
                return now.replace(hour=int(time_match.group(1)), minute=int(time_match.group(2)), second=0, microsecond=0)
            return now

        if 'ayer' in date_str_lower:
            yesterday = now - timedelta(days=1)
            time_match = re.search(r'(\d{1,2})[:\.](\d{2})', date_str_lower)
            if time_match:
                return yesterday.replace(hour=int(time_match.group(1)), minute=int(time_match.group(2)), second=0, microsecond=0)
            return yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

        if 'hace' in date_str_lower and 'minuto' in date_str_lower:
            minutes = re.search(r'(\d+)', date_str_lower)
            if minutes:
                return now - timedelta(minutes=int(minutes.group(1)))
            return now

        # Spanish Month Mapping
        months = {
            'enero': 1, 'feb': 2, 'febrero': 2, 'mar': 3, 'marzo': 3,
            'abr': 4, 'abril': 4, 'may': 5, 'mayo': 5, 'jun': 6, 'junio': 6,
            'jul': 7, 'julio': 7, 'ago': 8, 'agosto': 8, 'sep': 9, 'septiembre': 9,
            'oct': 10, 'octubre': 10, 'nov': 11, 'noviembre': 11, 'dic': 12, 'diciembre': 12
        }

        # Try parsing "DD de Month de YYYY" or "DD Month YYYY"
        # Remove "de" and extra spaces
        clean_str = date_str_lower.replace(' de ', ' ').replace(',', '').split()

        # Look for day, month, year
        day, month, year = None, None, None
        time_part = None

        for part in clean_str:
            if part.isdigit():
                val = int(part)
                if val > 1900: year = val
                elif val <= 31 and day is None: day = val
                elif val <= 31: pass # potential ambiguity, usually day comes first
            elif part in months:
                month = months[part]
            elif ':' in part:
                 # Time extraction HH:MM
                 try:
                     h, m = part.split(':')
                     time_part = (int(h), int(m))
                 except: pass

        if not year: year = now.year # Default to current year if missing
        if not day: day = 1

        if month:
            dt = datetime(year, month, day)
            if time_part:
                dt = dt.replace(hour=time_part[0], minute=time_part[1])
            return dt

        return now # Fail safe
