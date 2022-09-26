from threading import Event

from watchdog.events import PatternMatchingEventHandler

class Handler(PatternMatchingEventHandler):
    def __init__(self, reload_evt: Event, *args):
        super().__init__(*args)
        self.reload = reload_evt

    def on_created(self, e):
        self.reload.set()

    def on_deleted(self, e):
        self.reload.set()

    def on_moved(self, e):
        self.reload.set()

    def on_closed(self, e):
        self.reload.set()