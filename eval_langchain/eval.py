from datasets import load_dataset, Dataset
from simple_evaluator import MySimpleEvaluator


def create_dataset(dataset_name: str):
  ds = load_dataset('json', data_files='.\eval_flow\data.jsonl', name=dataset_name, split='train')
  return ds


def eval_prediction_vs_groundtruth(ds: Dataset, evaluator) -> Dataset:
  ds_eval = ds.map(lambda x: evaluator.evaluate_strings(prediction=x['prediction'], reference=x['groundtruth']) | x)
  return ds_eval


if __name__ == '__main__':
  dataset_name = 'robots dataset'
  dataset = create_dataset(dataset_name)
  print(dataset.shape)

  evaluator = MySimpleEvaluator()
  ds_eval = eval_prediction_vs_groundtruth(dataset, evaluator)
  ds_eval.to_json('eval_result.jsonl')
