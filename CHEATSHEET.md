# newsboat with spark -- the cheatsheet

newsboat gathers the news; spark reads with you. Section 1 is
newsboat on its own, section 2 is the key that puts your own AI
inside it.

The key spellings here are newsboat's: `,s` means press the comma
(the macro prefix), then s. `Ctrl-C` means hold Ctrl and press c.
Keys are case-sensitive.

## 1. newsboat, the basics

Three screens: feeds, articles, the article. Enter goes deeper, `q`
backs out (and quits from the feed list).

The feeds

    r              refresh the selected feed
    R              refresh all feeds
    Enter          open the feed's article list

Reading

    n              jump to the next unread article, from anywhere
    Enter          read the article
    Space          page down inside it
    q              back to the list
    A              mark the whole feed read

Links

    o              open the article's link in the browser
    u              the article's links, numbered -- Enter opens one

Anywhere

    /              search
    ?              the key list for the screen you are on

Your feeds live in `~/.newsboat/urls`, one URL per line; a `#` in
front rests one.

## 2. the article, with spark

One macro: `,s` -- on the article you are reading, or the one
selected in the list. The screen is spark's for the exchange: the
article's title, then `spark> `. The answer is revealed at a
reader's pace, every line quoting the article (SPARK_REVEAL_CPS sets
the letters a second; spark 1.31 or newer), and Enter brings
newsboat back exactly as it was.

    Enter or ?     the overview: what does this article cover?
    your words     your question (a leading ? works too)
    --part 2 words an article past 16 kB answers with its part
                   count; this asks part 2
    Ctrl-C         never mind -- newsboat comes straight back

By example

    a long read    ,s Enter
                   the overview, before you commit to reading it all
    a claim        ,s does it name a source for the numbers
                   the answer quotes the lines that do
    a release note ,s what changed for Linux
    a paywall tease
                   ,s Enter -- what the feed actually carried, no more

When the article does not hold the answer, the reply is one line
showing its own opening words -- never a guess. That is the design:
spark read says only what the article says.

From a plain shell, the same wrapper reads any text:

    w3m -dump URL | spark-newsboat your words

On newsboat 2.38 or newer, a commented `bind` line in `config.spark`
puts the same exchange on spark's key in every app, Alt-s.
