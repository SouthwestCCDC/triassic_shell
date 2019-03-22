import json
import time
import datetime
import os
import pickle

storage = None

DELAY_SLEEP = 0.15

class FenceSegment():
    def __init__(self, id, dinosaur_name):
        self.id = id
        self.dinosaur = dinosaur_name
        self._state = 1.0
        self._enabled = True

    def get_state_slow(self):
        return self.state

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        if self._state - value < 0:
            self._state = 0
        else:
            self._state = value
        if not self._state:
            self.enabled = False
        self._p_changed = True

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value
        self._p_changed = True

    def fence_status(self):
        if self.state == 0.0:
            return 'unreach'
        if not self.enabled:
            return 'pwroff'
        if self.state < 0.3:
            return 'fail'
        elif self.state < 1.0:
            return 'degrad'
        else:
            return 'ok'

    def resync(self):
        if self.state == 1.0:
            pass # TODO UH OH YOU BROKE IT
        elif self.state:
            self.state = 1.0
        else:
            # If we resync an unreachable node,
            #  we will also have to power it back up.
            self.state = 1.0
            self.enabled = False

def load_from_disk():
    global fence_segments
    global storage
    if not storage:
        return
    with open(storage, 'rb') as f:
        fence_segments = pickle.load(f)

def save_to_disk():
    global fence_segments
    global storage
    if not storage:
        return
    with open(storage, 'wb') as f:
        pickle.dump(fence_segments, f)

def init_db(filepath):
    global fence_segments
    global storage

    if filepath:
        storage = filepath
        try:
            with open(storage, 'rb') as f:
                fence_segments = pickle.load(f)
                return
        except:
            pass

    fence_segments = dict()
    
    for id in range(0x10000+10111, 0xfffff, 10111): # 97 elements
        if id % 5 == 0:
            dino_name = 'velociraptor'
        elif id % 4 == 0:
            dino_name = 'tyrannosaurus'
        elif id % 3 == 0:
            dino_name = 'guaibasaurus'
        else:
            dino_name = 'triceratops'

        fence_segments[id] = FenceSegment(
            id,
            dino_name,
        )
    
    save_to_disk()
