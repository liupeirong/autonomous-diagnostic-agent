from typing import Any, Optional
from langchain.evaluation import StringEvaluator

class MySimpleEvaluator(StringEvaluator):

  def __init__(self) -> None:
    super().__init__()

  @property
  def requires_input(self) -> bool:
    return False
  
  @property
  def requires_reference(self) -> bool:
    return True

  @property
  def evaluation_name(self) -> str:
    return "MySimpleEvaluator"

  def _evaluate_strings(
      self,
      prediction: str,
      input: Optional[str] = None,
      reference: Optional[str] = None,
      **kwargs: Any
  ) -> dict:
    keywords = reference.split(";")
    passed = True
    for keyword in keywords:
      if keyword.lower() in prediction.lower():
        continue
      else:
        passed = False
        break
    result = {"eval_result": "Pass" if passed else "Fail"}
    print(result)
    return result
