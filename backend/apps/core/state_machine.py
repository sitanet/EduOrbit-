import logging

logger = logging.getLogger("eduorbit.core.state_machine")

class InvalidStateTransitionError(ValueError):
    pass

class StateMachine:
    """
    Generic declaratively-configured State Machine to validate and transition states
    across system entities (e.g., student lifecycle, admissions stages).
    """
    def __init__(self, transitions: dict, initial_state: str):
        self.transitions = transitions
        self.initial_state = initial_state

    def validate_transition(self, current_state: str, next_state: str) -> bool:
        if current_state == next_state:
            return True
        allowed_transitions = self.transitions.get(current_state, [])
        return next_state in allowed_transitions

    def transition(self, current_state: str, next_state: str) -> str:
        if not self.validate_transition(current_state, next_state):
            logger.warning(f"Illegal state transition attempted: {current_state} -> {next_state}")
            raise InvalidStateTransitionError(f"Illegal state transition: {current_state} -> {next_state}")
        return next_state
