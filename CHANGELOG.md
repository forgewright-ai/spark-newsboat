# Changelog

## 1.1.2

- The wait is animated: `spark reads N characters | 12s` -- an ASCII
  spinner and the elapsed seconds, redrawn in place four times a
  second, erased the moment the answer starts. A counted, moving wait
  reads as work; a still line read as a hang.

## 1.1.1

- The first wait says what it is. Before the first answer byte the
  screen shows `spark reads N characters ...`, a dot a second -- the
  prefill on a big model is long, and a blank screen read as a hang.
  The line erases itself the moment the answer starts. Measured on
  the box: the article is barely reused between questions, so the
  wait is real each time; warming it while the reader types is a
  spark-core idea for another day.

## 1.1.0

- The answer at a reader's pace: the wrapper pipes through `spark
  reveal` when this spark has it (1.31 or newer) -- each grounded
  line letter by letter, SPARK_REVEAL_CPS the speed -- and the wrap
  is a line-flushing awk instead of fold, which held lines back in a
  pipe. An older spark keeps the line-at-a-time behavior. From the
  maintainer's first evening with the 12B: the pop at the end had to
  become a steady hand.

## 1.0.0

- The first release: newsboat's article, under spark's law. `,s` (the
  macro prefix, then s) pipes the article you are on -- open, or
  selected in the list -- to `spark read` on the terminal newsboat
  hands over: the title, the `spark> ` prompt, the grounded answer
  streaming line by line, Enter back to newsboat exactly as it was.
  Enter or ? alone is the overview, words are the question, `--part 2`
  rides, Ctrl-C is never mind. A refusal shows where the answer would
  be (stderr folded in); the wrapper reads any text from a plain
  shell too. On newsboat 2.38 or newer a commented bind line offers
  the same exchange on Alt-s.
