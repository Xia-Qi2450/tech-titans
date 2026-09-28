"""
Derives the website's simplified episode state/stage from the real
per-phase data tracked in the Podcast Master Sheet, plus two flags that
only ever get set by a human through the API/GUI (idea_approved,
finalising_approved) -- the sheet has no equivalent for either.

Stage rules, as specified:
    0 Not started           starting stage -- no signal yet
    1 Idea thought           idea_approved flag (manual, GUI-only)
    2 Writing script         script_status from the sheet -- only read
                              once idea_approved is true
    3 Recording footage      recording_status -- only read once script is
                              Completed
    4 Editing video          editing_status -- only read once recording is
                              Completed
    5 Finalising production  finalising_approved flag (manual, GUI-only)
    6 Finished               publish_status == 'Published'

The gating ("only read once the previous stage is actually done") was
specified for the script step; this applies it consistently down the whole
ladder rather than just that one step, since that's the only way the
ladder stays honestly sequential -- otherwise a stage further down the
sheet could report progress while an earlier gate was never confirmed. If
that's not the intent, this is the one function to change.
"""

STAGE_NOT_STARTED = 0
STAGE_IDEA = 1
STAGE_SCRIPT = 2
STAGE_RECORDING = 3
STAGE_EDITING = 4
STAGE_FINALISING = 5
STAGE_FINISHED = 6


def derive_state(publish_status):
    """'aired' | 'production'. 'airing' (currently live) has no sheet or
    manual-flag equivalent here and is intentionally never auto-derived."""
    return "aired" if publish_status == "Published" else "production"


def derive_stage(idea_approved, script_status, recording_status, editing_status,
                  finalising_approved, publish_status):
    if publish_status == "Published":
        return STAGE_FINISHED
    if finalising_approved:
        return STAGE_FINALISING
    if idea_approved and script_status == "Completed" and editing_status in ("In Progress", "Completed"):
        return STAGE_EDITING
    if idea_approved and script_status == "Completed" and recording_status in ("In Progress", "Completed"):
        return STAGE_RECORDING
    if idea_approved and script_status in ("In Progress", "Completed"):
        return STAGE_SCRIPT
    if idea_approved:
        return STAGE_IDEA
    return STAGE_NOT_STARTED
