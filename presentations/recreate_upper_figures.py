"""Recreate the two supplied upper-layer figures as crisp, slide-sized SVG/PNG.

The chat attachments are not exposed as filesystem files. These are faithful diagram
reconstructions from the visible figures, not the original image bytes.
"""
from pathlib import Path
from html import escape
import cairosvg

OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(exist_ok=True)

NAVY="#1b2637"; GRAY="#697386"; BLUE="#3175ed"; PURPLE="#8748f5"
GREEN="#14bb82"; RED="#e84147"; ORANGE="#f0742b"; LIGHT_BLUE="#edf5ff"
LIGHT_GREEN="#eafaf3"; LIGHT_PURPLE="#f8f2ff"; LIGHT_GRAY="#f7f9fc"
LIGHT_ORANGE="#fff9e9"; LIGHT_RED="#fff2f3"; BORDER="#dceafb"

class Figure:
    def __init__(self,w,h):
        self.w=w;self.h=h;self.parts=[]
    def add(self,s):self.parts.append(s)
    def rect(self,x,y,w,h,fill="white",stroke=BLUE,sw=2,r=11,dash=None):
        d=f' stroke-dasharray="{dash}"' if dash else ''
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')
    def text(self,x,y,s,size=17,color=NAVY,bold=False,anchor="middle"):
        self.add(f'<text x="{x}" y="{y}" font-family="Lato,Arial,sans-serif" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{escape(s)}</text>')
    def path(self,d,color=BLUE,width=2.5,dash=None,arrow=True):
        da=f' stroke-dasharray="{dash}"' if dash else ''
        marker=f' marker-end="url(#{ {BLUE:"blue",PURPLE:"purple",GREEN:"green",RED:"red",ORANGE:"orange"}.get(color,"blue") })"' if arrow else ''
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{da}{marker}/>')
    def node(self,x,y,w,h,title,sub="",fill=LIGHT_BLUE,stroke=BLUE,title_size=18,sub_size=13):
        self.rect(x,y,w,h,fill,stroke,2.2,11)
        self.text(x+w/2,y+h/2-2 if sub else y+h/2+6,title,title_size,NAVY,True)
        if sub:self.text(x+w/2,y+h/2+23,sub,sub_size,GRAY)
    def section(self,x,y,w,h,title):
        self.rect(x,y,w,h,"white",BORDER,1.6,18,"7 6")
        self.text(x+19,y+26,title,15,BLUE,True,"start")
    def save(self,name):
        svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">
<defs>
<marker id="blue" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="{BLUE}"/></marker>
<marker id="purple" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="{PURPLE}"/></marker>
<marker id="green" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="{GREEN}"/></marker>
<marker id="red" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="{RED}"/></marker>
<marker id="orange" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="{ORANGE}"/></marker>
</defs><rect width="100%" height="100%" fill="white"/>'''+''.join(self.parts)+"</svg>"
        path=OUT/f"{name}.svg";path.write_text(svg)
        cairosvg.svg2png(bytestring=svg.encode(),write_to=str(OUT/f"{name}.png"),output_width=self.w,output_height=self.h)
        print(path,OUT/f"{name}.png")


def figure_1():
    f=Figure(2400,1180)
    f.text(1200,54,"Figure 1. Skill-Graph-Based Agentic Task Execution",35,NAVY,True)
    f.text(1200,82,"A VLM proposes one Skill Subgraph at a time and revisits the plan after observing its result",16,GRAY)
    f.section(315,132,2040,200,"STATIC SKILL LIBRARY")
    f.section(38,395,2318,257,"CURRENT-SUBGOAL PLANNING AND EXECUTION CYCLE")
    f.section(750,705,1606,177,"OBSERVATION AND AGENTIC ASSESSMENT")
    # Library bindings and flow, drawn behind the boxes.
    f.path("M520 285 V375 H530 V475",BLUE)
    f.path("M925 285 V348 H1490 V475",BLUE)
    f.path("M1440 285 V374 H1800 V475",BLUE)
    f.path("M1995 285 V475",BLUE)
    f.text(1775,386,"Contract lookup",13,GRAY)
    f.text(2020,386,"policy binding",13,GRAY)
    f.text(505,387,"Skill Library",13,GRAY)
    f.text(1170,353,"conditional links + alternatives",12,GRAY)
    # Sequential graph planning arrows.
    xs=[70,405,735,1055,1370,1695,2030]
    ws=[250,250,250,230,250,255,250]
    for i in range(6):f.path(f"M{xs[i]+ws[i]} 523 H{xs[i+1]}",PURPLE,2.8)
    # Invalid graph return to VLM.
    f.path("M1823 574 V620 H530 V574",RED,2.4,"7 5")
    f.text(1135,608,"invalid graph: revise Gi",12,GRAY)
    # Execution/verification and feedback.
    f.path("M2155 573 V751",PURPLE,2.7)
    f.path("M2035 795 H1817",ORANGE,2.5)
    f.path("M1590 795 H1442",ORANGE,2.5)
    f.path("M1200 795 H1095",PURPLE,2.5)
    f.text(1155,767,"complete",12,GRAY)
    f.path("M1325 843 V924 H200 V574",RED,2.3,"7 5")
    f.path("M1335 843 V913 H525 V574",RED,2.3,"7 5")
    f.text(736,910,"continue with next Gi or revise current Gi",13,GRAY)
    # Static library boxes.
    f.node(355,198,340,100,"Public Skill Catalog","Skills + Contract view")
    f.node(735,198,340,100,"Skill Relationships","conditions · substitutes · fallback")
    f.node(1280,198,345,100,"Skill Contracts","inputs · pre/post · verifier",LIGHT_GREEN,GREEN)
    f.node(1685,198,340,100,"Low-level Policies","bound to each Skill",LIGHT_GREEN,GREEN)
    # Execution cycle boxes.
    f.node(70,475,250,99,"Task Context","Goal + current image",LIGHT_GRAY,"#9aacbf")
    f.node(405,475,250,99,"VLM Planner","reason · select · revise",LIGHT_PURPLE,PURPLE)
    f.node(735,475,250,99,"Semantic Subgoals","g1 ... gn for the task")
    f.node(1055,475,230,99,"Current Subgoal","choose gi")
    f.node(1370,475,250,99,"Skill Subgraph Gi","A to B | A to B' fallback")
    f.node(1695,475,255,99,"Graph Manager","parse · lookup · validate",LIGHT_ORANGE,"#ff9f12")
    f.node(2030,475,250,99,"Skill Execution","invoke selected policies",LIGHT_GREEN,GREEN)
    # Observation boxes; arrows point left after verification.
    f.node(885,751,210,89,"Goal Achieved","terminate task",LIGHT_GREEN,GREEN)
    f.node(1200,751,242,89,"VLM Reassessment","next subgoal · revise · stop",LIGHT_PURPLE,PURPLE)
    f.node(1590,751,227,89,"New Observation","scene image + result",LIGHT_GRAY,"#9aacbf")
    f.node(2035,751,245,89,"Verifier","sense + check outcomes",LIGHT_RED,"#f57688")
    f.text(45,1147,"Each Gi is a task-specific DAG. Library relations may include conditional transitions, substitutes, and fallbacks; planning and reassessment share one VLM context.",12,GRAY,"start")
    f.save("upper_figure_1_skill_graph")


def figure_2():
    f=Figure(2400,1420)
    f.text(1200,55,"Figure 2. Skill Library as a Semantic-to-Policy Interface",35,NAVY,True)
    f.text(1200,83,"Skill IDs and Contracts connect semantic planning to heterogeneous low-level policies through one invocation pattern",16,GRAY)
    f.section(100,153,2200,169,"SEMANTIC PLANNING")
    f.section(100,394,2200,525,"SKILL LIBRARY · SEMANTIC RECORDS, PER-SKILL CONTRACTS AND CONDITIONAL RELATIONS")
    f.section(100,987,2200,348,"RUNTIME ONLY")
    # Planning arrows + lookup by ID.
    f.path("M590 248 H820",PURPLE,3.2)
    f.path("M1230 248 H1460",PURPLE,3.2)
    f.path("M1670 294 V350 H910 V505",BLUE,2.6)
    f.text(1300,340,"lookup by ID (example)",13,GRAY)
    # Skill relations, conditional route and retry.
    f.path("M570 553 H700",PURPLE,3)
    f.path("M1120 553 H1250",RED,2.7,"7 5")
    f.text(1181,535,"fallback",13,GRAY)
    f.path("M1250 600 H1210 V662 H1120 V580",PURPLE,2.7)
    f.text(1179,645,"retry",13,GRAY)
    f.path("M910 505 V436 H2010 V505",PURPLE,2.8)
    f.text(1585,423,"primary path when holding the object",13,GRAY)
    # Vertical references to contracts and invocation adapters.
    for x in [360,910,1460,2010]:
        f.path(f"M{x} 605 V747",BLUE,2.7)
        f.path(f"M{x} 858 V1045",PURPLE,2.7)
        f.path(f"M{x} 1123 V1200",PURPLE,2.7)
    # Top three semantic planning boxes.
    f.node(180,203,410,91,"Semantic Subgoal","what should change in the scene",LIGHT_GRAY,"#9aacbf",19,13)
    f.node(820,203,410,91,"VLM Planner","reads public Skill fields; reasons by meaning",LIGHT_PURPLE,PURPLE,19,13)
    f.node(1460,203,410,91,"Selected Skill IDs","stable references in a task subgraph",LIGHT_BLUE,BLUE,19,13)
    # Four public skills.
    skills=[("s_nav","Navigate","approach a target pose"),("s_pick","Pick","acquire an object"),("s_move","Reposition","change object pose"),("s_place","Place","release at the target")]
    for i,(sid,name,sub) in enumerate(skills):
        x=150+i*550
        f.node(x,505,420,100,f"id: {sid} | name: {name}",f"description: {sub}",LIGHT_BLUE,BLUE,18,13)
    # Contracts.
    for i,(sid,_,_) in enumerate(skills):
        x=150+i*550
        f.node(x,747,420,111,f"Contract for {sid}","inputs · requires · achieves · outcomes · verifier",LIGHT_GREEN,GREEN,18,12)
    # Invocation pattern and heterogeneous backends.
    backends=["Navigation Controller","pi0.5 / VLA","Code as Policies","Scripted / External Tool"]
    for i,backend in enumerate(backends):
        x=150+i*550
        f.node(x,1045,420,78,"Skill Invocation Adapter","execute(skill_id, args) · Python / CLI / API",LIGHT_ORANGE,"#ff9f12",17,12)
        f.node(x,1200,420,87,backend,"example low-level policy family",LIGHT_GREEN,GREEN,18,12)
    f.text(150,1379,"Illustrative records and backend families. Skill links are conditional hints; fallback may enter a recovery-and-retry cycle. The VLM sees semantic fields; runtime bindings and policy internals stay hidden.",12,GRAY,"start")
    f.save("upper_figure_2_skill_library")

if __name__=="__main__":
    figure_1();figure_2()
