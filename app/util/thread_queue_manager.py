import concurrent.futures
import json
import threading
from datetime import datetime
from queue import PriorityQueue, Full

import app
from app.util.logger import logger


class ThreadPriorityQueueManager:
    def __init__(self, service: str = None, parallelism: int = None, max_limit: int = None,
                 queue_block_timeout: float = None):
        self.service = service
        self.parallelism = parallelism if parallelism else app.config.CONSUMER_PARALLELISM
        self.max_limit = max_limit if max_limit else app.config.QUEUE_SIZE
        self.queue_block_timeout = queue_block_timeout if queue_block_timeout else app.config.QUEUE_BLOCK_TIMEOUT
        self.queue = dict()
        logger.info(
            f'ThreadPriorityQueueManager for {service} with {self.parallelism} parallelism and {self.max_limit} queue size '
            f'initialized by Thread-{threading.current_thread()}')

    def start(self):
        logger.info(f'ThreadPriorityQueueManager for {self.service} queues are started')
        for i in range(self.parallelism):
            self.queue[i] = PriorityQueue(self.max_limit)

    def enqueue(self, data: str):
        payload = json.loads(data)
        task_id: str = payload['task_id']
        api: str = payload['api']
        if api == 'kill':
            priority = 0
        elif api == 'compute':
            priority = int(datetime.now().strftime('%s'))
        else:  # terminate
            priority = int(datetime.now().strftime('%s')) * 2
        bucket_id: int = hash(task_id) % self.parallelism
        queue: PriorityQueue = self.queue[bucket_id]
        try:
            if not self.queue_block_timeout:
                queue.put_nowait((priority, data))
            else:
                queue.put((priority, data), block=True, timeout=self.queue_block_timeout)
        except Full:
            logger.info(f'Queue[{bucket_id}] is full')
            raise Full

    def is_full(self, idx=0) -> bool:
        queue: PriorityQueue = self.queue[idx]
        return queue.full()

    def is_empty(self, idx=0) -> bool:
        queue: PriorityQueue = self.queue[idx]
        return queue.empty()

    def consumers(self, fn):
        with concurrent.futures.ThreadPoolExecutor(self.parallelism) as executor:
            futures = []
            for idx in range(self.parallelism):
                futures.append(executor.submit(fn, self.queue[idx]))

            for future in concurrent.futures.as_completed(futures):
                if future.exception():
                    logger.error(f"Exception encountered executing threading process: {future.exception()}")
