# spark-newsboat -- spark inside newsboat

spark (https://spark.forgewright.ai) is your own AI on your own machine;
this plugin puts it under one key in newsboat, the RSS reader. The
article you are on -- open, or selected in the list -- is piped to
`spark read`, and the answer says only what the article says: every
line quotes it, and the quote is checked -- a claim the article does
not hold never reaches you. The second client of `spark read`, after
spark-w3m.

The key is newsboat's macro prefix: `,` then `s`. The screen is spark's
for the exchange -- the article's header (feed, title, date, link),
then `spark> ` -- and Enter
brings newsboat back exactly as it was:

    Enter or ?         the overview: what does this article cover?
    your words         your question ("does it name a price"); a
                       leading ? works too, the editors' habit
    --part 2 words     an article past 16 kB answers with its part
                       count; this reads part 2
    Ctrl-C             never mind -- newsboat comes straight back

The answer appears at a reader's pace: with spark 1.31 or newer each
grounded line is revealed letter by letter (`spark reveal`;
SPARK_REVEAL_CPS sets the speed), so the model composing the next
line hides behind the reading of this one. An older spark shows each
line whole as it clears the check. When
the article does not answer, the reply is one line showing its own
opening words -- never a guess.

## Install

You need spark 1.20 or newer on this machine (`spark read -h` answers),
and newsboat 2.10 or newer (`newsboat --version`). Then:

```sh
git clone https://github.com/forgewright-ai/spark-newsboat ~/.newsboat/spark
ln -s ~/.newsboat/spark/spark-newsboat ~/.local/bin/spark-newsboat
cat ~/.newsboat/spark/config.spark >> ~/.newsboat/config
```

`spark-newsboat` is the wrapper around `spark read` that draws the
prompt on the terminal newsboat hands over, folds stderr into the
answer, so a refusal shows on screen instead of vanishing, and wraps
long lines at spaces (`SPARK_NEWSBOAT_WIDTH` sets the column, default
78). From a plain shell the same wrapper takes the words directly:
`newsboat` is not even needed -- any text on stdin reads. An update is
`git -C ~/.newsboat/spark pull`, then delete the old spark lines from
`~/.newsboat/config` and append again. The comment block in
`config.spark` is the help; `,s` is newsboat's native spelling, and on
newsboat 2.38 or newer a commented `bind` line in the snippet puts the
same exchange on spark's key in every app, Alt-s. The keys, and what
to ask: `CHEATSHEET.md`.

## What leaves this machine

The rendered article -- the Feed/Title/Date/Link header newsboat
prints and the text, 16 kB a part -- and your words, and only to the
brain spark is configured for. No file, no feed URL beyond the
article's own Link line, no path. Every run is one call to `spark
read` with the article on stdin; the plugin never speaks HTTP for
itself and never sees a token.

## Contributing

`git config core.hooksPath .githooks` once; the hook keeps the tree
free of private names, ASCII, and the payload config-only. `python3
tests/newsboat_pty.py` drives a real newsboat in a pty against a stub
spark (skips without newsboat). Another reader joins spark the same
way this one does: one client of `spark read`, in its own repo.

MIT. Credits in `CREDITS.md`. Built with Claude.
