# BEAVER-EDGE: An LLM-Orchestrated Framework for Edge AI Lifecycle Management Automation

This repository contains the code of the paper "BEAVER-EDGE: An LLM-Orchestrated Framework for Edge AI Lifecycle Management Automation".

> **NOTE: [experimental_data/](experimental_data/README_exp-data.md) stores the experimental data and results used to generate the report in the paper.**

## Installation

### Prerequisites
- Make sure the `.env` file contains all necessary information.
- [Ollama](https://ollama.com/download) hosts the open-source models via `OLLAMA_BASE_URL` in `.env`, or OpenAI access if you configure `OPENAI_API_KEY`.
- [`arduino-cli`](https://arduino.github.io/arduino-cli/latest/installation/) if you intend to compile generated `.ino` sketches, make sure to install the board support package and some common libraries.
- SSH access to a Coral Dev Board (or compatible Edge TPU host) if you plan to run the TPU sketch generator. Relplace the default values of `REMOTE_PYTHON_*` in the `.env` file. 
- a Langfuse account or self-hosted instance for tracing, put the keys and address for `LANGFUSE_*` in the `.env` file. 

### Steps

1. Clone the repository and install Python dependencies from `requirements.txt`.


2. Rename the example environment file `.env.example` to `.env` and fill in the required values.

    Key variables used in code:

    - `OPENAI_API_KEY`: required for OpenAI models through LiteLLM.
    - `OLLAMA_BASE_URL`: set if you run Ollama somewhere other than `http://localhost:11434`.
    - `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_HOST`: used for tracing when running against Langfuse Cloud.
    - `REMOTE_PYTHON_ENV`, `REMOTE_PYTHON_EXECUTABLE`: required when running the TPU sketch generator because execution happens over SSH on the remote Coral device.


3. Install the Arduino board support package used by the sketch generator.

    ```bash
    arduino-cli core update-index
    arduino-cli core install arduino:mbed_nano
    ```

    The project copies `compiling/model.h` into each build directory. Confirm the tensor in that header matches the model you deploy.

6. Install any Arduino libraries the generated sketches may request. The templates target `Arduino_APDS9960`, `Arduino_HTS221`, `Arduino_LSM9DS1`, `ArduinoBLE`, `Harvard_TinyMLx`, and `TensorFlowLite_ESP32`. Install the libraries you need via `arduino-cli lib install`.

 

## Usage

All commands assume you run them from the repository root.

> Note that we used short names of stages mismatching from the paper, the name mappings (- name_in_paper: names_in_code) are:
> - DP: data, dp, DataProcessor
> - MC: convert, mc, ModelConverter
> - ArdSG: sg, SketchGenerator
> - PyCPU-SG: psg, pysg, PySketchGenerator
> - PyTPU-SG: tpusg, TPUSketchGenerator

### Batch orchestration & Tutorial

`src/main.py` is the central entry point for running experiments and batch tests. It orchestrates repeated runs across selected processors and models.

#### How to configure `main.py`

To tweak and set parameters, open `src/main.py` and modify the `main()` function:

1.  **Set the number of runs**:
    ```python
    num_runs = 30  # Number of runs in each batch test
    ```
    If `num_runs >= 20`, benchmarking mode is automatically enabled.

2.  **Select Processors to run**:
    Uncomment the processors you want to test in the `testee_list_` dictionary:
    ```python
    testee_list_ = {
        # "data": f"{stamp}_dp_batch",      # DataProcessor
        # "convert": f"{stamp}_mc_batch",   # ModelConverter
        # "sketch": f"{stamp}_sg_batch",    # SketchGenerator
        "pysketch": f"{stamp}_psg_batch", # PySketchGenerator
        # "tpusketch": f"{stamp}_tpusg_batch", # TPUSketchGenerator
    }
    ```

3.  **Configure Models**:
    Update `model_config_list` with the LLM models and providers you want to test.
    Format: `("provider", "model_name", params_flag)`. (Change the LLM parameters in 'llm_strategy.py' if needed, they are applied when `params_flag` is `True`.)
    ```python
    model_config_list = (
        ("ollama", "qwen2.5-coder:7b", False),
        # ("ollama", "phi4:latest", True),
    )
    ```

4.  **Run the script**:
    ```bash
    python src/main.py
    ```

## File Structure & Processors

The project is structured to handle the lifecycle of EdgeML development through distinct processors.

### Source Code Structure

```text
src/
├── base/       # Base classes and utilities
|   ├── base_processor.py   # core logics shared by processors
|   └── llm_strategy.py     # Managing invocations to LLMs
├── factories/             
|   └── llm_factory.py      # LLM factory (OpenAI, Ollama)
├── processors/             # Core logic for each stage
│   ├── data_processor.py
│   ├── model_converter.py
│   ├── sketch_generator.py
│   ├── pysketch_generator.py
│   └── tpusketch_generator.py
├── prompt_templates/       # Prompt templates for each processor
|   ├── TMPL_DP.md
|   ├── TMPL_MC.md
|   ├── TMPL_SG.md
|   ├── TMPL_PSG.md
|   └── TMPL_TPUSG.md
└── main.py                 # Entrance to the framework, Batch orchestration script
```

### Processors Input & Output

Here is the breakdown of each processor, including where they read data from and where they write results to.

#### 1. DataProcessor
*   **Purpose**: Generates pandas transformations to engineering datasets (e.g., classifying fruits).
*   **Input**:
    *   Reads `data/fruit_to_emoji/SampleData/fruit_data.csv`.
*   **Output**:
    *   Writes processed data and `tmp_*.py` scripts to `data/fruit_to_emoji/playground/`.

#### 2. ModelConverter
*   **Purpose**: Converts Keras models to TensorFlow Lite format, optionally with quantization.
*   **Input**:
    *   Reads original model from `models/fruit_to_emoji/og_model/model.keras`.
    *   Uses dataset `data/fruit_to_emoji/SampleData/fruit_data.csv` for representative data during quantization.
*   **Output**:
    *   Writes converted models to `models/fruit_to_emoji/tflite_model/` (e.g., `model_quant.tflite`).
    *   Generates conversion scripts `tmp_converter*.py` in the same directory.

#### 3. SketchGenerator
*   **Purpose**: Generates and compiles Arduino `.ino` sketches for embedded boards (e.g., Arduino Nano 33 BLE Sense).
*   **Input**:
    *   Uses application specifications defined in `get_user_input`.
    *   Reads dataset samples (e.g., `data/fruit_to_emoji/SampleData/apple.csv`) to embed data samples if needed.
*   **Output**:
    *   Generates sketches in `compiling/`.
    *   Validated/Successful sketches are saved in place.
    *   Compiles using `arduino-cli`.

#### 4. PySketchGenerator
*   **Purpose**: Generates Python scripts for running TFLite models on devices like Raspberry Pi.
*   **Input**:
    *   Uses models like `models/ssd-mobilenet_v1/detect.tflite`.
    *   Reads input media (e.g., `data/object_detection/sheeps.mp4` or images).
*   **Output**:
    *   Generates Python scripts.
    *   Executes scripts to produce tagged media in `results/object_detection/test_results/`.

#### 5. TPUSketchGenerator
*   **Purpose**: Similar to PySketchGenerator but targets Coral Edge TPU hardware via SSH.
*   **Input**:
    *   Same model and media inputs as PySketchGenerator.
*   **Output**:
    *   Transfers scripts and data to the remote TPU device (configured in `.env` via `REMOTE_HOST`, `REMOTE_EXEC_PATH`).
    *   Retrieves results back to `results/object_detection/test_results/`.

## Extending the Project

1. Create a new processor in `src/processors/` that subclasses `BaseProcessor`.
2. Provide prompt templates in `src/prompt_templates/` if the workflow requires new prompt variants.
3. Register the processor in orchestration code (extend `processor_classes` in `main.py`).
4. Update `LLMFactory` if you need to support additional model providers.

## Debugging Steps

- Inspect `logs/<Processor>.log` for detailed error messages and the last generated code snippet.
- Verify `.env` values are loaded (`python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY'))"`).
- Check LLM connectivity: `curl http://localhost:11434/api/tags` for Ollama or run a minimal LiteLLM call for OpenAI.
- Ensure `arduino-cli` can compile a known example sketch before running the sketch generator.
- For TPU runs, confirm passwordless SSH and that the remote Python environment contains required packages.
- If Langfuse traces do not appear, double-check the credential set.

## License

This project is licensed under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html). Ensure all redistributions comply with the GPLv3 terms.


