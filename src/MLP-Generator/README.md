# Mexican License Plate Generator (MLP-Generator)

The **```MLP-Generator```** is the foundational module of the LPR-Sentinel pipeline, responsible for producing high-fidelity synthetic training data that adheres to the **NOM-001-SCT-2-2016** Mexican regulatory standard. By programmatically generating plates, the system avoids the privacy concerns of using real-world imagery while ensuring the OCR model (MLP-Recognizer) is exposed to the full diversity of Mexican state-specific formats, colors, and fonts.

## Core Logic and Architecture
The generation process is encapsulated in the ```LicensePlateGenerator``` class. It orchestrates the selection of state templates, character generation according to regulatory ranges, and the rendering of text using a specialized font.

### STATE_RANGES Configuration
The generator maintains a comprehensive dictionary, ```STATE_RANGES```, which defines the visual and logical parameters for all 32 Mexican states. Each entry specifies:
- **Prefix Ranges**: ```start``` - ```end``` strings defining the legal character boundaries for that state
- **Format Strings**: Logic for character placement (e.g., ```LLL-NNN-L``` for Aguascalientes)
- **Color Schemes**: RGB tuples for text rendering (e.g., Chihuahua uses blue (9, 37, 210))
- **Vertical Alignment**: ```y_offset``` to account for variations in background template designs (subjective position)

Example of a couple of ```STATE_RANGES``` entries:
```
STATE_RANGES = {
    "ags": {  # Aguascalientes
        "start": "AAA",
        "end": "AFZ",
        "format": "LLL-NNN-L",
        "color": (30, 30, 30),   # Dark gray
        "y_offset": 5
    },
    "chih": {  # Chihuahua
        "start": "DTA",
        "end": "ETZ",
        "format": "LLL-NNN-L",
        "color": (9, 37, 210),   # Blue
        "y_offset": 3
    }
    ...
}
```

## Plate Generation Logic
### Format Enforcement
The method ```_generate_plate_text(state_code)``` interprets the format string from ```STATE_RANGES``` to build the plate string:
1. L: Replaced by a random letter from SYMBOLS (excluding I, O, Ñ, Q per standard)
2. N: Replaced by a random digit (0-9)
3. -: Preserved as a class separator.

### Font Rendering
The generator uses ```NOM-001-SCT-2-2016.ttf```, a font specifically designed to mimic the official Mexican typography. The ```_create_plate_image``` method handles the drawing process:
- Loads the state template image from ```templates/{state}.jpg```
- Calculates the center position for the text
- Applies the ```y_offset``` and renders the text using ```ImageDraw.text()```

## Metadata and CSV Output
For every image generated, the system creates a corresponding entry in ```license_plates_metadata.csv```. This metadata includes randomized but realistic vehicle information sourced from data pools like ```MAKE_MODEL```, ```COLORS```, and ```OWNERS```.

### CSV Schema Fields 
- ```Matricula```: The generated plate text (e.g., "ABC-123-A").
- ```Estado```: Full name of the Mexican state.
- ```Marca/Modelo```: Vehicle make and model.
- ```Color```: Vehicle color.
- ```Propietario```: Randomly generated owner name.
- ```FechaRegistro```: Randomized registration date within the last 10 years 
- ```Filename```: Path to the saved .jpg file.

## Module Structure
```
/MLP-Generator
|---- /dataset                # Created after running generator.py
|     |-- /ags                # State-specific folders (Aguascalientes)
|     |-- /bc                 # Baja California
|     |-- /bcs                # Baja California Sur
|     |-- /...                # All 32 state folders
|     |-- license_plates_metadata.csv   # Complete metadata file
|
|---- /fonts                  # Font files directory
|     |-- NOM-001-SCT-2-2016.ttf   # Unofficial license plate font
|
|---- /templates              # State template images
|     |-- ags.jpg             # Template for Aguascalientes
|     |-- bc.jpg              # Template for Baja California
|     |-- df.jpg              # Template for Ciudad de México
|     |-- ...                 # Templates for all states
|
|---- generator.py            # Main generation script
```

## Usage
Run the script with default parameters:

```bash
python generator.py
```

This will generate 250 images per state (8,000 total images) in the */dataset* directory.

**Note**: Make sure you run the script from the directory ```~/LPR-Sentinel/src/MLP-Generator```

### Custom Configuration
Modify the parameters in the main() function:

```bash
N = 250
generator.generate_variants_with_csv(
    num_variants = N,                       # Images per state
    output_dir = "custom_dataset_folder",   # Output directory
    csv_filename = "metadata.csv"           # Metadata file name
)
```

## Limitations
- Does not generate license plates with special characters or accents
- Does not simulate physical wear, rotation, or weather conditions
- The font is an unofficial approximation (there is no official public font)

## License
This project is provided for research and educational purposes. The generated data should not be used for fraudulent activities or misrepresentation.

## References
- Secretaría de Comunicaciones y Transportes. (2016, 24 de junio). *NORMA Oficial Mexicana NOM-001-SCT-2-2016, Especificaciones de vehículos - Placas metálicas y calcomanías de identificación*. Diario Oficial de la Federación. Retrieved March 8, 2026, from [https://www.dof.gob.mx/normasOficiales.php?codp=6057&view=si](https://www.dof.gob.mx/normasOficiales.php?codp=6057&view=si)
- Carlos. (2026, 18 de febrero). *Matrículas de coches de México (MEX): guía completa de placas actualizada*. Matriculasdelmundo.com. Retrieved March 8, 2026, from [https://www.matriculasdelmundo.com/mexico.html](https://www.matriculasdelmundo.com/mexico.html)
