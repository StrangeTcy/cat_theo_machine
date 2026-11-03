"""Wire constants shared by the tap and the viewer, with no kernel import.

Kept in its own module so the visualiser server can agree with the observed
process on a format version without importing ``cat_theo_machine`` at all.
"""

#: Version of the event vocabulary written to a journal and a session file.
EVENT_VERSION = 1

#: File names the two sides agree on.
JOURNAL_NAME = "observed.jsonl"
SESSION_FORMAT = "ctm-visualiser-session"
SESSION_VERSION = 1
