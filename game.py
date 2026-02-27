from datetime import datetime, timedelta
import os

GAME_DIR = "data/game"
TEAMS_DIR = "data/teams"
PROGRESS_DIR = "data/progress"
SEPARATOR = "---\n"
DURATION_PREFIX = "duration:"
PENALTY_PREFIX = "penalty:"
CODE_PREFIX = "code:"
START_PREFIX = "START"
TIME_FORMAT = "%H:%M:%S"
SECONDS_PER_MINUTE = 60

def parse_stage_file(stage_id):
    with open(f"{GAME_DIR}/{stage_id}", "r") as f:
        content = f.read()
    parts = content.split(SEPARATOR)
    hints = []
    penalty = 0
    code = ""
    for part in parts:
        part = part.strip()
        if part.startswith(DURATION_PREFIX):
            lines = part.split("\n", 1)
            duration = int(lines[0].split(":")[1].strip())
            text = lines[1] if len(lines) > 1 else ""
            hints.append({"duration": duration, "text": text})
        else:
            for line in part.split("\n"):
                line = line.strip()
                if line.startswith(PENALTY_PREFIX):
                    penalty = int(line.split(":")[1].strip())
                elif line.startswith(CODE_PREFIX):
                    code = line.split(":", 1)[1].strip()
    return {"hints": hints, "penalty": penalty, "code": code}

def get_team_stages(team):
    with open(f"{TEAMS_DIR}/{team}", "r") as f:
        return [line.strip() for line in f if line.strip()]

def read_progress(team):
    try:
        with open(f"{PROGRESS_DIR}/{team}", "r") as f:
            lines = [line.strip() for line in f if line.strip()]
            return lines
    except FileNotFoundError:
        return []

def write_progress(team, lines):
    os.makedirs(PROGRESS_DIR, exist_ok=True)
    with open(f"{PROGRESS_DIR}/{team}", "w") as f:
        f.write("\n".join(lines) + "\n")

def init_progress(team):
    progress = read_progress(team)
    if not progress:
        start_time = datetime.now().strftime(TIME_FORMAT)
        write_progress(team, [f"{START_PREFIX} {start_time}"])

def get_current_stage_index(team):
    progress = read_progress(team)
    stages = get_team_stages(team)
    completed = len([l for l in progress if l and not
                     l.startswith(START_PREFIX)])
    return (min(completed, len(stages) - 1)
            if completed < len(stages) else -1)

def get_stage_start_time(team):
    progress = read_progress(team)
    if not progress:
        return None
    start_line = [l for l in progress if l.startswith(START_PREFIX)]
    if not start_line:
        return None
    start_time_str = start_line[0].split()[1]
    today = datetime.now().date()
    start_time = datetime.strptime(start_time_str, TIME_FORMAT)
    start_datetime = datetime.combine(today, start_time.time())
    completed = [l for l in progress if l and not
                 l.startswith(START_PREFIX)]
    for comp in completed:
        parts = comp.split()
        if len(parts) >= 2:
            time_parts = parts[1].split(":")
            mins = int(time_parts[0])
            secs = int(time_parts[1])
            start_datetime += timedelta(minutes=mins, seconds=secs)
    return start_datetime

def get_current_hint(stage_data, elapsed_seconds):
    current_seconds = 0
    for i, hint in enumerate(stage_data["hints"]):
        current_seconds += hint["duration"] * SECONDS_PER_MINUTE
        if elapsed_seconds < current_seconds:
            hint_start = current_seconds - hint["duration"] * SECONDS_PER_MINUTE
            hint_elapsed = elapsed_seconds - hint_start
            return (i, hint, hint_elapsed,
                    hint["duration"] * SECONDS_PER_MINUTE)
    last_hint = stage_data["hints"][-1]
    last_start = (sum(h["duration"] for h in stage_data["hints"][:-1]) *
                  SECONDS_PER_MINUTE)
    hint_elapsed = elapsed_seconds - last_start
    return (len(stage_data["hints"]) - 1, last_hint,
            hint_elapsed, last_hint["duration"] * SECONDS_PER_MINUTE)

def get_stage_total_time(stage_data):
    return sum(h["duration"] for h in stage_data["hints"]) * SECONDS_PER_MINUTE

def complete_stage(team, stage_id, elapsed_seconds):
    progress = read_progress(team)
    mins = int(elapsed_seconds // SECONDS_PER_MINUTE)
    secs = int(elapsed_seconds % SECONDS_PER_MINUTE)
    progress.append(f"{stage_id} {mins:02d}:{secs:02d}")
    write_progress(team, progress)

def get_game_state(team):
    init_progress(team)
    stage_index = get_current_stage_index(team)
    if stage_index == -1:
        with open(f"{GAME_DIR}/END", "r") as f:
            return {"finished": True, "end_text": f.read()}
    stages = get_team_stages(team)
    stage_id = stages[stage_index]
    stage_data = parse_stage_file(stage_id)
    stage_start = get_stage_start_time(team)
    now = datetime.now()
    elapsed = int((now - stage_start).total_seconds())
    total_time = get_stage_total_time(stage_data)
    if elapsed >= total_time:
        elapsed_with_penalty = (total_time + stage_data["penalty"] *
                                SECONDS_PER_MINUTE)
        complete_stage(team, stage_id, elapsed_with_penalty)
        return get_game_state(team)
    hint_index, hint, hint_elapsed, hint_total = get_current_hint(
        stage_data, elapsed)
    return {
        "finished": False,
        "stage_id": stage_id,
        "stage_time_elapsed": elapsed,
        "stage_time_total": total_time,
        "hint_index": hint_index,
        "hint_text": hint["text"],
        "hint_time_elapsed": hint_elapsed,
        "hint_time_total": hint_total,
        "code": stage_data["code"]
    }

def check_code(team, submitted_code):
    state = get_game_state(team)
    if state.get("finished"):
        return False
    submitted = submitted_code.replace(" ", "").upper()
    expected = state["code"].replace(" ", "").upper()
    if submitted == expected:
        stage_start = get_stage_start_time(team)
        elapsed = int((datetime.now() - stage_start).total_seconds())
        complete_stage(team, state["stage_id"], elapsed)
        return True
    return False

def get_all_teams():
    teams = []
    for filename in os.listdir(TEAMS_DIR):
        if not filename.startswith("."):
            teams.append(filename)
    return sorted(teams)

def has_team_file(team):
    try:
        with open(f"{TEAMS_DIR}/{team}", "r") as f:
            return True
    except FileNotFoundError:
        return False

def get_standings():
    teams = get_all_teams()
    standings = []
    for team in teams:
        stages = get_team_stages(team)
        progress = read_progress(team)
        completed = [l for l in progress if l and not
                     l.startswith(START_PREFIX)]
        stage_results = []
        total_seconds = 0
        for i, stage_id in enumerate(stages):
            if i < len(completed):
                parts = completed[i].split()
                stage_time = parts[1] if len(parts) > 1 else "00:00"
                stage_data = parse_stage_file(stage_id)
                total_time = get_stage_total_time(stage_data)
                time_parts = stage_time.split(":")
                elapsed_secs = (int(time_parts[0]) * SECONDS_PER_MINUTE +
                                int(time_parts[1]))
                total_seconds += elapsed_secs
                status = "failed" if elapsed_secs >= total_time else "passed"
                stage_results.append({
                    "stage_id": stage_id,
                    "status": status,
                    "time": stage_time
                })
            elif i == len(completed):
                stage_start = get_stage_start_time(team)
                if stage_start:
                    elapsed = int((datetime.now() -
                                   stage_start).total_seconds())
                    total_seconds += elapsed
                    mins = elapsed // SECONDS_PER_MINUTE
                    secs = elapsed % SECONDS_PER_MINUTE
                    stage_results.append({
                        "stage_id": stage_id,
                        "status": "progress",
                        "time": f"{mins:02d}:{secs:02d}"
                    })
                else:
                    stage_results.append({
                        "stage_id": stage_id,
                        "status": "notstarted",
                        "time": ""
                    })
            else:
                stage_results.append({
                    "stage_id": stage_id,
                    "status": "notstarted",
                    "time": ""
                })
        stage_results.sort(key=lambda x: x["stage_id"])
        total_mins = total_seconds // SECONDS_PER_MINUTE
        total_secs = total_seconds % SECONDS_PER_MINUTE
        total_time_str = f"{total_mins:02d}:{total_secs:02d}"
        standings.append({
            "team": team,
            "stages": stage_results,
            "total_time": total_time_str
        })
    return standings

