import time
from threading import Lock

class StateManager:
    def __init__(self):
        self._user_states = {}
        self._lock = Lock()
        self._timeout = 300  # 5分钟

    def set_state(self, user_id, state, temp_data=None):
        with self._lock:
            self._user_states[user_id] = {
                'state': state,
                'timestamp': time.time(),
                'temp_data': temp_data or {}
            }

    def get_state(self, user_id):
        with self._lock:
            info = self._user_states.get(user_id)
            if not info:
                return 'IDLE', {}
            # 超时处理
            if time.time() - info['timestamp'] > self._timeout:
                self._user_states.pop(user_id)
                return 'IDLE', {}
            return info['state'], info['temp_data']

    def clear_state(self, user_id):
        with self._lock:
            self._user_states.pop(user_id, None)

state_manager = StateManager()
