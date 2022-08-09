import json
import os
import time
import unittest
import uuid
from multiprocessing import Queue
from queue import Full, Empty

from app.util.logger import logger
from app.util.process_queue_manager import ProcessQueueManager


def task(queue: Queue):
    logger.info(f"Process-{os.getpid()} is running")
    while queue:
        try:
            payload = json.loads(queue.get_nowait())
        except Empty:
            logger.info(f'Queue is empty, exiting')
            break
        import time
        time.sleep(1)
        logger.info(f'Payload: {payload}; processed by: Process-{os.getpid()}; queue size: {queue.qsize()}')
        if payload['api'] == 'terminate':
            break


class TestThreadPriorityQueueManager(unittest.TestCase):
    qm: ProcessQueueManager = None
    max_limit = 10
    queue_block_timeout = 0.5

    @classmethod
    def setUpClass(cls) -> None:
        cls.qm = ProcessQueueManager(parallelism=2, service="test", max_limit=cls.max_limit,
                                     queue_block_timeout=cls.queue_block_timeout)

    # Test by lexographical order
    def test_1_kill_message(self):
        task_id = str(uuid.uuid4())
        self.qm.enqueue(json.dumps({'task_id': task_id, 'api': 'compute'}))
        self.qm.enqueue(json.dumps({'task_id': str(uuid.uuid4()), 'api': 'compute'}))
        self.qm.enqueue(json.dumps({'task_id': str(uuid.uuid4()), 'api': 'compute'}))
        self.qm.enqueue(json.dumps({'task_id': task_id, 'api': 'kill'}))
        self.qm.enqueue(json.dumps({'task_id': str(uuid.uuid4()), 'api': 'terminate'}))
        self.assertEqual(self.qm.qsize(), 5)

    def test_2_queue_limit(self):
        with self.assertRaises(Full):
            for _ in range(self.max_limit * 10):
                self.qm.enqueue(json.dumps({'task_id': str(uuid.uuid4()), 'api': 'compute'}))
        self.assertEqual(self.qm.is_full(), True)

    def test_3_consumers(self):
        self.qm.consumers(task)
        # Allocate processing time
        time.sleep(10)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.qm.stop()
