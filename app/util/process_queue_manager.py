import multiprocessing
import os
from queue import Full, Empty
from typing import List, Optional

from app.util.logger import logger


class ProcessQueueManager:
    def __init__(self, service: str = None, parallelism: int = None, max_limit: int = None,
                 queue_block_timeout: float = None):
        self.service = service
        self.parallelism = parallelism
        self.max_limit = max_limit
        self.queue_block_timeout = queue_block_timeout
        self.manager: Optional[multiprocessing.managers.SyncManager] = None
        self.queue: Optional[multiprocessing.Queue] = None
        self.processes: List[multiprocessing.Process] = []
        self.queue_setup = False
        self.task_setup = False
        logger.info(
            f"ProcessQueueManager-{service} with {self.parallelism} parallelism and {self.max_limit} queue size "
            f"initialized by Process-{os.getpid()}")
        self._start()

    def _start(self):
        if not self.queue_setup:
            logger.info(f"ProcessQueueManager-{self.service} manager, queues are started by Process-{os.getpid()}")
            # New child process will get spawn on top of parent process for manager
            self.manager = multiprocessing.Manager()
            self.queue = self.manager.Queue(self.max_limit)
            self.queue_setup = True

    def stop(self):
        if self.manager:
            logger.info(f'ProcessQueueManager-{self.service} manager is shut down by Process-{os.getpid()}')
            self.manager.shutdown()
        for i, process in enumerate(self.processes):
            logger.info(f'ProcessQueueManager-{self.service} process-{i} is cancelled by Process-{os.getpid()}')
            process.terminate()

    def enqueue(self, data: str):
        try:
            if not self.queue_block_timeout:
                self.queue.put_nowait(data)
            else:
                self.queue.put(data, block=True, timeout=self.queue_block_timeout)
        except Full:
            logger.info(f"Queue is full, please try again later")
            raise Full

    def dequeue(self):
        try:
            if not self.queue_block_timeout:
                output = self.queue.get_nowait()
            else:
                output = self.queue.get(block=True, timeout=self.queue_block_timeout)
            return output
        except Empty:
            logger.info(f'Queue is empty, please try again later')
            return None

    def is_full(self) -> bool:
        return self.queue.full()

    def is_empty(self) -> bool:
        return self.queue.empty()

    def qsize(self) -> int:
        return self.queue.qsize()

    def consumers(self, fn, *args):
        if not self.task_setup:
            logger.info(f"ProcessQueueManager-{self.service} processes are started by Process-{os.getpid()}")
            for _ in range(self.parallelism):
                # New child process will get spawn on top of parent process
                process = multiprocessing.Process(target=fn, args=(self.queue, *args))
                process.start()
                self.processes.append(process)
            self.task_setup = True
        else:
            logger.info(f"ProcessQueueManager-{self.service} processes have been started already")
