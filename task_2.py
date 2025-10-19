import random
from typing import Dict
import time
from collections import deque

class SlidingWindowRateLimiter:
    def __init__(self, window_size: int = 10, max_requests: int = 1):
        self.window_size = window_size
        self.max_requests = max_requests
        self.history: Dict[str, deque] = {}

    def _cleanup_window(self, user_id: str, current_time: float) -> None:
        dq = self.history.get(user_id)
        if not dq:
            return
        boundary = current_time - self.window_size
        while dq and dq[0] <= boundary:
            dq.popleft()
        if not dq:
            del self.history[user_id]

    def can_send_message(self, user_id: str) -> bool:
        now = time.time()
        self._cleanup_window(user_id, now)
        dq = self.history.get(user_id)
        if dq is None:
            return True
        return len(dq) < self.max_requests

    def record_message(self, user_id: str) -> bool:
        now = time.time()
        self._cleanup_window(user_id, now)
        dq = self.history.get(user_id)
        if dq is None:
            dq = deque()
            self.history[user_id] = dq
        if len(dq) < self.max_requests:
            dq.append(now)
            return True
        return False

    def time_until_next_allowed(self, user_id: str) -> float:
        now = time.time()
        self._cleanup_window(user_id, now)
        dq = self.history.get(user_id)
        if dq is None or len(dq) < self.max_requests:
            return 0.0
        wait = self.window_size - (now - dq[0])
        return max(0.0, wait)

def test_rate_limiter():
    limiter = SlidingWindowRateLimiter(window_size=10, max_requests=1)
    print("\n=== Симуляція потоку повідомлень ===")
    for message_id in range(1, 11):
        user_id = message_id % 5 + 1
        result = limiter.record_message(str(user_id))
        wait_time = limiter.time_until_next_allowed(str(user_id))
        print(f"Повідомлення {message_id:2d} | Користувач {user_id} | "
              f"{'✓' if result else f'× (очікування {wait_time:.1f}с)'}")
        time.sleep(random.uniform(0.1, 1.0))

    print("\nОчікуємо 4 секунди...")
    time.sleep(4)

    print("\n=== Нова серія повідомлень після очікування ===")
    for message_id in range(11, 21):
        user_id = message_id % 5 + 1
        result = limiter.record_message(str(user_id))
        wait_time = limiter.time_until_next_allowed(str(user_id))
        print(f"Повідомлення {message_id:2d} | Користувач {user_id} | "
              f"{'✓' if result else f'× (очікування {wait_time:.1f}с)'}")
        time.sleep(random.uniform(0.1, 1.0))

if __name__ == "__main__":
    test_rate_limiter()
