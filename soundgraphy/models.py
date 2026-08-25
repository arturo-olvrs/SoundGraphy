from enum import Enum
import numpy as np


class PAQ(Enum):
    """Enumeration of Perceptual Attribute Questions (PAQ) names and IDs."""
    PLEASANT = ("pleasant", "PAQ1")
    VIBRANT = ("vibrant", "PAQ2")
    EVENTFUL = ("eventful", "PAQ3")
    CHAOTIC = ("chaotic", "PAQ4")
    ANNOYING = ("annoying", "PAQ5")
    MONOTONOUS = ("monotonous", "PAQ6")
    UNEVENTFUL = ("uneventful", "PAQ7")
    CALM = ("calm", "PAQ8")

    def __init__(self, label: str, id: str):
        self.label = label
        self.id = id

PAQ_NAME_TO_ID = {paq.name.capitalize(): paq.id for paq in PAQ}
"""dict[str, str]: Mapping from PAQ names (e.g., 'Pleasant') to their corresponding IDs (e.g., 'PAQ1')."""

PAQ_DICT_REVERT = {paq.id: paq.label for paq in PAQ}
"""dict[str, str]: Mapping to revert PAQ IDs (e.g., 'PAQ1') back to their corresponding labels (e.g., 'pleasant')."""


def ssm_model(theta: float | np.ndarray, amp: float, dis: float, elev: float) -> float | np.ndarray:
    """Calculate the circumplex Soundscape Standard Model (SSM) cosine fitting value.

    Args:
        theta (float | np.ndarray): Angle in degrees along the circumplex plane.
        amp (float): Amplitude of the fitted wave.
        dis (float): Angular displacement/offset in degrees.
        elev (float): Elevation/vertical offset.

    Returns:
        float | np.ndarray: Fitted value(s) corresponding to the input angle(s).
    """
    return elev + amp * np.cos(np.radians(theta - dis))