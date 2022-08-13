import json
import os
from datetime import datetime
from multiprocessing import Queue
from queue import Empty

from app import CalculatorMicroservice, Config
from app.calculator.computation.database import CalculatorDatabase
from app.calculator.computation.model import Model
from app.util.logger import logger
from app.util.process_queue_manager import ProcessQueueManager


def task(queue: Queue, db: CalculatorDatabase, config: Config):
    def wrapper(data: dict):
        if data["api"] == "compute":
            try:
                model_name = data.get("model")
                num = int(data.get("number"))
                computation_model = Model.model_mapping.get(model_name, None)
                if not computation_model:
                    model_names = ",".join(Model.model_mapping.keys())
                    raise Exception(f"Invalid model - {model_name}; available models are [{model_names}]")
                else:
                    output = computation_model(num=num)
                    db.update_status_output_message(task_id=data["task_id"],
                                                    status="COMPLETED",
                                                    status_message="COMPLETED",
                                                    output=output)
            except Exception as e:
                db.update_status_output_message(task_id=data["task_id"],
                                                status="ERROR",
                                                status_message=str(e),
                                                output=-1.0)
        else:
            logger.info("Unsupported api type")

    while queue:
        # Block and wait if no incoming message in child process - not affecting parent process
        try:
            payload = json.loads(queue.get(block=True, timeout=config.QUEUE_BLOCK_TIMEOUT))
            logger.info(f"Task is being executed by Process-{os.getpid()}...")
            if payload["api"] == "terminate":
                break
            else:
                wrapper(data=payload)
        except Empty:
            logger.info(f"Queue is empty, rechecking by Process-{os.getpid()}...")


def startup_workflow(qm: ProcessQueueManager, db: CalculatorDatabase):
    messages = db.get_json_messages(event_time=int(datetime.now().strftime('%s')))
    for message in messages:
        qm.enqueue(message)


def run_calculator_qm_task(ms: CalculatorMicroservice):
    qm: ProcessQueueManager = ms.calculator_qm
    db: CalculatorDatabase = ms.calculator_db
    config: Config = ms.config
    qm.consumers(task, db, config)
    startup_workflow(qm, db)
