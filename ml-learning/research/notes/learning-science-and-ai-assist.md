# Learning science and AI assistance for 1-hour ML lab sessions

- Research date: 17 Oct 2026. Sources were fetched or seen on that date. Study dates are the publication dates I could confirm.
- Scope: a 1-hour hands-on ML lab for a Staff engineer who is strong in Python and distributed systems, new to ML, and who lets an AI assistant write most of the code.
- Method: more than 80 tool calls, including searches, page fetches, PDF downloads and checks. PDFs were read with pdftotext, and web pages with curl and tag stripping. Blocked publisher pages (PNAS, SAGE, Springer, ACM, MDPI) were replaced by PubMed Central, arXiv, author PDFs or search summaries, and those claims are tagged.
- Tags: [measured] = I read the paper, PDF or official page. [secondary] = from a search summary or third-party page I did not open. [unverified] = I could not confirm it; do not rely on it. (my arithmetic) = I recomputed the number from the source's own figures. arXiv IDs give the submission month from the prefix (2601 = January 2026).

## Key question 1: Learning-science findings

### Takeaway

Retrieval practice, spacing, prediction before feedback, and self-explanation have the best support for a lab that runs code and explains results. Worked examples help novices and should fade as skill grows. Interleaving helps on average, but less for maths tasks. Productive failure has conflicting effect sizes, so use it only as an optional move.

### Cited Findings

Retrieval practice and the testing effect

- Roediger and Karpicke (2006), Psychological Science 17(3), 249-255. [measured, PDF mirror] Experiment 1 had 120 undergraduates. After 5 minutes, restudy beat testing (81% vs 75%, t(39) = 3.22, d = 0.52). After 2 days, testing beat restudy (68% vs 54%, t(39) = 6.97, d = 0.95). After 1 week, testing beat restudy (56% vs 42%, t(39) = 6.41, d = 0.83). The d values are as printed. I did not recompute them, because the extracted text lacks the design details. Source: https://www.gwern.net/docs/spaced-repetition/2006-roediger.pdf (third-party mirror). Canonical record: https://www.jstor.org/stable/40064526
- (my arithmetic) Testing led by 14 points at 2 days and 14 points at 1 week. Restudy led by 6 points at 5 minutes.
- Dunlosky et al. (2013), Psychological Science in the Public Interest 14(1), 4-58. [measured, APS summary] The APS page says taking practice tests and spreading study sessions out over time "were found to be of high utility". It says underlining, rereading and mnemonic devices were of "surprisingly low utility", and that the authors used "high, medium, or low" ratings. I did not open the full review, because SAGE blocked the fetch. Source: https://www.psychologicalscience.org/publications/journals/pspi/learning-techniques.html (undated page, fetched 17 Oct 2026)
- Adesope, Trevisan and Sundararajan (2017), Review of Educational Research 87(3), 659-701. [unverified] I could not open the paper. A study-app blog reports g = 0.61 from 272 effect sizes. I did not verify that number, and I do not cite the blog. DOI: https://doi.org/10.3102/0034654316689306
- Richland, Kornell and Kao (2009), Journal of Experimental Psychology: Applied 15(3), 243-257. [measured] This is the pretesting effect. Experiment 1: tested items 75% (SE 3.2) vs extra study 56% (SE 2.7), t(61) = 4.26, p < .0001, d = 1.1 as reported. (my arithmetic) The printed SEs give a rough t of about 4.5 for the 19-point gap. The paper uses a pooled test, so a small difference is expected. Source: https://learninglab.uchicago.edu/Pre-Testing_files/RichlandKornellKao.pdf

Spacing

- Cepeda, Pashler, Vul, Wixted and Rohrer (2006), Psychological Bulletin 132(3), 354-380. [measured, abstract] "This review found 839 assessments of distributed practice in 317 experiments located in 184 articles", with 169 effect sizes. I did not extract a pooled effect size. Source: https://www.evullab.org/pdf/CepedaPashlerVulWixtedRohrer-PB-2006.pdf
- Cepeda, Vul, Rohrer, Wixted and Pashler (2008), Psychological Science 19(11), 1095-1102. [measured, abstract] The optimal gap "declined from about 20 to 40% of a 1-week test delay to about 5 to 10% of a 1-year test delay." The study had 1,354 new subjects. As printed in the text, the optimal gap beat a zero-day gap by 10%, 59%, 111% and 77% at retention intervals of 7, 35, 70 and 350 days. Source: https://www.evullab.org/pdf/CepedaVulRohrerWixtedPashler-PS-2008.pdf
- (my arithmetic) For a 1-week test delay, a 20 to 40% gap is 1.4 to 2.8 days. For a 1-year delay, a 5 to 10% gap is 18 to 37 days.

Interleaving

- Brunmair and Richter (2019), Psychological Bulletin. [measured, author manuscript] Search lists the published version as 145(11), 1029-1052. I did not check its numbers. Abstract: 59 studies, 238 effect sizes, 158 samples. "A multilevel meta-analysis revealed a moderate overall interleaving effect (Hedges' g = 0.42)." For mathematical tasks: "a small interleaving effect (g = 0.34)." For painting materials: g = 0.67. Source: https://www.psychologie.uni-wuerzburg.de/fileadmin/06020400/2019/Brunmair_Richter_in_press__2019_META-ANALYSIS_OF_INTERLEAVED_LEARNING.pdf

Desirable difficulties

- Bjork and Linn (2006), APS Observer, March 2006, vol 19 no 3. [measured] Such "desirable difficulties" (Bjork, 1994) "include: spacing rather than massing study sessions; interleaving rather than blocking practice on separate topics; varying how to-be-learned material is presented; reducing feedback; and using tests as learning events." Source: https://sites.lifesci.ucla.edu/psych-bjorklab/wp-content/uploads/sites/13/2016/07/RBjork_Linn_2006.pdf (the 1994 chapter was not found)

Worked examples and the expertise reversal effect

- Sweller and Cooper (1985), Cognition and Instruction 2(1), 59-89. [unverified] I did not open the paper. Search metadata only. I have no verified effect size.
- Barbieri and colleagues (2023), Educational Psychology Review, DOI 10.1007/s10648-023-09745-1. [secondary] A search summary reports g = 0.48 (p = 0.01) from 181 effect sizes in 55 studies. Moderators: example type, self-explanation prompts, and timing. The publisher page was blocked. DOI: https://doi.org/10.1007/s10648-023-09745-1
- Kalyuga (2007), Educational Psychology Review 19, 509-539. [measured, abstract] "This line of research has become known as the expertise reversal effect." Source: https://www.uky.edu/~gmswan3/EDC608/Kalyuga2007_Article_ExpertiseReversalEffectAndItsI.pdf. The 2003 original (Educational Psychologist 38(1), 23-31) has search metadata only: https://ro.uow.edu.au/edupapers/136

Generation effect

- Bertsch, Pesta, Wiscott and McDaniel (2007), Memory & Cognition 35(2), 201-210. [unverified] The PubMed page did not return abstract text to my fetch. A search summary reports 445 effect sizes from 86 studies, with a generation advantage of about 0.4 SD. Location: https://pubmed.ncbi.nlm.nih.gov/17645161/

Self-explanation

- Bisra et al. (2018), Educational Psychology Review, DOI 10.1007/s10648-018-9434-x. [measured, PDF mirror] Abstract: 69 effect sizes from 64 research reports. Results, Table 1: "a random effects analysis of 69 effect sizes (5917 participants) obtained an overall point estimate of g = .55 with a 95% confidence interval ranging from .45 to .65." Heterogeneity: Q = 196.63 (df = 68). Source: https://www.Gwern.net/doc/psychology/spaced-repetition/2018-bisra.pdf (third-party mirror)
- Chi, Bassok, Lewis, Reimann and Glaser (1989), Cognitive Science 13(2), 145-182 (some sources give 145-183). [secondary] This is the original self-explanation study. Search summaries say stronger learners generated more explanations for worked examples. I did not verify the text. Metadata: https://serc.carleton.edu/resources/19512.html

Productive failure and prediction

- Sinha and Kapur (2021), Review of Educational Research 91(5), 761-798, DOI 10.3102/00346543211019105. [unverified, conflicting] The publisher page returned 403. Search summaries say 53 studies with 166 comparative analyses. The effect sizes conflict (see Conflicts). DOI: https://doi.org/10.3102/00346543211019105
- Kapur (2008), Cognition and Instruction 26(3), 379-424. [metadata only] DOI: https://doi.org/10.1080/07370000802212669
- Predict-observe-explain (POE): I found no primary study with a verified effect size. The nearest measured evidence is the pretesting effect above. [gap]

### Inferences

- For a lab that runs code and explains results, the best-supported moves are: test yourself before you look, revisit across days, predict before feedback, and explain in your own words.
- Interleave experiments that look alike but differ in one choice, such as two metrics on the same split. The maths effect was small (g = 0.34), so do not mix unrelated topics just for variety. (my inference)
- The desirable-difficulties list maps onto lab mechanics. Do not show the answer the moment you guess. Show it after you write a prediction.
- Expertise reversal applies in a specific way. Strong general programming does not supply ML schemas. Expect worked examples to help for new ML procedures, then fade them. (my inference from Kalyuga 2007; not tested for this learner)

### Gaps

- No verified effect size for predict-observe-explain or for "break it" labs.
- Sinha and Kapur (2021) effect size is unresolved. Adesope (2017), Barbieri (2023) and Bertsch (2007) are unverified.
- No primary study I opened tests a 60-minute ML lab. I did not check fade-out studies in adult professionals.

## Key question 2: Evidence on AI assistance and learning

### Takeaway

AI assistance can raise output and still hurt learning when the learner hands over the thinking. The studies that protected learning used AI for hints, explanations or conceptual questions. Most measured learning is immediate or within a week. I found no study that measured ML learning over months.

### Cited Findings

Anthropic, randomized controlled trial (Shen and Tamkin). Blog 29 Jan 2026; arXiv 2601.20245 v2, dated 3 Feb 2026. [measured]

- Design: 52 mostly junior engineers. Each had used Python at least weekly for over a year. The new library was Trio (async). Randomly split: 26 AI, 26 hand-coding. Main task limit: 35 minutes. Quiz right after. The AI sidebar "could at any time produce the correct code if asked" (blog). Sources: https://www.anthropic.com/research/AI-assistance-coding-skills and https://arxiv.org/pdf/2601.20245
- Result: AI group quiz mean 50%; hand-coding group 67%. "Cohen's d = 0.738, p = 0.010" (Section 5.2.2, Results). With warm-up time as a covariate: d = 0.725, p = 0.016 (same section).
- Speed: the AI group was about 2 minutes faster on average, not significant (task time p = 0.391, Figure 6). Largest gap: debugging questions (blog). The quiz covered debugging, code reading and conceptual items (evaluation design).
- Interaction patterns (Section 6, Figure 11). Low scoring (quiz under 40%): AI delegation (n = 4), progressive AI reliance (n = 4), iterative AI debugging (n = 4). High scoring (65% or more): generation-then-comprehension (n = 2), hybrid code-explanation (n = 3), conceptual inquiry (n = 7). (my arithmetic) The six cluster sizes add to 24 of the 26 AI-group participants. Figure 1 labels show 24% to 39% for the low-scoring clusters and 65% to 86% for the high-scoring ones. I give ranges only, because the text does not map each percentage to a cluster.
- Authors' caveats (blog): "Our sample was relatively small." The quiz came shortly after the task. "Whether immediate quiz performance predicts longer-term skill development is an important question this study does not resolve." The qualitative analysis "does not draw a causal link between interaction patterns and learning outcomes."
- Footnote: the setup "is different from agentic coding products like Claude Code", and the authors expect larger effects for such tools. Source: https://www.anthropic.com/research/AI-assistance-coding-skills
- Measured: quiz scores, completion time, annotated screen recordings. Claimed: the general lesson that "AI-enhanced productivity is not a shortcut to competence" (abstract framing).

Bastani et al., PNAS (2025). Field RCT in a Turkish high school. [measured]

- Published 25 June 2025 (per the correction notice). The 20 Aug 2025 correction fixed one affiliation only. Sources: https://pmc.ncbi.nlm.nih.gov/articles/PMC12232635/ and https://pmc.ncbi.nlm.nih.gov/articles/PMC12403119/
- Design: about 1,000 students in about 50 classes, fall 2023 to 2024, four 90-minute sessions. Arms: control (textbooks), GPT Base (GPT-4 chat), GPT Tutor (teacher-designed hints, with the solution in the prompt).
- Exam: closed-book and closed-laptop. Each exam problem was "conceptually very similar" to a practice problem (Experimental Design). So this tests near transfer.
- Practice (Main Results, Table 1): GPT Base +0.137 on a 0-to-1 scale (48%). GPT Tutor +0.361 (127%). Control mean 0.28.
- Exam: GPT Base -0.054 on the 0-to-1 scale, which the paper states as 17% lower than control. GPT Tutor -0.004, not significant. The paper reports no positive exam effect for GPT Tutor either.
- Self-reports: students in the GPT Base arm did not perceive that they learned less. The authors call this self-perception "overly optimistic" (Discussion).
- Abstract: "asking the AI tutor to provide teacher-designed hints instead of giving away answers, can mitigate these negative effects."
- (my arithmetic) 0.137 / 0.28 = 49% and 0.361 / 0.28 = 129%. The paper's 48% and 127% imply a control mean near 0.285. If 0.054 is 17% of the control exam mean, that mean is about 0.32.

Kosmyna et al., MIT Media Lab, arXiv 2506.08872 (June 2025 by ID). [measured, preprint]

- The PDF is marked "Preprint, under review." Three groups: LLM, search engine, brain-only. Abstract: "This study focuses on finding out the cognitive cost of using an LLM in the educational context of writing an essay." "We recruited a total of 54 participants for Sessions 1, 2, 3, and 18 participants among them completed session 4."
- Measures: EEG, NLP analysis, interviews after each session, and scoring by teachers and an AI judge.
- "Cognitive debt" is the authors' interpretation of EEG and essay results. The sample is small (18 per arm), and the task was essay writing, not coding. Source: https://arxiv.org/pdf/2506.08872

Lee and colleagues, CHI 2025 ("The Impact of Generative AI on Critical Thinking"). [secondary; ACM PDF blocked]

- 319 knowledge workers, 936 first-hand examples of AI use at work. Self-reported. Greater trust in GenAI went with less critical thinking. Greater self-confidence went with more. The authors describe a shift toward checking, merging and overseeing AI output. This is a self-report survey, not a learning test.
- Sources: DOI https://doi.org/10.1145/3706598.3713778 (not opened). Microsoft Research listing https://www.microsoft.com/en-us/research/?p=1135061 (not opened for the abstract). Trade coverage (21 Feb 2025): https://campustechnology.com/articles/2025/02/21/study-generative-ai-could-inhibit-critical-thinking.aspx

Fan et al., arXiv 2412.09315 (December 2024 by ID). [measured, preprint]

- 117 university students in four support conditions: ChatGPT, human expert, writing-analytics tools, and none.
- Abstract: the ChatGPT group "outperformed in the essay score improvement but their knowledge gain and transfer were not significantly different."
- The authors define "metacognitive laziness" as dependence on AI and offloading of metacognitive load. Source: https://arxiv.org/pdf/2412.09315. A blog lists a journal version, which I did not verify.

Kazemitabaar et al., CHI 2023 (23-28 April 2023), arXiv 2302.07427. [measured]

- 69 learners aged 10 to 17 (M = 12.5). 45 Python code-authoring tasks. Half had Codex.
- Code authoring: 1.15x progress, 0.59x errors, 1.8x correctness, 0.57x time. No drop on manual code modification. The immediate post-test showed the Codex group performing similarly to baseline without AI. One-week retention was slightly better for Codex, not significant.
- "learners with higher Scratch pre-test scores performed significantly better on retention post-tests, if they had prior access to Codex." (Abstract)
- These are children, not adult professionals. Source: https://arxiv.org/pdf/2302.07427

Peng et al., arXiv 2302.06590 (February 2023 by ID). [measured; productivity, not learning]

- 95 professional developers wrote an HTTP server in JavaScript. The treated group "completed the task 55.8% faster (95% confidence interval: 21-89%)". t-test p = 0.0017. Source: https://arxiv.org/pdf/2302.06590

Prather et al., ICER 2024, arXiv 2405.17739 (May 2024 by ID). [measured abstract only]

- Abstract: novices "often struggle through programming problem solving due to a lack of metacognitive awareness and strategies." Accepted to ICER 2024. Search summaries mention lab sessions with eye tracking; I did not verify this. Source: https://arxiv.org/abs/2405.17739

METR, randomized controlled trial of 16 experienced open-source developers. Blog 10 Jul 2025; arXiv 2507.09089 v2, 25 Jul 2025. [measured]

- 246 real issues from the developers' own repositories. The blog calls the study a randomized controlled trial comparing AI-allowed and AI-barred work.
- Core result: developers "take 19% longer" when AI is allowed. They expected a 24% speedup and still believed in a 20% speedup afterward. Sources: https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/ and https://arxiv.org/pdf/2507.09089
- METR's FAQ asks: "You only had 16 developers, so these results will not generalize/replicate." It also says: "we can't rule out learning effects beyond 50 hours of Cursor usage."
- (my arithmetic) "19% longer" to finish is about 16% less speed (1 / 1.19 minus 1). That points the opposite way to the believed +20%. This is a productivity result, not a learning result. I include it for the perception gap.

Heilman, Kyllo and Murphy-Hill (Microsoft), arXiv 2606.00438, submitted 30 May 2026. [measured, observational]

- 16,223 engineers over 43 weeks. "Engineers are estimated to complete 40.5% more PRs in their highest GHCP usage weeks relative to their zero-usage weeks, holding measured development effort constant." Source: https://arxiv.org/pdf/2606.00438. A productivity estimate, not a learning test.

METR 2026 follow-ups. [secondary or unverified]

- METR's blog index, fetched 17 Oct 2026, lists 11 posts dated 17 Feb to 6 Oct 2026. None of those titles is about developer productivity. Source: https://metr.org/blog/
- Search summaries mention a February 2026 METR update and a May 2026 survey of 349 technical workers. I could not confirm either.

### Inferences

- The outcome seems to depend on how the learner uses the tool. Anthropic's high-scoring clusters and Bastani's hint-based tutor both point this way. Interaction style is the strongest signal, not whether AI was used.
- Guardrails reduced harm but did not add learning. Bastani's GPT Tutor showed no exam loss and no exam gain.
- Speed and learning can diverge. Peng and Heilman report productivity gains. Anthropic found no significant speed gain and lower quiz scores. METR found a slowdown while developers believed they were faster.
- For a Staff engineer, the highest-risk skills are debugging and code reading, which are the skills needed to supervise AI-written code. Anthropic's largest gap was there.

### Gaps

- No verified randomized trial of AI-assisted learning in ML specifically.
- Retention beyond one week is not measured in any study I verified.
- Kosmyna (preprint) and Lee (self-report) are not learning tests. Fan's journal version is not verified.

## Key question 3: Tool features (Claude Code, Claude.ai, ChatGPT, Gemini)

### Takeaway

Each vendor now has a tutor-style mode. All of them change the assistant's instructions or behaviour. None of the vendor pages I read reports a measured learning benefit. Claude Code's Learning style is the closest match to a lab, because it leaves code for you to write.

### Cited Findings

- Claude for Education and Learning mode (Anthropic, 2 Apr 2025). [official] Learning mode "guides students' reasoning process rather than providing answers". It uses "Socratic questioning", for example "What evidence supports your conclusion?" Access at launch was by an interest form. Source: https://www.anthropic.com/news/introducing-claude-for-education
- Claude.ai Learning style for all users (14 Aug 2025). [secondary] Search summaries give this date and say the Learning entry sits in the style dropdown. Source: https://alternativeto.net/news/2025/8/claude-s-learning-mode-is-now-available-to-all-users-with-new-coding-styles. I did not find an Anthropic help-center article for it.
- Claude Code output styles, built-in Explanatory and Learning. [official] The CHANGELOG entry for version 1.0.81 says "Released output styles, including new built-in educational output styles 'Explanatory' and 'Learning'." The npm publish time for 1.0.81 is 14 Aug 2025, 16:41 UTC. Sources: https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md and https://registry.npmjs.org/@anthropic-ai%2fclaude-code
- Claude Code docs (fetched 17 Oct 2026, undated page). Explanatory "adds short Insight blocks that explain the choices behind the code it writes." Learning "explains its choices and leaves small pieces of code for you to write yourself." In Learning, "Claude marks the spot with a TODO(human) comment", and then "stops and waits." Both styles "produce longer responses than Default by design, which increases output tokens." Source: https://code.claude.com/docs/en/output-styles
- ChatGPT study mode (OpenAI, 29 Jul 2025; the date string appears on the archived page). It "helps you work through problems step by step instead of just getting an answer." Features: interactive prompts (Socratic questions, hints, self-reflection), scaffolded responses, personalized support, knowledge checks, and a toggle. "Today, study mode is powered by custom system instructions." Source: https://openai.com/index/chatgpt-study-mode/
- Gemini Guided Learning (Google, 6 Aug 2025). "This new experience acts as a personal learning companion, using questions and rich responses to help you build a deep understanding of subjects." It adds images, videos and quizzes, runs on LearnLM models, and can be shared to Google Classroom. Source: https://blog.google/outreach-initiatives/education/guided-learning/
- Anthropic's 2026 paper names Claude Code Learning and Explanatory modes and ChatGPT Study Mode as "designed to foster understanding." It did not test them. Source: https://www.anthropic.com/research/AI-assistance-coding-skills (29 Jan 2026)

### Inferences

- For an ML lab, Claude Code Learning is the closest fit, because it leaves code for you to write. The other three are chat tutors.
- These modes change instructions, not the task. Treat them as scaffolds that still need your own checks. Explanatory and Learning produce longer answers, so token use per exchange is higher (docs).

### Gaps

- I found no independent evaluation of these modes.
- Claude.ai Learning availability in October 2026 is not confirmed, and coverage conflicts on how it is reached.

## Key question 4: How expert practitioners recommend learning ML hands-on

### Takeaway

Practitioners agree on building small things and learning by doing. I verified the pages of fast.ai, Karpathy and Ng, and Huyen's homepage and interview lines. I could not verify the Karpathy and Huyen tweets I looked for, so those are marked.

### Cited Findings

- fast.ai, Practical Deep Learning for Coders (course page fetched 17 Oct 2026, undated). "A free course designed for people with some coding experience, who want to learn how to apply deep learning and machine learning to practical problems." "The only prerequisite is that you know how to code." A myth-and-truth table says "Lots of math" is a myth, and "Just high school math is sufficient." Source: https://course.fast.ai/ The "top-down" wording I expected is not on this page, so I do not quote it.
- Karpathy, Neural Networks: Zero to Hero (page fetched 17 Oct 2026, undated). "A course by Andrej Karpathy on building neural networks, from scratch, in code." "In my opinion language models are an excellent place to learn deep learning." Source: https://karpathy.ai/zero-to-hero.html
- Karpathy, micrograd README (fetched 17 Oct 2026). "A tiny Autograd engine (with a bite! :)). Implements backpropagation (reverse-mode autodiff) over a dynamically built DAG and a small neural networks library on top of it with a PyTorch-like API." "Both are tiny, with about 100 and 50 lines of code respectively." Source: https://github.com/karpathy/micrograd
- Karpathy tweets on how to become an expert, or on "what I cannot create": not found. [unverified] His 2016 essay "Yes you should understand backprop" is on medium.com, which the brief excludes.
- Chip Huyen, homepage (fetched 17 Oct 2026). "I work to bring AI to production. I write about AI system design." "I graduated from Stanford, where I taught ML Systems. The lectures became the foundation for the book Designing Machine Learning Systems." Source: https://huyenchip.com/
- Chip Huyen, interview transcript on Eugene Yan's site (date not in the fetched text). "I saw teaching as a way to learn." "At Stanford, I wanted to teach because I wanted to learn the material better and improve my technical communication skills." Source: https://eugeneyan.com/writing/informal-mentors-chip-huyen. Her December 2019 tweet and W&B podcast lines are [unverified]: the tweet was not on the page the search cited, and the W&B page did not load.
- Andrew Ng, Machine Learning Yearning (draft). The deeplearning.ai page calls it a "FREE EBOOK": https://info.deeplearning.ai/machine-learning-yearning-book
- I read the draft text in a third-party GitHub copy, labelled "Machine Learning Yearning-Draft", which says "Machine Learning Yearning is a deeplearning.ai project." Parts: https://raw.githubusercontent.com/ajaymache/machine-learning-yearning/master/machine-learning-yearning-part1.pdf and https://raw.githubusercontent.com/ajaymache/machine-learning-yearning/master/machine-learning-yearning-part2.pdf The draft date is not verified.
- Ng quotes from that copy:
  - "Manually examining 100 examples does not take long. Even if you take one minute per image, you'd be done in under two hours. These two hours could save you a month of wasted effort."
  - "The process of looking at misclassified examples is called error analysis."
  - "I usually create a spreadsheet and fill it out while looking through ~100 misclassified dev set images."
  - "It often feels more exciting to jump in and implement some idea, rather than question if the idea is worth the time investment."

### Inferences

- "From scratch, in code" (Karpathy) and "inspect the errors yourself" (Ng) both match the lab idea. Rebuild a small piece, and inspect a sample of errors by hand.
- Ng's under-two-hours estimate for 100 errors gives a concrete time budget for the "break it" step. Huyen's "teaching as a way to learn" supports the explain-back step.

### Gaps

- No verified Karpathy tweet on learning. The fast.ai "top-down" wording is not on a primary page I could open.
- Huyen's tweet and podcast lines are unverified. Ng's draft date is unverified.

## Key question 5: Session mechanics, session length and breaks

### Takeaway

I found no primary study that tests the best length for a 60-minute ML lab. The spacing evidence says repeat contact across days matters more than one long session. Plan one main task in an hour, and a repeat contact within three days.

### Cited Findings

- Cepeda et al. (2008): the best gap between study sessions grows with the delay before the test. For a 1-week delay, the best gap is 20 to 40% of the delay. For a 1-year delay, it is 5 to 10%. Source: https://www.evullab.org/pdf/CepedaVulRohrerWixtedPashler-PS-2008.pdf
- Anthropic (2026): the main task had a 35-minute limit. Some participants spent "up to 11 minutes (30% of the total time allotted) composing up to 15 queries." Source: https://arxiv.org/pdf/2601.20245
- Anthropic (2026): the tasks and surveys together took at most 1 hour 15 minutes and averaged 58.5 minutes (study procedure, as extracted). Source: https://arxiv.org/pdf/2601.20245
- Ericsson, Krampe and Tesch-Romer (1993), Psychological Review 100(3), 363-406 (DOI 10.1037/0033-295x.100.3.363). [metadata only] I did not verify a claim that deliberate practice sessions last about an hour. Two 2019 papers I could open did not state a one-hour cap. Sources: https://www.frontiersin.org/articles/10.3389/fpsyg.2019.02396/pdf and https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6731745/
- Breaks during learning: I found no primary study that I could verify.

### Inferences

- A 60-minute lab fits the Anthropic time frame. Their whole study, surveys included, averaged 58.5 minutes.
- Schedule two or three short contacts with the same concept across the week, instead of one long session.

### Gaps

- Session length and break evidence for technical learning is missing from this research.

## Key question 6: Rules for using an AI assistant during a learning lab

### Takeaway

Delegate scaffolding, not judgement. Ask for hints and explanations, not answers. Check understanding closed-book and on a new case.

### Cited Findings

- Anthropic (2026): high-scoring patterns used explanations or conceptual questions. Low-scoring patterns relied on AI for code or debugging. Source: https://arxiv.org/pdf/2601.20245 (Section 6)
- Bastani et al. (2025): GPT Tutor with teacher hints had no significant exam loss. Unrestricted GPT Base had lower exam scores. Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC12232635/
- Kazemitabaar et al. (2023): AI help raised code-authoring output, with no drop on manual modification. One-week retention was not significant. Source: https://arxiv.org/pdf/2302.07427
- Fan et al. (2024): ChatGPT improved essay scores, but not knowledge gain or transfer. Source: https://arxiv.org/pdf/2412.09315

### Inferences

Delegation table (the "Why" column cites the evidence above):

| Task | Delegate? | Why |
|---|---|---|
| Imports, environment, data download | Yes | Not the learning target. (my inference) |
| Plotting boilerplate | Yes | Same reason. (my inference) |
| Core model code for the lab concept | Ask for the code and a line-by-line explanation. Then close the chat and retype from memory. | Anthropic's hybrid pattern (n = 3) and generation-then-comprehension (n = 2) scored high. Pure delegation scored under 40%. |
| Choosing the metric and the split | No | Judgement. Ng's error analysis. |
| Predicting outcomes | No | The prediction is the learning step (Richland et al. 2009). |
| Reading curves | No. Ask for a critique of your reading afterward. | Delegation patterns scored under 40% (Anthropic 2026). |
| Debugging | Ask for a hint and a question, not the fix. | Iterative AI debugging scored under 40%. Bastani's hints. |

Prompt patterns (my design suggestions, not tested):
- "Give me one hint, then ask me a question about my reasoning. Do not write code."
- "Before you answer, ask me what I predict the output will be."
- "Here is my explanation. Find the claim most likely to be wrong and ask me a question that tests it."
- "Quiz me with three closed-book questions, one at a time. Wait for my answer."
- "Explain why accuracy misleads on this data. Do not edit my code."

Understanding checks (my suggestions):
- Close-the-laptop test: write five sentences from memory, then compare them with the notebook.
- Transfer check: predict the output of a variant you have not run.
- Next-session quiz: three closed-book questions before the lab starts.
- Prediction log: track predicted against actual results. The hit rate is a rough measure of your judgement.

### Gaps

- No study I found tested these prompt patterns in ML labs, and the checks above are not validated.

## Sources

| URL | What it supports | Date | Access |
|---|---|---|---|
| https://www.anthropic.com/research/AI-assistance-coding-skills | Anthropic RCT design, quiz, patterns, caveats | 29 Jan 2026 | fetched |
| https://arxiv.org/pdf/2601.20245 | Anthropic paper: Section 5.2.2 results, d = 0.738, Figures 1, 6, 11, Section 6 | 3 Feb 2026 (v2) | pdftotext |
| https://www.anthropic.com/news/introducing-claude-for-education | Claude for Education and Learning mode | 2 Apr 2025 | fetched |
| https://alternativeto.net/news/2025/8/claude-s-learning-mode-is-now-available-to-all-users-with-new-coding-styles | Claude.ai Learning rollout (secondary) | Aug 2025 | search summary |
| https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md | Explanatory and Learning styles added in 1.0.81 | 1.0.81 | fetched |
| https://registry.npmjs.org/@anthropic-ai%2fclaude-code | npm publish time for 1.0.81 | 14 Aug 2025 | fetched |
| https://code.claude.com/docs/en/output-styles | Output style definitions and settings | undated; fetched 17 Oct 2026 | fetched |
| https://openai.com/index/chatgpt-study-mode/ | ChatGPT study mode features and system-instruction basis | 29 Jul 2025 | archived and reader copies |
| https://blog.google/outreach-initiatives/education/guided-learning/ | Gemini Guided Learning features | 6 Aug 2025 | fetched |
| https://pmc.ncbi.nlm.nih.gov/articles/PMC12232635/ | Bastani et al. PNAS full text | published 25 Jun 2025 | fetched |
| https://pmc.ncbi.nlm.nih.gov/articles/PMC12403119/ | Bastani correction (affiliation only) | 20 Aug 2025 | fetched |
| https://arxiv.org/pdf/2506.08872 | Kosmyna et al. preprint: sample, measures, caveats | June 2025 (ID) | pdftotext |
| https://arxiv.org/pdf/2507.09089 | METR arXiv paper | v2 25 Jul 2025 | pdftotext |
| https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/ | METR results, expectations and FAQ | 10 Jul 2025 | fetched |
| https://metr.org/blog/ | METR blog index with 2026 post titles | fetched 17 Oct 2026 | WebFetch summary |
| https://doi.org/10.1145/3706598.3713778 | Lee et al. CHI 2025 DOI | 2025 | not opened (ACM blocked) |
| https://www.microsoft.com/en-us/research/?p=1135061 | Lee et al. Microsoft Research listing | 2025 | not opened for abstract |
| https://campustechnology.com/articles/2025/02/21/study-generative-ai-could-inhibit-critical-thinking.aspx | Trade coverage of Lee et al. (secondary) | 21 Feb 2025 | search |
| https://arxiv.org/pdf/2412.09315 | Fan et al.: 117 students, essay vs knowledge and transfer | Dec 2024 (ID) | pdftotext |
| https://arxiv.org/abs/2405.17739 | Prather et al. abstract, ICER 2024 | May 2024 (ID) | fetched |
| https://arxiv.org/pdf/2302.07427 | Kazemitabaar et al. (CHI 2023): learners aged 10 to 17 | 23-28 Apr 2023 | pdftotext |
| https://arxiv.org/pdf/2302.06590 | Peng et al.: Copilot productivity, 95 developers | Feb 2023 (ID) | pdftotext |
| https://arxiv.org/pdf/2606.00438 | Heilman et al.: observational productivity, 2026 | 30 May 2026 | pdftotext |
| https://www.evullab.org/pdf/CepedaPashlerVulWixtedRohrer-PB-2006.pdf | Cepeda et al. 2006: 839 assessments, 317 experiments | 2006 | pdftotext |
| https://www.evullab.org/pdf/CepedaVulRohrerWixtedPashler-PS-2008.pdf | Cepeda et al. 2008: 20 to 40% gap ratio, 1,354 subjects | 2008 | pdftotext |
| https://www.gwern.net/docs/spaced-repetition/2006-roediger.pdf | Roediger and Karpicke 2006 (third-party mirror) | 2006 | pdftotext |
| https://www.jstor.org/stable/40064526 | Roediger and Karpicke canonical record | 2006 | search |
| https://learninglab.uchicago.edu/Pre-Testing_files/RichlandKornellKao.pdf | Richland, Kornell and Kao: pretesting effect | 2009 | pdftotext |
| https://www.psychologie.uni-wuerzburg.de/fileadmin/06020400/2019/Brunmair_Richter_in_press__2019_META-ANALYSIS_OF_INTERLEAVED_LEARNING.pdf | Brunmair and Richter: g = 0.42 (manuscript) | 2019 | pdftotext |
| https://www.psychologicalscience.org/publications/journals/pspi/learning-techniques.html | Dunlosky et al. 2013 utility ratings (APS summary) | 2013 | fetched |
| https://sites.lifesci.ucla.edu/psych-bjorklab/wp-content/uploads/sites/13/2016/07/RBjork_Linn_2006.pdf | Bjork and Linn: desirable difficulties list | Mar 2006 | pdftotext |
| https://www.uky.edu/~gmswan3/EDC608/Kalyuga2007_Article_ExpertiseReversalEffectAndItsI.pdf | Kalyuga 2007 review: expertise reversal | 2007 | pdftotext |
| https://ro.uow.edu.au/edupapers/136 | Kalyuga et al. 2003 metadata | 2003 | search |
| https://www.Gwern.net/doc/psychology/spaced-repetition/2018-bisra.pdf | Bisra et al.: g = .55, 69 effect sizes (mirror) | 2018 | pdftotext |
| https://serc.carleton.edu/resources/19512.html | Chi et al. 1989 metadata | 1989 | search |
| https://pubmed.ncbi.nlm.nih.gov/17645161/ | Bertsch et al. 2007 location (no abstract returned) | 2007 | not verified |
| https://doi.org/10.3102/0034654316689306 | Adesope et al. 2017 DOI | 2017 | not opened |
| https://doi.org/10.3102/00346543211019105 | Sinha and Kapur 2021 DOI | 2021 | not opened (403) |
| https://doi.org/10.1080/07370000802212669 | Kapur 2008 DOI | 2008 | metadata only |
| https://doi.org/10.1007/s10648-023-09745-1 | Barbieri et al. 2023 DOI | 2023 | not opened (redirect) |
| https://www.frontiersin.org/articles/10.3389/fpsyg.2019.02396/pdf | Ericsson and Harwell 2019: no one-hour cap found | 2019 | pdftotext |
| https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6731745/ | Macnamara and Maitra 2019 replication | 2019 | fetched |
| https://course.fast.ai/ | fast.ai course page: "only prerequisite" and math table | undated; fetched 17 Oct 2026 | fetched |
| https://karpathy.ai/zero-to-hero.html | Karpathy: "from scratch, in code" | undated; fetched 17 Oct 2026 | fetched |
| https://github.com/karpathy/micrograd | Karpathy micrograd README: about 100 lines | fetched 17 Oct 2026 | fetched |
| https://huyenchip.com/ | Huyen homepage | fetched 17 Oct 2026 | fetched |
| https://eugeneyan.com/writing/informal-mentors-chip-huyen | Huyen interview lines on teaching and learning | undated | fetched |
| https://info.deeplearning.ai/machine-learning-yearning-book | Ng: book page ("FREE EBOOK") | fetched 17 Oct 2026 | fetched |
| https://raw.githubusercontent.com/ajaymache/machine-learning-yearning/master/machine-learning-yearning-part1.pdf | Ng error analysis, third-party copy | draft; undated | pdftotext |
| https://raw.githubusercontent.com/ajaymache/machine-learning-yearning/master/machine-learning-yearning-part2.pdf | Ng: about 100 misclassified images, third-party copy | draft; undated | pdftotext |

## Conflicts and open questions

1. The "17%" in Anthropic (2026) is ambiguous. The blog says "17% lower". The paper says "17% or two grade points". The paper's own numbers give a mean difference of 4.15 points on a 27-point quiz, which is 15.4 percentage points (my arithmetic). The blog's 50% vs 67% is 17 percentage points. The relative drop is 25% (my arithmetic: 17 / 67). Read it as 15 to 17 points, not 17%. Source: https://arxiv.org/pdf/2601.20245
2. The "17%" in Bastani et al. (2025) is a relative change in exam scores, not points. It is a different metric from Anthropic's 17. Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC12232635/
3. Anthropic's cluster sizes add to 24 of 26 AI-group participants, and the text does not say where the other two went. Figure 1 percentages cannot be mapped to cluster names with confidence, so I report ranges only. Source: https://arxiv.org/pdf/2601.20245
4. Sinha and Kapur (2021) conflict across sources. A proxy copy of the article reports g = 0.87 for the problem-solving-first advantage after publication-bias adjustment. I do not cite that copy. Press reports say productive failure can reach "up to three times" a strong teacher's annual gain. Another write-up says "nearly twice". The publisher page is blocked. Unresolved. DOI: https://doi.org/10.3102/00346543211019105
5. Effect sizes for Adesope (2017), Bertsch (2007) and Barbieri (2023) are unverified, because I could not open those papers. DOIs: https://doi.org/10.3102/0034654316689306 and https://doi.org/10.1007/s10648-023-09745-1 ; PubMed location: https://pubmed.ncbi.nlm.nih.gov/17645161/
6. The Dunlosky APS page says "high, medium, or low". I did not check the review's exact labels. Source: https://www.psychologicalscience.org/publications/journals/pspi/learning-techniques.html
7. Roediger and Karpicke (2006) d values are as printed, and the t(39) values do not match a simple two-group design, so I did not reconstruct them. Richland et al. (2009) report t(61) = 4.26, against about 4.5 from the printed SEs. The paper uses a pooled test, so a gap is expected. Sources: https://www.gwern.net/docs/spaced-repetition/2006-roediger.pdf and https://learninglab.uchicago.edu/Pre-Testing_files/RichlandKornellKao.pdf
8. Kosmyna et al. (2025) is a preprint with 18 per arm. "Cognitive debt" is the authors' interpretation, and the task was essay writing, not coding. Source: https://arxiv.org/pdf/2506.08872
9. METR (2025) studied 16 developers, and its FAQ questions generalization. Learning effects beyond 50 hours of Cursor use are not ruled out. The 2026 METR follow-ups are secondary only, and the blog index I fetched shows no 2026 productivity-titled post on page 1. Sources: https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/ and https://metr.org/blog/
10. Lee et al. (CHI 2025) numbers come from search summaries. Carnegie Mellon's role comes from trade press, not the paper. DOI: https://doi.org/10.1145/3706598.3713778
11. Fan et al. is a single lab study with 117 students, and a preprint. The journal version is unverified. Source: https://arxiv.org/pdf/2412.09315
12. Kazemitabaar et al. (2023) used children aged 10 to 17 and a 2022-era Codex tool. Results may not transfer to adult professionals. Source: https://arxiv.org/pdf/2302.07427
13. Claude.ai Learning: coverage disagrees on placement (style dropdown vs mode selector). No Anthropic help-center article was verified. The 2025 Anthropic page directed people to an interest form. Source: https://www.anthropic.com/news/introducing-claude-for-education
14. The one-hour session claim in Ericsson (1993) is unverified. Source: https://www.frontiersin.org/articles/10.3389/fpsyg.2019.02396/pdf
15. Karpathy and Huyen tweets are not verified, and the fast.ai "top-down" wording is not on a primary page I opened. The Ng text I read is a third-party copy, so check deeplearning.ai for the official text and date. Sources: https://course.fast.ai/, https://huyenchip.com/, https://info.deeplearning.ai/machine-learning-yearning-book
16. The PNAS page is blocked by a bot check, so I read the PMC copy of the same article. The correction changes an affiliation only. Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC12403119/
17. Open questions: no study I found measures ML learning with AI assistance after weeks or months. Nor is there primary evidence on whether a "break it" lab beats a "build it" lab. The vendor pages I read report no measured learning results for their modes.

## Session design rules

1. Open every session with closed-book retrieval. Answer three questions from last session without notes. Evidence: testing beat restudy after 2 days (68% vs 54%, d = 0.95) and after 1 week (56% vs 42%, d = 0.83) in Roediger and Karpicke (2006). Dunlosky et al. (2013) rate practice testing "high utility". Sources: https://www.gwern.net/docs/spaced-repetition/2006-roediger.pdf and https://www.psychologicalscience.org/publications/journals/pspi/learning-techniques.html
2. Space each concept. Revisit it 1 to 3 days later, and again 1 to 2 weeks later. Evidence: Cepeda et al. (2008) found the best gap is 20 to 40% of a 1-week delay (my arithmetic: 1.4 to 2.8 days). Bjork and Linn (2006) list spacing as a desirable difficulty. Sources: https://www.evullab.org/pdf/CepedaVulRohrerWixtedPashler-PS-2008.pdf and https://sites.lifesci.ucla.edu/psych-bjorklab/wp-content/uploads/sites/13/2016/07/RBjork_Linn_2006.pdf
3. Predict, then run. Before each run, write the expected output and a 0-to-100 confidence. Evidence: pretesting in Richland et al. (2009) gave tested items 75% vs 56% with extra study (d = 1.1 as reported, Experiment 1). The generation effect (Bertsch et al. 2007) is about 0.4 SD, but unverified. Source: https://learninglab.uchicago.edu/Pre-Testing_files/RichlandKornellKao.pdf
4. Change one variable, and predict its direction and size. Evidence: interleaving gives g = 0.42 overall and g = 0.34 for maths tasks (Brunmair and Richter 2019). Source: https://www.psychologie.uni-wuerzburg.de/fileadmin/06020400/2019/Brunmair_Richter_in_press__2019_META-ANALYSIS_OF_INTERLEAVED_LEARNING.pdf
5. Start each new ML procedure from a worked example, then fade it over sessions. Evidence: the expertise reversal effect (Kalyuga 2007). The worked-example evidence (Sweller and Cooper 1985; Barbieri et al. 2023) is unverified here. Source: https://www.uky.edu/~gmswan3/EDC608/Kalyuga2007_Article_ExpertiseReversalEffectAndItsI.pdf
6. Break it, then explain it. Corrupt labels, leak a feature, or drop a key input. Predict, run, and explain the result in three sentences. Evidence: self-explanation prompts gave g = .55 (95% CI .45 to .65) across 69 effect sizes and 5,917 participants (Bisra et al. 2018). Source: https://www.Gwern.net/doc/psychology/spaced-repetition/2018-bisra.pdf
7. Let the AI give hints and explanations, not answers. Evidence: in Bastani et al. (2025), unrestricted GPT Base lowered exam scores by about 17% relative to control. GPT Tutor with hints showed no significant exam loss, but also no gain. In Anthropic (2026), the high-scoring patterns asked for explanations or concepts. Sources: https://pmc.ncbi.nlm.nih.gov/articles/PMC12232635/ and https://arxiv.org/pdf/2601.20245
8. Keep the judgement steps yourself: metric choice, data split, reading curves, and choosing the next step. Evidence: Anthropic's largest gap was on debugging and code reading. Ng's manual review of about 100 errors takes "under two hours". Sources: https://arxiv.org/pdf/2601.20245 and https://raw.githubusercontent.com/ajaymache/machine-learning-yearning/master/machine-learning-yearning-part1.pdf
9. Check closed-book, on a new case. Use a quiz at the start of the next session, and one variant you have not run. Do not trust your feeling of understanding. Evidence: Bastani et al. found self-reports "overly optimistic". In METR's study, developers believed they were 20% faster when the measured time was 19% longer. Sources: https://pmc.ncbi.nlm.nih.gov/articles/PMC12232635/ and https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
10. Rebuild one small piece each session with no AI. For example, a metric function or one update step, 15 to 20 lines. Evidence: Karpathy's course is "from scratch, in code"; micrograd is about 100 lines. In Anthropic (2026), the no-AI group resolved errors on their own, which the authors offer as an explanation, not a measured mechanism. Sources: https://karpathy.ai/zero-to-hero.html, https://github.com/karpathy/micrograd, and https://arxiv.org/pdf/2601.20245

### Session length

- Use one hour as the unit. In the Anthropic study, tasks and surveys together averaged 58.5 minutes, with a 35-minute main task. Source: https://arxiv.org/pdf/2601.20245
- No verified primary study gives a better length for technical learning. Plan a repeat contact instead of a longer block. Source: https://www.evullab.org/pdf/CepedaVulRohrerWixtedPashler-PS-2008.pdf

### Minute-by-minute template (60 minutes)

| Time | Block | What you do | Evidence |
|---|---|---|---|
| 0:00-0:05 | Retrieval | Answer three closed-book questions from last session. Log the misses. | [Roediger and Karpicke 2006](https://www.gwern.net/docs/spaced-repetition/2006-roediger.pdf) |
| 0:05-0:12 | Predict | Read the task. Write the expected result and a 0-to-100 confidence. No AI yet. | [Richland et al. 2009](https://learninglab.uchicago.edu/Pre-Testing_files/RichlandKornellKao.pdf) |
| 0:12-0:22 | Run and observe | Run the baseline. Compare it with your prediction. Write one sentence on the gap. | [Bjork and Linn 2006](https://sites.lifesci.ucla.edu/psych-bjorklab/wp-content/uploads/sites/13/2016/07/RBjork_Linn_2006.pdf) |
| 0:22-0:32 | Change one thing | Change one hyperparameter or one data choice. Predict the direction and size, then run. | [Brunmair and Richter 2019](https://www.psychologie.uni-wuerzburg.de/fileadmin/06020400/2019/Brunmair_Richter_in_press__2019_META-ANALYSIS_OF_INTERLEAVED_LEARNING.pdf) |
| 0:32-0:42 | Break it | Corrupt labels, leak a feature, or drop a key input. Predict, run, and explain in three sentences. | [Bisra et al. 2018](https://www.Gwern.net/doc/psychology/spaced-repetition/2018-bisra.pdf) |
| 0:42-0:50 | Explain-back | Write five sentences for a smart engineer new to ML, with no AI. Then ask the AI to find the weakest claim. Do not ask it to rewrite. | [Anthropic 2026](https://arxiv.org/pdf/2601.20245) (conceptual questions) |
| 0:50-0:57 | Rebuild | Write 15 to 20 lines of one piece, such as a metric or one update step, with no AI. Run a check. | [Karpathy course](https://karpathy.ai/zero-to-hero.html) |
| 0:57-1:00 | Close | Write three flashcards. Book the next retrieval for 1 to 3 days later. | [Cepeda et al. 2008](https://www.evullab.org/pdf/CepedaVulRohrerWixtedPashler-PS-2008.pdf) |
