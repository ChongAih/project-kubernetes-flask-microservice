import json
import uuid
from sqlite3 import Error as SQLiteError
from typing import Dict

from app.calculator.computation.db import get_status, get_result, insert_json_message
from app.calculator.model.model import Response, Result, CommonResponse
from app.util.logger import logger
from app.util.process_queue_manager import ProcessQueueManager


def handle_evaluate(data: Dict, qm: ProcessQueueManager) -> Response:
    data["api"] = "compute"
    task_id = str(uuid.uuid4())
    data["task_id"] = task_id
    logger.info(f"Computation API [evaluate] request task_id={data['task_id']}")
    if not qm.is_full():
        # Persist message into database
        try:
            insert_json_message(task_id=task_id, json_message=json.dumps(data))
        except SQLiteError as e:
            msg = f"Failed to persist input message to database - {str(e)}"
            logger.error(msg)
            return Response(task_id=task_id, response=CommonResponse(
                retcode=1, status="ERROR", message=msg))
        qm.enqueue(json.dumps(data))
        return Response(task_id=task_id, response=CommonResponse(
            retcode=0, status="PROCESSING", message="ok-queued"))
    else:
        return Response(task_id=task_id, response=CommonResponse(
            retcode=1, status="FAILED", message="queue-full"))


def handle_status(task_id: str) -> Response:
    logger.info(f"Computation API [status] request task_id={task_id}")
    try:
        status, status_message = get_status(task_id=task_id)
    except SQLiteError as e:
        return Response(task_id=task_id, response=CommonResponse(
            retcode=1, status="ERROR", message=str(e)))
    return Response(task_id=task_id, response=CommonResponse(
        retcode=0, status=status, message=status_message))


def handle_result(task_id: str) -> Result:
    logger.info(f"Computation API [result] request task_id={task_id}")
    try:
        status, output, status_message = get_result(task_id=task_id)
    except SQLiteError as e:
        return Result(task_id=task_id,
                      response=CommonResponse(retcode=1, status="ERROR", message=str(e)),
                      output=-1.0)
    retcode = 1 if status == "ERROR" else 0
    return Result(task_id=task_id,
                  response=CommonResponse(retcode=retcode, status=status, message=status_message),
                  output=output)


def handle_terminate(qm) -> None:
    logger.info(f"Computation API [terminate] requested")
    qm.enqueue(json.dumps({"task_id": "abc-efg-xyz-123", "api": "terminate"}))
