from memory_store import add_event


class EventBus:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type, handler):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(handler)

    def publish(self, event_type, payload):
        add_event(event_type, payload)

        handlers = self.subscribers.get(event_type, [])

        for handler in handlers:
            handler(payload)
