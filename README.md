# SoundGraphy 🎧📊

**A Graphical and Statistical Tool for Assessing Acoustic Perception according to ISO 12913-3**

[![Open Source](https://img.shields.io/badge/Open%20Source-%E2%9D%A4-red.svg)](https://github.com/arturo-olvrs/SoundGraphy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

SoundGraphy is an open-source, Python-based application designed to enhance the characterization, advanced filtering, and statistical visualization of soundscape data. Built upon the standard foundations of the **ISO 12913 series**, it bridges the gap between raw perceptual survey spreadsheets and nuanced human behavioral outcomes.

---

## 🚀 Key Features

SoundGraphy is established upon a robust functional tripod that includes:

1. **User-Friendly Graphical Interface (GUI):** Developed with `CustomTkinter`, it features intuitive data entry, custom spreadsheet column mapping, and full Light/Dark mode compatibility. No programming experience is required.
2. **Advanced Database Filtering System:** Real-time multi-conditional slicing for temporal data (date/time), quantitative metrics (e.g., age, sound levels), and categorical indicators (low-cardinality checklists).
3. **Enhanced ISO 12913 Representations:** 
   * **2-D Cartesian Circumplex Projections:** Free combination of Scatter plots, Bivariate Kernel Density Estimations (KDE), Percentile Contour Spectrums ($P_{10}$ to $P_{90}$), and marginal axis distributions.
   * **Adaptive Radar Plots:** Intelligent circular profiling. Displays individual survey responses for small datasets ($\le 7$ rows). To prevent visual clutter on larger datasets ($> 7$ rows), it triggers an interactive warning dialog and automatically computes group-wise or global medians.
   * **Box-and-Whisker Plots:** Includes both standard 8-attribute comparative rating spreads and highly flexible personalized bi-axis variable selections.
   * **Custom $X$ vs $Y$ Scatter Plots:** Dynamic bivariate graphing tool for cross-variable analysis with automatic data-cleaning, data-type enforcement, and categorical hue mapping.
4. **Native Structural Summary Method (SS) / Cosine Fitting:** Statistical validation of the circumplex structure of perceived affective quality by performing mathematical curve-fitting (sinusoidal waves) to extract *Elevation*, *Amplitude*, and *Angular Displacement* metrics ($R^2$)].

---

## 📦 Installation & Setup

### Option 1: Running from Source (Development)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/arturo-olvrs/SoundGraphy.git
   cd SoundGraphy
    ```
2. **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4. **Run the application:**
    ```bash
    python SoundGraphy.py
    ```
### Option 2: Using the Executable (End-User)
*Note*: It will be available soon. Stay tuned!
<!-- TODO: Add executable installation instructions -->

## 📊 Quick Start Guide

1. **Launch SoundGraphy** and select your survey data file (CSV or Excel).
    - Example datasets are provided in the `examples/` directory for testing and demonstration purposes.
2. **Map your columns** to the required attributes (e.g., Pleasantness, Eventfulness, etc.).
3. **Apply filters** to focus on specific subsets of your data (e.g., by date, age group, sound level).
4. **Choose your visualization** type (e.g., Circumplex, Radar, Box Plot) and customize it as needed.
5. **Export your results** as high-quality images or data summaries for reporting and publication.

## 🛠️ Built With
- **Python 3.12+**: The core programming language for SoundGraphy.
- **CustomTkinter**: For the graphical user interface.
- **Pandas**: For data manipulation and analysis.
- **Matplotlib & Seaborn**: For data visualization.
- **SciPy**: For statistical analysis and curve fitting.
- **Soundscapy**: For soundscape data processing and analysis.

## 🤝 Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your improvements or bug fixes. For major changes, please open an issue first to discuss what you would like to change.

## 🎓 Citation
If you use SoundGraphy in your research, please cite it as follows:

```
@software{SoundGraphy2024,
  title = {SoundGraphy: A Graphical and Statistical Tool for Assessing Acoustic Perception according to ISO 12913-3},
  author = {Olivares, Arturo},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/arturo-olvrs/SoundGraphy}}
}
```

<!--// TODO: Añadir bien la citación, con DOI.-->

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.