# llm-learning teaching and authoring rules

This is a continuous study text with chapters and practicals. Read `README.md`, `curriculum.md`, and `sources.md` before changing its structure.

- Teach in prerequisite order. A later abstraction must name the earlier mechanism it uses.
- The chapters are the main text. Do not create separate revision notes. Organize the book into parts, numbered chapter sections, exercises, further reading, and practical references.
- Chapters use connected explanations, worked examples, tensor shapes or formulas where useful, colored Mermaid diagrams, limitations, and end-of-chapter exercises. Avoid presenting a short course outline as a finished full-length textbook.
- Follow the root color legend. Diagrams have at most 15 nodes, labeled arrows, and a preceding Mermaid comment. Use simple language and no em-dashes in study notes.
- All Stanford source IDs and section reading assignments live in `sources.md`. Keep the latest CME295 edition in required reading. Label authored supplements clearly. Do not imply that source coverage is complete.
- Existing `ml-learning/` rules remain in force for that course. Do not search/open its answers, reveal its empirical results, or edit its learner notes while authoring this course. Safe module READMEs may be linked.
- New practicals use synthetic fixtures or explicit learner-supplied data. Do not present synthetic examples as real observations. Worked arithmetic is labeled as arithmetic.
- Before a learner measures an experiment, ask for a prediction or competing hypotheses. Do not fabricate outcomes or runtime measurements. Chapters may explain mechanisms; they do not contain measured results from these practicals.
- Scripts support bounded demonstrations and explicit output paths. Never download data, install packages, train a long job, or write home-directory artifacts as an incidental import or smoke check.
- Checkpoints, corpora, measurements, plots, and library caches stay outside this repo. No dependencies, build system, notebook outputs, or CI are added here.
- The decoder is an educational implementation. State precisely which production features it omits. Do not equate a toy objective demonstration with full fine-tuning, RLHF, or a deployed LLM.
- Learner progress is not inferred from file creation. This course's content is authored; practical completion requires the learner's evidence.
