import multiprocessing
import os
from queue import Full, Empty
from typing import List, Optional

import app
from app.util.logger import logger


# https://github.com/vterron/lemon/blob/d60576bec2ad5d1d5043bcb3111dff1fcb58a8d6/methods.py#L536-L573
class SharedCounter(object):
    """
    A synchronized shared counter.
    The locking done by multiprocessing.Value ensures that only a single
    process or thread may read or write the in-memory ctypes object. However,
    in order to do n += 1, Python performs a read followed by a write, so a
    second process may read the old value before the new one is written by the
    first process. The solution is to use a multiprocessing.Lock to guarantee
    the atomicity of the modifications to Value.
    This class comes almost entirely from Eli Bendersky's blog:
    http://eli.thegreenplace.net/2012/01/04/shared-counter-with-pythons-multiprocessing/
    """

    def __init__(self, n: int = 0):
        self.count = multiprocessing.Value('i', n)

    def increment(self, n: int = 1):
        """ Increment the counter by n (default = 1) """
        with self.count.get_lock():
            self.count.value += n

    @property
    def value(self):
        """ Return the value of the counter """
        return self.count.value


class ProcessQueueManager:
    def __init__(self, service: str = None, parallelism: int = None, max_limit: int = None,
                 queue_block_timeout: float = None):
        self.service = service
        self.parallelism = parallelism if parallelism else app.config.CONSUMER_PARALLELISM
        self.max_limit = max_limit if max_limit else app.config.QUEUE_SIZE
        self.queue_block_timeout = queue_block_timeout if queue_block_timeout else app.config.QUEUE_BLOCK_TIMEOUT
        self.manager: Optional[multiprocessing.managers.SyncManager] = None
        self.queue: Optional[multiprocessing.Queue] = None
        self.size: Optional[SharedCounter] = None
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
            """
            Because of multithreading / multiprocessing semantics, Queue.qsize() may
            raise the NotImplementedError exception on Unix platforms like Mac OS X
            where sem_getvalue() is not implemented. This subclass addresses this
            problem by using a synchronized shared counter (initialized to zero) and
            increasing / decreasing its value every time the put() and get() methods
            are called, respectively. This not only prevents NotImplementedError from
            being raised, but also allows us to implement a reliable version of both
            qsize() and empty().
            """
            self.size = SharedCounter(0)
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
            self.size.increment(1)
        except Full:
            logger.info(f"Queue is full, please try again later")
            raise Full

    def dequeue(self):
        try:
            if not self.queue_block_timeout:
                output = self.queue.get_nowait()
            else:
                output = self.queue.get(block=True, timeout=self.queue_block_timeout)
            self.size.increment(-1)
            return output
        except Empty:
            logger.info(f'Queue is empty, please try again later')
            return None

    def is_full(self) -> bool:
        return self.queue.full()

    def is_empty(self) -> bool:
        return self.queue.empty()

    def qsize(self) -> int:
        try:
            return self.queue.qsize()
        except Exception:
            return self.size.value

    def consumers(self, fn):
        if not self.task_setup:
            logger.info(f"ProcessQueueManager-{self.service} processes are started by Process-{os.getpid()}")
            for _ in range(self.parallelism):
                # New child process will get spawn on top of parent process
                process = multiprocessing.Process(target=fn, args=(self.queue,))
                process.start()
                self.processes.append(process)
            self.task_setup = True
        else:
            logger.info(f"ProcessQueueManager-{self.service} processes have been started already")
