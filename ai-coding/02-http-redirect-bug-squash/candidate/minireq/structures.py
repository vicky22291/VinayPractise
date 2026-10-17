"""Data structures used by minireq."""
from collections.abc import Mapping, MutableMapping


class CaseInsensitiveDict(MutableMapping):
    """A dict whose keys compare case-insensitively but keep the case they were set with.

        >>> h = CaseInsensitiveDict({"Content-Type": "text/plain"})
        >>> h["content-type"]
        'text/plain'
        >>> list(h)
        ['Content-Type']
    """

    def __init__(self, data=None, **kwargs):
        self._store = {}
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (cased for cased, _ in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        return ((lower, pair[1]) for lower, pair in self._store.items())

    def __eq__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        other = CaseInsensitiveDict(other)
        return dict(self.lower_items()) == dict(other.lower_items())

    def copy(self):
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return str(dict(self.items()))
