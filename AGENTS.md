# Elliott Runtime Rules

This folder is the only writable Codex workspace for the Elliott project.

## Protected Brain

The canonical Elliott Brain is located at:

C:\ElliottCodex\Brain_LOCKED

Codex may read files from Brain_LOCKED when needed for analysis or implementation.

Codex must never:

- modify Brain_LOCKED;
- create files inside Brain_LOCKED;
- rename or delete anything inside Brain_LOCKED;
- overwrite any Brain file;
- change the Elliott methodology, source policy, prompts, schemas, tests, or behavioral rules stored there.

If a methodology change appears necessary, Codex must:

1. stop;
2. describe the proposed change;
3. identify the exact Brain file affected;
4. provide the proposed diff;
5. wait for explicit user approval.

No methodology change may be applied from Runtime_WORKSPACE.

## Runtime

All implementation code, TradingView tools, logs, analysis outputs, screenshots, experiments, and tests must be written only inside:

C:\ElliottCodex\Runtime_WORKSPACE

## Source Lock

Elliott Wave analysis must follow the source-lock and evidence rules defined in Brain_LOCKED.

Do not import Elliott Wave rules from model memory or unrelated external sources unless the user explicitly authorizes them.