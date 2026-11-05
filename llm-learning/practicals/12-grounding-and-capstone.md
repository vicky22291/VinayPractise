# P12. Grounding and capstone

Separate retrieval evidence from generation behavior, then assemble the course artifacts into a defensible capstone.

**Prerequisites:** [Chapter 19](../chapters/19-retrieval-tools-and-compound-systems.md), [Chapter 20](../chapters/20-interpretability-and-the-capstone.md). [Setup and evidence rules](README.md).

**Before running:** record your prediction or competing explanations, including the chosen metric and fixed settings. Start with the script's `--smoke`. Commands below run from `llm-learning/`.


## 1. Inspect the synthetic document set

Read the four fixture documents and their ids in `systems_lab.py`. Mark which facts are actually present, which policy versions exist, and which content is an instruction embedded in untrusted evidence. No tool is executed by this program.

## 2. Retrieval and missing evidence

```
python practicals/scripts/systems_lab.py --query 'refund receipt days' --k 2
python practicals/scripts/systems_lab.py --query 'refund receipt days' --k 2 --omit-refunds
python practicals/scripts/systems_lab.py --query 'international warranty' --k 2
```

Log relevance/absence predictions before each command. The retriever uses lexical TF-IDF cosine similarity on synthetic text. A nonempty top-k list is not proof that the requested evidence exists, and a positive similarity is not an answer-confidence probability.

## 3. Evidence and authority

Write a prompt containing document ids and delimited evidence. Define an abstention and citation-support rubric. Explain what an application must validate before executing any generated tool proposal. Inspect the untrusted document without following its instructions.

## 4. Interpretation hypothesis

Choose an activation or attention pattern in the small decoder. State an observational hypothesis, a controlled intervention, a matched control, and the narrow claim an outcome could support. Do not name a human semantic feature solely from a large activation.

## 5. Capstone

Follow [the capstone brief](../capstone.md). Use the actual byte-model evidence for the model-mechanism investigation and the separate retrieval fixture for evidence-flow reasoning. A useful factual assistant needs an explicitly chosen capable generator; it is not claimed as an output of tiny-model training.


## Evidence to keep

Keep retrieval judgments, missing-evidence cases, a citation rubric, an authorization diagram, an interpretation protocol, and the capstone artifact index.

## Scope and next step

This is retrieval plus system reasoning, not a trained question-answering assistant. Optional real-model integration is a distinct extension with its own dataset, runtime, and evaluation choices.

Return to the corresponding chapter and answer its exercises after explaining your result without the code.
