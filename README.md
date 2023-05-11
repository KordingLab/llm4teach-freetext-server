# freetext

A LLM-guided feedback tool that guides freeform essay responses, for educational use.

## Installation

```bash
poetry install
```

## Usage

For development server usage (with live reloads), run:

```bash
uvicorn freetext.server:app --reload --port 9900
```

For production server usage, run:

```bash
uvicorn freetext.server:app --port 9900
```

## Examples

#### Neuron explanation

##### Student Question

Explain what a neuron is, detailing how they transmit information and what unique features they have.

##### Student Response

Neurons are cells that transmit information to other nerve, muscle, or gland cells. They use synapses.

##### Feedback Requirements (Hidden from student, shown to LLM)

-   Must include the terms 'synapse' and 'action potential'.
-   Must mention the role of neurotransmitters.

##### Feedback (Auto-Generated)

-   The author did not mention the role of neurotransmitters. The author should include a sentence or two explaining the role of neurotransmitters in the transmission of information between neurons.
-   The author did not explain what an action potential is. The author should include a sentence or two explaining what an action potential is.
