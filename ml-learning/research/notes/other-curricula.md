# Other ML curricula (not fast.ai): factual cards, comparison, and 1-hour lab picks

Status date: 2026-10-17. Learner: Staff engineer, strong Python, new to ML, will let an AI assistant write most code. Hardware: Apple M4 Pro, 24 GB unified memory, macOS 26, Homebrew Python 3.14.

## 0. Method and marks

- Tool calls: about 40 (4 web searches, 1 WebFetch, the rest shell fetches with curl, the GitHub API, a reader proxy, and local parsing). Downloads were kept in a session scratch folder outside the repo.
- Sources: course sites, GitHub READMEs and API metadata, author sites, publisher pages, university syllabi, and YouTube watch pages (exact `lengthSeconds`). Reader proxy (r.jina.ai) for JS-heavy pages: Kaggle, Coursera, Maven, Manning. Its text can drop small items.
- Blocked: O'Reilly returned HTTP 403 to curl, the reader proxy, and WebFetch. The 2025 Geron and Huyen book pages are therefore not checked on O'Reilly.
- "pushed" means the last code push (GitHub API `pushed_at`). "updated_at" moves with stars, so I did not use it as an activity signal.
- Marks: [unverified] = not confirmed on a primary page. "not seen" = not in the text I read, which does not prove absence. STALE = last changed before 2024, or old enough that APIs may have moved.
- No em-dashes in this file (learner rule).

## 1. Answers to the key questions

### Q1. Which curriculum fits which goal

Takeaway: no single winner. Pick by goal.
- Neural-net intuition from scratch: Karpathy's Zero to Hero series (https://karpathy.ai/zero-to-hero.html). Second: d2l.ai for math plus code per layer (https://d2l.ai/).
- Classical tabular ML: Andrew Ng's Machine Learning Specialization (https://www.coursera.org/specializations/machine-learning-introduction) for theory plus labs. Kaggle Intermediate ML (https://www.kaggle.com/learn/intermediate-machine-learning) for pipelines, cross-validation, and leakage habits.
- Modern LLMs: Raschka's two from-scratch books (https://github.com/rasbt/LLMs-from-scratch and https://github.com/rasbt/reasoning-from-scratch), nanochat (https://github.com/karpathy/nanochat), Stanford CS336 (https://cs336.stanford.edu/), and the Hugging Face LLM course (https://huggingface.co/learn/llm-course/chapter1/1).
- Production ML: Full Stack Deep Learning (https://fullstackdeeplearning.com/), Made With ML (https://madewithml.com/), and Chip Huyen's AI Engineering for LLM apps (https://github.com/chiphuyen/aie-book).
- Gap: no fetched source ranks these for a learner. The picks are my judgement from the pages.

### Q2. Pacing for 1-hour sessions

Takeaway: a few units fit one session. Most need 2 to 10 sessions. A few need a cloud GPU.
- One session: Karpathy makemore part 5 (0:56:21, https://www.youtube.com/watch?v=t3YJ5hKiMQ0) and the Intro to LLMs talk (0:59:48, https://www.youtube.com/watch?v=zjkBMFhNj_g). Google MLCC exercises run 5 to 40 minutes each (https://developers.google.com/machine-learning/crash-course/prereqs-and-prework).
- Kaggle courses with a stated time total 4 to 5 hours each, with 7 lessons (card 2.10). Inference: about one lesson per session.
- Two sessions: Karpathy videos of 1h55m to 2h25m (micrograd, makemore 1, 3, 4, "Let's build GPT", the tokenizer).
- Five or more sessions: the GPT-2 reproduction at 4:01:26 (https://www.youtube.com/watch?v=l8pRSuU81PU). Hugging Face LLM course: "approximately 6-8 hours of work per week" for each chapter (https://huggingface.co/learn/llm-course/chapter1/1). DeepLearning.AI courses run 7 to 37 hours each (cards 2.8 and 2.9).
- Assume 5 to 10 hours per unit: Stanford CS224n, CS231n, and CS336 (weekly lectures plus multi-week assignments). MIT 6.S191 runs one lecture and one lab a week (https://introtodeeplearning.com/).
- GPU-bound: the nanochat speedrun needs "~1.5 hours to run" on 8xH100 (https://raw.githubusercontent.com/karpathy/nanochat/master/README.md). The nanoGPT GPT-2 reproduction runs "about 4 days" on 8xA100 40GB (https://raw.githubusercontent.com/karpathy/nanoGPT/master/README.md).

### Q3. Consensus core

Takeaway: training and generalization appear in most cards. Transformers, tokenization, and LLM evaluation appear mainly in the LLM cards. Leakage, cross-validation, and pipelines appear mainly in Kaggle.
- Gradient descent and backprop: explicit in 6 cards. Karpathy micrograd (https://www.youtube.com/watch?v=VMj-3S1tku0). MLCC linear regression, "loss, gradient descent" (https://developers.google.com/machine-learning/crash-course). DL Specialization, "optimization algorithms" (https://www.coursera.org/specializations/deep-learning). d2l chapter 12, "Gradient Descent" (https://d2l.ai/). Kaggle Intro to Deep Learning, "Stochastic Gradient Descent" (https://www.kaggle.com/learn/intro-to-deep-learning). CS224n A2, "calculating tensor derivatives" (https://web.stanford.edu/class/cs224n/). Implied in 6 more: ML Specialization, CS229, CS231n, MIT 6.S191, Raschka (training loop), smol course.
- Train, validation, test, overfitting: explicit in 7 cards. Karpathy makemore 2, "train/dev/test splits, under/overfitting" (https://www.youtube.com/watch?v=TCH_1BHY58I). MLCC, "Datasets, Generalization, and Overfitting". Kaggle Intro ML and Intro DL, "Underfitting and Overfitting". d2l sections 3.6 and 5.5 (https://d2l.ai/). DL Specialization, "train test sets". CS229, "bias/variance tradeoffs" (https://cs229.stanford.edu/).
- Classification metrics: MLCC classification module, "thresholding, confusion matrices, and metrics like accuracy, precision, recall, and AUC" (https://developers.google.com/machine-learning/crash-course).
- Transformers and attention: explicit in 8 cards. Karpathy GPT video (https://www.youtube.com/watch?v=kCc8FmEb1nY). HF LLM course, "How do Transformers work?" (https://huggingface.co/learn/llm-course/chapter1/1). d2l 11.7. CS224n A3, "Self-attention and Transformers". Raschka ch 3. DL Specialization course 5. CME 295 lecture 1, "Transformers" (https://cme295.stanford.edu/syllabus/). LLM101n chapters 4 and 5 (https://github.com/karpathy/LLM101n).
- Tokenization: explicit in 5 cards. Karpathy tokenizer video (https://www.youtube.com/watch?v=zduSFxRajkE). HF LLM course, "Chapters 5 to 8 teach the basics of Datasets and Tokenizers". Raschka book, "Byte Pair Encoding (BPE)", chapter 2.5 (https://www.manning.com/books/build-a-large-language-model-from-scratch). LLM101n chapter 6. nanochat pipeline stage (https://raw.githubusercontent.com/karpathy/nanochat/master/README.md).
- LLM evaluation: explicit in 6 cards. Huyen chapters 3 and 4 (https://raw.githubusercontent.com/chiphuyen/aie-book/main/chapter-summaries.md). CME 295 lecture 7, "LLM evaluation". smol course module 2 (https://github.com/huggingface/smol-course). Raschka reasoning chapter 3 (https://github.com/rasbt/reasoning-from-scratch). HF Agents bonus unit 2, "Observability and Evaluation" (https://github.com/huggingface/agents-course). Maven AI Evals (https://maven.com/courses/ai/evals).
- Leakage, cross-validation, pipelines: Kaggle Intermediate ML only (lessons 4, 5, 7). Not seen in the other cards.
- Deployment and monitoring: FSDL lecture 5 "Deployment" and lab 8 "Model Monitoring" (https://fullstackdeeplearning.com/). MLCC "Production ML systems". Made With ML "Production" section (https://madewithml.com/).
- Reinforcement learning: HF Deep RL (https://github.com/huggingface/deep-rl-class), CS336 assignment 5, Raschka reasoning chapters 6 to 8, MIT 6.S191 lecture 5, CME 295 lecture 4, smol module 5, CS229, LLM101n chapter 15.
- Diffusion: HF Diffusion course (https://huggingface.co/learn/diffusion-course/unit0/1), CME 295 lecture 8, LLM101n chapter 17.
- Agents: HF Agents course (https://github.com/huggingface/agents-course), CME 295 lecture 6, Huyen chapter 6 "RAG and agents", FSDL "Working with AI Agents" page.
- Fairness and ethics: MLCC Fairness module, FSDL lecture 9 "Ethics", MIT 6.S191 lecture 7 "The Three Laws of AI", Microsoft GenAI lesson 03 (https://github.com/microsoft/generative-ai-for-beginners).

### Q4. Explicit guidance on AI coding assistants

Takeaway: two sources give explicit guidance. Only one is written for learners.
- Stanford CS336 (Spring 2026), learner policy, verbatim: "Prompting LLMs such as ChatGPT is permitted for low-level programming questions or high-level conceptual questions about language models, but using it directly to solve the problem is prohibited. We strongly encourage you to disable AI autocomplete (e.g., Cursor Tab, GitHub CoPilot) in your IDE when completing assignments..." (https://cs336.stanford.edu/).
- nanochat, contributor policy (not for learners), verbatim: "Current AI policy: disclosure. When submitting a PR, please declare any parts that had substantial LLM contribution and that you have not written or that you do not fully understand." The same README suggests DeepWiki for questions about the repo (https://raw.githubusercontent.com/karpathy/nanochat/master/README.md).
- Karpathy's GPT video shows GitHub Copilot writing code: "We watch GitHub Copilot, itself a GPT, help us write a GPT". It gives no advice on use (https://karpathy.ai/zero-to-hero.html).
- Not seen in the pages I read: CS224n, CS231n, CS229, MIT 6.S191, FSDL, Made With ML, Microsoft GenAI, and the Hugging Face courses. Check each policy page before you rely on that.

## 2. Curriculum cards

Each card: owner and version; format and length; hands-on, prerequisites, cost, framework; best at; 1-hour unit; flags.

### 2.1 Karpathy, Neural Networks: Zero to Hero (YouTube)
- Owner and version: Andrej Karpathy. Series page https://karpathy.ai/zero-to-hero.html. Videos published 2022-08-16 to 2024-06-09. Nine videos sum to 18h38m18s. The eight on the series page sum to 14h36m52s.
- Format and units: YouTube live-coding videos. The series page lists eight and ends with "ongoing...". It does not list the GPT-2 video, which YouTube does.

| Video (YouTube title, short form) | Length (exact) | Published | Watch |
|---|---|---|---|
| micrograd: "The spelled-out intro to neural networks and backpropagation" | 2:25:52 | 2022-08-16 | https://www.youtube.com/watch?v=VMj-3S1tku0 |
| makemore 1: "The spelled-out intro to language modeling" | 1:57:45 | 2022-09-07 | https://www.youtube.com/watch?v=PaCmpygFfXo |
| makemore 2: MLP | 1:15:39 | 2022-09-12 | https://www.youtube.com/watch?v=TCH_1BHY58I |
| makemore 3: activations, gradients, BatchNorm | 1:55:57 | 2022-10-04 | https://www.youtube.com/watch?v=P6sfmUTpUmc |
| makemore 4: "Becoming a Backprop Ninja" | 1:55:24 | 2022-10-11 | https://www.youtube.com/watch?v=q8SA3rM6ckI |
| makemore 5: "Building a WaveNet" | 0:56:21 | 2022-11-20 | https://www.youtube.com/watch?v=t3YJ5hKiMQ0 |
| "Let's build GPT: from scratch, in code, spelled out." | 1:56:20 | 2023-01-17 | https://www.youtube.com/watch?v=kCc8FmEb1nY |
| "Let's build the GPT Tokenizer" | 2:13:34 | 2024-02-20 | https://www.youtube.com/watch?v=zduSFxRajkE |
| "Let's reproduce GPT-2 (124M)" | 4:01:26 | 2024-06-09 | https://www.youtube.com/watch?v=l8pRSuU81PU |
| Bonus: "[1hr Talk] Intro to Large Language Models" | 0:59:48 | 2023-11-22 | https://www.youtube.com/watch?v=zjkBMFhNj_g |

- Hands-on: nearly all of each video is live code. The GPT-2 description says it builds the "build-nanogpt" repo with "all the changes in this video as individual commits" (https://www.youtube.com/watch?v=l8pRSuU81PU).
- Prerequisites: "solid programming (Python), intro-level math (e.g. derivative, gaussian)" (https://karpathy.ai/zero-to-hero.html). Cost: free. Framework: plain Python (micrograd), then PyTorch tensors (makemore 1 description: "introducing torch.Tensor").
- Best at: backprop from scalars up, then tensor backprop by hand (makemore 4), then a full GPT.
- 1-hour unit: makemore 5 (56 min) as the lab. The Intro to LLMs talk works as a lecture.
- Flags: STALE? Five videos date from 2022 and 2023. The ideas hold, but check PyTorch API details.

### 2.2 nanoGPT (karpathy/nanoGPT)
- Owner and version: Karpathy. Repo https://github.com/karpathy/nanoGPT. Last push 2025-11-12, not archived, MIT (https://api.github.com/repos/karpathy/nanoGPT).
- Status: "nanoGPT (this repo) is now very old and deprecated" (https://raw.githubusercontent.com/karpathy/nanoGPT/master/README.md). The README points to nanochat.
- Format and hands-on: one training script (`train.py`), a sampler, and config files. The Shakespeare character model takes "about 3 minutes" on one A100. On Apple Silicon, "add `--device=mps` ... (2-3X)". GPT-2 reproduction: "at least an 8X A100 40GB node", "about 4 days" (README).
- Prerequisites: Python and PyTorch. Cost: free code. Framework: PyTorch, transformers, tiktoken (README install line).
- Best at: the smallest readable GPT training loop. 1-hour unit: the Shakespeare character model with `--device=mps`.

### 2.3 nanochat (karpathy/nanochat)
- Owner and version: Karpathy. Repo https://github.com/karpathy/nanochat. Created 2025-10-13, last push 2026-09-07, MIT, 58,696 stars (API, 2026-10-17). Guide dated "Feb 1 2026" (https://github.com/karpathy/nanochat/discussions/481).
- Format: one repo with `runs/*.sh` scripts. Stages: tokenization, pretraining, finetuning, evaluation, inference (README). The leaderboard "time to GPT-2" falls from 3.04 (Jan 29 2026) to 1.65 (Mar 14 2026) (README table).
- Length and cost: the intro says "$48 (~2 hours of 8XH100 GPU node)". The speedrun section says "~1.5 hours to run" (README). The README cites "~$3/GPU/hr".
- Hands-on: almost all code. `runs/runcpu.sh` "dramatically shrinks the LLM ... a few ten minutes of training. You will not get strong results" (README).
- Prerequisites: Python and PyTorch basics. Framework: PyTorch, with `uv` for setup (`uv sync --extra cpu` for CPU or MPS).
- Best at: the full LLM pipeline in one small codebase, with cost and time budgets. 1-hour unit: `runs/runcpu.sh` on the M4 Pro with MPS.
- Flags: the author writes "I haven't personally exercised all of these code paths", so MPS "might be sharp edges" (README). The speedrun time conflicts (section 5).

### 2.4 llm.c (karpathy/llm.c)
- Owner and version: Karpathy. Created 2024-04-08, last code push 2025-06-26, not archived, MIT (https://api.github.com/repos/karpathy/llm.c).
- Format and scope: "LLMs in simple, pure C/CUDA with no need for 245MB of PyTorch or 107MB of cPython". "The best introduction ... is reproducing the GPT-2 (124M) model" (https://raw.githubusercontent.com/karpathy/llm.c/master/README.md).
- Hands-on: CUDA setup steps in the README. The CPU path is "an even earlier checkpoint", and "you won't go too far" on CPU (same README).
- Prerequisites: C, some CUDA. Cost: free code, GPU for speed. Framework: C and CUDA, with a PyTorch reference.
- Best at: what one training step costs at kernel level. 1-hour unit: the layernorm tutorial at `doc/layernorm/layernorm.md`, as the README describes it.
- Flags: STALE? The README says "Current focus is on pretraining", but the last code push is mid-2025.

### 2.5 LLM101n and Eureka Labs (status)
- Owner: Eureka Labs (Karpathy). Announced July 16, 2024. "Today, we are heads down building LLM101n" (https://eurekalabs.ai/).
- Repo https://github.com/karpathy/LLM101n: "this course does not yet exist ... Until it is ready I am archiving this repo." Archived, last push 2024-08-01 (API). Planned syllabus: 17 chapters, from "Bigram Language Model" to "Multimodal" (README).
- Status on 2026-10-17: no launch found. The GitHub org EurekaLabsAI returned an empty repo list (https://api.github.com/orgs/EurekaLabsAI/repos). Web search found only 2024 coverage. [unverified: launch or private cohort.]
- Use: not usable now. STALE (2024 plans).

### 2.6 Hugging Face LLM course
- Owner and version: Hugging Face. Course pages at https://huggingface.co/learn/llm-course/chapter1/1 (fetched 2026-10-17). The repo https://github.com/huggingface/llm-course is a 56-byte README, last push 2025-03-24 (API).
- Structure: chapters 1 to 4 cover Transformers, 5 to 8 cover Datasets and Tokenizers, and 9 covers demos on the Hub (chapter 1 page). Titles seen: "1. Transformer models" and "3. Fine-tuning a pretrained model".
- Length: "Each chapter ... is designed to be completed in 1 week, with approximately 6-8 hours of work per week" (chapter 1 page).
- Hands-on: code-first; notebook count [unverified]. Prerequisites: Python basics. Cost: no fee in the fetched text [unverified]. Framework: Transformers, Datasets, Tokenizers (page text).
- Best at: the Hub workflow for LLM apps. 1-hour unit: a fine-tuning or pipeline section (length not stated).
- Flags: the intro lists 9 chapters, and newer chapters may exist [unverified]. The GitHub path `chapters/en` returned 404.

### 2.7 Google Machine Learning Crash Course (MLCC)
- Owner and version: Google. https://developers.google.com/machine-learning/crash-course calls itself "a refreshed version of MLCC that covers recent advances in AI". No refresh date appears in the fetched HTML, so the "2024 refresh" is [unverified].
- Format: "animated videos, interactive visualizations, and hands-on practice exercises" (landing page). Units: 12 modules in four groups. ML models: Linear Regression, Logistic Regression, Classification. Data: Numerical, Categorical, Datasets/Generalization/Overfitting. Advanced: Neural Networks, Embeddings, Intro to LLMs (new). Real-world: Production ML Systems, AutoML (new), Fairness.
- Length: no total hours on the landing or prerequisites page [unverified]. Exercises run 5 to 40 minutes (https://developers.google.com/machine-learning/crash-course/prereqs-and-prework).
- Prerequisites: Python, NumPy, pandas; algebra, linear algebra, statistics; calculus optional. Framework: NumPy, pandas, Keras (prereqs page). Cost: no fee shown [unverified].
- Best at: fast, interactive intuition on ML basics and metrics. 1-hour unit: the Classification module (threshold and confusion-matrix exercises).

### 2.8 DeepLearning.AI and Stanford, Machine Learning Specialization (Coursera)
- Owner and version: DeepLearning.AI with Stanford Online; instructor Andrew Ng. https://www.coursera.org/specializations/machine-learning-introduction (fetched through the reader proxy, 2026-10-17). Enrolled count on the page: 850,885.
- Format and length: 3 courses of 33 h, 34 h, and 28 h. The page headline says "2 months at 10 hours a week" (section 5).
- Content: regression, classification, neural nets in TensorFlow, decision trees, tree ensembles (page). Hands-on: coding labs; ratio not stated. Prerequisites: "beginner-friendly" (page).
- Cost: "Enroll for free". The page says "A Coursera subscription costs $49 / month" and mentions financial aid (page text, 2026-10-17). Framework: NumPy, scikit-learn, TensorFlow (page).
- Best at: gradient descent and classical ML with clear intuition. 1-hour unit: course 1, linear regression with gradient descent.

### 2.9 DeepLearning.AI Deep Learning Specialization (Coursera)
- Owner and version: DeepLearning.AI; instructor Andrew Ng. https://www.coursera.org/specializations/deep-learning (fetched through the reader proxy). The page says "Recently updated with cutting-edge techniques!" Enrolled count: 1,004,905.
- Format and length: 5 courses of 25 h, 24 h, 7 h, 36 h, and 37 h (total 129 h). The page says "3 months at 10 hours a week".
- Content: CNNs, RNNs, LSTMs, Transformers, dropout, batch norm, train/dev/test sets, bias and variance (page). Prerequisites: Python (page tag). Framework: TensorFlow (page). Cost: same subscription model as 2.8.
- Best at: deep learning practice, diagnosing errors, and tuning. 1-hour unit: course 3 (7 h), error analysis on a synthetic dataset.

### 2.10 Kaggle Learn micro-courses (ML-relevant, fetched)
- Owner: Kaggle. The index https://www.kaggle.com/learn is a JavaScript shell, so the full course list is incomplete.

| Course (URL) | Hours on page | Lessons (titles from the page slugs) | Leakage, CV, pipelines |
|---|---|---|---|
| Intro to Machine Learning (https://www.kaggle.com/learn/intro-to-machine-learning) | not captured | 7: How models work; Basic data exploration; Your first model; Model validation; Underfitting and overfitting; Random forests; ML competitions | no |
| Intermediate ML (https://www.kaggle.com/learn/intermediate-machine-learning) | 4 | 7: Introduction; Missing values; Categorical variables; Pipelines; Cross-validation; XGBoost; Data leakage | yes: lessons 4, 5, 7 |
| Feature Engineering (https://www.kaggle.com/learn/feature-engineering) | 5 | 4 seen: What is feature engineering; Mutual information; Creating features; Clustering with k-means | no |
| Intro to Deep Learning (https://www.kaggle.com/learn/intro-to-deep-learning) | not captured | 6 plus 1 bonus: A single neuron; Deep neural networks; Stochastic gradient descent (Keras and TensorFlow); Overfitting and underfitting; Dropout and batch normalization; Binary classification | no |
| Computer Vision (https://www.kaggle.com/learn/computer-vision) | 4 | The convolutional classifier; Convolution and ReLU; Maximum pooling; The sliding window | no |
| Time Series (https://www.kaggle.com/learn/time-series) | 5 | Linear regression with time series; Trend; Seasonality; Time series as features | no |
| Machine Learning Explainability (https://www.kaggle.com/learn/machine-learning-explainability) | 4 | Use cases for model insights; Permutation importance; Partial plots; SHAP values | no |

- data-leakage: https://www.kaggle.com/learn/data-leakage returns the Kaggle home page, not a course. Leakage is lesson 7 of Intermediate ML.
- Hands-on: each lesson has a "Tutorial" and an "Exercise" (page headers). Cost: free [unverified]. Framework: pandas (feature engineering lesson text), Keras and TensorFlow (Intro DL lesson 3).
- Best at: short applied habits: pipelines, cross-validation, leakage. 1-hour unit: Intermediate ML lessons 4 and 5. Flags: no dates on the fetched pages, so their age is [unverified].

### 2.11 d2l.ai, Dive into Deep Learning
- Owner and version: the d2l.ai project (GitHub org d2l-ai). The site https://d2l.ai/ shows "1.0.3 documentation". Last tagged release v1.0.3 on 2023-08-18. Last push 2024-08-18. 29,850 stars (https://api.github.com/repos/d2l-ai/d2l-en). STALE? (2023 release).
- Format: 23 chapters. Chapter 2 covers linear algebra, calculus, and probability. Chapters 3 and 4 cover linear networks. Chapter 5 covers MLPs. Chapters 7 and 8 cover CNNs, 9 and 10 cover RNNs, 11 covers attention and Transformers, 12 covers optimization, and 14 to 21 cover CV, NLP, RL, Gaussian processes, HPO, GANs, and recommenders (https://d2l.ai/).
- Length: not stated. Hands-on: code for each section. The site navigation lists PyTorch and MXNet (https://d2l.ai/). Prerequisites: math basics. Cost: free online [unverified fee text].
- Best at: math plus code per layer, in one reference. 1-hour unit: section 3.4 "Linear Regression Implementation from Scratch", or section 11.7 "The Transformer Architecture".

### 2.12 Aurelien Geron, Hands-On Machine Learning
- Owner and version: Aurelien Geron. The author site https://homl.info/ lists "Hands-On Machine Learning with Scikit-Learn and PyTorch", O'Reilly, "10-2025", copyright 2025.
- ISBN 9798341607989 (distributor listing: https://ingramacademic.com/products/hands-on-machine-learning-with-scikit-learn-and-pytorch-9798341607989). The O'Reilly page is blocked (403). The 2025 table of contents is NOT verified (gap).
- Third edition (Keras and TensorFlow 2): repo https://github.com/ageron/handson-ml3, last push 2026-10-06. The README calls it "the third edition" of the Scikit-Learn, Keras and TensorFlow book.
- Hands-on: notebooks in the third-edition repo. The 2025 edition's notebooks are not checked. Cost: book price not verified. Framework: scikit-learn plus PyTorch (2025 title). 1-hour unit: one chapter notebook from handson-ml3 [chapter choice waits on the TOC].

### 2.13 Sebastian Raschka, the two LLM books
- Build a Large Language Model (From Scratch): Manning, 2024, ISBN 978-1633437166 (https://github.com/rasbt/LLMs-from-scratch). Repo last push 2026-10-02, 106,674 stars (API). Manning page: https://www.manning.com/books/build-a-large-language-model-from-scratch.
- Chapters (README): 1 Understanding LLMs (no code); 2 Working with text data; 3 Coding attention mechanisms; 4 Implementing a GPT model from scratch; 5 Pretraining on unlabeled data; 6 Finetuning for text classification; 7 Finetuning to follow instructions. Appendices A to E cover PyTorch, training-loop extras, and LoRA.
- Hands-on: a notebook per chapter plus exercises with solutions. Companion video course: "A 17-hour and 15-minute companion video course" (README). Hardware: "designed to run on conventional laptops" (README). Framework: PyTorch, no LLM libraries.
- Build a Reasoning Model (From Scratch): Manning, 2025, ISBN 9781633434677, 440 pages (https://www.manning.com/books/build-a-reasoning-model-from-scratch). Repo https://github.com/rasbt/reasoning-from-scratch, last push 2026-10-02, 5,415 stars. Base model Qwen3. Chapters: 2 text generation; 3 evaluating reasoning models; 4 inference-time scaling; 5 self-refinement; 6 RL; 7 improving GRPO; 8 distillation (README). "designed to mostly run on consumer hardware".
- Best at: building a GPT on a laptop, then reasoning training. 1-hour unit: chapter 2 text-data pipeline, or chapter 6 [check length].

### 2.14 Chip Huyen, AI Engineering (O'Reilly, 2025)
- Owner and version: Chip Huyen. Repo https://github.com/chiphuyen/aie-book ("[WIP] Resources for AI engineers"), last push 2026-07-03, 17,869 stars. Citation: "O'Reilly Media, 2025" (README).
- Chapters (repo summary file): 1 Introduction to building AI applications with foundation models; 2 Understanding foundation models; 3 Evaluation methodology; 4 Evaluate AI systems; 5 Prompt engineering; 6 RAG and agents; 7 Finetuning; 8 Dataset engineering; 9 Inference optimization; 10 AI engineering architecture and user feedback (https://raw.githubusercontent.com/chiphuyen/aie-book/main/chapter-summaries.md).
- Hands-on: low (concepts and design, my judgement). Framework: framework-neutral [unverified]. Cost: book purchase. The O'Reilly page is blocked (403), so the exact month and table of contents are [unverified].
- Best at: production LLM app design: evaluation, RAG, agents, inference cost. 1-hour unit: chapter 3 evaluation (build a 20-item eval set and score two prompts).

### 2.15 Stanford: CS229, CS231n, CS224n, CS336
- CS229, https://cs229.stanford.edu/: Summer 2026. Topics: supervised and unsupervised learning, learning theory (bias/variance), RL and adaptive control. Prerequisites: Python/NumPy, probability, multivariable calculus and linear algebra. Problem sets (count not verified). Cost: public materials [unverified].
- CS231n, https://cs231n.stanford.edu/: Spring 2026. Lectures Tue and Thu 12:00-1:20 PM PT. "All class assignments will be in Python (and use numpy)". Assignments are 45% of the grade. Lecture videos are for enrolled students. PyTorch not seen.
- CS224n, https://web.stanford.edu/class/cs224n/: Winter 2026. "All class assignments will be in Python (using NumPy and PyTorch)". Four weekly assignments: A1 word vectors (6%), A2 neural net foundations (14%), A3 self-attention and transformers (14%), plus a final project. Public videos are the 2024 offering.
- CS336, https://cs336.stanford.edu/: Spring 2026 (Spring 2025 also linked). Five assignments: 1 Basics, 2 Systems, 3 Scaling, 4 Data, 5 Alignment and Reasoning RL. Prerequisites: Python, PyTorch, memory hierarchy. GPU runs are needed for A1, A4, A5 training and A2 benchmarks. AI policy quoted in Q4.
- Best at: CS229 for theory, CS231n for CNNs, CS224n for NLP and transformers, CS336 for building and profiling an LLM stack. 1-hour unit: CS224n A3 (self-attention), or CS336 A2 profiling (length not stated).

### 2.16 MIT 6.S191, Introduction to Deep Learning (2026 run)
- Owner and version: MIT. Site https://introtodeeplearning.com/. The 2026 run was Mon Mar 30 to Mon May 25, 2026, with lectures "Every Monday at 10am ET". The in-person edition has finished. The online edition is live weekly (site).
- Units: lectures 1 to 9 and software labs 1 to 3. Lab 3 is "Fine-Tune an LLM, You Must!" (site). Labs repo https://github.com/MITDeepLearning/introtodeeplearning, last push 2026-01-04 (API).
- Hands-on: 3 software labs. Cost: free. The site says "New lectures, slides, and labs will be open-sourced every week". Framework: not verified [unverified].
- 1-hour unit: Software Lab 3 (LLM fine-tuning) [length and framework unverified].

### 2.17 Full Stack Deep Learning (FSDL)
- Owner and version: Full Stack Deep Learning. https://fullstackdeeplearning.com/. Latest deep learning course on the site: "FSDL 2022". Other sections: "LLM Bootcamp Spring 2023" and "Working with AI Agents" (date not seen).
- Units (FSDL 2022 navigation): lectures 1 to 9 (course vision, dev infrastructure, troubleshooting and testing, data management, deployment, continual learning, foundation models, ML teams, ethics). Labs 4 to 8 (experiment management, troubleshooting and testing, data annotation, web deployment, model monitoring).
- Hours: not stated. Hands-on: labs. Framework and cost: not verified [unverified]. Best at: production ML (testing, deployment, monitoring). 1-hour unit: lab 4, experiment management.
- Flags: STALE? The deep learning course is from 2022 and the LLM Bootcamp from 2023.

### 2.18 Made With ML (Goku Mohandas; site brand "Made With ML by Anyscale")
- Owner and version: Goku Mohandas. https://madewithml.com/. Repo https://github.com/GokuMohandas/Made-With-ML, last push 2026-03-04, 49,754 stars (API). Description: "Learn how to develop, deploy and iterate on production-grade ML applications."
- Modules (site navigation): Design; Data; Model (training, tracking, tuning, evaluation, serving); Developing; Utilities; Testing; Reproducibility; Production (jobs and services, CI/CD workflows, monitoring).
- Hands-on: code repo. "Your personal laptop (single machine) will act as the cluster" (README), using Ray, or an Anyscale workspace. Prerequisites: Python. Cost: course free, Anyscale optional. Best at: taking one model from data to production. 1-hour unit: the data preprocessing lesson on the laptop.

### 2.19 Hugging Face short courses: Deep RL, Diffusion, smol, Agents
- Deep RL: https://github.com/huggingface/deep-rl-class. README title "(v2.0)", last push 2026-10-14, 5,059 stars. "low-maintenance state"; Unit 7 "non-functional"; leaderboard "no longer operational" (README). Units 0 to 8 plus bonus units 1, 2, 3, and 5 (https://api.github.com/repos/huggingface/deep-rl-class/contents/units/en). Citation year 2023. STALE? Hours and framework [unverified].
- Diffusion: https://github.com/huggingface/diffusion-models-class, last push 2026-10-14. Course page https://huggingface.co/learn/diffusion-course/unit0/1: "The course consists in four units. Each unit is made up of a theory section ... and two notebooks." Course date and hours not stated [unverified].
- smol: https://github.com/huggingface/smol-course, last push 2026-10-06. README: "smol course v2 is live!". Modules: 1 Instruction Tuning, 2 Evaluation, 3 Preference Alignment, 4 Vision Language Models (released); 5 Reinforcement Learning (Oct 2025), 6 Synthetic Data (Nov 2025), 7 Award Ceremony (Dec 2025). "everything runs on most local machines". Prerequisites: Python, PyTorch, transformers.
- Agents: https://github.com/huggingface/agents-course, last push 2026-10-14. "divided into 4 units" plus bonus units. Sign-up "(it's free)". Units: 1 agents intro, 2 frameworks (smolagents, LlamaIndex, LangGraph), 3 agentic RAG, 4 final project with automated evaluation and a leaderboard. Citation year 2025.
- 1-hour unit: smol module 1 (instruction tuning), or Agents unit 2.1 (smolagents).

### 2.20 Microsoft Generative AI for Beginners (2025-2026)
- Repo https://github.com/microsoft/generative-ai-for-beginners: "21 Lessons", "Generative AI for Beginners (Version 3)", last push 2026-10-15, 121,482 stars (API and README).
- Format: lessons in folders, marked "Learn" or "Build". Code in Python and TypeScript. Providers: Azure OpenAI, Microsoft Foundry Models, or the OpenAI API. The README says "GitHub Models is retiring at the end of July 2026".
- Cost: free repo [license not checked]. Best at: software engineers building GenAI apps. 1-hour unit: lesson 06, "Building Text Generation Applications".

### 2.21 Hamel Husain and Shreya Shankar, AI Evals for Engineers and PMs (Maven)
- Course listing https://maven.com/courses/ai/evals: "AI Evals For Engineers & PMs", rating 4.7, "6 weeks", "Oct 10 - Nov 21". The year is not printed in the fetched text.
- This is a course-platform page, not the authors' own site. Price not in the fetched text [unverified]. Best at: designing and running LLM evals. 1-hour unit: a session that designs a 20-case eval set [format unverified].

### 2.22 Stanford CME 295, Transformers and LLMs (Autumn 2026)
- Syllabus https://cme295.stanford.edu/syllabus/ (copyright 2026). Lectures: Sep 25 Transformers; Oct 2 LLMs; Oct 9 LLM training; Oct 16 RL with LLMs; Oct 23 midterm; Oct 30 LLM systems; Nov 6 AI agents; Nov 13 LLM evaluation; Nov 20 diffusion LLMs; Dec 4 trending topics; Dec 9 final.
- Hands-on: exams. Labs not seen. Cost: [unverified]. Best at: a current overview of transformers and LLM training. 1-hour unit: lecture 7, LLM evaluation, plus a short notebook of your own [unverified].

## 3. Comparison table

Each curriculum name links to its primary page. The row values repeat the claims cited in the cards.

| Curriculum | Owner and latest version (2026-10-17) | Format and length | Units | Hands-on | Cost | Framework | Best at | 1-hour unit |
|---|---|---|---|---|---|---|---|---|
| [Karpathy Zero to Hero](https://karpathy.ai/zero-to-hero.html) | Karpathy; videos 2022-08 to 2024-06 | YouTube; 18h38m for 9 videos | 9 + 1 bonus | live code | free | Python, PyTorch | backprop and GPT from scratch | makemore 5 (56m) |
| [nanoGPT](https://github.com/karpathy/nanoGPT) | Karpathy; deprecated Nov 2025 | one script and configs | 1 | yes | free | PyTorch | smallest GPT loop | Shakespeare on MPS |
| [nanochat](https://github.com/karpathy/nanochat) | Karpathy; created 2025-10-13, pushed 2026-09-07 | repo; speedrun ~1.5 h on 8xH100 | 6 stages | code | ~$48 GPU for speedrun (README) | PyTorch, uv | full pipeline and budgets | runcpu.sh on MPS |
| [llm.c](https://github.com/karpathy/llm.c) | Karpathy; pushed 2025-06-26 | C and CUDA | GPT-2 steps | code | free; GPU for speed | C, CUDA | kernel-level cost | layernorm tutorial |
| [LLM101n](https://github.com/karpathy/LLM101n) | Eureka Labs; archived, last push 2024-08-01 | planned course | 17 planned chapters | n/a | n/a | n/a | not usable yet | none |
| [HF LLM course](https://huggingface.co/learn/llm-course/chapter1/1) | Hugging Face; intro lists chapters 1-9 | web course; 6-8 h per chapter | 9+ | code | no fee in text [unverified] | Transformers, Datasets, Tokenizers | Hub workflow | fine-tuning section |
| [HF Deep RL](https://github.com/huggingface/deep-rl-class) | Hugging Face; v2.0, low maintenance | web course | units 0-8 + bonus | notebooks | [unverified] | [unverified] | RL basics to policy methods | unit 1 [unverified] |
| [HF Diffusion](https://huggingface.co/learn/diffusion-course/unit0/1) | Hugging Face; repo pushed 2026-10-14 | web course | 4 units | theory + 2 notebooks per unit | [unverified] | [unverified] | diffusion models | unit 1 notebook |
| [HF smol course](https://github.com/huggingface/smol-course) | Hugging Face; v2 live, pushed 2026-10-06 | GitHub course | 7 modules (4 released) | exercises | [unverified] | Transformers, PyTorch | alignment of small models | module 1 |
| [HF Agents](https://github.com/huggingface/agents-course) | Hugging Face; pushed 2026-10-14; cites 2025 | web course | 4 units + bonus | yes | free sign-up | smolagents, LlamaIndex, LangGraph | agent frameworks | unit 2.1 |
| [Google MLCC](https://developers.google.com/machine-learning/crash-course) | Google; "refreshed" (date not shown) | videos + exercises; no total hours | 12 modules | exercises of 5-40 min | no fee shown [unverified] | NumPy, pandas, Keras | fast ML basics | Classification module |
| [DL.AI ML Specialization](https://www.coursera.org/specializations/machine-learning-introduction) | DeepLearning.AI with Stanford Online; Andrew Ng | 33 + 34 + 28 h | 3 courses | coding labs | free to enroll; $49/month subscription (page) | NumPy, scikit-learn, TensorFlow | gradient descent, classical ML | course 1 |
| [DL.AI DL Specialization](https://www.coursera.org/specializations/deep-learning) | DeepLearning.AI; "recently updated" | 25 + 24 + 7 + 36 + 37 h | 5 courses | coding labs | same as above | TensorFlow | DL practice, error analysis | course 3 |
| [Kaggle Learn](https://www.kaggle.com/learn/intermediate-machine-learning) | Kaggle; no dates on pages | 4-5 h where stated | 7 lessons each | tutorial + exercise | free [unverified] | pandas, Keras | applied tabular habits | Intermediate ML lessons 4-5 |
| [d2l.ai](https://d2l.ai/) | d2l-ai; v1.0.3 (2023-08-18), pushed 2024-08-18 | book; hours not stated | 23 chapters | code per section | free online [unverified] | PyTorch, MXNet | math plus code reference | section 3.4 or 11.7 |
| [Geron, Hands-On ML](https://homl.info/) | Geron; O'Reilly 10-2025 (PyTorch edition) | book + notebooks | TOC not verified | notebooks (3rd ed. repo) | book price [unverified] | scikit-learn, PyTorch | broad practical ML | one notebook (TOC gap) |
| [Raschka, LLM from scratch](https://github.com/rasbt/LLMs-from-scratch) | Raschka; Manning 2024 | book; 17h15m companion video | 7 chapters + appendices | notebook per chapter + exercises | book price | PyTorch | build a GPT on a laptop | chapter 2 |
| [Raschka, reasoning](https://github.com/rasbt/reasoning-from-scratch) | Raschka; Manning 2025 | book, 440 pages | 8 chapters + appendices | notebooks | book price | PyTorch, Qwen3 | reasoning training | chapter 2 or 3 |
| [Huyen, AI Engineering](https://github.com/chiphuyen/aie-book) | Huyen; O'Reilly 2025 | book | 10 chapters | low | book price | framework-neutral [unverified] | LLM app design, evals | chapter 3 |
| [CS229](https://cs229.stanford.edu/) | Stanford; Summer 2026 | course | lectures + problem sets | problem sets | public materials [unverified] | Python, NumPy | ML theory | theory section |
| [CS231n](https://cs231n.stanford.edu/) | Stanford; Spring 2026 | course | lectures + assignments | assignments (45%) | public materials [unverified] | Python, NumPy | CNNs | assignment part |
| [CS224n](https://web.stanford.edu/class/cs224n/) | Stanford; Winter 2026 | course | 4 assignments + project | assignments | 2024 videos public | Python, NumPy, PyTorch | NLP and transformers | A3 |
| [CS336](https://cs336.stanford.edu/) | Stanford; Spring 2026 | course | 5 assignments | heavy code, GPU | public materials [unverified] | Python, PyTorch | LLM systems from scratch | A2 profiling |
| [MIT 6.S191](https://introtodeeplearning.com/) | MIT; 2026 run Mar 30 to May 25 | 9 lectures + 3 labs | 9 + 3 | labs | free | [unverified] | intro DL with labs | Lab 3 [unverified] |
| [FSDL](https://fullstackdeeplearning.com/) | Full Stack DL; FSDL 2022 | 9 lectures + labs 4-8 | 9 + 5 | labs | free site [unverified] | [unverified] | production ML | lab 4 |
| [Made With ML](https://madewithml.com/) | Mohandas; repo pushed 2026-03-04 | modules | many lessons | code | free; Anyscale optional | Python, Ray | data to production | data lesson |
| [MS GenAI for Beginners](https://github.com/microsoft/generative-ai-for-beginners) | Microsoft; Version 3, pushed 2026-10-15 | repo | 21 lessons | code | free | Python, TypeScript | GenAI app building | lesson 06 |
| [Maven AI Evals](https://maven.com/courses/ai/evals) | Husain and Shankar; cohort Oct 10 - Nov 21 | 6-week cohort | 6 weeks | cohort format [unverified] | price not in text | n/a | LLM eval design | eval-set session |
| [CME 295](https://cme295.stanford.edu/syllabus/) | Stanford; Autumn 2026 | 9 lectures, midterm, final | 9 | exams | [unverified] | n/a | LLM and transformer theory | lecture 7 |

## 4. Sources table

| URL | What it supports | Date (as seen) |
|---|---|---|
| https://karpathy.ai/zero-to-hero.html | series syllabus, prerequisites, Copilot remark | fetched 2026-10-17 |
| https://www.youtube.com/watch?v=VMj-3S1tku0 , https://www.youtube.com/watch?v=PaCmpygFfXo , https://www.youtube.com/watch?v=TCH_1BHY58I , https://www.youtube.com/watch?v=P6sfmUTpUmc , https://www.youtube.com/watch?v=q8SA3rM6ckI | exact lengths (8752, 7065, 4539, 6957, 6924 s) and publish dates | 2022-08-16 to 2022-10-11 |
| https://www.youtube.com/watch?v=t3YJ5hKiMQ0 , https://www.youtube.com/watch?v=kCc8FmEb1nY , https://www.youtube.com/watch?v=zduSFxRajkE , https://www.youtube.com/watch?v=l8pRSuU81PU , https://www.youtube.com/watch?v=zjkBMFhNj_g | exact lengths (3381, 6980, 8014, 14486, 3588 s); GPT-2 description; Intro to LLMs description | 2022-11-20 to 2024-06-09 |
| https://api.github.com/repos/karpathy/nanoGPT | created, last push, MIT, stars | fetched 2026-10-17 |
| https://raw.githubusercontent.com/karpathy/nanoGPT/master/README.md | deprecation note, MPS flag, GPT-2 hardware | Nov 2025 note |
| https://api.github.com/repos/karpathy/nanochat | created 2025-10-13, pushed 2026-09-07, stars | fetched 2026-10-17 |
| https://raw.githubusercontent.com/karpathy/nanochat/master/README.md | $48, ~1.5 h, runcpu, MPS, leaderboard, AI policy, DeepWiki | README fetched 2026-10-17 |
| https://github.com/karpathy/nanochat/discussions/481 | guide linked from the README | dated Feb 1 2026 in README |
| https://api.github.com/repos/karpathy/llm.c | created 2024-04-08, pushed 2025-06-26 | fetched 2026-10-17 |
| https://raw.githubusercontent.com/karpathy/llm.c/master/README.md | scope, 245MB/107MB claim, CPU path, layernorm doc, tinyshakespeare link | README fetched 2026-10-17 |
| https://eurekalabs.ai/ | Eureka Labs launch post and LLM101n status | 2024-07-16 |
| https://github.com/karpathy/LLM101n | archived note, planned 17-chapter syllabus | last push 2024-08-01 |
| https://api.github.com/orgs/EurekaLabsAI/repos | no public repos returned | fetched 2026-10-17 |
| https://huggingface.co/learn/llm-course/chapter1/1 | 6-8 h per chapter; chapter ranges; library names | fetched 2026-10-17 |
| https://api.github.com/repos/huggingface/llm-course | 56-byte stub README, last push | 2025-03-24 |
| https://raw.githubusercontent.com/huggingface/deep-rl-class/main/README.md | v2.0 title, maintenance notice, citation 2023 | fetched 2026-10-17 |
| https://api.github.com/repos/huggingface/deep-rl-class/contents/units/en | unit folders 0-8 and bonus units | fetched 2026-10-17 |
| https://github.com/huggingface/diffusion-models-class | repo pushed 2026-10-14, 4,378 stars | fetched 2026-10-17 |
| https://huggingface.co/learn/diffusion-course/unit0/1 | four units, theory plus two notebooks each | fetched 2026-10-17 |
| https://github.com/huggingface/smol-course | v2 live, module table, prerequisites, local-machine remark | pushed 2026-10-06 |
| https://github.com/huggingface/agents-course | 4 units, free sign-up, citation 2025 | pushed 2026-10-14 |
| https://developers.google.com/machine-learning/crash-course | landing page: 12 modules, "refreshed version" text | fetched 2026-10-17 |
| https://developers.google.com/machine-learning/crash-course/prereqs-and-prework | exercise minutes, prerequisites, Keras/NumPy/pandas | fetched 2026-10-17 |
| https://www.coursera.org/specializations/machine-learning-introduction | 3 courses (33/34/28 h), "2 months", $49/month, enrolled count | fetched 2026-10-17 (reader proxy) |
| https://www.coursera.org/specializations/deep-learning | 5 courses (25/24/7/36/37 h), "3 months", enrolled count | fetched 2026-10-17 (reader proxy) |
| https://www.kaggle.com/learn/intermediate-machine-learning , https://www.kaggle.com/learn/intro-to-machine-learning , https://www.kaggle.com/learn/intro-to-deep-learning | lesson titles; Intermediate 4 h; pipelines, CV, leakage; Keras and TensorFlow | fetched 2026-10-17 (reader proxy) |
| https://www.kaggle.com/learn/feature-engineering , https://www.kaggle.com/learn/computer-vision , https://www.kaggle.com/learn/time-series , https://www.kaggle.com/learn/machine-learning-explainability | hours (5, 4, 5, 4) and lesson titles | fetched 2026-10-17 (reader proxy) |
| https://www.kaggle.com/learn/data-leakage | returns Kaggle home page, not a course | fetched 2026-10-17 |
| https://d2l.ai/ and https://api.github.com/repos/d2l-ai/d2l-en (also /releases) | 23-chapter table of contents, PyTorch and MXNet nav, v1.0.3 (2023-08-18), last push 2024-08-18 | fetched 2026-10-17 |
| https://homl.info/ | Scikit-Learn and PyTorch edition, O'Reilly 10-2025 | fetched 2026-10-17 |
| https://ingramacademic.com/products/hands-on-machine-learning-with-scikit-learn-and-pytorch-9798341607989 | ISBN 9798341607989 | listing, 2026-10-17 |
| https://github.com/ageron/handson-ml3 | third edition, Keras and TensorFlow 2, last push | 2026-10-06 |
| https://github.com/rasbt/LLMs-from-scratch | chapter table, Manning 2024 ISBN, 17h15m video, laptops | last push 2026-10-02 |
| https://www.manning.com/books/build-a-large-language-model-from-scratch | book listing, BPE chapter 2.5 | fetched 2026-10-17 (reader proxy) |
| https://github.com/rasbt/reasoning-from-scratch | chapters, Manning 2025, Qwen3, consumer hardware | last push 2026-10-02 |
| https://www.manning.com/books/build-a-reasoning-model-from-scratch | ISBN 9781633434677, 440 pages, eight chapters | fetched 2026-10-17 (reader proxy) |
| https://github.com/chiphuyen/aie-book | WIP status, O'Reilly 2025 citation | last push 2026-07-03 |
| https://raw.githubusercontent.com/chiphuyen/aie-book/main/chapter-summaries.md | 10 chapter titles | fetched 2026-10-17 |
| https://cs229.stanford.edu/ | Summer 2026, topics, prerequisites | fetched 2026-10-17 |
| https://cs231n.stanford.edu/ | Spring 2026, Python and numpy, 45% assignments | fetched 2026-10-17 |
| https://web.stanford.edu/class/cs224n/ | Winter 2026, NumPy and PyTorch, assignment weights, 2024 public videos | fetched 2026-10-17 |
| https://cs336.stanford.edu/ | Spring 2026, five assignments, AI policy, GPU note | fetched 2026-10-17 |
| https://introtodeeplearning.com/ | 2026 run dates, lectures 1-9, labs 1-3 | fetched 2026-10-17 |
| https://github.com/MITDeepLearning/introtodeeplearning | labs repo, last push | 2026-01-04 |
| https://fullstackdeeplearning.com/ | FSDL 2022 units, labs 4-8, LLM Bootcamp 2023 | fetched 2026-10-17 |
| https://madewithml.com/ and https://github.com/GokuMohandas/Made-With-ML | course modules; description; laptop-as-cluster path; last push | pushed 2026-03-04 |
| https://github.com/microsoft/generative-ai-for-beginners | 21 lessons, Version 3, provider note | pushed 2026-10-15 |
| https://maven.com/courses/ai/evals | cohort listing, rating 4.7, Oct 10 - Nov 21 | fetched 2026-10-17 (reader proxy) |
| https://cme295.stanford.edu/syllabus/ | 2026 lecture and exam dates | fetched 2026-10-17 |
| https://www.oreilly.com/library/view/hands-on-machine-learning/9798341607989/ | blocked (HTTP 403); no facts taken | checked 2026-10-17 |

## 5. Conflicts and open questions

- nanochat cost and time: the intro says "$48 (~2 hours of 8XH100 GPU node)". The speedrun section says "~1.5 hours to run" (https://raw.githubusercontent.com/karpathy/nanochat/master/README.md). Check runs/speedrun.sh before you budget.
- Karpathy series: the series page lists 8 videos and "ongoing..." (https://karpathy.ai/zero-to-hero.html). YouTube has a ninth, the GPT-2 video, published 2024-06-09 (https://www.youtube.com/watch?v=l8pRSuU81PU). Treat the page as out of date.
- ML Specialization: the headline says "2 months at 10 hours a week", but the per-course hours total 95 h (https://www.coursera.org/specializations/machine-learning-introduction). Use the per-course hours.
- smol course: the module table still shows Oct to Dec 2025 release dates for modules 5 to 7. The repo was pushed 2026-10-06, and the README says the course "will soon be re-released on Hugging Face Learn" (https://github.com/huggingface/smol-course). Status unclear.
- HF LLM course: the intro lists 9 chapters, the GitHub repo is a 56-byte stub (pushed 2025-03-24), and `chapters/en` returned 404. More chapters may exist [unverified].
- HF Deep RL: low maintenance, leaderboard down, Unit 7 broken, citation year 2023 (https://github.com/huggingface/deep-rl-class).
- d2l: the newest tag is v1.0.3 (2023-08-18) and the last push is 2024-08-18 (https://api.github.com/repos/d2l-ai/d2l-en). Possibly stale.
- Geron 2025 and Huyen 2025: "10-2025" on the Geron author site (https://homl.info/), while search listings show Oct to Dec 2025 (https://ingramacademic.com/products/hands-on-machine-learning-with-scikit-learn-and-pytorch-9798341607989). The Geron table of contents and the exact Huyen date are NOT verified, because O'Reilly is blocked.
- CME 295: a search summary said the syllabus lists 2025 dates. The fetched official syllabus lists 2026 dates (https://cme295.stanford.edu/syllabus/). I used the official page.
- MIT 6.S191: the labs repo's last push is 2026-01-04, before the Mar to May 2026 run (https://github.com/MITDeepLearning/introtodeeplearning). The 2026 labs may be on the course site only [unverified].
- Stanford CS224n and CS231n: the CS224n site says the public videos are the 2024 offering (https://web.stanford.edu/class/cs224n/). The CS231n site says Python and numpy, with no PyTorch mention (https://cs231n.stanford.edu/).
- MLCC: the "2024 refresh" date does not appear in the fetched HTML, and no total hours are stated (https://developers.google.com/machine-learning/crash-course).
- Kaggle: hours for Intro ML and Intro DL were not captured. The full index is a JavaScript shell. The data-leakage URL is not a course (https://www.kaggle.com/learn/data-leakage).
- Eureka and llm.c: the EurekaLabsAI org shows no public repos (https://api.github.com/orgs/EurekaLabsAI/repos). The README of llm.c says "Current focus is on pretraining", but its last code push is 2025-06-26 (https://api.github.com/repos/karpathy/llm.c). Possibly stale.
- Prices: the Maven cohort has no year in the fetched text and no price. A third-party listing gives $1,995, which I did not use (https://maven.com/courses/ai/evals). The $49/month Coursera figure is page text from 2026-10-17 and will change.
- Coverage gaps: O'Reilly pages were blocked. Kaggle's full index was not captured. Made With ML lesson counts and the MIT 2026 lab notebooks were not fetched.

## 6. Lab ideas from this topic

Hardware: M4 Pro with 24 GB. Use PyTorch on MPS (Apple GPU). nanochat's README says bf16 works on MPS on recent macOS. Use Kaggle or Colab for anything larger. Free GPU quotas were not checked.

**Lab 1. Backprop by hand (micrograd, first hour).** Concept: the chain rule on a graph of scalars (https://www.youtube.com/watch?v=VMj-3S1tku0). Dataset: none. Use 20 random expressions built with your own Value class. Outcome: analytic and finite-difference gradients agree within a tolerance you pick (for example 1e-6). Log the largest error. CPU only.

**Lab 2. Overfit a character model (makemore 2, MLP).** Concept: train vs dev loss, model size, data splits (https://www.youtube.com/watch?v=TCH_1BHY58I). Dataset: tinyshakespeare, a single 1 MB text file (https://raw.githubusercontent.com/karpathy/nanoGPT/master/README.md; the llm.c README links the file at https://raw.githubusercontent.com/karpathy/llm.c/master/README.md). Outcome: train and dev loss at three hidden sizes. Note the size where dev loss turns up while train loss keeps falling. Mac CPU or MPS.

**Lab 3. The BPE merge loop (tokenizer video).** Concept: tokens, compression, and round-trip safety (https://www.youtube.com/watch?v=zduSFxRajkE). Dataset: tinyshakespeare, as in Lab 2. Outcome: encode then decode returns the input for 10 of 10 test strings. Record tokens per 1,000 characters before and after 256 merges. CPU.

**Lab 4. Sliding-window training pairs (Raschka chapter 2).** Concept: next-token training data and stride (https://github.com/rasbt/LLMs-from-scratch). Dataset: tinyshakespeare. Outcome: the number of (input, target) pairs for stride 1, and for stride equal to the context length. Check that each target is its input shifted by one token. CPU.

**Lab 5. nanochat on the Mac (runs/runcpu.sh).** Concept: the LLM pipeline end to end, plus cost and throughput (https://raw.githubusercontent.com/karpathy/nanochat/master/README.md). Dataset: whatever shards the script downloads. Read the script first. Outcome: val_bpb after a 10 to 20 minute run, tokens per second, and peak memory for float32 vs bfloat16 on MPS.

**Lab 6. Thresholds and metrics (MLCC classification).** Concept: precision, recall, AUC, and threshold choice (https://developers.google.com/machine-learning/crash-course). Dataset: the one the exercise uses [check the notebook]. Outcome: precision and recall at three thresholds. Pick one for a stated cost ratio (for example, a missed positive costs five times a false alarm) and justify it.

**Lab 7. Pipelines, cross-validation, and leakage (Kaggle Intermediate ML, lessons 4, 5, 7).** Concept: data leakage, cross-validation, and pipelines (https://www.kaggle.com/learn/intermediate-machine-learning). Dataset: a house-price table. Kaggle pages mention "House Prices", and d2l section 5.7 is "Predicting House Prices on Kaggle" (https://d2l.ai/). Outcome: 5-fold CV mean absolute error for a pipeline that fits the imputer inside each fold, vs one that fits it on all rows. Report the gap. The leaky version should look better, which is the trap.

**Lab 8. Instruction tuning a small model (smol course module 1).** Concept: supervised fine-tuning, chat format, and evaluation (https://github.com/huggingface/smol-course). Dataset: a 50-example instruction set you write, or the course set [verify]. Outcome: format adherence on 20 held-out prompts before and after tuning, and seconds per training step on MPS. Use a small model and check memory first.
