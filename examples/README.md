# Example Datasets

This folder contains sample datasets (`Example_1stop.xlsx` and `Example_4stops.xlsx`) formatted according to the ISO 12913-3 standard for demonstration and testing in SoundGraphy.

---

### Dataset Structure & Column Descriptions

| Column | Description | Details / Mapping |
| :--- | :--- | :--- |
| **N** | Respondent / Series ID | Unique identifier for each data record |
| **STOP** | Evaluation Location | Categorical location index (1 location in `Example_1stop`, 4 in `Example_4stops`) |
| **AGE** | Respondent Age | Age in years (fictitious) |
| **Q2.1** | Perceptual Attribute (PA) | **Pleasant** ($p$) |
| **Q2.2** | Perceptual Attribute (PA) | **Chaotic** ($ch$) |
| **Q2.3** | Perceptual Attribute (PA) | **Vibrant** ($v$) |
| **Q2.4** | Perceptual Attribute (PA) | **Uneventful** ($u$) |
| **Q2.5** | Perceptual Attribute (PA) | **Calm** ($ca$) |
| **Q2.6** | Perceptual Attribute (PA) | **Annoying** ($a$) |
| **Q2.7** | Perceptual Attribute (PA) | **Eventful** ($e$) |
| **Q2.8** | Perceptual Attribute (PA) | **Monotonous** ($m$) |

---

### Perceptual Coordinates

The 8 Perceptual Attributes (**Q2.1–Q2.8**) are scored on standard ordinal scales and are used by SoundGraphy to calculate the two-dimensional ISO 12913-3 soundscape coordinates:

* **ISOPleasant ($P_{\text{ISO}}$)**
* **ISOEventful ($E_{\text{ISO}}$)**