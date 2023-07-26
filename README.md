# freetext

A LLM-guided feedback tool that guides freeform essay responses, for educational use.

## Installation

```bash
poetry install
```

Before you can use the server, you must either (1) change the assignment and response stores in `server.py` to run locally (e.g., JSON stores), or (2) update the AWS credentials in the `config.py` file. Note that no `config.py` is provided; **you must create a new file.** But we do provide a [`config.example.py`](freetext/config.example.py) file that you can use as a template. See that file for itemwise documentation of the configuration options.

## Usage

For development server usage (with live reloads), run:

```bash
poetry run uvicorn freetext.server:app --reload --port 9900
```

For production server usage, run:

```bash
poetry run uvicorn freetext.server:app --port 9900
```

## Examples

See the manuscript for examples.


<hr /><p align='center'><small>Made with 💚 at <a href='https://kordinglab.com/'> the Kording Lab <img alt='KordingLab.com' align='center' src='https://github.com/KordingLab/chatify-server/assets/693511/39f519fe-b05d-43fb-a5d4-f6792de1dbb6' height='32px'></a></small></p>
