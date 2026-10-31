# Issue shape

```markdown
Origin: <project> (<link>)            <- only when the `from: <project>` label is unavailable

## What happens
<one paragraph, the behaviour as a user of the tool sees it>

## Reproduce
<versions (tool, OS, runtime)>, then the smallest input and command:
    <command>
Actual: <output, trimmed>
Expected: <what should happen, and why (doc link if any)>

## Impact
<one line: what it blocks or costs in the consumer project>

## Possible direction
<optional: where in the code, an option you considered, a workaround in use>
```

Title: behaviour, present tense, under 70 characters ("Lint passes on overlapping labels",
not "Fix lint"). One problem per issue; link siblings instead of merging them.
