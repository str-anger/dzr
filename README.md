# dzr

Game engine for team-based timed puzzle challenges.

## Setup

1. Install dependencies: `pip install flask`
2. Run server: `python server.py`
3. Access at: `http://localhost:8888`

## Features

- **Team Login**: Teams authenticate with username/password
- **Timed Stages**: Multiple stages with timed hints that auto-advance
- **Code Submission**: Case-insensitive codes (spaces ignored)
- **Auto-Progression**: Stages auto-complete with penalty if time expires
- **Live Standings**: Real-time leaderboard for observers
- **Time Format**: All times displayed as mm:ss
- **Alphabetical Ordering**: Stages sorted alphabetically on standings

## Pages

- `/login` - Team authentication
- `/` - Main game page (redirects here after login if team has file)
- `/standings` - Live leaderboard (only for authenticated users without 
team files)

## How to Add a New Game

### Step 1: Create Game Stage Files

Create stage files in `/data/game/` directory. Name them sequentially: 
`00`, `01`, `02`, etc.

Each file structure:
```
duration: NN
hint text for first hint
---

duration: MM
hint text for second hint
---

duration: KK
hint text for third hint
---
penalty: PP
code: ANSWER
```

- `duration`: Time in minutes for each hint
- `penalty`: Extra minutes added if stage times out
- `code`: Answer players must enter to complete stage
- Use `---` to separate hints
- Last section has penalty and code

Example `/data/game/00`:
```
duration: 15
Find the red book in the library.
---

duration: 20
Look for page 42 in the red book.
---
penalty: 5
code: ALPHA
```

### Step 2: Create Teams

Add team credentials to `/data/passwd`:
```
team1:password1
team2:password2
observer:observer123
```

Format: `teamname:password` (one per line, plain text)

**Note**: Users in `/data/passwd` without a corresponding team file in 
`/data/teams/` can access `/standings` page to view live leaderboard.

### Step 3: Assign Stage Order to Teams

Create files in `/data/teams/` for each team (use exact team names).

Each file contains stage IDs in order (one per line):
```
00
02
01
```

Different teams should have different orders to prevent following.

Example `/data/teams/team1`:
```
00
02
01
```

### Step 4: Create End Message

Create `/data/game/END` with completion message:
```
Congratulations! You completed all challenges!
```

### Step 5: Clean Progress (Optional)

Remove `/data/progress/` directory to reset all team progress for new 
game.

### File Structure Summary

```
/data/
  passwd          - team credentials (team:password)
  /game/
    00, 01, 02    - stage files with hints
    END           - completion message
  /teams/
    team1         - stage order for team1
    team2         - stage order for team2
  /progress/      - auto-created, tracks team progress
    team1
    team2
```

## Standings Page

The standings table shows:
- **Rows**: Teams
- **Columns**: Stages (alphabetically sorted) + Total time
- **Cell Colors**:
  - White (empty): Stage not started
  - Green: Stage passed successfully
  - Red: Stage failed (timeout with penalty)
  - Gray: Stage in progress
- **Times**: Displayed in mm:ss format
- **Access**: Only for authenticated users without team files

## Game Flow

1. Team logs in at `/login`
2. Game starts automatically, recording START time
3. Team sees current stage with hints on `/` page
4. Hints auto-advance based on duration timers
5. Team enters code (case-insensitive, spaces ignored)
6. Correct code advances to next stage
7. If time expires, penalty applied and auto-advances
8. After all stages complete, END message shown
9. Progress saved in `/data/progress/team_name`
