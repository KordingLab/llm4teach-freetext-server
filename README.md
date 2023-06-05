# freetext

A LLM-guided feedback tool that guides freeform essay responses, for educational use.

## Installation

```bash
poetry install
```

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

#### Neuron explanation

> ##### Student Question
> 
> Explain what a neuron is, detailing how they transmit information and what unique features they have.
> 
> ##### Student Response
> 
> Neurons are cells that transmit information to other nerve, muscle, or gland cells. They use synapses.
> 
> ##### Feedback Requirements (Hidden from student, shown to LLM)
> 
> -   Must include the terms 'synapse' and 'action potential'.
> -   Must mention the role of neurotransmitters.
> 
> ##### Feedback (Auto-Generated)
> 
> -   The author did not mention the role of neurotransmitters. The author should include a sentence or two explaining the role of neurotransmitters in the transmission of information between neurons.
> -   The author did not explain what an action potential is. The author should include a sentence or two explaining what an action potential is.

#### List/Tuple explanation

> ##### Student Question
> 
> Explain the difference between a list and a tuple.
> 
> ##### Student Response
> 
> Lists and tuples are different because one uses parentheses and one uses square brackets.
> 
> ##### Feedback Requirements (Hidden from student, shown to LLM)
> 
> -   Must mention immutability and indicate which is which.
> 
> ##### Feedback (Auto-Generated)
> 
> -   The author did not mention immutability and did not indicate which is which. To remedy this, the author should explain that tuples are immutable while lists are mutable.
> 
