import json
import os
import time
import unittest

from app import Config, CalculatorMicroservice
from app.calculator.computation.api import handle_terminate, handle_status, handle_evaluate, handle_result
from app.calculator.computation.database import CalculatorDatabase
from app.calculator.computation.service import run_calculator_qm_task
from app.util.process_queue_manager import ProcessQueueManager


class TestCalculator(unittest.TestCase):
    calculator_ms: CalculatorMicroservice = None
    db: CalculatorDatabase = None
    qm: ProcessQueueManager = None
    config: Config = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.calculator_ms = CalculatorMicroservice("test")
        cls.config = cls.calculator_ms.config
        cls.db = cls.calculator_ms.calculator_db
        cls.db.create_table()
        cls.qm = cls.calculator_ms.calculator_qm
        run_calculator_qm_task(cls.calculator_ms)

    def test_calculator_api(self):
        payload = {
            "model": "sum_math_cos",
            "number": 0.5
        }

        # Test handle_status by directly inserting message into DB
        task_id = "1234-5678-91011"
        self.db.insert_json_message(task_id=task_id, json_message=json.dumps(payload))
        status, status_message = self.db.get_status(task_id=task_id)
        self.assertEqual(status, "PROCESSING")
        self.assertEqual(status_message, "PROCESSING")

        response = handle_status(task_id=task_id, ms=self.calculator_ms)
        self.assertEqual(response.response.retcode, 0)
        self.assertEqual(response.response.status, "PROCESSING")
        self.assertEqual(response.response.message, "PROCESSING")

        # Test handle_evaluate
        response = handle_evaluate(data=payload, ms=self.calculator_ms)
        task_id = response.task_id
        self.assertEqual(response.response.retcode, 0)
        self.assertEqual(response.response.status, "PROCESSING")
        self.assertEqual(response.response.message, "ok-queued")

        # Test handle_status by calling handle_evaluate
        time.sleep(1)  # To give time for qm to process
        status, status_message = self.db.get_status(task_id=task_id)
        self.assertEqual(status, "COMPLETED")
        self.assertEqual(status_message, "COMPLETED")
        response = handle_status(task_id=task_id, ms=self.calculator_ms)
        self.assertEqual(response.response.retcode, 0)
        self.assertEqual(response.response.status, "COMPLETED")
        self.assertEqual(response.response.message, "COMPLETED")

        # Test handle_result
        result = handle_result(task_id=task_id, ms=self.calculator_ms)
        self.assertEqual(result.response.retcode, 0)
        self.assertEqual(result.response.status, "COMPLETED")
        self.assertEqual(result.response.message, "COMPLETED")
        self.assertEqual(result.output, 1000000.0)

    def test_error(self):
        payload = {
            "model": "invalid",
            "number": 0.5
        }

        response = handle_evaluate(data=payload, ms=self.calculator_ms)
        task_id = response.task_id
        self.assertEqual(response.response.retcode, 0)
        self.assertEqual(response.response.status, "PROCESSING")
        self.assertEqual(response.response.message, "ok-queued")

        # Test handle_status by calling handle_evaluate
        time.sleep(1)  # To give time for qm to process
        response = handle_status(task_id=task_id, ms=self.calculator_ms)
        self.assertEqual(response.response.retcode, 0)
        self.assertEqual(response.response.status, "ERROR")
        self.assertEqual(response.response.message,
                         "Invalid model - invalid; available models are [sum_math_cos]")

        result = handle_result(task_id=task_id, ms=self.calculator_ms)
        self.assertEqual(result.response.retcode, 1)
        self.assertEqual(result.response.status, "ERROR")
        self.assertEqual(result.response.message,
                         "Invalid model - invalid; available models are [sum_math_cos]")
        self.assertEqual(result.output, -1)

    @classmethod
    def tearDownClass(cls) -> None:
        handle_terminate(cls.qm)
        cls.db.execute(f"DROP TABLE IF EXISTS {cls.config.CALCULATOR_SQLITE_TABLE_NAME}")
        os.remove(os.path.join(cls.config.DB_PATH, f'{cls.config.CALCULATOR_SQLITE_DB_NAME}.db'))
        cls.qm.stop()
