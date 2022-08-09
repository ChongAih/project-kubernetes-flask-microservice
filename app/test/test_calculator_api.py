import json
import os
import time
import unittest

import app
from app import initialize_calculator_process_qm
from app.calculator.computation.api import handle_terminate, handle_status, handle_evaluate, handle_result
from app.calculator.computation.db import execute, insert_json_message, get_status, create_table
from app.calculator.computation.service import run_calculator_qm_task
from app.util.process_queue_manager import ProcessQueueManager


class TestCalculator(unittest.TestCase):
    qm: ProcessQueueManager = None

    @classmethod
    def setUpClass(cls) -> None:
        initialize_calculator_process_qm()
        create_table()
        cls.qm = app.calculator_qm
        run_calculator_qm_task()

    def test_calculator_api(self):
        payload = {
            "model": "sum_math_cos",
            "number": 0.5
        }

        # Test handle_status by directly inserting message into DB
        task_id = "1234-5678-91011"
        insert_json_message(task_id=task_id, json_message=json.dumps(payload))
        status, status_message = get_status(task_id=task_id)
        self.assertEqual(status, "PROCESSING")
        self.assertEqual(status_message, "PROCESSING")

        response = handle_status(task_id=task_id)
        self.assertEqual(response.response.retcode, 0)
        self.assertEqual(response.response.status, "PROCESSING")
        self.assertEqual(response.response.message, "PROCESSING")

        # Test handle_evaluate
        response = handle_evaluate(data=payload, qm=self.qm)
        task_id = response.task_id
        self.assertEqual(response.response.retcode, 0)
        self.assertEqual(response.response.status, "PROCESSING")
        self.assertEqual(response.response.message, "ok-queued")

        # Test handle_status by calling handle_evaluate
        time.sleep(1)  # To give time for qm to process
        status, status_message = get_status(task_id=task_id)
        self.assertEqual(status, "COMPLETED")
        self.assertEqual(status_message, "COMPLETED")
        response = handle_status(task_id=task_id)
        self.assertEqual(response.response.retcode, 0)
        self.assertEqual(response.response.status, "COMPLETED")
        self.assertEqual(response.response.message, "COMPLETED")

        # Test handle_result
        result = handle_result(task_id=task_id)
        self.assertEqual(result.response.retcode, 0)
        self.assertEqual(result.response.status, "COMPLETED")
        self.assertEqual(result.response.message, "COMPLETED")
        self.assertEqual(result.output, 1000000.0)

    def test_error(self):
        payload = {
            "model": "invalid",
            "number": 0.5
        }

        response = handle_evaluate(data=payload, qm=self.qm)
        task_id = response.task_id
        self.assertEqual(response.response.retcode, 0)
        self.assertEqual(response.response.status, "PROCESSING")
        self.assertEqual(response.response.message, "ok-queued")

        # Test handle_status by calling handle_evaluate
        time.sleep(1)  # To give time for qm to process
        response = handle_status(task_id=task_id)
        self.assertEqual(response.response.retcode, 0)
        self.assertEqual(response.response.status, "ERROR")
        self.assertEqual(response.response.message,
                         "Invalid model - invalid; available models are [sum_math_cos]")

        result = handle_result(task_id=task_id)
        self.assertEqual(result.response.retcode, 1)
        self.assertEqual(result.response.status, "ERROR")
        self.assertEqual(result.response.message,
                         "Invalid model - invalid; available models are [sum_math_cos]")
        self.assertEqual(result.output, -1)

    @classmethod
    def tearDownClass(cls) -> None:
        handle_terminate(cls.qm)
        execute(f"DROP TABLE IF EXISTS {app.config.CALCULATOR_SQLITE_TABLE_NAME}")
        os.remove(os.path.join(app.config.DB_PATH, f'{app.config.CALCULATOR_SQLITE_DB_NAME}.db'))
        cls.qm.stop()
