import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

logger = logging.getLogger(__name__)

try:
    # Initialize global TracerProvider if not already configured
    if not isinstance(trace.get_tracer_provider(), TracerProvider):
        provider = TracerProvider()
        processor = SimpleSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
except Exception as e:
    logger.warning(f"Failed to initialize OpenTelemetry TracerProvider: {e}")

tracer = trace.get_tracer("medagentx")
