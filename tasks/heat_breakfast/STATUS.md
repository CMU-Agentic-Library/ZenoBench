# Breakfast transfer task status

The final microwave has a complete shell and a powered door. The refrigerator,
microwave, and task scenes pass physics checks. The complete task of taking
chilled oatmeal from the refrigerator, loading it into the microwave, heating
it, and serving it at the table has **not** passed.

Earlier exploratory runs used a prototype with an open right side. They showed
a refrigerator bowl grasp and carry, but the bowl stalled about 6.5 cm short
of the microwave floor. Those runs do not establish a valid loading route for
the current shell. The current generic handle-pull skill also cannot open the
complete-shell microwave; this task needs to use the powered door and a new
front-loading trajectory before it can be reported as successful.

Run the experimental task with:

```bash
$ISAACLAB_PYTHON tools/run_task.py --task heat_breakfast --no-video
```

The validated `heat_breakfast_combo` task starts with oatmeal already inside
the microwave. It presses the blue door button, opens and closes the physical
door, presses the green start button, heats the oatmeal, and brings chilled
milk from the refrigerator to the dining table. Its recorded result is
[`media/tasks/heat_breakfast_combo.result.json`](../../media/tasks/heat_breakfast_combo.result.json).
