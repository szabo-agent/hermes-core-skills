## 0. Preconditions

Confirm these before writing files:

1. Hermes CLI works: `hermes --help`
2. You know `$HOME` and `$HERMES_HOME` (default `~/.hermes`)
3. You will **not** move, rewrite, or delete existing `~/.hermes/config.yaml`, `.env`, sessions, or `state.db`
4. You **may** create missing identity/memory files if they do not exist, and you **must** create the AgentOS tree below
5. If `~/AgentOS` already exists, do not wipe it. Merge: create only missing paths, do not overwrite a non-empty `AGENTS.md`, `SOUL.md`, or vault note without asking

Default root (change only if the human names another path):

```text
AGENTOS=~/AgentOS
```

Hermes home stays where it is. AgentOS is the working world. Hermes home is identity, memory, skills, cron, secrets.

---

## 1. Mental model (do not collapse these layers)

| Layer | Path | Purpose | You write? |
|---|---|---|---|
| Identity | `$HERMES_HOME/SOUL.md` | Who you are, tone, hard stops | Yes, once, short |
| User model | `$HERMES_HOME/memories/USER.md` | How this human wants work done | Sparse facts only |
| Agent memory | `$HERMES_HOME/memories/MEMORY.md` | Environment facts, tool quirks | Facts, never procedures |
| Skills | `$HERMES_HOME/skills/<category>/<name>/` | Repeatable how-to | Yes, after real wins |
| Config / secrets | `$HERMES_HOME/config.yaml`, `.env` | Model, tools, MCP, keys | Touch only if asked |
| Commander map | `$AGENTOS/AGENTS.md` | How you pick work and where you write | Yes |
| This playbook | `$AGENTOS/instruction.md` | How you deployed / how to re-deploy | Copy of this file |
| Workspaces | `$AGENTOS/workspaces/<domain>/` | Writable sandboxes | Yes |
| Vault | `$AGENTOS/vault/` | Compounding notes | Append |
| Projects | `$AGENTOS/projects/` | Real git repos (or symlinks) | Only when a repo exists |
| Board | `$AGENTOS/board/` | Inbox / doing / done handoffs | Yes |

Rules that never change:

- Procedures live in skills, not `MEMORY.md`
- Project conventions live in that project's `AGENTS.md`
- Artifacts live in a workspace `out/` or a project repo — never in `$HERMES_HOME`
- One workspace per task. If work spans two domains, write a board card and switch. Do not mix trees
- Default cwd for commander sessions: `$AGENTOS`
- Never use `$HOME` as a dump. Never crawl outside the assigned workspace plus `$AGENTOS/vault` and `$AGENTOS/board` unless the human named a path

---

## 2. Create the tree

Run equivalent mkdir commands. Create `.gitkeep` in empty dirs so the tree survives git.

```text
~/AgentOS/
├── instruction.md              # this file (copy it here)
├── AGENTS.md                   # commander constitution (section 4)
├── README.md                   # human-facing one-pager (section 5)
├── board/
│   ├── inbox.md
│   ├── doing.md
│   ├── blocked.md
│   └── done/
├── vault/
│   ├── index.md
│   ├── inbox/
│   ├── research/
│   │   └── YYYY/MM/            # create current year/month
│   ├── decisions/
│   ├── people/
│   ├── runbooks/
│   └── logs/
├── workspaces/
│   ├── coding/
│   │   ├── AGENTS.md
│   │   ├── inbox/
│   │   ├── active/
│   │   └── out/
│   ├── home-energy/
│   │   ├── AGENTS.md
│   │   ├── inbox/
│   │   ├── active/
│   │   └── out/
│   ├── cyber/
│   │   ├── AGENTS.md
│   │   ├── inbox/
│   │   ├── active/
│   │   └── out/
│   ├── research/
│   │   ├── AGENTS.md
│   │   ├── inbox/
│   │   ├── active/
│   │   └── out/
│   ├── property/
│   │   ├── AGENTS.md
│   │   ├── inbox/
│   │   ├── active/
│   │   └── out/
│   └── personal/
│       ├── AGENTS.md
│       ├── inbox/
│       ├── active/
│       └── out/
├── projects/                   # leave empty except README
│   └── README.md
└── shared/
    ├── templates/
    │   ├── vault-note.md
    │   ├── board-card.md
    │   └── handoff.md
    └── schemas/
        └── board-card.schema.json
```

Create current vault month:

```bash
mkdir -p "$HOME/AgentOS/vault/research/$(date +%Y/%m)"
```