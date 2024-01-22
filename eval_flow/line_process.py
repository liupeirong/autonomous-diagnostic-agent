from promptflow import tool

@tool
def line_process(prediction: str, groundtruth: str):
  keywords = groundtruth.split(";")
  passed = True
  for keyword in keywords:
    if keyword.lower() in prediction.lower():
      continue
    else:
      passed = False
      break
  return "Pass" if passed else "Fail"