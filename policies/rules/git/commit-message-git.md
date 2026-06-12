Git Commit Message Rules
- All commit must be strictly  reversable so if anything goes wrong we can easly revert it with proper rollaback strategy
- Must Per module/feature/even if changes are complicated per change one commit and push with changes
- One commit = one logical change (feature, fix, refactor — not mixed)
- Review before committing using git diff
- Focus on intent, not implementation details
- Stage selectively (git add -p), never do avoid git add .
- Write subject as: WHAT changed (short, ≤ 50 chars) and if possible add ascii desison tree 

be on point short and direct on unnessary detailes
[<feature or module or logic or class or flow>-ST-01 | Previous State]
   |
   +-- [<feature or module or logic or class or flow>-IN-01 | Any Input]
       |
       +-- [<feature or module or logic or class or flow>-PR-01 | Any processing or logic or algorithem ref explain on points]
           |
           +-- [<feature or module or logic or class or flow>-DC-01 | any decision or rational or depndencies or logical relationship with other compoents/classes/functions or explanation of any logic]
               |-- [affected branch a | before | after ] 
               |-- [affected branch a | before | after ]
               `-- [<feature or module or logic or class or flow>-OUT-01 |  any Output](data / response / event / update / artifact)
                   |   
                   |
                   `-- [<feature or module or logic or class or flow>-CS-01 | Current State]

IN-01   → Input step 1
PR-01   → Processing step 1
DC-01   → Decision step 1
OUT-01  → Output step 1
CS-01   → Current state step 1
make sure you make it queriesble for humans and AI agents

- Use imperative mood (“add”, “fix”, “remove”)
- Add body for: WHY it changed (clear reason/context)
- Keep commits small and atomic (independent & reversible)
- Do not commit unrelated changes together
- Avoid vague messages (“update”, “fix stuff”)
- Use standard types (feat, fix, refactor, docs, etc.)
- Separate subject and body with a blank line

- do not push secrets, api keys, or sensitive information and if you accidentally push then immediately remove it and create a new commit to remove it and notify the team.