from uuid import uuid4

from app.core.enums import ModelArchitectures
from app.presentation.schemas import (
    DatasetCreateRequest,
    InferenceTaskCreateRequest,
    ModelCreateRequest,
    TaskListRequest,
    TrainingTaskCreateRequest,
)


def test_dataset_create_request_as_form_maps_fields():
    request = DatasetCreateRequest.as_form(name="dataset-1", description="demo")

    assert request.name == "dataset-1"
    assert request.description == "demo"


def test_model_create_request_as_form_accepts_enum_and_optional_dataset():
    dataset_id = uuid4()

    request = ModelCreateRequest.as_form(
        name="model-1",
        architecture=ModelArchitectures.yolo,
        architecture_profile="nano",
        dataset_id=dataset_id,
    )

    assert request.name == "model-1"
    assert request.architecture == ModelArchitectures.yolo
    assert request.architecture_profile == "nano"
    assert request.dataset_id == dataset_id


def test_inference_task_create_request_as_form_maps_model_id():
    model_id = uuid4()
    request = InferenceTaskCreateRequest.as_form(model_id=model_id)

    assert request.model_id == model_id


def test_training_task_create_request_as_form_maps_all_fields():
    model_id = uuid4()
    dataset_id = uuid4()

    request = TrainingTaskCreateRequest.as_form(
        model_id=model_id,
        dataset_id=dataset_id,
        image_size=640,
        num_epochs=15,
        name="run-1",
    )

    assert request.model_id == model_id
    assert request.dataset_id == dataset_id
    assert request.image_size == 640
    assert request.num_epochs == 15
    assert request.name == "run-1"


def test_task_list_request_defaults_are_stable():
    request = TaskListRequest()

    assert request.skip == 0
    assert request.limit == 100
