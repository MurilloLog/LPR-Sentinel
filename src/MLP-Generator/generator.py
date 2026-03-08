"""
Mexican License Plate Generator
(Based on NOM-001-SCT-2-2016 standard)

This script generates synthetic Mexican license plates for training machine learning models.
It creates realistic license plates following the official Mexican standard, with associated
metadata for each generated plate. Images are saved with the license plate text as filename
to facilitate image-label association for training systems.
"""

#region Imports
import os
import random
import csv
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
#endregion

#region Constants
# Valid characters according to NOM-001-SCT-2-2016
SYMBOLS = "0123456789ABCDEFGHJKLMNPRSTUVWXYZ"

# State ranges with specific Mexican formats
# Each state has its own prefix ranges and plate formats
# Color codes are RGB tuples for text color
# y_offset adjusts vertical text position per state template
STATE_RANGES = {
    "ags": { # Aguascalientes
        "start": "AAA", 
        "end": "AFZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 0
    },
    "bc": { # Baja California
        "start": "AGA", 
        "end": "CYZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 5
    },
    "bcs": { # Baja California Sur
        "start": "CZA", 
        "end": "DEZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 5
    },
    "camp": { # Campeche
        "start": "DFA", 
        "end": "DKZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": -7
    },
    "chis": { # Chiapas
        "start": "DLA", 
        "end": "DSZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": -7
    },
    "chih": { # Chihuahua
        "start": "DTA", 
        "end": "ETZ", 
        "format": "LLL-NNN-L", 
        "color": (9, 37, 210), 
        "y_offset": 7
    },
    "coah": { # Coahuila
        "start": "EUA", 
        "end": "FPZ", 
        "format": "LLL-NNN-L", 
        "color": (17, 125, 26), 
        "y_offset": -3
    },
    "col": { # Colima
        "start": "FRA", 
        "end": "FWZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": -10
    },
    "df": { # Ciudad de Mexico
        "start": "A01", 
        "end": "Z99", 
        "format": "LNN-LLL", 
        "color": (30, 30, 30), 
        "y_offset": 0
    },
    "dgo": { # Durango
        "start": "FXA", 
        "end": "GFZ", 
        "format": "LLL-NNN-L", 
        "color": (13, 182, 25), 
        "y_offset": -5
    },
    "gto": { # Guanajuato
        "start": "GGA", 
        "end": "GYZ", 
        "format": "LLL-NN-LL", 
        "color": (30, 30, 30), 
        "y_offset": 0
    },
    "gro": { # Guerrero
        "start": "GZA", 
        "end": "HFZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": -7
    },
    "hgo": { # Hidalgo
        "start": "HGA", 
        "end": "HRZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": -12
    },
    "jal": { # Jalisco
        "start": "HSA", 
        "end": "LFZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": -2
    },
    "mex": { # Estado de Mexico
        "start": "LGA", 
        "end": "PEZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": -5
    },
    "mich": { # Michoacan
        "start": "PFA", 
        "end": "PUZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 10
    },
    "mor": { # Morelos
        "start": "PVA", 
        "end": "RDZ", 
        "format": "LLL-NNN-L", 
        "color": (255, 255, 255), 
        "y_offset": 7
    },
    "nay": { # Nayarit
        "start": "REA", 
        "end": "RJZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": -7
    },
    "nl": { # Nuevo Leon
        "start": "RKA", 
        "end": "TGZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 3
    },
    "oax": { # Oaxaca
        "start": "THA", 
        "end": "TMZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 3
    },
    "pue": { # Puebla
        "start": "TNA", 
        "end": "UJZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 0
    },
    "qro": { # Queretaro
        "start": "UKA", 
        "end": "UPZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 0
    },
    "qr": { # Quintana Roo
        "start": "URA", 
        "end": "UVZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 0
    },
    "slp": { # San Luis Potosi
        "start": "UWA", 
        "end": "VEZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": -5
    },
    "sin": { # Sinaloa
        "start": "VFA", 
        "end": "VSZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": -3
    },
    "son": { # Sonora
        "start": "VTA", 
        "end": "WKZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 0
    },
    "tab": { # Tabasco
        "start": "WLA", 
        "end": "WWZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": -3
    },
    "tamps": { # Tamaulipas
        "start": "WXA", 
        "end": "XSZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 0
    },
    "tlax": { # Tlaxcala
        "start": "XTA", 
        "end": "XXZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": -7
    },
    "ver": { # Veracruz
        "start": "XYA", 
        "end": "YVZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 0
    },
    "yuc": { # Yucatan
        "start": "YWA", 
        "end": "ZCZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 0
    },
    "zac": { # Zacatecas
        "start": "ZDA", 
        "end": "ZHZ", 
        "format": "LLL-NNN-L", 
        "color": (152, 84, 73), 
        "y_offset": -3
    },
}
#endregion

#region Data pools
# for the synthetic dataset metadata

MAKE_MODEL = [
    "Nissan Versa", "Nissan Sentra", "Nissan NP300", "Nissan March",
    "Chevrolet Aveo", "Chevrolet Spark", "Chevrolet Beat", "Chevrolet Cruze",
    "Volkswagen Vento", "Volkswagen Jetta", "Volkswagen Golf", "Volkswagen Amarok",
    "Toyota Corolla", "Toyota Hilux", "Toyota Yaris", "Toyota Prius",
    "Honda Civic", "Honda CR-V", "Honda Accord", "Honda HR-V",
    "Mazda 3", "Mazda CX-5", "Mazda 2", "Mazda MX-5",
    "Ford Fiesta", "Ford Focus", "Ford Fusion", "Ford Ranger",
    "Kia Rio", "Kia Forte", "Kia Sportage", "Kia Sorento",
    "Hyundai Accent", "Hyundai Elantra", "Hyundai Tucson", "Hyundai Santa Fe",
    "Fiat 500", "Fiat Argo", "Fiat Cronos", "Fiat Toro",
    "Renault Kwid", "Renault Duster", "Renault Logan", "Renault Sandero",
    "Peugeot 208", "Peugeot 308", "Peugeot 3008", "Peugeot 5008",
    "BMW 3 Series", "BMW X5", "BMW X3", "BMW 5 Series",
    "Mercedes-Benz A-Class", "Mercedes-Benz C-Class", "Mercedes-Benz GLA", "Mercedes-Benz GLC",
    "Audi A3", "Audi A4", "Audi Q3", "Audi Q5",
    "Jeep Wrangler", "Jeep Grand Cherokee", "Jeep Compass", "Jeep Renegade"
]

COLORS = [
    "Blanco", "Negro", "Gris", "Plateado", "Azul", "Rojo", "Verde",
    "Vino", "Cafe", "Beige", "Dorado", "Naranja", "Amarillo", "Morado",
    "Gris Oscuro", "Azul Marino", "Rojo Oscuro", "Verde Oscuro", "Blanco Perlado"
]

LEGAL_STATUS = [
    "Activo", "Activo", "Activo", "Activo",  # Higher probability for active
    "Robado", "Recuperado", "En Proceso Legal", "Baja Temporal",
    "Baja Definitiva", "Reposicion", "Homologacion", "Importacion Temporal",
    "Importacion Definitiva", "Remarcaje", "Irregular", "Cancelado"
]

# Mexican first names and last names for virtual owners
FIRST_NAMES = [
    "Juan", "Maria", "Jose", "Ana", "Carlos", "Patricia", "Jorge", "Martha",
    "Roberto", "Elizabeth", "Luis", "Laura", "Miguel", "Veronica", "Alejandro",
    "Sandra", "Ricardo", "Claudia", "Fernando", "Leticia", "Javier", "Rosa",
    "Manuel", "Alicia", "Pedro", "Gabriela", "Jesus", "Teresa", "David", "Adriana",
    "Andres", "Carmen", "Guillermo", "Silvia", "Hector", "Paola", "Raul", "Norma",
    "Armando", "Beatriz", "Francisco", "Lorena", "Eduardo", "Susana", "Victor", "Daniela",
    "Salvador", "Monica", "Ernesto", "Yolanda", "Oscar", "Isabel", "Arturo", "Rebeca",
    "Felipe", "Angela", "Hugo", "Marisol", "Antonio", "Rocio", "Sergio", "Julieta",
    "Alberto", "Estela", "German", "Guadalupe", "Marco", "Cecilia", "Mauricio", "Liliana",
    "Ruben", "Fabiola", "Ignacio", "Elsa", "Benjamin", "Marina", "Cristian", "Alejandra",
    "Adolfo", "Daniel", "Marcos", "Lucia", "Noe", "Carolina", "Emilio", "Sofia",
    "Elias", "Regina", "Mateo", "Valeria", "Diego", "Camila", "Sebastian", "Renata"
]

LAST_NAMES = [
    "Hernandez", "Garcia", "Martinez", "Lopez", "Gonzalez", "Perez", "Rodriguez",
    "Sanchez", "Ramirez", "Cruz", "Flores", "Castillo", "Reyes", "Morales",
    "Ortega", "Delgado", "Castro", "Jimenez", "Torres", "Mendoza", "Ruiz",
    "Aguilar", "Gutierrez", "Contreras", "Vazquez", "Diaz", "Fernandez", "Romero",
    "Alvarez", "Rivera", "Ramos", "Herrera", "Medina", "Vargas", "Soto",
    "Suarez", "Dominguez", "Pacheco", "Campos", "Silva", "Carrillo", "Navarro",
    "Valdez", "Cordero", "Montoya", "Escobar", "Palacios", "Rios", "Villanueva",
    "Salazar", "Camacho", "Mejia", "Acosta", "Fuentes", "Pineda", "Bravo",
    "Mora", "Solano", "Peña", "Arroyo", "Correa", "Velazquez", "Espinoza",
    "Maldonado", "Serrano", "Gallegos", "Orozco", "Cabrera", "Trejo", "Avila",
    "Rosales", "Valencia", "Sandoval", "Arellano", "Del Valle", "Quiroz", "Estrada",
    "Villalobos", "Plascencia", "Tapia", "Zamora", "Beltran", "Cervantes", "Huerta",
    "Luna", "Moya", "Nieto", "Olvera", "Portillo", "Quintero", "Sepulveda",
    "Tovar", "Urbina", "Villegas", "Zarate", "Barajas", "Chavez", "De La Cruz",
    "Esquivel", "Figueroa", "Guerrero", "Izquierdo", "Juarez", "Leal", "Montes"
]
#endregion

#region Gen-utilities
def text_to_int(text: str) -> int:
    """Convert a license plate string to an integer value for range calculations.
    
    Args:
        text: License plate string (may contain hyphens)
    
    Returns:
        Integer representation for ordering/comparison
    """
    val = 0
    for char in text:
        if char == '-':
            continue
        val = val * len(SYMBOLS) + SYMBOLS.index(char)
    return val

def int_to_text(val: int, length: int = 3) -> str:
    """Convert an integer to a license plate string.
    
    Args:
        val: Integer value to convert
        length: Desired output string length
    
    Returns:
        License plate string without hyphens
    """
    result = ""
    for _ in range(length):
        result = SYMBOLS[val % len(SYMBOLS)] + result
        val //= len(SYMBOLS)
    return result

def generate_random_timestamp(start_date: datetime = datetime(2017, 1, 1), 
                              end_date: datetime = datetime(2026, 5, 30)) -> str:
    """Generate a random timestamp between two dates.
    
    Args:
        start_date: Start of date range
        end_date: End of date range
    
    Returns:
        Formatted timestamp string (YYYY-MM-DD HH:MM:SS)
    """
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86400)
    result_date = start_date + timedelta(days=random_days, seconds=random_seconds)
    return result_date.strftime("%Y-%m-%d %H:%M:%S")

def generate_virtual_owner() -> str:
    """Generate a random Mexican-sounding virtual owner name.
    
    Returns:
        Full name string (First Name + Last Name1 + Last Name2)
    """
    first = random.choice(FIRST_NAMES)
    last1 = random.choice(LAST_NAMES)
    last2 = random.choice(LAST_NAMES)
    return f"{first} {last1} {last2}"
#endregion

#region LP-Generator
class LicensePlateGenerator:
    """Generator for Mexican license plates with CSV metadata export.
    
    This class handles the generation of synthetic license plates following
    the NOM-001-SCT-2-2016 standard. It creates realistic images with proper
    formatting and generates associated metadata for machine learning datasets.
    
    Attributes:
        font_path: Path to the TrueType font file for license plate text
        template_dir: Directory containing state template images
        base_font_size: Base font size for text rendering
        generated_plates: Set of already generated plates to ensure uniqueness
    """
    
    def __init__(self, font_path: str, template_dir: str):
        """Initialize the license plate generator.
        
        Args:
            font_path: Path to the font file (relative to script location)
            template_dir: Directory containing template images
        
        Raises:
            FileNotFoundError: If font file or template directory doesn't exist
        """
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.font_path = os.path.join(self.base_dir, font_path)
        self.template_dir = os.path.join(self.base_dir, template_dir)
        self.base_font_size = 180
        self.generated_plates = set()  # Track unique plates globally
        
        # Validate paths
        if not os.path.exists(self.font_path):
            raise FileNotFoundError(f"Font file not found: {self.font_path}")
        if not os.path.exists(self.template_dir):
            raise FileNotFoundError(f"Template directory not found: {self.template_dir}")
    
    def _find_template_image(self, state: str) -> str:
        """Find the template image for a given state.
        
        Args:
            state: State code (e.g., 'df', 'jal', 'nl')
        
        Returns:
            Full path to the template image file
        
        Raises:
            FileNotFoundError: If no template image found for the state
        """
        for ext in ['.jpg', '.png', '.jpeg']:
            test_path = os.path.join(self.template_dir, f"{state}{ext}")
            if os.path.exists(test_path):
                return test_path
        raise FileNotFoundError(f"No template image found for state: {state}")
    
    def _generate_plate(self, state: str, ensure_unique: bool = True, max_attempts: int = 100) -> str:
        """Generate a valid license plate for a given state.
        
        Args:
            state: State code
            ensure_unique: Whether to ensure plate uniqueness
            max_attempts: Maximum attempts to generate unique plate
        
        Returns:
            Generated license plate string
        """
        config = STATE_RANGES[state]
        attempts = 0
        
        while attempts < max_attempts:
            # Generate prefix based on range
            low = text_to_int(config["start"])
            high = text_to_int(config["end"])
            prefix = int_to_text(random.randint(low, high), length=len(config["start"]))
            
            # Generate plate according to format
            format_str = config["format"]
            result = ""
            prefix_idx = 0
            letters_set = SYMBOLS[10:]  # Letters only
            
            for char in format_str:
                if char == 'L':
                    if prefix_idx < len(prefix):
                        result += prefix[prefix_idx]
                        prefix_idx += 1
                    else:
                        result += random.choice(letters_set)
                elif char in ['0', 'N']:
                    result += random.choice("0123456789")
                elif char == '-':
                    result += "-"
                else:
                    result += char
            
            if not ensure_unique or result not in self.generated_plates:
                self.generated_plates.add(result)
                return result
            
            attempts += 1
        
        # If can't generate unique after max_attempts, return with a number suffix
        base_plate = result
        suffix = 1
        while f"{base_plate}_{suffix}" in self.generated_plates and suffix < 10:
            suffix += 1
        unique_plate = f"{base_plate}_{suffix}"
        self.generated_plates.add(unique_plate)
        return unique_plate
    
    def _get_font(self, text: str, image_width: int) -> ImageFont.FreeTypeFont:
        """Get appropriately sized font for the given text and image width.
        
        Args:
            text: Text to be rendered
            image_width: Width of the target image
        
        Returns:
            Configured font object with appropriate size
        """
        target_width = image_width * 0.90
        font_size = self.base_font_size
        
        while True:
            font = ImageFont.truetype(self.font_path, font_size)
            if font.getlength(text) <= target_width or font_size < 20:
                return font
            font_size -= 5
    
    def generate_variants_with_csv(self, num_variants: int = 5, states: Optional[List[str]] = None, 
                                   output_dir: str = "dataset", csv_filename: str = "metadata.csv") -> Dict[str, List[str]]:
        """Generate multiple variants with associated CSV metadata.
        
        This is the main method for dataset generation. It creates license plate images
        and a CSV file with associated metadata. Images are saved with filenames containing
        the license plate text to facilitate image-label association for training systems.
        
        Args:
            num_variants: Number of variants to generate per state
            states: List of state codes. If None, generates for all states
            output_dir: Base directory where state folders will be created
            csv_filename: Name of the CSV file with metadata
        
        Returns:
            Dictionary mapping state codes to lists of generated plate texts
        """
        if states is None:
            states = list(STATE_RANGES.keys())
        
        results = {}
        total = len(states) * num_variants
        count = 0
        
        # Prepare CSV data
        csv_data = []
        csv_headers = ["Matricula", "Estado", "Marca/Modelo", "Color del vehiculo", 
                       "Estatus Legal", "Propietario Virtual", "Fecha de registro", "Filename"]
        
        print(f"\n{'='*60}")
        print(f"Generating {num_variants} variants for {len(states)} states")
        print(f"Total images to generate: {total}")
        print(f"{'='*60}\n")
        
        # Main progress bar for overall generation
        with tqdm(total=total, desc="Overall Progress", unit="img", position=0) as pbar:
            for state in states:
                if state not in STATE_RANGES:
                    continue
                
                # Create state-specific directory
                state_dir = os.path.join(self.base_dir, output_dir, state)
                os.makedirs(state_dir, exist_ok=True)
                
                # Load template once per state
                template_path = self._find_template_image(state)
                template_img = Image.open(template_path).convert("RGB")
                
                state_config = STATE_RANGES[state]
                text_color = state_config["color"]
                y_offset = state_config["y_offset"]
                
                state_plates = []
                
                # Inner progress bar for state-specific generation
                with tqdm(total=num_variants, desc=f"State {state.upper()}", 
                         unit="img", position=1, leave=False) as state_pbar:
                    
                    for i in range(num_variants):
                        # Create fresh copy of template
                        img = template_img.copy()
                        draw = ImageDraw.Draw(img)
                        
                        # Generate unique plate
                        plate = self._generate_plate(state)
                        state_plates.append(plate)
                        
                        # Generate random metadata
                        make_model = random.choice(MAKE_MODEL)
                        color = random.choice(COLORS)
                        legal_status = random.choice(LEGAL_STATUS)
                        owner = generate_virtual_owner()
                        timestamp = generate_random_timestamp()
                        
                        # Create filename - using plate text only for easy association
                        # Replace hyphens with underscores for filesystem compatibility
                        #safe_plate = plate.replace('-', '_')
                        filename = f"{plate}.jpg"
                        filepath = os.path.join(state_dir, filename)
                        
                        # Get font and draw text
                        font = self._get_font(plate, img.width)
                        position = (img.width // 2, img.height // 2 + y_offset)
                        draw.text(position, plate, font=font, fill=text_color, anchor="mm")
                        
                        # Save image
                        img.save(filepath)
                        
                        # Add to CSV data
                        csv_data.append([
                            plate, state.upper(), make_model, color, 
                            legal_status, owner, timestamp, filename
                        ])
                        
                        # Update progress bars
                        count += 1
                        state_pbar.update(1)
                        pbar.update(1)
                        
                        # Update main progress bar description with current plate
                        pbar.set_description(f"Generating {plate}")
                
                results[state] = state_plates
        
        # Write CSV file
        csv_path = os.path.join(self.base_dir, output_dir, csv_filename)
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(csv_headers)
            writer.writerows(csv_data)
        
        # Final summary
        print(f"\nGeneration Complete!")
        print(f"{'='*60}")
        print(f"Statistics:")
        print(f"   - Total images generated: {count}")
        print(f"   - Total states processed: {len(states)}")
        print(f"   - Images per state: {num_variants}")
        print(f"\nOutput structure:")
        print(f"   - Base directory: {output_dir}/")
        print(f"   - CSV file: {csv_filename}")
        print(f"   - State folders: {', '.join(states[:5])}{'...' if len(states) > 5 else ''}")
        
        return results
#endregion

#region main()
def main():
    """Main execution function.
    
    This function initializes the generator and creates the synthetic dataset.
    Modify parameters here to customize dataset generation.
    
    Returns:
        0 for success, 1 for error
    """
    try:
        # Initialize generator with required paths
        # Note: Ensure these files exist in the specified locations
        generator = LicensePlateGenerator(
            font_path = "font/NOM-001-SCT-2-2016.ttf", # Path to license plate font
            template_dir = "templates" # Directory with state templates
        )
        
        # Generate complete dataset for all states
        # This creates N images per state with full metadata
        N = 250
        generator.generate_variants_with_csv(
            num_variants = N, # Images per state
            output_dir = "dataset", # Output directory
            csv_filename = "license_plates_metadata.csv" # Metadata file
        )
        
        # Alternative for testing: 
        # Generator for specific states with fewer variants
        # generator.generate_variants_with_csv(
        #     num_variants = 50,
        #     states = ["ags", "bc", "chih", "df", "jal", "mex", "nl", "ver"],
        #     output_dir = "dataset_reduced",
        #     csv_filename = "metadata_reduced.csv"
        # )
        
    except FileNotFoundError as e:
        print(f"\nFile Error: {e}")
        print("\nPlease ensure the following files/directories exist:")
        print("  - font/NOM-001-SCT-2-2016.ttf (license plate font)")
        print("  - templates/ directory with state template images")
        print("\nTemplate images should be named: [state_code].jpg (e.g., df.jpg, jal.jpg)")
        return 1
        
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
        return 1
    
    return 0
#endregion

#region Entry point
if __name__ == "__main__":
    """
    Script entry point.
    Executes main() and exits with appropriate return code.
    """
    exit(main())
#endregion