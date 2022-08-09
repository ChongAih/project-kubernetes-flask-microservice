import json
from datetime import datetime
from multiprocessing import Queue
from queue import Empty

import app
from app.calculator.computation.db import get_json_messages, update_status_output_message
from app.calculator.computation.model import model_mapping
from app.util.logger import logger
from app.util.process_queue_manager import ProcessQueueManager


def task(queue: Queue):
    def wrapper(data: dict):
        if data["api"] == "compute":
            try:
                model_name = data.get("model")
                num = int(data.get("number"))
                computation_model = model_mapping.get(model_name, None)
                if not computation_model:
                    model_names = ",".join(model_mapping.keys())
                    raise Exception(f"Invalid model - {model_name}; available models are [{model_names}]")
                else:
                    output = computation_model(num=num)
                    update_status_output_message(task_id=data["task_id"],
                                                 status="COMPLETED",
                                                 status_message="COMPLETED",
                                                 output=output)
            except Exception as e:
                update_status_output_message(task_id=data["task_id"],
                                             status="ERROR",
                                             status_message=str(e),
                                             output=-1.0)
        else:
            logger.info("Unsupported api type")

    while queue:
        # Block and wait if no incoming message
        try:
            payload = json.loads(queue.get(block=True, timeout=app.config.QUEUE_BLOCK_TIMEOUT))
            if payload["api"] == "terminate":
                break
            else:
                wrapper(data=payload)
        except Empty:
            logger.info("Queue is empty, rechecking...")


def startup_workflow(qm: ProcessQueueManager):
    messages = get_json_messages(event_time=int(datetime.now().strftime('%s')))
    for message in messages:
        qm.enqueue(message)


def run_calculator_qm_task():
    qm = app.calculator_qm
    qm.consumers(task)
    startup_workflow(qm)
