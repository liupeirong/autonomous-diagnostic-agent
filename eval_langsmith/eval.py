import sys
import json
from langsmith import Client 
from langchain.smith import RunEvalConfig, run_on_dataset

sys.path.append('./eval_langchain')
from simple_evaluator import MySimpleEvaluator


def create_dataset(client: Client, dataset_name: str):
  existing_ds = client.list_datasets(dataset_name=dataset_name)
  ds = next(existing_ds)
  if ds:
    client.delete_dataset(dataset_id=ds.id)
  dataset = client.create_dataset(dataset_name, description='robots questions.')

  with open('.\eval_flow\data.jsonl', 'r') as json_file:
    for line in json_file:
      data = json.loads(line)
      client.create_example(
        dataset_id=dataset.id,
        inputs={"prediction": data['prediction']},
        outputs={"groundtruth": data['groundtruth']},
      )
  return dataset


def passthrough_prediction(input_: dict):
  # run_on_dataset will pass each row in the inputs of the dataset to this function,
  # the result of this function is treated as a prediction,
  # which can be used to evaluate against the groundtruth or reference in the outputs of the dataset
  # in this case,
  # we assume we ran the prediction elsewhere, and this is just to do evaluation
  return input_


def eval_prediction_vs_groundtruth(client: Client, dataset_name: str):
  evaluation_config = RunEvalConfig(
    custom_evaluators=[MySimpleEvaluator()],
    reference_key='groundtruth'
  )
  run_on_dataset(
    dataset_name=dataset_name,
    llm_or_chain_factory=passthrough_prediction,
    client=client,
    evaluation=evaluation_config)


if __name__ == '__main__':
  client = Client()
  dataset_name = 'robots dataset'
  dataset = create_dataset(client, dataset_name)
  eval_prediction_vs_groundtruth(client, dataset_name)
