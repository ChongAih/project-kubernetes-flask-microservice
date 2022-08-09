import json
import os
import threading
import unittest
import uuid
from queue import PriorityQueue, Full, Empty

from app.util.logger import logger
from app.util.thread_queue_manager import ThreadPriorityQueueManager


def task(consumer: PriorityQueue):
    logger.info(f"Process-{os.getpid()}, Thread-{threading.current_thread()} is running")
    while consumer:
        try:
            payload = json.loads(consumer.get()[1])
        except Empty:
            logger.info(f'Queue is empty, exiting')
            break
        logger.info(payload)
        if payload['api'] == 'terminate':
            break


class TestThreadPriorityQueueManager(unittest.TestCase):
    qm: ThreadPriorityQueueManager = None
    max_limit = 10
    queue_block_timeout = 0.5

    @classmethod
    def setUpClass(cls) -> None:
        cls.qm = ThreadPriorityQueueManager(parallelism=1, service="test", max_limit=cls.max_limit,
                                            queue_block_timeout=cls.queue_block_timeout)
        cls.qm.start()

    def test_kill_message(self):
        task_id = str(uuid.uuid4())
        self.qm.enqueue(json.dumps({'task_id': task_id, 'api': 'compute'}))
        self.qm.enqueue(json.dumps({'task_id': str(uuid.uuid4()), 'api': 'compute'}))
        self.qm.enqueue(json.dumps({'task_id': str(uuid.uuid4()), 'api': 'compute'}))
        self.qm.enqueue(json.dumps({'task_id': task_id, 'api': 'kill'}))
        self.qm.enqueue(json.dumps({'task_id': str(uuid.uuid4()), 'api': 'terminate'}))
        # First message should be api - kill because of high priority
        self.assertEqual(json.loads(self.qm.queue.get(0).get()[1])['api'], 'kill')
        self.assertEqual(self.qm.queue.get(0).qsize(), 4)
        self.qm.consumers(task)

    def test_queue_limit(self):
        with self.assertRaises(Full):
            for _ in range(self.max_limit * 10):
                self.qm.enqueue(json.dumps({'task_id': str(uuid.uuid4()), 'api': 'compute'}))
        self.assertEqual(self.qm.is_full(), True)
