"""Code voxel: heartbeat attached to V(2,2,4) (orchestrator home).

on_pulse(ctx) is called by the pulse engine whenever the wavefront re-pulses
this voxel and code_every ticks have passed. It stamps a heartbeat line so we
can prove, from disk, that code living inside a voxel actually executes.
"""
import os, time
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pulse_heartbeat.log")

def on_pulse(ctx):
    st = ctx["state"]
    line = ("tick=%d %s cells=%d hops=%d\n" % (
        ctx["tick"], time.strftime("%H:%M:%S"),
        st.get("stats", {}).get("cells", -1), len(st.get("last_hops", []))))
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line)
    return "hb"
