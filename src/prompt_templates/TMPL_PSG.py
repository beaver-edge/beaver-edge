context_pro_tem =  """
You are an expert in Machine Learning on Edge Devices, highly skilled in the TinyML workflows, tools, techniques, and best practices. Your expertise covers both software and hardware, including microcontrollers and microprocessors. You will be asked questions related to various stages of the TinyML lifecycle, including data engineering, model design, model evaluation, model conversion and quantization, and deployment sketch development. The main task is to generate code to perform corresponding tasks (e.g., data cleaning, model quantization).

Your output will be executed **directly**, without additional checks or modifications. Therefore, it is critical that your code strictly adheres to the given format requirements and task instructions."""


format_code_gen_pro_tem = r"""
### RESPONSE FORMAT ###
- Output must consist of a single Python code block (```python ... ```).
- The code should be a complete, **directly** runnable script that  implements the provided Application Description and Requirements.
- Use only standard Python libraries (`os`, `time`, `numpy`, and `cv2` if image/video processing is explicitly required).
- Code must be:
  - Fully executable without placeholders (no "path_to...").
  - Well-structured and commented for clarity.
  - Named consistently to reflect quantization details if relevant.
- If model/tooling error info conflicts with requirements, regenerate strictly according to requirements.
- Provide the complete Python script enclosed in a single ```python ... ``` block, you cannot skip outputting any part of the code.
"""



# ! [ ] FIXME: **The first 10 lines of labelmap** now is hardcoded, should be a placeholder which to be filled by the first 10 lines read by the programe from the defined labelmap file path.
# Task prompt for generating the Python sketch
code_gen_pro_tem = r"""
### OBJECTIVE ###
Generate a complete Python script for the application named '{application_name}'. The deployment target device is '{target_device}'.


### CONFIGURATION PARAMETERS ###
All the required paths and parameters are provided below, use them in generated code:
- model_path: '{model_path}'
- label_path: '{label_path}'  
- Input Method Description: '{input_description}'
- input_path: '{input_path}'  
- Output Method Description: '{output_description}'
- output_path: '{output_path}' 
- Confidence Threshold: '{confidence_threshold}'

### USEFUL INFORMATION ###
**The first 10 lines of labelmap**:
```
person
bicycle
car
motorcycle
airplane
bus
train
truck
boat
traffic light
```

### INSTRUCTIONS ###
- Strictly follow Application Description and Core Requirements.  
- Use the paths and parameters provided under ### CONFIGURATION PARAMETERS ###
- Follow the phase structure outlined in the ### PROGRAMMING GUIDELINE ### reference provided below.
- Explicitly implement Phases 2, 4.2, and 4.3 according to Input/Output method descriptions.  
- Import standard libraries only as needed for the described application logic.
- Only import libraries that are explicitly required by the application logic (no assumptions like `cv2` unless image/video is involved).  
- Ensure **no placeholders** remain: all paths and parameters are already defined under ### CONFIGURATION PARAMETERS ###.

### PROGRAMMING GUIDELINE###
{core_logic_reference_formatted}

"""

# Task prompt for handling errors in generated code
error_handling_code_gen_pro_tem = r"""
### OBJECTIVE ###
- The previous Python script generated has error as logged under ### CAUSED ERROR BEFORE ###.
- The "CAUSED ERROR BEFORE" lists the error message and your previous faulty code caused the error is under ### EXECUTED CODE BEFORE ###. 
- Following the phase structure outlined in the ### PROGRAMMING GUIDELINE ### reference logic provided below, REWRITE the complete Python script for the application '{application_name}' to avoid the error.
- *MAKE SURE YOU USED THE PROVIDED PATHS AND PARAMETERS*


### CONFIGURATION PARAMETERS ###
All the required paths and parameters are provided below, use them in generated code:
- Input Method Description: '{input_description}'
- Output Method Description: '{output_description}'
- model_path = '{model_path}'
- label_path = '{label_path}'  
- input_path = '{input_path}'  
- output_path = '{output_path}' 
- confidence_threshold = '{confidence_threshold}'



### USEFUL INFORMATION ###
**The first 10 lines of labelmap**:
```
person
bicycle
car
motorcycle
airplane
bus
train
truck
boat
traffic light
```

### INSTRUCTIONS ###
- Regenerate the complete script, adhering strictly to Application Description and Core Requirements.
- Use the paths and parameters provided under ### CONFIGURATION PARAMETERS ###
- Follow the phase structure outlined in the ### PROGRAMMING GUIDELINE ### reference provided below.
- Explicitly implement Phases 2, 4.2, and 4.3 according to Input/Output method descriptions.  
- Import standard libraries only as needed for the described application logic.
- Only import libraries that are explicitly required by the application logic (no assumptions like `cv2` unless image/video is involved).  
- Ensure **no placeholders** remain: all paths and parameters are already defined under ### CONFIGURATION PARAMETERS ###.



### PROGRAMMING GUIDELINE###
{core_logic_reference_formatted}

### CAUSED ERROR BEFORE ###
{error_message}

### EXECUTED CODE BEFORE ###
```python
{faulty_code}
```

### OUTPUT TEMPLATE ###
```python
<complete_code>
```
<REPORT THE FIX OF THE LAST ERROR>
"""


core_logic_reference_tem = r"""{
"Programming Guidelines for TFLite Inference": {
  "Phase 1: Setup": {
    
      "1.1": {"Imports": "Import interpreter literally by `from ai_edge_litert.interpreter import Interpreter`"},
      "1.2": {"Paths/Parameters": "Define necessary variables using the model path, input path (if provided and relevant), label path (if provided and relevant), output paths, or other parameters provided in the main prompt."},
      "1.3": {"Load Labels (Conditional)": "If a label path variable was defined and is needed for the application (check main prompt's description), implement code to read the label file into a Python list."},
      "1.4": {"Load Interpreter": "Instantiate interpreter with `interpreter = Interpreter(model_path=...)` using the provided model path variable, and call `interpreter.allocate_tensors()`."},
      "1.5": {"Get Model Details": "Retrieve `input_details = interpreter.get_input_details()` and `output_details = interpreter.get_output_details()`. Store necessary indices and properties (shape, dtype) for input/output tensors."}
    
  },
  "Phase 2: Input Acquisition & Preprocessing Loop (Implement based on main prompt's input description)": {
    
      "2.1": {"Acquire Input Data": "Implement code to get raw data according to the input description provided in the main prompt. Use the input path variable if it was provided and is relevant to the described input method (e.g., reading a specific file/folder). This phase is highly application-dependent."},
      "2.2": {"Preprocess Data": "Implement code to transform the raw data into the `numpy` array(s) based on the extracted information of shape and `dtype` from the retrieved `input_details`. Store result in an `input_data` variable."},
      "2.3": {"Quantization Handling": "Check if model uses floating point inputs: `floating_model = (input_details[0]['dtype'] == np.float32)`. If floating model, normalize: `input_data = (np.float32(input_data) - 127.5) / 127.5`."},
      "2.4": {"Loop Control": "If the input description implies processing continuous data (stream, camera, multiple files), implement the appropriate loop structure and exit conditions. If processing single input, plan to run Phase 3 once."}
    
  },
  "Phase 3: Inference (Run per preprocessed input)": {
    
      "3.1": {"Set Input Tensor(s)": "For each required input tensor: `interpreter.set_tensor(input_details[idx]['index'], input_data_variable[idx])`. Use the preprocessed `input_data` variable."},
      "3.2": {"Run Inference": "`interpreter.invoke()`."}
    
  },
  "Phase 4: Output Interpretation & Handling Loop (Implement based on main prompt's application and output descriptions)": {
    
      "4.1": {"Get Output Tensor(s)": "Retrieve results using `output_variable[idx] = interpreter.get_tensor(output_details[idx]['index'])`. Store in an `output_data` variable."},
      "4.2": {"Interpret Results": "Implement code to process the raw `output_data` variable according to the specific task (defined in the main prompt's application name and description) to generate meaningful results. If labels were loaded in Phase 1.3 and are relevant (e.g., for classification), use the label list here to map indices to names."},
      "4.3": {"Post-processing": "For detection models, apply confidence thresholding, coordinate scaling, and bounding box clipping to ensure results are within valid ranges."},
      "4.4": {"Handle Output": "Implement code to deliver the interpreted results according to the output description provided in the main prompt (e.g., print, write to file using the provided output path variable, send data, control actuator)."},
      "4.5": {"Loop Continuation": "If inside a loop from Phase 2.4, implement logic to continue or break based on exit conditions."}
    
  },
  "Phase 5: Cleanup": {
      "5.1": {"Resources Release": "Implement code to release any resources acquired in Phase 2 (e.g., close files, release camera)."}
    
  }
}}
"""
 
