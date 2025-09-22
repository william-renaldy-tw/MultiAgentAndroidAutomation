# app/controller.py

import time
import hashlib
from typing import Optional
import json

from app.config import settings
from app.chatroom import ChatRoom
from app.orchestrator import run_next_step

from app.appium_controller import AppiumController

def hash_content(content: str) -> str:
    """Return an MD5 hash of any string content."""
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def run_task(task: str, max_iterations: int = settings.MAX_ITERATIONS, sleep_between: int = 2,
             driver=None, chatroom=None, task_status=None
             ) -> ChatRoom:
    """
    Run the full browser automation loop for the given user task.

    Args:
        task: Task description from user
        max_iterations: Max number of cycles to run
        sleep_between: Seconds to wait between iterations

    Returns:
        ChatRoom instance containing full interaction history
    """
    driver = AppiumController(
        appium_server_url=settings.APPIUM_SERVER_URL
    )
    driver.setup_driver()
    if not chatroom:
        chatroom = ChatRoom()


    task_status = "In Progress"
    
    chatroom.add_message("User", "task", task)

    prev_error: Optional[str] = None

    for iteration in range(1, max_iterations + 1):
        print(f"\nIteration {iteration} started.")

        if driver.driver is not None:
            screenshot = driver.take_screenshot()
            if screenshot["success"]:
                chatroom.add_message("Controller", "screen_image", screenshot["screenshot_path"])


        result = run_next_step(chatroom, driver, time)

        if result == "done":
            print("Task completed.")
            task_status = "Completed"
            chatroom.add_message("Controller", "feedback", "Task completed successfully.")
            break
        elif result == "wait_user":
            print("Awaiting user input or response...")
            task_status = "Paused"
            chatroom.add_message("Controller", "feedback", "Waiting for user input.")
            break

        time.sleep(sleep_between)


    else:
        print("⏹️ Max iterations reached. Ending task.")
        task_status = "Max Iterations Reached"

    
    with open("debug_chatroom.json", "w", encoding="utf-8") as f:
        json.dump(chatroom.get_history(), f, indent=2, ensure_ascii=False)
    print("Chatroom history saved to debug_chatroom.json")

    return driver, chatroom, task_status