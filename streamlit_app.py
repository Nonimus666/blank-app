import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import streamlit as st

st.set_page_config(page_title="Weekoverzicht productiviteit", layout="centered")

DATA_FILE = Path(__file__).with_name("tasks.json")
DAYS = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
BLOCK_PX = 30  # breedte van 1 uur

CSS = f"""
<style>
:root {{
    --green: #2e9e5b;
    --yellow: #f2b705;
    --open: rgba(128, 128, 128, .55);
}}
.day-row {{ display:flex; align-items:center; gap:16px; padding:10px 0 4px 0; }}
.day-name {{ width:110px; font-weight:600; font-size:1.05rem; }}
.blocks {{ display:flex; flex-wrap:wrap; gap:4px 14px; align-items:center; }}
.task-blocks {{ display:flex; gap:3px; }}
.block {{ height:{BLOCK_PX}px; width:{BLOCK_PX}px; border-radius:4px; box-sizing:border-box; }}
.block.half {{ width:{BLOCK_PX // 2}px; }}
.block.done {{ background:var(--green); }}
.block.late {{ background:var(--yellow); }}
.block.open {{ border:2px solid var(--open); }}
.block.running {{ border:2px solid var(--yellow); }}
.empty {{ opacity:.45; font-size:.9rem; }}
.legend {{ display:flex; gap:20px; font-size:.85rem; opacity:.8; margin:4px 0 12px 0; }}
.legend span {{ display:inline-flex; align-items:center; gap:6px; }}
.legend .block {{ height:12px; width:12px; border-radius:3px; }}
.summary {{ font-size:.95rem; opacity:.85; margin:6px 0 2px 0; }}
.task-title {{ font-size:.95rem; }}
.task-meta {{ opacity:.6; font-size:.85rem; }}
.countdown {{ font-variant-numeric:tabular-nums; font-weight:600; }}
.countdown.over {{ color:var(--yellow); }}
</style>
"""


def now() -> datetime:
    """Huidige tijd in Nederland (de online server draait anders op UTC)."""
    return datetime.now(ZoneInfo("Europe/Amsterdam")).replace(tzinfo=None)


# ---------- inloggen ----------
def require_password():
    """Vraagt om een wachtwoord als er een is ingesteld (online). Lokaal: geen wachtwoord."""
    try:
        password = st.secrets["app_password"]
    except (KeyError, FileNotFoundError):
        return
    if st.session_state.get("ingelogd"):
        return
    st.title("Inloggen")
    with st.form("login"):
        entered = st.text_input("Wachtwoord", type="password")
        if st.form_submit_button("Open") and entered == password:
            st.session_state.ingelogd = True
            st.rerun()
        elif entered:
            st.error("Wachtwoord klopt niet.")
    st.stop()


# ---------- opslag ----------
# Online: Supabase (database, bewaart alles blijvend).
# Lokaal zonder instellingen: een bestandje tasks.json naast de app.
def supabase_config():
    try:
        sb = st.secrets["supabase"]
        return sb["url"].rstrip("/") + "/rest/v1/tasks", {
            "apikey": sb["key"],
            "Authorization": f"Bearer {sb['key']}",
            "Content-Type": "application/json",
        }
    except (KeyError, FileNotFoundError):
        return None


def load_tasks():
    cfg = supabase_config()
    if cfg:
        url, headers = cfg
        r = requests.get(url, headers=headers, params={"select": "*"}, timeout=15)
        r.raise_for_status()
        return r.json()
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except json.JSONDecodeError:
            return []
    return []


def _save_local(tasks):
    DATA_FILE.write_text(json.dumps(tasks, indent=2))


def add_task(task):
    cfg = supabase_config()
    if cfg:
        url, headers = cfg
        requests.post(url, headers=headers, json=task, timeout=15).raise_for_status()
    else:
        _save_local(load_tasks() + [task])


def update_task(task_id, **changes):
    cfg = supabase_config()
    if cfg:
        url, headers = cfg
        requests.patch(
            url, headers=headers, params={"id": f"eq.{task_id}"}, json=changes, timeout=15
        ).raise_for_status()
    else:
        tasks = load_tasks()
        for t in tasks:
            if t["id"] == task_id:
                t.update(changes)
        _save_local(tasks)


def delete_task(task_id):
    cfg = supabase_config()
    if cfg:
        url, headers = cfg
        requests.delete(url, headers=headers, params={"id": f"eq.{task_id}"}, timeout=15).raise_for_status()
    else:
        _save_local([t for t in load_tasks() if t["id"] != task_id])


# ---------- helpers ----------
def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def blocks_html(task, running=False):
    state = task["status"] if task["status"] != "open" else ("running" if running else "open")
    full, rest = int(task["hours"]), task["hours"] - int(task["hours"])
    parts = [f'<div class="block {state}"></div>' for _ in range(full)]
    if rest:
        parts.append(f'<div class="block half {state}"></div>')
    return f'<div class="task-blocks" title="{task["title"]}">{"".join(parts)}</div>'


def fmt_hours(h):
    return f"{h:g} uur"


def finish(task, in_time_required=True):
    """Markeer als gelukt. Als de timer liep en de deadline verstreken is -> geel."""
    status = "done"
    if task.get("started_at"):
        deadline = datetime.fromisoformat(task["started_at"]) + timedelta(hours=task["hours"])
        if now() > deadline:
            status = "late"
    update_task(task["id"], status=status, finished_at=now().isoformat())


@st.fragment(run_every="1s")
def countdown(task):
    deadline = datetime.fromisoformat(task["started_at"]) + timedelta(hours=task["hours"])
    left = (deadline - now()).total_seconds()
    over = left < 0
    secs = int(abs(left))
    text = f"{secs // 3600}:{secs % 3600 // 60:02d}:{secs % 60:02d}"
    label = "Tijd over" if not over else "Tijd verstreken"
    st.markdown(
        f'<span class="task-meta">{label}</span> '
        f'<span class="countdown {"over" if over else ""}">{text}</span>',
        unsafe_allow_html=True,
    )


# ---------- state ----------
if "week_start" not in st.session_state:
    st.session_state.week_start = monday_of(now().date())

st.markdown(CSS, unsafe_allow_html=True)
require_password()
st.title("Weekoverzicht")

tasks = load_tasks()
week_start: date = st.session_state.week_start
week_days = [week_start + timedelta(days=i) for i in range(7)]
week_tasks = [t for t in tasks if date.fromisoformat(t["date"]) in week_days]

# navigatie
nav_l, nav_m, nav_r = st.columns([1, 3, 1])
if nav_l.button("Vorige", use_container_width=True):
    st.session_state.week_start = week_start - timedelta(days=7)
    st.rerun()
if nav_r.button("Volgende", use_container_width=True):
    st.session_state.week_start = week_start + timedelta(days=7)
    st.rerun()
iso = week_start.isocalendar()
nav_m.markdown(
    f"<div style='text-align:center;padding-top:6px'>Week {iso.week} &middot; "
    f"{week_days[0]:%d-%m} t/m {week_days[6]:%d-%m-%Y}</div>",
    unsafe_allow_html=True,
)

has_weekend_tasks = any(date.fromisoformat(t["date"]).weekday() >= 5 for t in week_tasks)
show_weekend = st.checkbox("Weekend tonen (za / zo)", value=has_weekend_tasks)

st.markdown(
    '<div class="legend">'
    '<span><div class="block done"></div>Op tijd gelukt</span>'
    '<span><div class="block late"></div>Niet op tijd</span>'
    '<span><div class="block open"></div>Nog open</span>'
    "</div>",
    unsafe_allow_html=True,
)

# ---------- dagen ----------
visible = week_days if show_weekend else week_days[:5]
for day in visible:
    day_tasks = [t for t in week_tasks if t["date"] == day.isoformat()]
    row = "".join(
        blocks_html(t, running=bool(t.get("started_at"))) for t in day_tasks
    ) or '<span class="empty">geen taken</span>'
    today_mark = " (vandaag)" if day == now().date() else ""
    st.markdown(
        f'<div class="day-row"><div class="day-name">{DAYS[day.weekday()]}{today_mark}</div>'
        f'<div class="blocks">{row}</div></div>',
        unsafe_allow_html=True,
    )

    for t in day_tasks:
        c_title, c_time, c_a, c_b, c_del = st.columns([3.5, 3, 1.5, 1.8, 1.2])
        c_title.markdown(
            f'<div class="task-title">{t["title"]}</div>'
            f'<div class="task-meta">{fmt_hours(t["hours"])}</div>',
            unsafe_allow_html=True,
        )
        if t["status"] == "open":
            if t.get("started_at"):
                with c_time:
                    countdown(t)
            else:
                if c_time.button("Start timer", key=f"start_{t['id']}"):
                    update_task(t["id"], started_at=now().isoformat())
                    st.rerun()
            if c_a.button("Gelukt", key=f"done_{t['id']}", type="primary"):
                finish(t)
                st.rerun()
            if c_b.button("Niet gelukt", key=f"late_{t['id']}"):
                update_task(t["id"], status="late", finished_at=now().isoformat())
                st.rerun()
        else:
            label = "Op tijd afgerond" if t["status"] == "done" else "Niet op tijd afgerond"
            c_time.markdown(f'<span class="task-meta">{label}</span>', unsafe_allow_html=True)
            if c_a.button("Heropen", key=f"reopen_{t['id']}"):
                update_task(t["id"], status="open", started_at=None, finished_at=None)
                st.rerun()
        if c_del.button("Wis", key=f"del_{t['id']}"):
            delete_task(t["id"])
            st.rerun()

    with st.popover("Taak toevoegen", use_container_width=False):
        with st.form(f"add_{day.isoformat()}", clear_on_submit=True):
            title = st.text_input("Taak")
            hours = st.number_input("Binnen hoeveel uur af? (1 blok = 1 uur)", 0.5, 12.0, 2.0, 0.5)
            if st.form_submit_button("Toevoegen") and title.strip():
                add_task(
                    {
                        "id": uuid.uuid4().hex,
                        "date": day.isoformat(),
                        "title": title.strip(),
                        "hours": hours,
                        "status": "open",
                        "started_at": None,
                        "finished_at": None,
                    }
                )
                st.rerun()
    st.divider()

# ---------- samenvatting ----------
shown = [t for t in week_tasks if date.fromisoformat(t["date"]) in visible]
done = [t for t in shown if t["status"] == "done"]
late = [t for t in shown if t["status"] == "late"]
open_ = [t for t in shown if t["status"] == "open"]
st.markdown(
    f'<div class="summary">Deze week: <b>{len(done)}</b> op tijd '
    f"({sum(t['hours'] for t in done):g} uur), <b>{len(late)}</b> niet op tijd, "
    f"<b>{len(open_)}</b> open.</div>",
    unsafe_allow_html=True,
)
