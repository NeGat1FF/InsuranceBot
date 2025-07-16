from mindee import ClientV2, InferencePredictOptions
from mindee.parsing.v2 import InferenceResponse
from config import config

# Init a new client
mindee_client = ClientV2(config.MINDEE_API_KEY)

# Set inference options
passport_options = InferencePredictOptions(
    # ID of the model, required.
    model_id=config.MINDEE_PASS_MODEL,
    # If set to `True`, will enable Retrieval-Augmented Generation.
    rag=False,
)

vihcle_options = InferencePredictOptions(
    model_id=config.MINDEE_VEHICLE_MODEL,
    rag=False,
)

def process_passport(bytes, filename):
    input_doc = mindee_client.source_from_bytes(bytes, filename)
    response: InferenceResponse = mindee_client.enqueue_and_parse(
    input_doc, passport_options
    )

    return response.inference

def process_vehicle(bytes, filename):
    input_doc = mindee_client.source_from_bytes(bytes, filename)
    response: InferenceResponse = mindee_client.enqueue_and_parse(
        input_doc, vihcle_options
    )

    return response.inference