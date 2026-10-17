# fast.ai "Practical Deep Learning for Coders": course map, method, notebooks, and library state

As of 17 Oct 2026. Built from primary sources only: course.fast.ai pages, YouTube watch pages, GitHub repos and API, PyPI JSON, fast.ai and answer.ai posts, Microsoft Learn, SerpAPI pricing, and Kaggle pages. Measured values (video minutes, file sizes, install results) are my own readings, and each one names its source. Items marked [unverified] could not be opened or confirmed. Anything last updated before 2024 is flagged as stale.

## 0. Takeaways

- Part 1 is the 2022 recording. The home page says "Practical Deep Learning for Coders 2022 part 1". It has 8 numbered lessons plus 1 bonus ethics lesson recorded in 2020. Measured video total: 14.7 h. ([home](https://course.fast.ai/), [lesson 8a](https://course.fast.ai/Lessons/lesson8a.html))
- Part 2 is "Deep Learning Foundations to Stable Diffusion" (2022-23). It has 17 numbered lessons (9 to 25) plus 2 community bonus videos. Measured video total: 30.3 h. ([part 2](https://course.fast.ai/Lessons/part2.html))
- I found no newer Part 1 edition on course.fast.ai or on the fast.ai and answer.ai post indexes (read 2026-10-17). ([fast.ai index](https://www.fast.ai/), [answer.ai index](https://www.answer.ai/))
- The site advises against training models on your own computer. Its notebooks run on Kaggle or Paperspace. ([home](https://course.fast.ai/))
- fastai 2.8.12 (uploaded 2026-09-09) resolves with wheels only on this Mac's Python 3.14.3. A one-epoch test on this Mac trained on MPS (section 7). MPS (Apple GPU) is chosen by default when torch reports it. ([PyPI](https://pypi.org/pypi/fastai/json), [torch_core.py](https://github.com/fastai/fastai/blob/main/fastai/torch_core.py))
- The 2022 notebook repos are old: course22 last pushed 2024-10-08, course22p2 last commit 2023-05-04. fastbook is active (pushed 2026-10-12). Chapter 2 now needs a SerpAPI key because Microsoft retired the Bing Image Search API. ([course22 API](https://api.github.com/repos/fastai/course22), [fastbook API](https://api.github.com/repos/fastai/fastbook), [fastbook ch2](https://github.com/fastai/fastbook/blob/master/02_production.ipynb))
- solveit is a separate paid 5-week course. The solve.it.com snapshot shows a $500 fee and closed signups. ([solve.it.com](https://solve.it.com/))

## 1. Course versions, lengths, and prerequisites

| Item | Fact | Source |
|---|---|---|
| Part 1 edition | "Practical Deep Learning for Coders 2022 part 1, recorded at the University of Queensland" | [home](https://course.fast.ai/) |
| Part 1 count | Home text: "There are 9 lessons, and each lesson is around 90 minutes long." Nav: lessons 1-8 plus "Bonus: Data ethics" | [home](https://course.fast.ai/), [2022 launch post, 2022-07-21](https://www.fast.ai/posts/2022-07-21-dl-coders-22.html) |
| Part 1 video (measured) | Lessons 1-8: 753.9 min (12.6 h). Average 94.2 min. Range 76.7 to 106.7 min. Ethics: 127.4 min | [YouTube watch pages, read 2026-10-17](https://www.youtube.com/watch?v=8SF_h3xF3cE) (IDs in section 2) |
| Part 1 publish dates | Lessons 1-8: 2022-07-21. Ethics: 2020-08-21, page says "recorded in 2020 during the previous iteration of this course" | YouTube publishDate; [lesson 8a](https://course.fast.ai/Lessons/lesson8a.html) |
| Part 2 edition | "Practical Deep Learning for Coders part 2: Deep Learning Foundations to Stable Diffusion". Overview: "containing over 30 hours of video content" | [part 2](https://course.fast.ai/Lessons/part2.html) |
| Part 2 count | 17 numbered lessons (9-25). Bonus 9a (John Whitaker deep dive) and 9b (math of diffusion) are community videos | [lesson 9](https://course.fast.ai/Lessons/lesson9.html) |
| Part 2 video (measured) | 1,817.6 min (30.3 h). Average 106.9 min. Shortest L16 (85.7 min), longest L9 (135.2 min) | YouTube watch pages |
| Part 2 publish dates | L9-10: 2022-10-19. L11-25: 2023-04-04 | YouTube publishDate |
| Part 1 prerequisite | "The only prerequisite is that you know how to code (a year of experience is enough), preferably in Python, and that you have at least followed a high school math course." | [home](https://course.fast.ai/) |
| Part 2 prerequisite | "If you've finished fast.ai's Practical Deep Learning course then you'll be ready!" | [part 2](https://course.fast.ai/Lessons/part2.html) |
| Refresh status | No 2024-2026 Part 1 edition found. Post index shows solveit posts and 2026 essays only | [fast.ai index](https://www.fast.ai/) |

Video length is the `lengthSeconds` field on each YouTube watch page, read 2026-10-17.

## 2. Part 1 lesson map

Takeaway: Part 1 teaches a bird classifier first, then builds up to models from scratch and to CNNs. Kaggle notebooks carry the hands-on work. The book chapters cited on each page are in the Chapter column.

| L | Topic (nav) | Min | YouTube ID | Kaggle notebooks linked on page | course22 root notebook | Dataset | Book ch. |
|---|---|---|---|---|---|---|---|
| 1 | Getting started | 82.9 | 8SF_h3xF3cE | "Is it a bird? Creating a model from your own data"; "Jupyter Notebook 101" | 00-is-it-a-bird; 01-jupyter-notebook-101 | Web images from DuckDuckGo search | 1 |
| 2 | Deployment | 76.7 | F4tvM4Vb3A0 | saving-a-basic-fastai-model; Colab link; Hugging Face Spaces | 02-saving-a-basic-fastai-model; 03-which-image-models-are-best | PETS (812 MB); timm benchmark CSVs | 2 |
| 3 | Neural net foundations | 90.4 | hBBOjCiFcuo | how-does-a-neural-net-really-work; which-image-models-are-best; Titanic competition | 04-how-does-a-neural-net-really-work | Titanic spreadsheet (xl folder) | 4 |
| 4 | Natural language (NLP) | 94.6 | toUgBQv1BT8 | getting-started-with-nlp-for-absolute-beginners (links US Patent Phrase to Phrase Matching) | none in root | US Patent Phrase to Phrase Matching (Kaggle) | 10 |
| 5 | From-scratch model | 102.8 | _rXzeWq4C6w | linear-model-and-neural-net-from-scratch; why-you-should-use-a-framework | 05-; 06- | Titanic train.csv and test.csv | 4, 9 |
| 6 | Random forests | 102.9 | AdhG64NF76E | how-random-forests-really-work; first-steps-road-to-the-top-part-1 | 07-; 08- | Titanic (07); Paddy Doctor (08) | 9 |
| 7 | Collaborative filtering | 106.7 | p4ZZq0736Po | collaborative-filtering-deep-dive; scaling-up-road-to-the-top-part-3; multi-target-road-to-the-top-part-4 | 10- (part 3); xl/collab_filter.xlsx | ML-100k (4.9 MB) | 8 |
| 8 | Convolutions (CNNs) | 96.9 | htiNBPxcXgo | none; fastbook 13_convolutions linked | 09- (Road to the Top part 2) is in root, not linked here | MNIST and MNIST_SAMPLE (fastbook 13) | 13 |
| 8a | Bonus: data ethics (2020) | 127.4 | krIVOb23EH8 | none; fastbook 03_ethics linked | none | none in code | 3 |

Concept per lesson (community summaries and page text):
- L1: train and use a bird classifier end to end. Summary: "How to download and display a photo of a bird from DuckDuckGo using simple codes?" ([S1](https://course.fast.ai/Lessons/Summaries/lesson1.html))
- L2: deploy the model. The 2022 launch says "By the end of the second lesson, students will have built and deployed their own deep learning model on their own data." ([launch](https://www.fast.ai/posts/2022-07-21-dl-coders-22.html)). The home page names Gradio and Hugging Face Transformers as tools.
- L3: how a neural net works; comparing image models ([lesson 3](https://course.fast.ai/Lessons/lesson3.html))
- L4: NLP fine-tuning with Hugging Face, "rather than fastai library" ([S4](https://course.fast.ai/Lessons/Summaries/lesson4.html))
- L5: linear model, then a neural net with hidden layers ([S5](https://course.fast.ai/Lessons/Summaries/lesson5.html))
- L6: decision trees built by hand, gini, random forests ([S6](https://course.fast.ai/Lessons/Summaries/lesson6.html))
- L7: ensembles, multi-target models, cross-entropy and softmax ([S7](https://course.fast.ai/Lessons/Summaries/lesson7.html))
- L8: embeddings, collaborative filtering, convolutions ([S8](https://course.fast.ai/Lessons/Summaries/lesson8.html))
- L8a: data ethics with case studies, taught by Rachel Thomas ([lesson 8a](https://course.fast.ai/Lessons/lesson8a.html))

## 3. Part 2 lesson map

Takeaway: Part 2 builds Stable Diffusion from scratch in a library called miniai. Most notebooks are in course22p2, and the names are matched to lesson topics by me, except where a lesson page links the file.

| L | Title (nav) | Min | YouTube ID | What it builds (lesson summary) | Notebook (course22p2/nbs unless noted) | Dataset |
|---|---|---|---|---|---|---|
| 9 | Stable Diffusion | 135.2 | _7rMfsA24Ls | Diffusers pipelines; links "Stable Diffusion Deep Dive" (diffusion-nbs) | diffusion-nbs (linked) | pretrained models |
| 10 | Diving Deeper | 109.2 | 6StU6UtZEbU | Diffusers pipeline from VAE, UNet, scheduler, tokenizer; starts miniai | course22p2 and diffusion-nbs (linked, no file named) | none stated |
| 11 | Matrix multiplication | 108.3 | Tf-8F5q8Xww | matmul from scratch; reading the DiffEdit paper | 01_matmul (topic match) | MNIST (in code) |
| 12 | Mean shift clustering | 110.4 | _xIzPbCgutY | CLIP Interrogator; einsum; CUDA/Numba kernel; mean shift | 02_meanshift (topic match) | synthetic data (summary) |
| 13 | Backpropagation and MLP | 106.0 | vGdB4eI4KBs | chain rule; MLP from scratch | 03_backprop; 04_minibatch_training (topic match) | not checked |
| 14 | Backpropagation | 109.6 | veqj0DsZSXU | nn.Module and nn.Sequential; custom modules | 03_backprop (topic match) | not checked |
| 15 | Autoencoders | 97.3 | 0Hi2r4CaHvk | convolution from scratch; CNN; motivation for Learner | 08_autoencoder (topic match) | Fashion-MNIST (in code) |
| 16 | The Learner framework | 85.7 | 9YZaYjRKuEc | callbacks, metrics, DeviceCB | 09_learner (topic match) | not checked |
| 17 | Initialization and normalization | 116.6 | vGsc_NbU7xc | weight init; hooks; ActivationStats | 10_activations; 11_initializing (topic match) | not checked |
| 18 | Accelerated SGD and ResNets | 125.9 | nlVOG2Nzc3k | momentum, RMSProp, Adam (in Excel); cosine annealing; ResNets | 12_accel_sgd; 13_resnet; xl/graddesc.xlsm (linked) | Fashion-MNIST (in code) |
| 19 | DDPM and Dropout | 90.0 | ItyO8s48zdc | dropout; DDPM with guests Tanishq and Johno | 15_DDPM (topic match) | not checked |
| 20 | Mixed precision | 105.7 | PdNHkTLU2oQ | MixedPrecision callback; Hugging Face Accelerate | none linked | not checked |
| 21 | DDIM | 115.8 | PXiD7ZjOKhA | experiments on Fashion-MNIST and CIFAR-10; Weights and Biases | 20_DDIM; 21_cifar10_and_wandb (topic match) | Fashion-MNIST, CIFAR-10 (summary) |
| 22 | Karras et al (2022) | 86.7 | 6Bta1tXRUfM | Karras et al. diffusion paper | 23_karras (topic match) | not checked |
| 23 | Super-resolution | 100.9 | z1In7QaG0fg | U-Net super-resolution; AdamW; mixed precision | 25_superres; 24_imgnet_tiny (topic match) | Tiny ImageNet (in code) |
| 24 | Attention and transformers | 115.8 | DH5bp6zTPB4 | time embedding; attention; unconditional model on Fashion-MNIST | 27_attention (topic match) | Fashion-MNIST (summary) |
| 25 | Latent diffusion | 98.4 | 8AgZ9jcQ9v8 | VAE latents as pixels; bird-song generator (Johno Whitaker) | 29_vae; 30_lsun_diffusion-latents; 31_imgnet_latents-widish (linked) | LSUN (in code, nb 30) |

Bonus: 9a is a deep dive by John Whitaker with a notebook. 9b is "The Math of Diffusion". Neither is timed here ([lesson 9](https://course.fast.ai/Lessons/lesson9.html)).

Part 2 notebook list (course22p2 nbs, read 2026-10-17): 01_matmul, 02_meanshift, 03_backprop, 04_minibatch_training, 05_datasets, 06_foundations, 07_convolutions, 08_autoencoder, 09_learner, 10_activations, 11_initializing, 12_accel_sgd, 13_resnet, 14_augment, 15_DDPM, 16A/16B (style transfer, NCA), 17_DDPM_v2, 18_fid, 19_DDPM_v3, 20_DDIM, 21_cifar10_and_wandb, 22_cosine, 22_noise-pred, 23_karras, 24_imgnet_tiny (variants), 25_superres, 26_diffusion_unet, 27_attention, 28_diffusion-attn-cond, 29_vae, 30_lsun_diffusion-latents, 30_lsun_diffusion-simple, 31_imgnet_latents-widish ([nbs](https://github.com/fastai/course22p2/tree/master/nbs)).

## 4. Teaching method (quotes with links)

- Top-down. "But we go 'top down': start with complete useful solutions to real world problems, and gradually work down to the basic foundations. Education experts recommend this approach for more effective learning." ([lesson 1](https://course.fast.ai/Lessons/lesson1.html))
- Whole game. The 2016 post says: "Teaching 'the whole game'" means starting "by showing how to use a complete, working, very usable, state of the art deep learning network to solve real world problems". ([2016 post, stale](https://www.fast.ai/posts/2016-10-08-teaching-philosophy.html))
- Elementitis. The 2016 post credits David Perkins: not doing anything complicated "until you've taught all the individual elements first" is "a disease: 'elementitis'." ([2016 post](https://www.fast.ai/posts/2016-10-08-teaching-philosophy.html)). Lesson 1 lists "Making Learning Whole by David Perkins" as a recommended book. ([lesson 1](https://course.fast.ai/Lessons/lesson1.html))
- Spaced repetition: "The whole game method of learning dovetails nicely with spaced repetition learning." ([2016 post](https://www.fast.ai/posts/2016-10-08-teaching-philosophy.html))
- Notebooks first: "If you don't work through the notebooks yourself, you're not going to get nearly as much out of this course." ([lesson 1](https://course.fast.ai/Lessons/lesson1.html))
- Video plus book: "As well as watching the video and working through the notebooks, you should also read the relevent [sic] chapter(s) of the fast.ai book." ([lesson 1](https://course.fast.ai/Lessons/lesson1.html))
- Part 2 notebooks: "Each video goes through one or more Jupyter notebooks, which you'll need to run and experiment with to get the most out of the course." ([lesson 9](https://course.fast.ai/Lessons/lesson9.html))
- Effort: "you should expect to work hard and put in plenty of hours of study" ([lesson 9](https://course.fast.ai/Lessons/lesson9.html)). No official hours per lesson was found. The home page gives video length (about 90 min per lesson). A 2019 community guide asks for "At least 8 hours a week to commit to the course (includes time for homework)" ([study group guide, 2019, stale](https://forums.fast.ai/t/fastai-study-group-guide/42616)).
- Skim first: "To get a sense of what's covered in a lesson, you might want to skim through some lesson notes taken by one of our students" ([home](https://course.fast.ai/)).
- Do not train locally: "We strongly suggest not using your own computer for training models in this course, unless you're very experienced with Linux system adminstration [sic] and handling GPU drivers, CUDA, and so forth." ([home](https://course.fast.ai/))
- Share and blog: the home page links the "Share your work here" thread ([home](https://course.fast.ai/), [thread](https://forums.fast.ai/t/share-your-work-here/96015)). Lesson 1 lists "Blogging: fastpages" as a resource ([lesson 1](https://course.fast.ai/Lessons/lesson1.html)).
- The exact sequence "watch, run the notebook, rebuild it, share or blog it" was not found on any page I read. Treat it as a paraphrase [unverified].
- Study groups: Lesson 9 says "Studying in groups has been shown to be more effective for most people than studying alone" ([lesson 9](https://course.fast.ai/Lessons/lesson9.html)). The 2019 guide notes that Jeremy Howard "facilitated the creation of local fastai Part 1 (2018) study groups" and lists a teaching practice: "each course should get a time for practice" ([guide](https://forums.fast.ai/t/fastai-study-group-guide/42616)). A 2023 Discord group is "a free format study group for fastai Course Parts 1 and 2" where "it doesn't matter what lesson you're on" ([forum topic, 2023-08-20](https://forums.fast.ai/t/deep-learners-study-group-for-fastai-course-parts-1-and-2/107763)).
- From scratch: "When we say 'from scratch', we mean that you'll rely on nothing other than Python and its standard library." ([part 2](https://course.fast.ai/Lessons/part2.html))

## 5. The book (fastbook)

- Free and licensed: "Everything in this repo is copyright Jeremy Howard and Sylvain Gugger, 2020 onwards." The code is GPL v3. The prose "is not licensed for any redistribution or change of format or medium". Some chapters are read online at fastai.github.io/fastbook2e. Each chapter opens in Colab. ([fastbook README](https://github.com/fastai/fastbook))
- Last push: 2026-10-12, a SerpAPI change to chapter 2 ([commits](https://github.com/fastai/fastbook/commits/master)).
- Lessons cite these chapters: 1, 2, 3, 4, 8, 9, 10, 13. Chapters 5-7, 11, 12, and 14-20 are cited by no Part 1 page.

| Ch | Title | Cited by Part 1 lesson | Datasets loaded in code | Questionnaire items | Further Research items |
|---|---|---|---|---|---|
| 1 | Your Deep Learning Journey | L1 | ADULT_SAMPLE, CAMVID_TINY, IMDB, ML_SAMPLE, PETS | 33 | 2 |
| 2 | From Model to Production | L2 | Bing images via SerpAPI (needs key) | 27 | 4 |
| 3 | Data Ethics | L8a | none | 18 | 0 |
| 4 | Under the Hood: Training a Digit Classifier | L3, L5 | MNIST_SAMPLE | 37 | 2 |
| 5 | Image Classification | none | PETS | 23 | 2 |
| 6 | Other Computer Vision Problems | none | BIWI_HEAD_POSE, PASCAL_2007 | 17 | 2 |
| 7 | Training a State-of-the-Art Model | none | IMAGENETTE | 14 | 4 |
| 8 | Collaborative Filtering Deep Dive | L7 | ML_100k (MovieLens) | 31 | 4 |
| 9 | Tabular Modeling Deep Dive | L5, L6 | Blue Book for Bulldozers (Kaggle) | 30 | 4 |
| 10 | NLP Deep Dive: RNNs | L4 | IMDB | 22 | 2 |
| 11 | Data Munging with fastai's Mid-Level API | none | IMDB, PETS | 15 | 2 |
| 12 | A Language Model from Scratch | none | HUMAN_NUMBERS | 39 | 4 |
| 13 | Convolutional Neural Networks | L8 | MNIST, MNIST_SAMPLE | 40 | 3 |
| 14 | ResNets | none | IMAGENETTE_160, IMAGENETTE_320 | 22 | 4 |
| 15 | Application Architectures Deep Dive | none | PETS | 18 | 5 |
| 16 | The Training Process | none | IMAGENETTE_160 | 27 | 4 |
| 17 | A Neural Net from the Foundations | none | none | 40 | 4 |
| 18 | CNN Interpretation with CAM | none | PETS | 13 | 2 |
| 19 | A fastai Learner from Scratch | none | IMAGENETTE_160 | 34 | 9 |
| 20 | Concluding Thoughts | none | none | 0 | 0 |

Counts come from my parser over the chapter notebooks on master (read 2026-10-17). Totals: 500 numbered questionnaire items in ch 1-19, and 63 Further Research items. Source: [fastbook notebooks](https://github.com/fastai/fastbook).

Questionnaire examples:
- Ch 4: "How is a grayscale image represented on a computer? How about a color image?" (recall and explain)
- Ch 13: "Write out the convolutional kernel matrix for a top edge detector." (write the math)
- Ch 17: "Write the Python code to implement a single neuron." (code from scratch)

Further Research examples:
- Ch 8: "Take a look at all the differences between the `Embedding` version of `DotProductBias` and the `create_params` version, and try to understand why each of those changes is required." (read and diff code)
- Ch 7: "Use the fastai documentation to build a function that crops an image to a square in each of the four corners, then implement a TTA method that averages the predictions..." (build and measure)

## 6. Notebook repos, Kaggle notebooks, and datasets

- course22 (2022 edition): "the notebooks, slides, and spreadsheets for the 2022 edition". Root has 00 to 10 (Kaggle-style). Last push 2024-10-08 ([README](https://github.com/fastai/course22), [API](https://api.github.com/repos/fastai/course22)).
- course22p2 (2022-23): "the notebooks for part 2 of fast.ai's 2022-23 course". miniai is built from them with nbdev. Apache-2.0. Last commit 2023-05-04 ([README](https://github.com/fastai/course22p2), [API](https://api.github.com/repos/fastai/course22p2)).
- Kaggle notebooks named by the user exist (HTTP 200, read 2026-10-17): [Is it a bird](https://www.kaggle.com/code/jhoward/is-it-a-bird-creating-a-model-from-your-own-data), [NLP for absolute beginners](https://www.kaggle.com/code/jhoward/getting-started-with-nlp-for-absolute-beginners), [Linear model and neural net from scratch](https://www.kaggle.com/code/jhoward/linear-model-and-neural-net-from-scratch), [Road to the Top part 1](https://www.kaggle.com/code/jhoward/first-steps-road-to-the-top-part-1).
- Road to the Top data: the Kaggle competition "Paddy Doctor: Paddy Disease Classification" ([competition](https://www.kaggle.com/competitions/paddy-disease-classification)). course22 notebooks 08 to 10 reference it ([08](https://github.com/fastai/course22/blob/master/08-first-steps-road-to-the-top-part-1.ipynb), [10](https://github.com/fastai/course22/blob/master/10-scaling-up-road-to-the-top-part-3.ipynb)).
- "Is it a bird?" data: the notebook calls `search_images` with `DDGS` from `duckduckgo_search` ([notebook 00](https://github.com/fastai/course22/blob/master/00-is-it-a-bird-creating-a-model-from-your-own-data.ipynb)).
- Titanic data (Lessons 3, 5, 6): notebooks 05 and 07 read `train.csv` and `test.csv` from the Titanic competition ([notebook 05](https://github.com/fastai/course22/blob/master/05-linear-model-and-neural-net-from-scratch.ipynb), [competition](https://www.kaggle.com/competitions/titanic)).

Dataset sizes (fastai dataset registry, HTTP HEAD on 2026-10-17):

| Name | Archive (registry source) | Size | Used in |
|---|---|---|---|
| MNIST_SAMPLE | fast-ai-sample/mnist_sample.tgz | 3.2 MB | fastbook 4, 13 |
| ML_100k | files.grouplens.org ml-100k.zip | 4.9 MB | fastbook 8 |
| ADULT_SAMPLE | fast-ai-sample/adult_sample.tgz | 1.0 MB | fastbook 1 |
| ML_SAMPLE | fast-ai-sample/movie_lens_sample.tgz | 52 KB | fastbook 1 |
| PETS | fast-ai-imageclas/oxford-iiit-pet.tgz | 812 MB | fastbook 1, 2, 5, 11, 15, 18; Part 1 L2 |
| IMDB | fast-ai-nlp/imdb.tgz | 144 MB | fastbook 1, 10, 11 |
| IMAGENETTE | fast-ai-imageclas/imagenette2.tgz | 1.56 GB | fastbook 7; IMAGENETTE_160 in 14, 16, 19 |

Registry: [external.py](https://github.com/fastai/fastai/blob/main/fastai/data/external.py). Sizes: [HEAD checks against the same URLs](https://s3.amazonaws.com/fast-ai-sample/mnist_sample.tgz). Chapter dataset usage: [fastbook](https://github.com/fastai/fastbook).

Other datasets: Fashion-MNIST, Tiny ImageNet, LSUN, and CIFAR-10 appear in Part 2 notebooks. I did not check their loading sources [unverified].

## 7. fastai library state (as of 2026-10-17)

- Latest: 2.8.12, uploaded 2026-09-09 ([PyPI](https://pypi.org/pypi/fastai/json), [GitHub releases](https://api.github.com/repos/fastai/fastai/releases)).
- 2025 releases: 2.7.19 (2025-03-12), 2.8.0 (03-18), 2.8.1 (04-18), 2.8.2 (05-24), 2.8.3 (08-07), 2.8.4 (08-19), 2.8.5 (10-26), 2.8.6 (12-15). 2026: 2.8.7 (02-14), 2.8.8 (07-30), 2.8.9 and 2.8.10 (09-06), 2.8.11 (09-07), 2.8.12 (09-09). ([PyPI](https://pypi.org/pypi/fastai/json))
- Commits on the default branch: about 93 in 2025 and about 52 in 2026 (through 2026-09-21, the latest commit). Counted from the paginated GitHub commits API. ([API](https://api.github.com/repos/fastai/fastai/commits))
- Python range: `requires-python = ">=3.10"` ([pyproject](https://github.com/fastai/fastai/blob/main/pyproject.toml)). CI tests Python 3.11, 3.12, 3.13 only ([main.yml](https://github.com/fastai/fastai/blob/main/.github/workflows/main.yml)).
- Dependencies: torch<3,>=1.10; torchvision>=0.11; spacy<4; plum-dispatch<2.10; fastcore>=2.2.22 ([PyPI requires_dist](https://pypi.org/pypi/fastai/json)).
- Install check (pip dry run, nothing installed, wheels only): on Python 3.14.3 for macOS arm64, pip resolves 90 packages. These include torch 2.14.1 (cp314 macosx_14_0_arm64 wheel, uploaded 2026-09-30), torchvision 0.29.1, spacy 3.8.16, thinc 8.3.13, numpy 2.5.4, pandas 3.0.6, scikit-learn 1.9.1. The same resolve works with `--python-version 3.13` tags ([PyPI torch](https://pypi.org/pypi/torch/json)).
- Install size: torch wheel 127.7 MB. The 18 resolved packages whose PyPI metadata I had cached total about 216 MB of wheels. The largest are torch, scipy (29.2 MB), spacy, numpy, pandas, matplotlib, and scikit-learn. Other packages were not counted ([PyPI](https://pypi.org/pypi/torch/json)).
- Install command from README: "You can install fastai on your own machines with: `pip install fastai`." ([README](https://github.com/fastai/fastai/blob/main/README.md))
- Scratch-venv smoke test on this M4 Pro (Python 3.14.3, fastai 2.8.12, torch 2.14.1). The venv sits in the session scratchpad, outside the repo.
  - `pip install fastai` into a fresh venv succeeded with wheels only (exit 0). `from fastai.vision.all import *` imports cleanly.
  - `fastai.torch_core.default_device()` returned `mps:0`, and `dls.device` was `mps:0`.
  - One epoch on MNIST_SAMPLE with a tiny conv net took 7.0 s on the default device and 6.4 s with `defaults.use_cuda=False`. The model is too small for a GPU gain to show.
  - Before `fit`, the model parameters are on `cpu`. After `fit` they are on `mps:0`, so fastai moves the model during training. The Learner's callback list had no `DeviceCB` in this version (observed).
  - Larger model, same data: `xresnet18(n_out=2)` on MNIST_SAMPLE at native size, batch size 64, one epoch. Default device: 13.5 s (`mps:0`). With `defaults.use_cuda=False`: 155.3 s (`cpu`). Each is a single run, not an average, and about 11.5 times faster on MPS for this model and data only.
  - Python 3.14 printed a torch FutureWarning: "`torch.jit.script` is not supported in Python 3.14+".

## 8. MPS (Apple GPU) status in fastai

- Code path (fastai main, read 2026-10-17):
  - `defaults.use_cuda = None` (torch_core.py line 261).
  - `_has_mps()` checks `torch.backends.mps.is_available()` (lines 264-266).
  - `default_device()` returns `torch.device('mps', 0)` when CUDA is absent and MPS is present (lines 268-277).
  - `to_device` goes to CPU only if `defaults.use_cuda==False` (line 282).
  - Data loaders call `default_device()` (data/core.py lines 251 and 326). Sources: [torch_core.py](https://github.com/fastai/fastai/blob/main/fastai/torch_core.py), [data/core.py](https://github.com/fastai/fastai/blob/main/fastai/data/core.py).
- To force CPU for debugging: set `defaults.use_cuda = False`. Tested on this Mac: `default_device()` returned `cpu`, and the model stayed on `cpu` through `fit`. The relevant lines are 270-271 and 282 in torch_core.py.
- History:
  - v2.7.6 (2022-07-07): "Initial Mac GPU (mps) support (#3719)" ([release](https://api.github.com/repos/fastai/fastai/releases/tags/2.7.6)).
  - Issue #3769 "revert auto-enable of mac mps due to pytorch limitations" closed 2022-08-07 ([issue](https://github.com/fastai/fastai/issues/3769)).
  - PR #3858 "Fix default_device to correctly detect + use mps (Apple Silicon)" opened 2023-01-14, merged 2023-01-16 ([PR](https://github.com/fastai/fastai/pull/3858)).
- Open PR #4134 "use the torch way of setting default device", opened 2025-11-24, still open on 2026-10-17 ([PR](https://github.com/fastai/fastai/pull/4134)). My search of titles and bodies found no other MPS item created in 2025 or 2026.
- Open MPS issues (still open when read):
  - #3742 tabular dtypes on MPS, 2022-07-20 ([issue](https://github.com/fastai/fastai/issues/3742)).
  - #3911 mask_tensor crash on mps, 2023-05-05 ([issue](https://github.com/fastai/fastai/issues/3911)).
  - #3913 PyTorch 2.0 with fastai 2.7.12 on M2, 2023-05-07 ([issue](https://github.com/fastai/fastai/issues/3913)).
  - #3924 collab_learner and fit_one_cycle crash the kernel on M2, 2023-06-29. The reporter says "Same source runs ok on 'cpu'-Device" ([issue](https://github.com/fastai/fastai/issues/3924)).
  - #3952 "The MPS backend is supported on MacOS 12.3+", 2023-09-01 ([issue](https://github.com/fastai/fastai/issues/3952)).
  - Closed: #3761 IntToFloatTensor missing an MPS op, 2022-08-01 ([issue](https://github.com/fastai/fastai/issues/3761)).
- Forum: "What makes fastai unstable in M1 Mac?" (2022-10-21). The kernel dies in ImageDataLoaders "despite reducing batch size or image size" ([thread](https://forums.fast.ai/t/what-makes-fastai-unstable-in-m1-mac/101386)). These threads date from the PyTorch 1.12-1.13 era, so treat their fixes as stale.
- PyTorch docs: "tensors with double-precision types cannot be allocated or copied to MPS", so `PYTORCH_ENABLE_MPS_FALLBACK=1` does not apply to them ([PyTorch MPS notes](https://github.com/pytorch/pytorch/blob/main/docs/source/notes/mps.md)).

## 9. Answer.AI and solveit (since 2024)

| Date | Item | Author (meta tag) | Source |
|---|---|---|---|
| 2024-11-07 | "Introducing solveit" (platform for "Dialog Engineering") | Jeremy Howard | [post](https://fast.ai/posts/2024-11-07-solveit.html) |
| late 2024 | Trial course "How To Solve It With Code": about 1,000 students, signups closed after one day | Johno Whitaker (launch post) | [launch post](https://www.answer.ai/posts/2025-10-01-solveit-full.html) |
| 2025-10-02 (page text; URL says 10-01) | Launch of the five-week course: "From October 20th for five weeks" | Johno Whitaker | [launch post](https://www.answer.ai/posts/2025-10-01-solveit-full.html) |
| 2025-10-15 | Jeremy's email: "a brand new version is ready to go now" | Jeremy Howard | [post](https://www.fast.ai/posts/2025-10-15-solveit2.html) |
| 2025-11-07 | Solveit features post | Solveit and Kerem Turgutlu | [post](https://www.fast.ai/posts/2025-11-07-solveit-features.html) |
| 2026-08-18 | "returning to AI" essay on Pólya and SolveIt design | Rachel Thomas | [post](https://www.fast.ai/posts/2026-08-18-returning-to-AI/index.html) |

Format and price (solve.it.com, undated snapshot read 2026-10-17):
- "Across 10 lessons, which you can watch at your own pace" and "5 week course" ([solve.it.com](https://solve.it.com/)).
- "The course fee includes access to the Solveit platform (with no quotas) for 30 days. After this, you will be able to subscribe for $10/month." ([solve.it.com](https://solve.it.com/))
- "The cost is $500." ([solve.it.com](https://solve.it.com/))
- "Signups are currently closed." ([solve.it.com](https://solve.it.com/))
- solveit.fast.ai and newsi.fast.ai did not connect from my environment (HTTP 000). Their claimed 2026 status is [unverified].
- The 2025 launch post names no price.

Method and quotes:
- Jeremy, 2024: "It's the first tool specifically designed for Dialog Engineering, embedding AI deeply into the development process." ([2024 post](https://fast.ai/posts/2024-11-07-solveit.html))
- Jeremy, 2024: "Yet something interesting happens when people start using AI for coding. At first, it feels magical ... You can create an app in 15 minutes that would have taken weeks before. But then reality hits: you need to make changes, add features, fix bugs." ([2024 post](https://fast.ai/posts/2024-11-07-solveit.html))
- Jeremy, 2025: "I've been using this approach for the last couple of years and it's changed my life very much for the better." ([2025-10-15 post](https://www.fast.ai/posts/2025-10-15-solveit2.html))
- Jeremy, 2025: "It's designed mainly for experienced coders, AI practitioners, and data scientists" ([2025-10-15 post](https://www.fast.ai/posts/2025-10-15-solveit2.html)).
- Jeremy, 2025: "I call it the 'solveit method'. It's designed to help you, as a person, harness AI to help you grow and learn in a way you can sustain over months and years." ([2025-10-15 post](https://www.fast.ai/posts/2025-10-15-solveit2.html))
- Johno Whitaker, 2025 launch: "The course shows how to use AI in small doses to help learn as you build, but doesn't rely on AI." Also: "In 'Learning' mode especially, the AI will gently guide you to writing small steps rather than providing a big chunk of code, unless you really specifically ask it to do so." ([launch post](https://www.answer.ai/posts/2025-10-01-solveit-full.html))
- Course site: "Don't outsource your thinking to AI. Instead, use AI to become a better problem solver, clearer thinker, and more elegant coder." ([solve.it.com](https://solve.it.com/))
- Rachel Thomas, 2026 (not Jeremy): "When chatbots rush from your initial request to a finished answer, you skip the work through which you come to deeply understand the problem." ([2026 essay](https://www.fast.ai/posts/2026-08-18-returning-to-AI/index.html))
- No 2025-2026 Part 1 refresh or new fast.ai course appears on the post index besides solveit ([fast.ai index](https://www.fast.ai/)).

## 10. What deep learning can do (chapter 1) and 1-hour feasibility

- Chapter 1 application list (condensed): NLP (answering questions, speech recognition, summarizing and classifying documents); computer vision (satellite imagery, face recognition, captioning, traffic signs, pedestrians); medicine (CT, MRI, and X-ray anomalies; diabetic retinopathy); biology (protein folding, genomics, cell classification); image generation (colorizing, super-resolution, denoising, art style); recommendation systems (web search, product recommendations); games (chess, Go, most Atari games); other (forecasting, text to speech). ([ch 1](https://github.com/fastai/fastbook/blob/master/01_intro.ipynb))

Feasibility on this M4 Pro in about 1 hour. Timing is my estimate. No source gives run times for these notebooks.

| Application | Book dataset (size) | About 1 hour on Mac | Free Kaggle GPU |
|---|---|---|---|
| Digit classifier | MNIST_SAMPLE (3.2 MB) | Yes | Yes |
| Pet breeds (transfer learning) | PETS (812 MB) | Download plus a few epochs at small size | Yes |
| Tabular income model | ADULT_SAMPLE (1.0 MB) | Yes | Yes |
| Recommender | ML-100k (4.9 MB) | Yes | Yes |
| Sentiment (NLP) | IMDB (144 MB) | Use a subset; full fine-tune is borderline | Yes |
| Super-resolution | Tiny ImageNet | Borderline | Yes |
| Tiny diffusion | Fashion-MNIST | Tiny model only | Yes |
| Medicine, proteins, games, speech | not in these labs | No | Not in scope |

## 11. Setup facts for this Mac

- Local interpreter: `/opt/homebrew/bin/python3` is Python 3.14.3. Chip: Apple M4 Pro (arm64). macOS 26.5.1 (local probe).
- Kaggle docs (read 2026-10-17 through a reader proxy): "12 hours execution time for CPU and GPU notebook sessions". "You can add a single NVIDIA Tesla P100 to your Notebook for free." The weekly GPU quota is not in the docs ([Kaggle docs](https://www.kaggle.com/docs/notebooks)).
- `duckduckgo_search` (8.1.1, 2025-07-06) says: "This package (`duckduckgo_search`) has been renamed to `ddgs`! Use `pip install ddgs` instead." ([PyPI duckduckgo_search](https://pypi.org/pypi/duckduckgo_search/json)). ddgs 9.16.0 was uploaded 2026-08-26 ([PyPI ddgs](https://pypi.org/pypi/ddgs/json)).
- SerpAPI free plan: 250 searches per month (pricing page read 2026-10-17) ([SerpAPI](https://serpapi.com/pricing)).
- Microsoft: "Bing Search APIs will be retired on August 11, 2025." ([Microsoft Learn](https://learn.microsoft.com/en-us/lifecycle/announcements/bing-search-api-retirement))

## 12. Staleness flags

- Before 2024: 2016 teaching post ([link](https://www.fast.ai/posts/2016-10-08-teaching-philosophy.html)); 2019 study group guide ([link](https://forums.fast.ai/t/fastai-study-group-guide/42616)); 2020 ethics lesson ([link](https://course.fast.ai/Lessons/lesson8a.html)); 2022 Part 1 notebooks; 2022 MPS threads and issues; course22p2 (last commit 2023-05-04).
- 2024: course22 last push 2024-10-08 ([API](https://api.github.com/repos/fastai/course22)).
- Undated: solve.it.com price and status snapshot ([solve.it.com](https://solve.it.com/)).

## 13. Lab ideas from this topic

Nine one-hour labs. Speed numbers in each outcome are for the learner to measure. No source gives them.

1. Pixel similarity vs a learned linear model. Concept: baseline, loss, gradient step (Part 1 L3-5; fastbook ch4). Dataset: MNIST_SAMPLE (3.2 MB). Outcome: accuracy of the baseline vs after 1, 5, and 20 SGD steps, a loss curve, and seconds per epoch on CPU vs MPS.
2. Titanic from scratch. Concept: linear model, then one hidden layer (Part 1 L5; course22 05). Dataset: Kaggle Titanic train.csv and test.csv. Outcome: validation accuracy for each model, and the train-validation gap.
3. Decision tree and random forest by hand. Concept: splits, gini, ensembles (Part 1 L6; course22 07). Dataset: ADULT_SAMPLE (1.0 MB). Outcome: validation accuracy at 1, 10, and 100 trees, and tree depth vs accuracy.
4. Embedding recommender. Concept: embeddings, bias terms, weight decay (Part 1 L7; fastbook ch8). Dataset: ML-100k (4.9 MB). Outcome: RMSE for a mean baseline, a dot product, and a dot product with biases. Report which wins.
5. Convolutions by hand, then a CNN. Concept: kernels and feature maps (Part 1 L8; fastbook ch13). Dataset: MNIST_SAMPLE. Outcome: a hand-computed 3x3 edge output that matches code, and CNN vs MLP accuracy after one epoch.
6. Backprop by hand. Concept: chain rule (Part 2 L13-14; course22p2 03_backprop). Dataset: synthetic, no download. Outcome: finite-difference gradient check agrees with the analytic gradient, and the loss falls.
7. Initialization and activation statistics. Concept: why init matters (Part 2 L17; course22p2 10 and 11). Dataset: Fashion-MNIST or synthetic. Outcome: standard deviation of activations per layer after 10 layers, with naive vs scaled init.
8. Device and serving benchmark. Concept: MPS vs CPU vs Kaggle GPU, plus inference latency (Part 1 L2; fastbook ch2 without the SerpAPI step). Dataset: MNIST_SAMPLE or PETS (812 MB). Outcome: seconds per epoch on each device, and p50 and p95 latency over 200 calls to the exported model.
9. Mini diffusion run. Concept: forward noising and noise prediction (Part 2 L19-21; course22p2 15_DDPM and 20_DDIM). Dataset: Fashion-MNIST. Outcome: a loss curve, a sample grid after N steps, and time per step on MPS vs Kaggle GPU.

## 14. Sources

| URL | Supports | Date or version |
|---|---|---|
| https://course.fast.ai/ | Part 1 edition, 9 lessons, 90 min, Part 2 30+ h, prerequisites, "do not train locally", skim notes | read 2026-10-17 |
| https://course.fast.ai/Lessons/lesson1.html | top-down quote, notebooks, book, Perkins, Kaggle list | read 2026-10-17 |
| https://course.fast.ai/Lessons/lesson2.html ... lesson8.html | per-lesson links: Kaggle, Colab, Spaces, fastbook chapters, spreadsheets | read 2026-10-17 |
| https://course.fast.ai/Lessons/lesson8a.html | ethics lesson, chapter 3, recorded 2020 | read 2026-10-17 |
| https://course.fast.ai/Lessons/part2.html | Part 2 overview, 30+ h, prerequisites, "from scratch", miniai | read 2026-10-17 |
| https://course.fast.ai/Lessons/lesson9.html ... lesson25.html | Part 2 summaries, study-hours quote, group study quote, linked notebooks (L9, L18, L25) | read 2026-10-17 |
| https://course.fast.ai/Lessons/Summaries/lesson1.html ... lesson8.html | community summaries for Part 1 topics | read 2026-10-17 |
| https://www.youtube.com/watch?v=8SF_h3xF3cE (and the other IDs in sections 2-3) | lengthSeconds, publishDate, title | read 2026-10-17 |
| https://www.fast.ai/posts/2022-07-21-dl-coders-22.html | 2022 launch, 9 lessons, 90 min, by Jeremy Howard | 2022-07-21 |
| https://www.fast.ai/posts/2016-10-08-teaching-philosophy.html | whole game, Perkins elementitis, spaced repetition; by Rachel Thomas | 2016-10-08 (stale) |
| https://github.com/fastai/course22 and https://api.github.com/repos/fastai/course22 | 2022 edition, notebook root, last push | pushed 2024-10-08 |
| https://github.com/fastai/course22p2 and https://github.com/fastai/course22p2/tree/master/nbs | Part 2 notebooks, miniai, Apache-2.0 | last commit 2023-05-04 |
| https://github.com/fastai/course22/blob/master/00-is-it-a-bird-creating-a-model-from-your-own-data.ipynb | DDGS image search code | 2022 (stale) |
| https://github.com/fastai/course22/blob/master/05-linear-model-and-neural-net-from-scratch.ipynb | Titanic train and test files | 2022 (stale) |
| https://github.com/fastai/course22/blob/master/08-first-steps-road-to-the-top-part-1.ipynb | Paddy Doctor competition files | 2022 (stale) |
| https://github.com/fastai/course22/blob/master/10-scaling-up-road-to-the-top-part-3.ipynb | Paddy Doctor competition files | 2022 (stale) |
| https://github.com/fastai/course22/blob/master/02-saving-a-basic-fastai-model.ipynb | URLs.PETS | 2022 (stale) |
| https://github.com/fastai/fastbook | README: license, 2020 copyright, free online chapters | pushed 2026-10-12 |
| https://github.com/fastai/fastbook/commits/master | SerpAPI commits for chapter 2 (2026-09-13, 2026-10-12) | 2026-10-12 |
| https://github.com/fastai/fastbook/blob/master/01_intro.ipynb | chapter 1 application list, datasets, questionnaire | master, read 2026-10-17 |
| https://github.com/fastai/fastbook/blob/master/02_production.ipynb | Bing retired, SerpAPI, 250 free searches per month | master, read 2026-10-17 |
| https://github.com/fastai/fastbook/blob/master/utils.py | search helpers (SerpAPI, Bing, DuckDuckGo) | master, read 2026-10-17 |
| https://github.com/fastai/fastai/blob/main/fastai/data/external.py | dataset URL registry | main, read 2026-10-17 |
| https://github.com/fastai/fastai/blob/main/fastai/torch_core.py | _has_mps, default_device, use_cuda | main, read 2026-10-17 |
| https://github.com/fastai/fastai/blob/main/fastai/data/core.py | default_device calls in DataLoaders | main, read 2026-10-17 |
| https://github.com/fastai/fastai/blob/main/pyproject.toml | requires-python >=3.10 | main, read 2026-10-17 |
| https://github.com/fastai/fastai/blob/main/.github/workflows/main.yml | CI Python matrix 3.11-3.13 | main, read 2026-10-17 |
| https://github.com/fastai/fastai/blob/main/README.md | pip install fastai | main, read 2026-10-17 |
| https://pypi.org/pypi/fastai/json | version 2.8.12, release list, requires_dist | 2026-09-09 |
| https://api.github.com/repos/fastai/fastai/releases | release list; 2.7.6 MPS note | 2026-09-09; 2022-07-07 |
| https://api.github.com/repos/fastai/fastai/commits | commit counts 2025 and 2026 | latest 2026-09-21 |
| https://github.com/fastai/fastai/pull/3858 | MPS detection PR | merged 2023-01-16 |
| https://github.com/fastai/fastai/pull/4134 | open PR on default device | opened 2025-11-24 |
| https://github.com/fastai/fastai/issues/3769 | revert auto-enable of MPS | closed 2022-08-07 |
| https://github.com/fastai/fastai/issues/3742, 3911, 3913, 3924, 3952 | open MPS issues | 2022-07-20 to 2023-09-01 |
| https://github.com/fastai/fastai/issues/3761 | missing MPS op (closed) | 2022-08-01 |
| https://forums.fast.ai/t/what-makes-fastai-unstable-in-m1-mac/101386 | M1 kernel dies | 2022-10-21 (stale) |
| https://forums.fast.ai/t/fastai-study-group-guide/42616 | study group guide; 8 hours per week | v1 2019-04-01 (stale) |
| https://forums.fast.ai/t/deep-learners-study-group-for-fastai-course-parts-1-and-2/107763 | Discord group, free format | 2023-08-20 |
| https://forums.fast.ai/t/share-your-work-here/96015 | share-your-work thread | linked from home, read 2026-10-17 |
| https://github.com/pytorch/pytorch/blob/main/docs/source/notes/mps.md | float64 not on MPS; fallback limits | main, read 2026-10-17 |
| https://fast.ai/posts/2024-11-07-solveit.html | solveit introduction, Dialog Engineering, by Jeremy Howard | 2024-11-07 |
| https://www.answer.ai/posts/2025-10-01-solveit-full.html | launch; October 20 start; five weeks; by Johno Whitaker | page text 2025-10-02 |
| https://www.fast.ai/posts/2025-10-15-solveit2.html | Jeremy email; audience; "changed my life" | 2025-10-15 |
| https://www.fast.ai/posts/2025-11-07-solveit-features.html | features update | 2025-11-07 |
| https://www.fast.ai/posts/2026-08-18-returning-to-AI/index.html | Pólya stages; chatbots skip thinking; by Rachel Thomas | 2026-08-18 |
| https://solve.it.com/ | 10 lessons, 5 weeks, $500, $10/month, signups closed | undated snapshot, read 2026-10-17 |
| https://www.fast.ai/ and https://www.answer.ai/ | post indexes used for the refresh check | read 2026-10-17 |
| https://learn.microsoft.com/en-us/lifecycle/announcements/bing-search-api-retirement | Bing Search APIs retired August 11, 2025 | read 2026-10-17 |
| https://serpapi.com/pricing | free plan 250 searches per month | read 2026-10-17 |
| https://www.kaggle.com/docs/notebooks | 12-hour sessions; single P100; no weekly quota stated | read 2026-10-17 (via reader) |
| Kaggle pages: is-it-a-bird, getting-started-with-nlp, linear-model-and-neural-net-from-scratch, first-steps-road-to-the-top-part-1, and the paddy, titanic, us-patent competitions | notebooks and competitions exist (HTTP 200) | read 2026-10-17 |
| https://pypi.org/pypi/duckduckgo_search/json and https://pypi.org/pypi/ddgs/json | renamed to ddgs; versions and dates | 8.1.1 (2025-07-06); 9.16.0 (2026-08-26) |
| https://pypi.org/pypi/torch/json | torch 2.14.1 wheels, sizes, upload date | 2026-09-30 |
| https://fastai.github.io/fastbook2e/ | free online chapters (named in README) | not opened [unverified] |

## 15. Conflicts and open questions

- Lesson count: the home page says "9 lessons"; the nav lists 8 numbered lessons plus a bonus. I count 9 videos in total.
- Lesson length: the home page says "around 90 minutes". Measured lessons 1-8 run from 76.7 to 106.7 min.
- solveit launch date: the answer.ai URL says 2025-10-01; the page text says October 2, 2025.
- solveit price and status: the $500 fee is undated. The 2025 launch post names no price. Signups read as closed. The 2026 cohort dates are unknown. solveit.fast.ai and newsi.fast.ai did not connect from here.
- Python 3.14: pip resolves wheels, and a one-epoch run trained on MPS on this Mac (section 7). CI tests only 3.11 to 3.13. Python 3.14 also printed a torch FutureWarning about `torch.jit.script`.
- MPS default: the code picks MPS automatically. Open PR #4134 proposes "use the torch way of setting default device". My single run on this Mac did train on MPS, but no 2025-2026 issue confirms or denies that for other models.
- DuckDuckGo: course22 notebook 00 installs `duckduckgo_search`, which PyPI says was renamed to `ddgs`. I did not run the notebook, so it is untested.
- Notebook compatibility: none of the 2022 notebooks was run against fastai 2.8.12. Compatibility is unverified.
- Kaggle GPU quota: the docs give a 12-hour session cap and no weekly figure. Secondary write-ups disagree about a 30-hour weekly figure, so this stays open.
- Part 2 notebook mapping is by topic, except where a lesson page links the file (lessons 9, 18, 25).
- The exact phrase "watch, run the notebook, rebuild it, share or blog it" is not on any page I read.
- Hours per lesson: no official figure was found. The only numbers are 90 minutes of video and a 2019 guide's 8 hours per week.
- Keynote: a 2026 fast.ai essay lists "Growing on Purpose" by Jeremy Howard at the 2026 AI Engineer Conference. I could not find the talk [unverified].
- fastbook second edition: the README mentions a web version (fastai.github.io/fastbook2e). I did not open it [unverified].
- Part 2 loading sources for Fashion-MNIST, Tiny ImageNet, LSUN, and CIFAR-10 are unchecked [unverified].
