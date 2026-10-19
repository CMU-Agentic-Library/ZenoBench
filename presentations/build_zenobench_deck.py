"""Build the editable ZenoBench group-meeting deck (skill library, task suite, planning benchmark).

Run from the repository root with python-pptx installed.
"""

from __future__ import annotations

from pathlib import Path
import json
import cv2

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "presentations"
OUT.mkdir(exist_ok=True)
FRAMES = OUT / "frames"
FRAMES.mkdir(exist_ok=True)
DEST = OUT / "ZenoBench_group_meeting.pptx"

PPT = Presentation()
PPT.slide_width = Inches(13.333)
PPT.slide_height = Inches(7.5)
BLANK = PPT.slide_layouts[6]

NAVY = RGBColor(16, 31, 52)
INK = RGBColor(25, 40, 61)
BLUE = RGBColor(36, 104, 188)
TEAL = RGBColor(0, 143, 147)
AMBER = RGBColor(239, 163, 60)
PALE = RGBColor(241, 246, 251)
MID = RGBColor(88, 105, 123)
WHITE = RGBColor(255, 255, 255)
GREEN = RGBColor(38, 147, 101)
RED = RGBColor(196, 78, 75)
LINE = RGBColor(219, 228, 236)
FOOTERS = []      # (page-number textbox, slide number); filled in once the slide count is known


def box(slide, x, y, w, h, fill=WHITE, line=None, radius=False):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
                               Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = fill
    s.line.fill.background() if line is None else None
    if line is not None:
        s.line.color.rgb = line
    return s


def text(slide, content, x, y, w, h, size=18, color=INK, bold=False,
         font="Aptos", align=None, margin=0, valign=MSO_ANCHOR.TOP):
    s = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = s.text_frame
    tf.clear(); tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = Inches(margin)
    tf.vertical_anchor = valign
    for i, line in enumerate(str(content).split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.name = font; p.font.size = Pt(size); p.font.bold = bold; p.font.color.rgb = color
        p.space_after = Pt(3)
        if align is not None: p.alignment = align
    return s


def pic(slide, rel, x, y, w, h, crop=True):
    path = ROOT / rel
    from PIL import Image
    im = Image.open(path)
    iw, ih = im.size
    if not crop:
        scale = min(w / iw, h / ih)
        ww, hh = iw * scale, ih * scale
        return slide.shapes.add_picture(str(path), Inches(x + (w - ww) / 2),
                                        Inches(y + (h - hh) / 2), Inches(ww), Inches(hh))
    ratio = w / h
    ir = iw / ih
    if ir > ratio:
        side = (1 - ratio / ir) / 2
        s = slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w), height=Inches(h))
        s.crop_left = s.crop_right = side
    else:
        side = (1 - ir / ratio) / 2
        s = slide.shapes.add_picture(str(path), Inches(x), Inches(y), width=Inches(w), height=Inches(h))
        s.crop_top = s.crop_bottom = side
    return s


def slide(title, kicker=None, subtitle=None, dark=False):
    s = PPT.slides.add_slide(BLANK)
    box(s, 0, 0, 13.333, 7.5, NAVY if dark else WHITE)
    fg = WHITE if dark else INK
    if kicker: text(s, kicker.upper(), .55, .28, 10.8, .23, 10, TEAL if not dark else AMBER, True)
    text(s, title, .55, .64, 12.05, .75, 28, fg, True)
    if subtitle: text(s, subtitle, .57, 1.38, 12.0, .43, 12.5, MID if not dark else RGBColor(181, 200, 219))
    box(s, .55, 7.08, 12.23, .012, LINE if not dark else RGBColor(81, 102, 124))
    text(s, "ZenoBench  ·  CMU Agentic Library", .56, 7.13, 8, .18, 8.5,
         MID if not dark else RGBColor(180, 196, 215))
    FOOTERS.append((text(s, "", 12.14, 7.12, .62, .2, 8.5,
                         MID if not dark else RGBColor(180, 196, 215), align=PP_ALIGN.RIGHT), len(PPT.slides)))
    return s


def card(slide, x, y, w, h, head, body, accent=BLUE, bg=PALE, head_size=17, body_size=13):
    box(slide, x, y, w, h, bg, LINE, radius=True)
    box(slide, x, y, .055, h, accent)
    if h < 1.6:
        text(slide, head, x + .22, y + .12, w - .45, .33, head_size, INK, True)
        text(slide, body, x + .22, y + .48, w - .45, h - .54, body_size, MID)
    else:
        text(slide, head, x + .22, y + .2, w - .45, .42, head_size, INK, True)
        text(slide, body, x + .22, y + .72, w - .45, h - .85, body_size, MID)


def note(s, txt):
    try:
        s.notes_slide.notes_text_frame.text = txt
    except Exception:
        pass


def frame(video, frac, name):
    dst = FRAMES / f"{name}.jpg"
    if dst.exists(): return str(dst.relative_to(ROOT))
    cap = cv2.VideoCapture(str(ROOT / "media/tasks" / video))
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * frac))
    ok, image = cap.read()
    cap.release()
    if not ok: raise RuntimeError(f"Could not read {video} at {frac}")
    cv2.imwrite(str(dst), image)
    return str(dst.relative_to(ROOT))


heat_fridge = frame("heat_breakfast.mp4", .15, "heat_fridge")
heat_microwave = frame("heat_breakfast.mp4", .45, "heat_microwave")
heat_table = frame("heat_breakfast.mp4", .75, "heat_table")
fruits = frame("collect_fruits.mp4", .48, "collect_fruits")
toys = frame("tidy_toys.mp4", .45, "tidy_toys")
books = frame("shelve_books.mp4", .16, "shelve_books")

# 1. Title
s = PPT.slides.add_slide(BLANK)
box(s, 0, 0, 13.333, 7.5, NAVY)
pic(s, "media/scenes/house_topdown.jpg", 6.20, .32, 6.72, 6.85, crop=True)
box(s, 6.08, .32, .09, 6.85, TEAL)
text(s, "ZenoBench", .65, 1.16, 5.12, .75, 36, WHITE, True)
text(s, "From generated worlds to household tasks", .65, 2.12, 5.17, 1.33, 25, WHITE, True)
text(s, "What we have · What it can do · A benchmark for the planner", .66, 4.01, 5.20, .71, 16, RGBColor(194, 216, 234))
box(s, .65, 5.59, 4.98, .67, RGBColor(27, 57, 79), radius=True)
text(s, "Group meeting  |  October 2026", .88, 5.77, 4.48, .32, 14, WHITE, True)
text(s, "github.com/CMU-Agentic-Library/ZenoBench", .67, 6.83, 5.64, .25, 10.8, RGBColor(188, 211, 228))
note(s, "The talk is a high-level overview: upstream EmbodiedGen V2, what ZenoBench contains, task demos, and the proposed upper-level skill-graph interface.")

# 2. EmbodiedGen V2 in one slide
s = slide("EmbodiedGen V2 generates simulation-ready worlds", "Background", "The upstream system turns language or images into assets, rooms and task layouts.")
for i,(head,body,color) in enumerate([
    ("Assets", "3D objects with geometry, appearance and physical properties", TEAL),
    ("Scenes", "Navigable multi-room environments", BLUE),
    ("Task worlds", "Objects arranged for interactive robot tasks", AMBER),
]):
    x=.65+i*4.19
    box(s,x,2.09,3.73,2.49,PALE,LINE,radius=True)
    box(s,x,2.09,3.73,.13,color)
    text(s,head,x+.22,2.49,3.28,.47,23,INK,True)
    text(s,body,x+.22,3.17,3.27,1.03,15,MID)
    if i<2: text(s,"→",x+3.78,3.07,.28,.39,24,BLUE,True)
box(s,.65,5.12,12.07,.83,RGBColor(229,242,248),radius=True)
text(s,"ZenoBench uses these generated objects in a reusable house and turns them into runnable, measurable tasks.",.89,5.34,11.59,.40,17,NAVY,True)
text(s,"Source: HorizonRobotics / EmbodiedGen V2 README",.68,6.43,11.45,.22,10,MID)
note(s, "EmbodiedGen V2 is upstream. It documents text/image-to-3D assets, multi-room scenes and task-driven world composition: https://github.com/HorizonRobotics/EmbodiedGen/blob/master/README.md")

# 3. What is in ZenoBench
s = slide("ZenoBench at a glance", "What I built", "One reusable home, generated task objects, and a suite of executable household goals.")
things=[
    ("Assets", "EmbodiedGen V2 task objects prepared for physical interaction", "media/assets_gallery.jpg", TEAL),
    ("Rooms", "10-room Infinigen house with furniture and articulated storage", "media/scenes/house_topdown.jpg", BLUE),
    ("Tasks", "8 whole-task definitions, plus a 10-task benchmark for an upper-level planner", heat_table, AMBER),
]
for i,(head,body,im,color) in enumerate(things):
    x=.61+i*4.19
    box(s,x,1.94,3.79,4.47,PALE,LINE,radius=True)
    pic(s,im,x+.10,2.04,3.59,2.28,crop=(i!=0))
    box(s,x+.10,4.40,3.59,.08,color)
    text(s,head,x+.22,4.73,3.34,.43,20,INK,True)
    text(s,body,x+.22,5.28,3.31,.81,13.6,MID)
note(s, "The house is an Infinigen layout, and the task objects are EmbodiedGen V2-generated. The repo prepares assets, room interactions, task scenes and scoring. This slide is intentionally a simple inventory, not an implementation pipeline.")

# 4. What it can do
s = slide("What can the robot do here?", "Capabilities", "Zeno Malo can execute connected household actions in the same environment.")
capabilities=[
    ("Move", "Travel between rooms and approach workspaces", "media/scenes/house_topdown.jpg", TEAL),
    ("Handle objects", "Pick, carry, place and sort different object shapes", fruits, BLUE),
    ("Interact", "Open/close storage and operate appliance controls", "tasks/heat_breakfast_combo/check/microwave_framed.png", AMBER),
    ("Complete tasks", "Combine actions toward a goal checked from simulator state", heat_table, GREEN),
]
for i,(head,body,im,color) in enumerate(capabilities):
    x=.61+(i%2)*6.27; y=1.97+(i//2)*2.31
    box(s,x,y,5.94,2.05,PALE,LINE,radius=True)
    pic(s,im,x+.09,y+.09,2.34,1.87,crop=True)
    box(s,x+2.55,y+.31,.07,1.46,color)
    text(s,head,x+2.80,y+.29,2.90,.40,18.2,INK,True)
    text(s,body,x+2.80,y+.81,2.91,.95,12.7,MID)
note(s, "Keep this high-level. These are things the system can demonstrate; do not explain trajectory controllers here. Recorded videos show whole scripted-policy runs and state-based evaluation.")

# Skill library — the planner-visible layer: SkillNode -> Contract -> policy paths.
s = slide("Skill library: 70 verb SkillNodes over low-level policies", "Current capabilities",
          "Each SkillNode is one verb + one noun. Its Contract checks GT preconditions, picks a policy path, then checks GT postconditions.")
layers=[
    ("70 SkillNodes", "What the planner calls\nnavigate · pick · place · expose · push\nopen · heat · uncover · search · wipe ...", TEAL),
    ("70 Contracts", "requires / ensures from 71 GT predicates\nfailure codes + fallback candidates", BLUE),
    ("120 policy paths", "chosen by the noun (book, mug, door ...)\nover 114 low-level policies", AMBER),
]
for i,(h,b,c) in enumerate(layers):
    x=.61+i*4.19
    box(s,x,1.98,3.79,2.62,PALE,LINE,radius=True)
    box(s,x,1.98,3.79,.11,c)
    text(s,h,x+.22,2.30,3.35,.42,21,INK,True)
    text(s,b,x+.22,2.90,3.37,1.50,13.2,MID)
    if i<2: text(s,"→",x+3.83,2.98,.28,.39,24,BLUE,True)
fams=[("Move + body","navigate · approach · face · retreat · crouch · bend"),
      ("Perceive","look · inspect · search · explore · count · measure"),
      ("Manipulate","pick · place · stack · lift · flip · push · expose"),
      ("Appliance + tasks","open · close · press · heat · cover · wipe · collect")]
for i,(h,b) in enumerate(fams):
    x=.61+(i%2)*6.28; y=4.82+(i//2)*.62
    text(s,h,x,y,1.85,.3,12.5,INK,True)
    text(s,b,x+1.85,y,4.3,.3,12,MID)
box(s,.64,6.18,12.00,.52,RGBColor(232,244,248),radius=True)
text(s,"Library regression (35 scenarios, 2026-10-18): 27 pass  ·  8 fail (6 before, 2 also on 15d948e)  ·  0 new",.87,6.31,11.55,.29,14.6,NAVY,True)
note(s, "The planner sees SkillNodes only. A Contract checks GT preconditions before execution, chooses a policy path by noun, and checks GT postconditions afterwards; a failure returns an error code and the measured predicates. Numbers: 70 SkillNodes / 70 Contracts / 120 policy paths over 114 policies (README). Regression on benchmark-v1: 27/35 scenarios pass. 6 failed before at the same step (sort, empty, fridge place, microwave oatmeal place, pour, two-hand box). k_separate and k_restore_swap fail identically on a clean 15d948e, so they are baseline failures, not new ones. Do not say all 70 skills are stable.")

# 5. Suite categories
s = slide("Eight tasks across four household themes", "Task suite", "The same house supports different goals rather than a single scripted demonstration.")
cats=[
    ("Collect", "collect_fruits", "Gather objects into a shared container", TEAL),
    ("Organize", "tidy_toys\nshelve_books", "Put floor toys away; place books on shelves", BLUE),
    ("Prepare", "desk_prep\nbreakfast_setup", "Set up a workspace or a dining table", AMBER),
    ("Appliances", "heat_breakfast_preloaded\nheat_breakfast_combo\nheat_breakfast", "Operate fridge/microwave and serve food", GREEN),
]
for i,(head,names,body,color) in enumerate(cats):
    x=.59+i*3.14
    box(s,x,2.02,2.76,3.93,PALE,LINE,radius=True)
    box(s,x,2.02,2.76,.13,color)
    text(s,head,x+.19,2.42,2.40,.39,20,INK,True)
    text(s,names,x+.19,3.12,2.42,1.17,13.5,color,True)
    text(s,body,x+.19,4.72,2.39,.94,13,MID)
text(s,"Representative rollouts and result JSONs are included in the repository.",.66,6.41,11.98,.32,14,NAVY,True)
note(s, "All eight names come from task_specs. There are five organization/preparation tasks and three appliance tasks. The README includes representative runs; the task list is not a claim of robust success across all seeds.")

# 6. Task examples
s = slide("Task showcase: three different behaviors", "Demo", "Use the recorded videos to show the system acting in the house.")
stories=[
    (fruits,"Collect fruits","Cross rooms; put two fruits into one container",TEAL,"collect_fruits"),
    (toys,"Tidy toys","Pick floor objects and store them",BLUE,"tidy_toys"),
    (books,"Shelve books","Handle flat books and place them on shelves",AMBER,"shelve_books"),
]
for i,(im,h,b,color,video) in enumerate(stories):
    x=.60+i*4.18
    box(s,x,1.99,3.80,4.40,PALE,LINE,radius=True)
    preview=pic(s,im,x+.09,2.08,3.62,2.29)
    preview.click_action.hyperlink.address = f"https://github.com/CMU-Agentic-Library/ZenoBench/blob/main/media/tasks/{video}.mp4"
    box(s,x+.09,4.46,3.62,.08,color)
    text(s,h,x+.23,4.79,3.35,.41,19,INK,True)
    text(s,b,x+.23,5.36,3.34,.73,13.4,MID)
note(s, "If time is limited, play only one clip. These stills come from the recorded collect_fruits, tidy_toys and shelve_books videos. Video paths are listed in SPEAKER_NOTES.md.")

# 7. Hero task
s = slide("One longer example: fridge → microwave → table", "Task demo", "A single goal ties together object handling, appliance use and movement through the home.")
for i,(im,head) in enumerate([(heat_fridge,"Take from fridge"),(heat_microwave,"Heat in microwave"),(heat_table,"Serve at table")]):
    x=.59+i*4.18
    box(s,x,1.99,3.80,3.50,PALE,LINE,radius=True)
    preview=pic(s,im,x+.09,2.08,3.62,2.31)
    preview.click_action.hyperlink.address = "https://github.com/CMU-Agentic-Library/ZenoBench/blob/main/media/tasks/heat_breakfast.mp4"
    text(s,head,x+.21,4.68,3.40,.40,17.5,INK,True)
    if i<2: text(s,"→",x+3.86,3.05,.28,.41,24,BLUE,True)
box(s,.66,5.83,12.01,.58,RGBColor(231,246,238),radius=True)
text(s,"Recorded run: all task goals met; oatmeal served warm, doors closed, no object dropped.",.90,5.99,11.52,.31,15,GREEN,True)
text(s,"One representative rollout; not a multi-seed benchmark result.",.69,6.60,11.92,.25,10.8,MID)
note(s, "The heat_breakfast seed-0 rollout achieved 100% of its four goals. The repo video shows the full sequence. Heating is modeled at task level, not with PhysX thermal simulation. Avoid quoting this as general success rate.")

# Representative whole-task status, without implying multi-seed robustness.
s = slide("What whole tasks run today?", "Task results", "Eight task definitions; results shown are representative recorded rollouts.")
records=[
    ("collect_fruits", "Two fruits into one container", "SUCCESS", GREEN),
    ("tidy_toys", "Floor toys into toy box / basket", "SUCCESS", GREEN),
    ("shelve_books", "Flat books onto a bookcase", "SUCCESS", GREEN),
    ("desk_prep", "Notebook, pen and mug on desk", "SUCCESS", GREEN),
    ("breakfast_setup", "Dining table place setting", "67%", AMBER),
    ("heat_breakfast_preloaded", "Microwave heating from preloaded food", "SUCCESS", GREEN),
    ("heat_breakfast_combo", "Microwave cycle plus chilled milk", "SUCCESS", GREEN),
    ("heat_breakfast", "Fridge → microwave → dining table", "SUCCESS", GREEN),
]
for i,(name,desc,status,color) in enumerate(records):
    col=i//4; row=i%4
    x=.61+col*6.27; y=1.93+row*1.03
    box(s,x,y,5.93,.87,PALE,LINE,radius=True)
    box(s,x,y,.075,.87,color)
    text(s,name,x+.19,y+.14,3.48,.28,13.6,INK,True)
    text(s,desc,x+.19,y+.47,4.65,.25,11.2,MID)
    box(s,x+4.83,y+.18,.89,.36,RGBColor(230,245,236) if status=="SUCCESS" else RGBColor(252,239,216),radius=True)
    text(s,status,x+4.90,y+.28,.76,.20,9.4,color,True,align=PP_ALIGN.CENTER)
box(s,.66,6.23,12.00,.51,RGBColor(236,246,250),radius=True)
text(s,"7 successful representative runs; breakfast_setup remains partial after a mug drop.",.90,6.38,11.49,.27,14.5,NAVY,True)
note(s, "These are recorded examples, not a statistical benchmark result. The repo has six successful videos in the main task table, a separate successful preloaded microwave smoke run, and one partial breakfast_setup run at 67% after a mug drop. The full heat_breakfast task has a seed-0 successful rollout.")

# 8. Why useful
s = slide("Why this matters for our setting", "Research value", "These tasks give an upper-level planner a meaningful environment to reason, act and recover in.")
for i,(head,body,color) in enumerate([
    ("Plan", "Choose a sequence of skills for a household goal", TEAL),
    ("Ground", "Bind each skill to objects, rooms and executable actions", BLUE),
    ("Verify & replan", "Observe the outcome, detect failure and revise the next step", AMBER),
]):
    x=.61+i*4.18
    box(s,x,2.13,3.79,3.35,PALE,LINE,radius=True)
    box(s,x,2.13,3.79,.13,color)
    text(s,f"0{i+1}",x+.22,2.48,.57,.40,19,color,True)
    text(s,head,x+.22,3.12,3.30,.49,22,INK,True)
    text(s,body,x+.22,3.80,3.31,1.18,15,MID)
text(s,"The planning benchmark (next slides) turns this into a measured test of the upper layer.",.68,6.02,11.98,.53,18,NAVY,True)
note(s, "Transition to the planning benchmark. The task suite above shows what the skills can do; the benchmark asks whether a planner picks the right skills when things go wrong.")

# ---------------- Planning benchmark ----------------
s = slide("Planning benchmark: does the planner recover from what it sees?", "Planning benchmark",
          "10 household tasks where the obvious plan fails or is unavailable. Same skills and same limits for every planner.", dark=True)
for i,(head,body,color) in enumerate([
    ("Same low-level skills", "All planners call the same 70 SkillNodes; no new policy, no hidden retries (auto-recovery off)", TEAL),
    ("Limited observation", "First-person image, objects seen so far, known places, robot state, last feedback. No GT state", BLUE),
    ("GT verifier decides", "Isaac Sim state after the run settles: goal atoms hold, nothing on the floor", AMBER),
]):
    x=.61+i*4.18
    box(s,x,2.15,3.79,3.20,RGBColor(27,52,78),RGBColor(64,88,112),radius=True)
    box(s,x,2.15,3.79,.12,color)
    text(s,head,x+.24,2.55,3.30,.45,20,WHITE,True)
    text(s,body,x+.24,3.20,3.30,1.80,14.5,RGBColor(196,212,228))
text(s,"Question: does the planner choose an effective fallback or alternative from its own observation and execution feedback?",
     .66,5.80,12.0,.7,17,AMBER,True)
note(s, "Built on benchmark-v1. No new skills or policies: a planner differs only in which calls it makes. The observation is LimitedSession.observe(); the planner never sees GT. Success is decided from Isaac Sim GT, 60 ticks after the last call.")

# Observation boundary and gate
s = slide("What the planner sees, and what it may call", "Observation boundary",
          "A call naming an object the robot has not observed is refused before anything moves.")
box(s,.61,1.98,5.95,4.45,PALE,LINE,radius=True); box(s,.61,1.98,.09,4.45,TEAL)
text(s,"Planner input",.86,2.18,5.4,.4,19,INK,True)
text(s,"• first-person camera image\n• objects observed so far (observation cache)\n• known places and receptacles\n• robot pose, room, what each hand holds\n• temperatures the robot has measured\n• feedback of the last call: success, error code, message",
     .86,2.75,5.5,3.4,14.2,MID)
box(s,6.78,1.98,5.95,4.45,PALE,LINE,radius=True); box(s,6.78,1.98,.09,4.45,AMBER)
text(s,"Gate and feedback classes",7.03,2.18,5.4,.4,19,INK,True)
text(s,"• Grounding: NOT_OBSERVED · NOT_IN_VIEW · NOT_FOUND\n   (an object that is not in the episode gets the same refusal)\n• Precondition: PRECONDITION_FAILED · NO_PATH\n   (nothing was executed)\n• Execution: POLICY_FAILED · SUBSKILL_FAILED · POSTCONDITION_FAILED\n   (the robot tried; the physics said no)",
     7.03,2.75,5.55,3.4,14.2,MID)
note(s, "The gate keeps the planner honest: it cannot act on an object it never saw, so search/explore are real decisions. Planner interface: reset(task_instruction, skills) and next_call(observation) -> {skill, args} or None. None ends the episode (planner_done); max_calls ends it with budget; an exception makes it incomplete.")

# Ten tasks x three tiers
s = slide("Ten tasks, three difficulty tiers", "Task design",
          "The instruction never changes across tiers; only the scene does. Medium adds one condition, hard adds a second.")
rows=[
    ("T01","Paperback → dining table","no overhang: pick fails → expose → pick","fallback"),
    ("T02","Stack two blocks","boxed in: pick fails → separate / push → pick","fallback"),
    ("T03","Pin + spoon in one container","pin does not fit the mug → storage bin","alternative"),
    ("T04","Cup (or mug) on wall cabinet","no cup: count 0, search fails → mug","alternative"),
    ("T05","Pen (or pencil) to the desk","no pen → pencil (no easy tier)","alternative"),
    ("T06","Block on display","cabinet top full: place fails → TV stand","alternative"),
    ("T07","Warm oatmeal ≥ 40 °C","microwave does not heat → stove","alternative"),
    ("T08","Wipe the island","sponge elsewhere → fetch, approach, wipe","search"),
    ("T09","Tomato soup","lid on: collect refused → uncover → collect","fallback"),
    ("T10","Can into the trash","can not observed: pick refused → search","fallback"),
]
kc={"fallback":TEAL,"alternative":AMBER,"search":BLUE}
for i,(tid,goal,cond,kind) in enumerate(rows):
    col=i//5; r=i%5
    x=.61+col*6.27; y=1.98+r*.86
    box(s,x,y,5.93,.76,PALE,LINE,radius=True)
    box(s,x,y,.075,.76,kc[kind])
    text(s,tid,x+.18,y+.12,.6,.28,13.5,kc[kind],True)
    text(s,goal,x+.78,y+.10,3.6,.28,13.2,INK,True)
    text(s,cond,x+.78,y+.42,4.95,.26,10.8,MID)
    box(s,x+4.62,y+.11,1.15,.27,WHITE,LINE,radius=True)
    text(s,kind,x+4.64,y+.14,1.11,.2,9,kc[kind],True,align=PP_ALIGN.CENTER)
text(s,"Fallback: a real failure, an auxiliary skill repairs the state, the same action is retried.   Alternative: another object, skill or destination reaches the same goal.   29 task × tier combinations + 21 single-skill probes.",
     .63,6.35,12.1,.6,11,MID)
note(s, "Medium = the fallback or alternative condition holds. Hard = that condition plus a second one, e.g. starting in another room or facing away. T05 has no easy tier because the pen slips out of the hand 4/4; its pen route is diagnostic. Probes P01-P22 (21, no P10) cover SkillNodes that do not fit the ten tasks.")

# Worked example: T01 fallback
s = slide("Example: T01 fallback, seen from the robot", "Task demo",
          "Medium tier: the book lies flat, with no overhang to pinch. Frames from the head camera after each call.")
steps=[
    (FRAMES/"bench_t01_navigate.jpg","navigate","book flat on the island",BLUE),
    (FRAMES/"bench_t01_pick_fail.jpg","pick → POLICY_FAILED","edge pinch: not held (lift 0.000 m)",RED),
    (FRAMES/"bench_t01_expose.jpg","expose","slide the book over the edge",AMBER),
    (FRAMES/"bench_t01_place.jpg","pick → navigate → place","book on the dining table",GREEN),
]
for i,(im,h,b,c) in enumerate(steps):
    x=.58+i*3.15
    box(s,x,1.98,2.92,3.48,PALE,LINE,radius=True)
    pic(s,str(Path(im).relative_to(ROOT)),x+.08,2.06,2.76,2.07)
    box(s,x+.08,4.20,2.76,.07,c)
    text(s,h,x+.18,4.42,2.62,.36,14,INK,True)
    text(s,b,x+.18,4.86,2.62,.5,11.5,MID)
    if i<3: text(s,"→",x+2.93,2.85,.25,.39,20,BLUE,True)
box(s,.64,5.80,12.04,.6,RGBColor(231,246,238),radius=True)
text(s,"Retest on current code: nominal 2/2 · fallback_expose 2/2 · hard 1/2 (seed 1: the book slips during place)",.88,5.95,11.6,.31,14.5,GREEN,True)
text(s,"fixed (nominal plan once) stops after the failed pick; the book stays on the island.",.66,6.62,11.9,.25,10.8,MID)
note(s, "Real images from benchmark/runs/retest (seed 0). The pick failure is a real physics failure, not injected: without an overhang the edge pinch cannot close on the book. The planner has to read the feedback and choose expose. The hard tier starts in the dining room, so it must search first.")

# More recoveries
s = slide("Other recoveries in the suite", "Task demo", "Each one starts with a real refusal or failure that the planner has to read.")
ex=[
    (FRAMES/"bench_t02_pick_fail.jpg","T02 · pick fails → push","Block boxed in by a bowl and the rolling pin; push it free, pick again, stack",TEAL),
    (FRAMES/"bench_t09_uncover.jpg","T09 · collect refused → uncover","The pot lid is on; uncover, then collect the tomatoes, stir, cover, heat",BLUE),
    (FRAMES/"bench_t07_stove.jpg","T07 · heat fails → stove","The microwave does not heat; stop it, take the oatmeal out, use the stove",AMBER),
]
for i,(im,h,b,c) in enumerate(ex):
    x=.60+i*4.18
    box(s,x,1.99,3.80,4.40,PALE,LINE,radius=True)
    pic(s,str(Path(im).relative_to(ROOT)),x+.09,2.08,3.62,2.53)
    box(s,x+.09,4.70,3.62,.08,c)
    text(s,h,x+.23,4.95,3.35,.4,16,INK,True)
    text(s,b,x+.23,5.47,3.34,.8,12.6,MID)
note(s, "Head-camera frames from the declared scripted routes in benchmark/runs/final (seed 0). T02 and T09 are fallbacks (repair, then the same action); T07 is an alternative (another appliance).")

# Evaluation protocol
s = slide("How a planner is scored", "Evaluation",
          "Task success and skill success are reported separately. Crashed runs are 'incomplete', never a success or a failure.")
planners=[("fixed","nominal plan once",MID),("retry","repeat a failed call ≤ 2×",MID),
          ("VLM (recovery)","closed loop, ≤ max_calls",TEAL),("oracle","GT route, upper bound",AMBER)]
for i,(h,b,c) in enumerate(planners):
    x=.61+i*3.14
    box(s,x,1.98,2.88,1.05,PALE,LINE,radius=True); box(s,x,1.98,2.88,.08,c)
    text(s,h,x+.2,2.16,2.5,.35,16,INK,True)
    text(s,b,x+.2,2.56,2.5,.3,12,MID)
metrics=[("SR","Task Success: every GT goal atom holds, nothing dropped"),
         ("skill_SR / GC","Successful calls / calls; share of goal atoms reached"),
         ("SPL-c","Success weighted by calls vs. the verified oracle route; N/A if that route never passed"),
         ("recov_gate / pre / exec","Of episodes with that failure class, the share that still succeeded (denominator shown)"),
         ("repeat","Share of failures followed by the identical call (blind retry)")]
for i,(h,b) in enumerate(metrics):
    y=3.32+i*.5
    text(s,h,.66,y,2.75,.3,13.5,BLUE,True)
    text(s,b,3.45,y,9.2,.3,13,MID)
box(s,.64,5.95,12.04,.62,RGBColor(232,244,248),radius=True)
text(s,"Eval grid: 29 task × tier combinations × 2 seeds = 58 episodes per planner (174 for the three baselines)",.88,6.11,11.6,.31,14.5,NAVY,True)
note(s, "fixed, retry and the VLM share the gate, low-level settings and budget, so they are comparable. The oracle uses full GT state and nested repair, so it is an upper bound and reported separately; the fixed-oracle gap is not a VLM gain. Empty denominators show N/A, not 0%. The eval grid is defined in benchmark/batches/eval.json and has not been run yet.")

# Current status
s = slide("Where it stands", "Status · 2026-10-18",
          "Route evidence shows the tasks are physically solvable with the existing skills. Planner numbers come later.")
stats=[("59 / 62","declared route episodes pass","27 stable · 3 flaky routes",GREEN),
       ("9 / 10","tasks solved by the oracle","fixed 2 / 10 · retry 2 / 10",BLUE),
       ("65 / 70","SkillNodes succeeded in a real call","4 called but failed · 1 never called",AMBER),
       ("14 / 21","single-skill probes pass","brace, pour, empty, swap ... fail",RED)]
for i,(n,h,b,c) in enumerate(stats):
    x=.61+i*3.14
    box(s,x,1.98,2.88,2.55,PALE,LINE,radius=True); box(s,x,1.98,2.88,.1,c)
    text(s,n,x+.22,2.30,2.5,.6,30,c,True)
    text(s,h,x+.22,3.08,2.5,.6,13.5,INK,True)
    text(s,b,x+.22,3.80,2.5,.6,11.5,MID)
text(s,"Checked this round",.66,4.82,6,.33,15,INK,True)
text(s,"• Edge-pinch regression fixed (opt-in flag); g_expose_then_pick_book 3/3\n• Result fields checked live: normal, recovered, failure exit, budget exit, crash → incomplete",
     .66,5.18,6.1,1.2,12.3,MID)
text(s,"Not done yet",6.95,4.82,5.6,.33,15,INK,True)
text(s,"• No real VLM connected yet (interface tested with test planners)\n• 174-episode eval grid not run; baselines are 1 seed per task",
     6.95,5.18,5.75,1.2,12.3,MID)
note(s, "Route episodes are scripted replays of the declared routes: feasibility evidence, not planner results. Flaky: T01 hard (book slips on seed 1) and the two T02 separate routes. Baseline numbers are from one episode per task, mostly medium. 105 of 113 route episodes ran on 15d948e+dc4ae8f; only T01 was rerun on the current code.")

# Next steps
s = slide("Next steps", "Plan")
for i,(head,body,color) in enumerate([
    ("1 · Connect a VLM", "3–4 stable tasks (T01, T03, T08, T10), easy + medium: check that it reads the feedback and the gate", TEAL),
    ("2 · Rerun all routes", "on the current code, so every route has fresh evidence", BLUE),
    ("3 · Fix flaky routes", "T01 hard, T02 separate: adjust the local layout first; otherwise mark diagnostic", AMBER),
    ("4 · Run the eval grid", "fixed / retry / oracle + VLM, 58 episodes each: the first comparable numbers", GREEN),
]):
    x=.61+i*3.14
    box(s,x,1.98,2.88,2.75,PALE,LINE,radius=True); box(s,x,1.98,2.88,.12,color)
    text(s,head,x+.22,2.36,2.5,.75,17,INK,True)
    text(s,body,x+.22,3.05,2.5,1.5,13.5,MID)
text(s,"Lower priority: k_separate / k_restore_swap, which already fail on 15d948e.",.66,5.15,12,.3,13,MID)
note(s, "Order matters: connecting a real VLM is most likely to expose interface issues, so it comes before the expensive grid.")

# Upper-level handoff: the two supplied architecture figures are reconstructed
# at full resolution in presentations/figures/ and inserted as standalone slides.
for figure, note_text in [
    ("presentations/figures/upper_figure_1_skill_graph.png",
     "Handoff to the upper-layer presenter: Figure 1 shows one Skill Subgraph per subgoal, validation, execution, verification and replanning."),
    ("presentations/figures/upper_figure_2_skill_library.png",
     "Handoff to the upper-layer presenter: Figure 2 shows public SkillNodes, per-skill Contracts, the invocation adapter and heterogeneous low-level policies."),
]:
    s = PPT.slides.add_slide(BLANK)
    box(s,0,0,13.333,7.5,WHITE)
    pic(s,figure,0,0,13.333,7.5,crop=False)
    note(s,note_text)

for tb, n in FOOTERS:
    p = tb.text_frame.paragraphs[0]
    p.text = f"{n:02d} / {len(PPT.slides)}"
    p.font.name = "Aptos"; p.font.size = Pt(8.5); p.font.color.rgb = MID
    p.alignment = PP_ALIGN.RIGHT

PPT.core_properties.title = "ZenoBench: Generated Worlds to Household Tasks"
PPT.core_properties.subject = "Group meeting overview: skill library, task demos, planning benchmark and upper-level handoff"
PPT.core_properties.keywords = "ZenoBench; EmbodiedGen V2; SkillNode; planning benchmark; Skill Graph"
PPT.save(DEST)
print(DEST)
print(f"slides={len(PPT.slides)}")
