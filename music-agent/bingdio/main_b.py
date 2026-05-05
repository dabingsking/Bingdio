"""Bingody B-mode entry point."""

import logging
import queue
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bingdio.b")


def run():
    """Run B-mode autonomous agent."""
    logger.info("Bingody B-Mode 启动中...")

    from agent.autonomous import AutonomousAgent

    agent_queue: queue.Queue = queue.Queue()
    event_queue: queue.Queue = queue.Queue()

    agent = AutonomousAgent(command_queue=agent_queue, event_queue=event_queue)
    agent.start()

    logger.info("Agent 已启动，进入对话模式（输入 quit 退出）")
    print("Bingody B-Mode 已启动，输入指令或自然语言对话，输入 quit 退出。\n")

    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.lower() in ("quit", "exit", "退出"):
            logger.info("Bingody B-Mode 退出")
            agent_queue.put({"type": "stop"})
            agent.stop()
            break

        if not user_input:
            continue

        agent_queue.put({"type": "user_input", "text": user_input})

        # Collect responses
        responses = []
        try:
            while True:
                event = event_queue.get(timeout=3)
                if event.get("type") == "agent_response":
                    responses.append(event.get("data", ""))
                elif event.get("type") == "playback_changed":
                    pass
        except queue.Empty:
            pass

        if responses:
            print(f"Bingody: {responses[-1]}")
        else:
            try:
                event = event_queue.get(timeout=2)
                if event.get("type") == "agent_response":
                    print(f"Bingody: {event.get('data', '')}")
            except queue.Empty:
                pass


if __name__ == "__main__":
    run()