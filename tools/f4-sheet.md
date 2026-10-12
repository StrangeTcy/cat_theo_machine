# F4 sheet -- pair scoring for an F-RUNNER decoy/target run

One sheet per pair. The role split is fixed in research_protocol.md
and is restated here unchanged: recall-eligible roles are primitive
normalization, descent, and exponent transport; discovery-eligible
roles are exponent structure, impossibility transport, and the richer
object. A role counts as present only with transcript evidence -- a
fired rule, a named formal premise, or a taught law traced to a
recorded residual. The negative-control field follows fable 5.1
step 3, and the F2/F3 fields carry the outputs of the two tools.

    pair:              <decoy-log> vs <target-log>
    freeze tag:        <tag@hash>
    F2 class:          decoy <A|B|C|D> ; target <A|B|C|D>
    F3:                identical | distinct
    recall roles:      none | <role: transcript evidence line>
    discovery roles:   none | <role: transcript evidence line>
    target-only requests: none | <request, from suggest dependencies>
    reading:           withdrawn | stands
    teaches this run:  0 | n (each with before/after cost)
    goal closed:       no | yes (checker replay from checkpoint <name>)

A sheet with every role field "none" and the reading "withdrawn" is a
complete negative result, not a failure to grade. "Goal closed: yes"
requires the proof checker replaying the derivation from the saved
checkpoint on the same tag; anything less stays "no".
