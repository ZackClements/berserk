# -*- coding: utf-8 -*-
import collections
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional


def to_millis(dt: datetime) -> int:
    """Return the milliseconds between the given datetime and the epoch.

    :param datetime dt: a datetime
    :return: milliseconds since the epoch
    :rtype: int
    """
    return int(dt.timestamp() * 1000)


def datetime_from_seconds(ts: float) -> datetime:
    """Return the datetime for the given seconds since the epoch.

    UTC is assumed. The returned datetime is timezone aware.

    :return: timezone aware datetime
    :rtype: :class:`datetime`
    """
    return datetime.fromtimestamp(ts, timezone.utc)


def datetime_from_millis(millis: float) -> datetime:
    """Return the datetime for the given millis since the epoch.

    UTC is assumed. The returned datetime is timezone aware.

    :return: timezone aware datetime
    :rtype: :class:`datetime`
    """
    return datetime_from_seconds(millis / 1000)


def datetime_from_str(dt_str: str) -> datetime:
    """Convert the time in a string to a datetime.

    UTC is assumed. The returned datetime is timezone aware. The format
    must match ``%Y-%m-%dT%H:%M:%S.%fZ``.

    :return: timezone aware datetime
    :rtype: :class:`datetime`
    """
    dt = datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    return dt.replace(tzinfo=timezone.utc)


_RatingHistoryEntry = collections.namedtuple('Entry', 'year month day rating')


def rating_history(data):
    return _RatingHistoryEntry(*data)


def inner(func: Callable, *keys: str) -> Callable:
    def convert(data: Dict[str, int]) -> Dict[str, int]:
        for k in keys:
            try:
                data[k] = func(data[k])
            except KeyError:
                pass  # normal for keys to not be present sometimes
        return data

    return convert


def listing(func):
    def convert(items):
        result = []
        for item in items:
            result.append(func(item))
        return result

    return convert


def noop(arg: str) -> str:
    return arg


def build_adapter(mapper: Dict[str, str], sep: str = '.') -> Callable:
    """Build a data adapter.

    Uses a map to pull values from an object and assign them to keys.
    For example:

    .. code-block:: python

        >>> mapping = {
        ...   'broadcast_id': 'broadcast.id',
        ...   'slug': 'broadcast.slug',
        ...   'name': 'broadcast.name',
        ...   'description': 'broadcast.description',
        ...   'syncUrl': 'broadcast.sync.url',
        ... }

        >>> cast = {'broadcast': {'id': 'WxOb8OUT',
        ...   'slug': 'test-tourney',
        ...   'name': 'Test Tourney',
        ...   'description': 'Just a test',
        ...   'ownerId': 'rhgrant10',
        ...   'sync': {'ongoing': False, 'log': [], 'url': None}},
        ...  'url': 'https://lichess.org/broadcast/test-tourney/WxOb8OUT'}

        >>> adapt = build_adapter(mapping)
        >>> adapt(cast)
        {'broadcast_id': 'WxOb8OUT',
        'slug': 'test-tourney',
        'name': 'Test Tourney',
        'description': 'Just a test',
        'syncUrl': None}

    :param dict mapper: map of keys to their location in an object
    :param str sep: nested key delimiter
    :return: adapted data
    :rtype: dict
    """

    def get(data: Dict[str, Any], location: str) -> str:
        for key in location.split(sep):
            data = data[key]
        return data

    def adapter(
        data: Dict[str, Any],
        default: Optional[object] = None,
        fill: bool = False,
    ) -> Dict[str, Any]:
        result = {}
        for key, loc in mapper.items():
            try:
                result[key] = get(data, loc)
            except KeyError:
                if fill:
                    result[key] = default
        return result

    return adapter
