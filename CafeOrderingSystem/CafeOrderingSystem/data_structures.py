class ChainedHashTable:
    """Manually implemented hash table using separate chaining."""
    def __init__(self, capacity=17):
        self.capacity = capacity
        self.buckets = [[] for _ in range(capacity)]
        self.size = 0

    def _index(self, key):
        return hash(key) % self.capacity

    def insert(self, key, value):
        bucket = self.buckets[self._index(key)]
        for i, (existing_key, _existing_value) in enumerate(bucket):
            if existing_key == key:
                bucket[i] = (key, value)
                return
        bucket.append((key, value))
        self.size += 1

    def search(self, key):
        for existing_key, value in self.buckets[self._index(key)]:
            if existing_key == key:
                return value
        return None

    def delete(self, key):
        bucket = self.buckets[self._index(key)]
        for i, (existing_key, _value) in enumerate(bucket):
            if existing_key == key:
                del bucket[i]
                self.size -= 1
                return True
        return False


class _QueueNode:
    def __init__(self, value):
        self.value = value
        self.next = None


class OrderQueue:
    """Manually implemented linked queue; first order in is first order out."""
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def enqueue(self, value):
        node = _QueueNode(value)
        if self.tail is None:
            self.head = self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self.size += 1

    def dequeue(self):
        if self.head is None:
            return None
        value = self.head.value
        self.head = self.head.next
        if self.head is None:
            self.tail = None
        self.size -= 1
        return value

    def peek(self):
        return None if self.head is None else self.head.value

    def is_empty(self):
        return self.head is None
