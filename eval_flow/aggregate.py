from typing import List
from promptflow import tool

@tool
def aggregate(processed_results: List[str]):
  passed_num = processed_results.count("Pass")
  total_num = len(processed_results)
  from promptflow import log_metric
  log_metric("passed", passed_num)
  log_metric("pass_ratio", passed_num/total_num)