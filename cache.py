from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int = 50):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key not in self.cache:
            return None
        # move key to end because it was recently used
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key, value):
        self.cache[key] = value
        self.cache.move_to_end(key)

        # if cache exceeds capacity, remove least recently used
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

# global cache object
status_cache = LRUCache(capacity=100)
