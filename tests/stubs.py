"""Stand-ins for what the tests do not have: a Flet page."""


class StubPage:
    """What the app asks of a Flet page; the threads and tasks run on the spot."""

    def __init__(self):
        self.controls = []
        self.updates = 0
        self.width = None
        self.tasks = []

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        self.updates += 1

    def run_thread(self, handler, *args, **kwargs):
        handler(*args, **kwargs)

    def run_task(self, handler, *args, **kwargs):
        self.tasks.append((handler, args, kwargs))

    def scroll_to(self, **kwargs):
        pass
