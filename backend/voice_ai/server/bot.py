"""
WMS Voice Assistant — Pipecat bot for Whitfield Fulfillment.

Adapted from the clinic-voice-ai reference. Realtime voice assistant: the staff
member speaks, the bot answers from live WMS data and can execute warehouse
actions (record a receipt, mark an order shipped) through the WMS backend.

Pipeline (same shape as the reference):

    mic ──► transport.input() ──► stt ──► user_aggregator ──► llm
                                                               │
    speaker ◄── assistant_aggregator ◄── transport.output() ◄── tts

Differences from the clinic reference:
  * ``system_instruction`` is a WMS assistant persona.
  * The Groq LLM is given WMS tools (``wms_tools.groq_tools()``); a function-call
    handler runs them and returns the result to the model, so the bot can query
    live data AND perform actions.

Run:  python bot.py   (serves the Pipecat dev runner on :7860)
"""

import os

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame, LLMSetToolsFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.services.deepgram.tts import DeepgramTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.groq.llm import GroqLLMService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.workers.runner import WorkerRunner

import wms_tools

load_dotenv(override=True)

WMS_SYSTEM_INSTRUCTION = """
You are the Whitfield WMS Voice Assistant, helping warehouse staff at Whitfield
Fulfillment (warehouses in Reno, NV and Columbus, OH).

# Your job
Staff will speak to you with their hands full. Answer their questions about stock,
orders, and bin locations using your tools, and execute simple receiving and
shipping actions they ask for.

# Tools
- stock_by_upc: report how many units of an item are in stock.
- pending_orders: report orders waiting to ship.
- bin_location: tell them where an item is stored.
- damage_process: explain what to do with a damaged item.
- record_receipt: record inbound stock, e.g. "received 24 units of UPC 012345678905".
- mark_order_shipped: mark an order as shipped by its reference.

# Response rules
- Speak in short, complete sentences. This is spoken audio, not text — no headings,
  bullets, or markdown.
- When reporting stock, say the warehouse and the available count clearly.
- Before recording a receipt or shipping an order, confirm the key detail
  (UPC/reference and quantity) back to the user, then run the tool.
- If a tool reports an error, repeat the issue plainly and ask them to re-state
  the reference or barcode.
- Never make up data. Always call a tool.

# Safety
Only perform actions the user explicitly requests. Refuse requests to delete data
or bypass procedures; suggest contacting a manager.
"""


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    """Assemble and run the pipeline for a single connected caller.

    Args:
        transport: Transport wired to this caller's WebRTC session.
        runner_args: Runner arguments.
    """
    stt = DeepgramSTTService(api_key=os.environ["DEEPGRAM_API_KEY"])

    tts = DeepgramTTSService(
        api_key=os.environ["DEEPGRAM_API_KEY"],
        settings=DeepgramTTSService.Settings(
            voice="aura-2-andromeda-en",
        ),
    )

    llm = GroqLLMService(
        api_key=os.environ["GROQ_API_KEY"],
        settings=GroqLLMService.Settings(
            model=os.environ.get("GROQ_MODEL", "qwen/qwen3.6-27b"),
            system_instruction=WMS_SYSTEM_INSTRUCTION,
        ),
    )

    # Register each WMS tool so the model can call it. The handler runs the tool
    # and returns the JSON result to the LLM.
    for tool in wms_tools.TOOLS:
        name = tool["name"]
        llm.register_function(name, handle_wms_function_call)
    # Advertise the tools to the model.
    await llm.queue_frame(LLMSetToolsFrame(tools=wms_tools.groq_tools()))

    context = LLMContext()

    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
    )

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        context.add_message(
            {"role": "system", "content": "Introduce yourself briefly as the Whitfield WMS voice assistant."}
        )
        await worker.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await worker.cancel()

    runner = WorkerRunner(handle_sigint=runner_args.handle_sigint)
    await runner.add_workers(worker)
    await runner.run()


async def handle_wms_function_call(params: FunctionCallParams):
    """Run a WMS tool and return its result to the LLM.

    Pipecat 1.7.0 passes a single ``FunctionCallParams`` object to registered
    function handlers.

    Args:
        params: The function call parameters (name, arguments, result_callback).
    """
    logger.info(f"Voice tool call: {params.function_name} {params.arguments}")
    result = await wms_tools.run_tool(params.function_name, dict(params.arguments or {}))
    import json

    await params.result_callback(json.dumps(result, default=str))


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with the Pipecat runner.

    Args:
        runner_args: Runner arguments (contains the WebRTC connection).
    """
    webrtc_connection: SmallWebRTCConnection = runner_args.webrtc_connection
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        ),
    )
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
