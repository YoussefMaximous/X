Routing (for the user, do not paste): new Fable chat. Paste the reply back to the Lead in full.

----- paste from here -----

# The core of the product: why did this trade lose?

Date: 2026-11-20. You are advising a trading team. You do not write code. The person who will read your answer is not a programmer. Write the screen in plain words first, then a precise spec.

## What he said

"knowing the type of the loss as in classifying it is extremely challenging and hard but it is the core of our product basically"

"a loss can be multiple reasons or not there are no locked rules"

"if multiple reasons of loss it should have 1 main reason which is the most and maybe put a gate that says if it actually can count as 2 or 3 or all 5 or only 1 there should be gates or something like a score enough to the loss total or something"

"we want a part where we turn on and off these type of losses because sometimes the user dont want certain types, what does these type of losses do, they first of all list all the losses in the run from how big is it and maybe fable 5.2 can put more ideas like the pattern this loss happend in and after this name this loss type, so each loss type have the amount of money it lost and on its standard deviation or something like this, we want it in an extremely good way"

## What the software is

A local tool. It runs an MT4 expert advisor over a year of real gold ticks, on the real bid and the real ask, and shows the losses. The people who will use it live in MT4, so the chart and the tools should feel like MT4. They inspect a loss by clicking it: the chart goes to that moment and they can replay the ticks. Nothing in the tool is sent online. You have not seen their trades. Do not pretend you have.

A draft list of about 45 possible reasons exists (entered too late, stop too tight, the spread knocked it out, entered again right after a stop, and others). It is a draft. The expert will review it after the software works, and he can add or remove a reason by asking an AI in one sentence. Do not treat that list as the answer.

## The problem

Saying why a trade lost is the product. It is also the part most likely to be wrong. A loss may have one reason, several, or none we can honestly name.

He has now asked for this shape, and it is the one to design, not a rule you may replace with "exactly one label":

- If several reasons fit, one of them is the main reason: the one that explains the most of that loss.
- Every other reason has to pass a gate. The gate is a score against the size of the loss. Clear it, and the reason counts (so a loss can show 2, 3 or all 5). Miss it, and that reason is not listed.
- Design the score and the gate. Say what "enough" means with a worked number. A reason that explains little of the money must not appear just because its rule matched.
- Show the main reason and the score of each extra reason on the loss, so he can see why one counted and another did not.

## Design this

1. The screen a trader sees after a run. He must understand it in a minute. It should feel at home next to MT4, not like a new kind of app.
2. Every loss in the run, listed from the biggest money lost.
3. Loss types he can turn on and off, because he will not always want all of them. Say what the screen does with a loss when one of its reasons is switched off, and what it does with a loss that has no reason.
4. The pattern first, the name second. Show what the losses have in common, in a way he can check on the chart, and only then the name of the type. Give one worked example with 12 losses: the pattern in plain words, the name, and the proof a sceptical EA maker would accept. If the ticks cannot prove it, do not name it.
5. For each type: how much money it lost, and how spread out those losses are. He suggested standard deviation. Use a better set of numbers if you know one, and say which numbers lie when a type has only a few losses.
6. Your own ideas, beyond what he named. Keep them inside this problem. Do not add a second product.

## Also answer

- When one loss has three reasons, how is its money shown so he is not misled into thinking he lost that money three times?
- What should the tool refuse to call a reason, even if it would make the screen look smarter?
- What should we do next, and what are we not seeing?

## How to answer

Start with the screen, top to bottom. Then the hard part: how a reason is decided, how several reasons sit on one loss, and how "we don't know" is shown. Then the numbers. End with a spec: rows, columns, switches, sorting, and the empty state.

Mark guesses as guesses. No code. No online features. Do not copy MT4's name, logo or icons.
