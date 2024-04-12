import os
import sys
import json

from src.scheduler.fifo_scheduler import FIFOScheduler

from src.scheduler.rr_scheduler import RRScheduler

from src.utils.utils import (
    parse_global_args,
)

from src.agents.agent_factory import AgentFactory

from src.agents.agent_process import AgentProcessFactory

import warnings

from src.llms import llms

from concurrent.futures import ThreadPoolExecutor, as_completed

def main():
    warnings.filterwarnings("ignore")
    parser = parse_global_args()
    args = parser.parse_args()

    llm_name = args.llm_name
    max_gpu_memory = args.max_gpu_memory
    eval_device = args.eval_device
    max_new_tokens = args.max_new_tokens
    scheduler_log_mode = args.scheduler_log_mode
    agent_log_mode = args.agent_log_mode

    llm = llms.LLMKernel(
        llm_name,
        max_gpu_memory,
        eval_device,
        max_new_tokens
    )

    # start the scheduler
    # scheduler = FIFOScheduler(
    #     llm = llm,
    #     log_mode = scheduler_log_mode
    # )

    scheduler = RRScheduler(
        llm = llm,
        log_mode = scheduler_log_mode
    )

    agent_process_factory = AgentProcessFactory()

    agent_factory = AgentFactory(
        llm = llm,
        agent_process_queue = scheduler.agent_process_queue,
        agent_process_factory = agent_process_factory,
        agent_log_mode = agent_log_mode
    )

    agent_thread_pool = ThreadPoolExecutor(max_workers=64)

    scheduler.start()

    # construct agents
    math_agent = agent_thread_pool.submit(
        lambda p: agent_factory.run_agent(*p),
        [
            "MathAgent",
            f"Solve the problem that Albert is wondering how much pizza he can eat in one day. He buys 2 large pizzas and 2 small pizzas. A large pizza has 16 slices and a small pizza has 8 slices. If he eats it all, how many pieces does he eat that day?"
        ]
    )

    narrative_agent = agent_thread_pool.submit(
        lambda p: agent_factory.run_agent(*p),
        [
            "NarrativeAgent",
            f"Craft a tale about a valiant warrior on a quest to uncover priceless treasures hidden within a mystical island."
        ]
    )

    rec_agent = agent_thread_pool.submit(
        lambda p: agent_factory.run_agent(*p),
        [
            "RecAgent",
            f"I want to take a tour to New York during the spring break, recommend some restaurants around for me."
        ]
    )

    agent_tasks = [math_agent, narrative_agent, rec_agent]
    # agent_tasks = [math_agent]

    for r in as_completed(agent_tasks):
        res = r.result()

    scheduler.stop()

if __name__ == "__main__":
    main()
