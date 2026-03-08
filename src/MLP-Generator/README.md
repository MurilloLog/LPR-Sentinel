# Mexican License Plate Generator

A Python-based synthetic data generator for Mexican license plates following the **NOM-001-SCT-2-2016** standard. This tool creates realistic license plate images with associated metadata for training machine learning models, particularly for OCR and license plate recognition systems.

## Overview

This generator produces synthetic Mexican license plates for all 32 Mexican states, following the official format specifications. Each generated plate includes realistic templates, metadata, and is saved with the license plate text as the filename for easy image-label association.

### Key Features

- **Standard-Compliant**: Follows NOM-001-SCT-2-2016 Mexican official standard
- **All 32 States**: Supports all Mexican states with their specific formats and color schemes
- **Rich Metadata**: Includes vehicle details, ownership information, and legal status
- **Unique Generation**: Ensures unique license plates across the dataset
- **Organized Output**: Structured directory layout with CSV metadata
- **Progress Tracking**: Visual progress bars for generation monitoring

## Project Structure
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

### Custom Configuration
Modify the parameters in the main() function:

```bash
generator.generate_variants_with_csv(
    num_variants = 250,                    # Images per state
    states = ["df", "jal", "nl", "mex"],   # Specific states (optional)
    output_dir = "custom_dataset",          # Output directory
    csv_filename = "metadata.csv"           # Metadata file name
)
```

## License
This project is provided for research and educational purposes. The generated data should not be used for fraudulent activities or misrepresentation.

## References
- Secretaría de Comunicaciones y Transportes. (2016, 24 de junio). *NORMA Oficial Mexicana NOM-001-SCT-2-2016, Especificaciones de vehículos - Placas metálicas y calcomanías de identificación*. Diario Oficial de la Federación. Retrieved March 8, 2026, from [https://www.dof.gob.mx/normasOficiales.php?codp=6057&view=si](https://www.dof.gob.mx/normasOficiales.php?codp=6057&view=si)
- Carlos. (2026, 18 de febrero). *Matrículas de coches de México (MEX): guía completa de placas actualizada*. Matriculasdelmundo.com. Retrieved March 8, 2026, from [https://www.matriculasdelmundo.com/mexico.html](https://www.matriculasdelmundo.com/mexico.html)
