"""
Mexican License Plate Generator
Based on NOM-001-SCT-2-2016 standard
Includes CSV generation for dataset persistence
"""

import os
import random
import csv
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple, Dict, Any, List

# Valid characters according to NOM-001-SCT-2-2016
SYMBOLS = "0123456789ABCDEFGHJKLMNPRSTUVWXYZ"

# State ranges with specific Mexican formats
STATE_RANGES = {
    "df": {
        "start": "A01", 
        "end": "Z99", 
        "format": "LNN-LLL", 
        "color": (30, 30, 30), 
        "y_offset": 0
    },
    "ags": {
        "start": "AAA", 
        "end": "AFZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 0
    },
    "bc": {
        "start": "AGA", 
        "end": "CYZ", 
        "format": "LLL-NNN-L", 
        "color": (30, 30, 30), 
        "y_offset": 5
    },
    "bcs": {"start": "CZA", "end": "DEZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": 5},
    "camp": {"start": "DFA", "end": "DKZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": -7},
    "chis": {"start": "DLA", "end": "DSZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": -7},
    "chih": {"start": "DTA", "end": "ETZ", "format": "LLL-NNN-L", "color": (9, 37, 210), "y_offset": 7},
    "coah": {"start": "EUA", "end": "FPZ", "format": "LLL-NNN-L", "color": (17, 125, 26), "y_offset": -3},
    "col": {"start": "FRA", "end": "FWZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": -10},
    "dgo": {"start": "FXA", "end": "GFZ", "format": "LLL-NNN-L", "color": (13, 182, 25), "y_offset": -5},
    "gto": {"start": "GGA", "end": "GYZ", "format": "LLL-NN-LL", "color": (30, 30, 30), "y_offset": 0},
    "gro": {"start": "GZA", "end": "HFZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": -7},
    "hgo": {"start": "HGA", "end": "HRZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": -12},
    "jal": {"start": "HSA", "end": "LFZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": -2},
    "mex": {"start": "LGA", "end": "PEZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": -5},
    "mich": {"start": "PFA", "end": "PUZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": 10},
    "mor": {"start": "PVA", "end": "RDZ", "format": "LLL-NNN-L", "color": (255, 255, 255), "y_offset": 7},
    "nay": {"start": "REA", "end": "RJZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": -7},
    "nl": {"start": "RKA", "end": "TGZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": 3},
    "oax": {"start": "THA", "end": "TMZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": 3},
    "pue": {"start": "TNA", "end": "UJZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": 0},
    "qro": {"start": "UKA", "end": "UPZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": 0},
    "qr": {"start": "URA", "end": "UVZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": 0},
    "slp": {"start": "UWA", "end": "VEZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": -5},
    "sin": {"start": "VFA", "end": "VSZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": -3},
    "son": {"start": "VTA", "end": "WKZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": 0},
    "tab": {"start": "WLA", "end": "WWZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": -3},
    "tamps": {"start": "WXA", "end": "XSZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": 0},
    "tlax": {"start": "XTA", "end": "XXZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": -7},
    "ver": {"start": "XYA", "end": "YVZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": 0},
    "yuc": {"start": "YWA", "end": "ZCZ", "format": "LLL-NNN-L", "color": (30, 30, 30), "y_offset": 0},
    "zac": {"start": "ZDA", "end": "ZHZ", "format": "LLL-NNN-L", "color": (152, 84, 73), "y_offset": -3},
}

# Data pools for random generation
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
    "Armando", "Beatriz", "Francisco", "Lorena", "Eduardo", "Susana", "Victor", "Daniela", "Salvador", "Monica", "Ernesto", "Yolanda", "Oscar", "Isabel", "Arturo", "Rebeca", "Felipe", "Angela", "Hugo", "Marisol", "Antonio", "Rocio", "Sergio", "Julieta", "Alberto", "Estela", "German", "Guadalupe", "Marco", "Cecilia", "Mauricio", "Liliana", "Ruben", "Fabiola", "Ignacio", "Elsa", "Benjamin", "Marina", "Cristian", "Alejandra", "Adolfo", "Daniel", "Marcos", "Lucia", "Noe", "Carolina", "Emilio", "Sofia", "Elias", "Regina", "Mateo", "Valeria", "Diego", "Camila", "Sebastian", "Renata"
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

def text_to_int(text: str) -> int:
    """Convert a license plate string to an integer value."""
    val = 0
    for char in text:
        if char == '-':
            continue
        val = val * len(SYMBOLS) + SYMBOLS.index(char)
    return val

def int_to_text(val: int, length: int = 3) -> str:
    """Convert an integer to a license plate string."""
    result = ""
    for _ in range(length):
        result = SYMBOLS[val % len(SYMBOLS)] + result
        val //= len(SYMBOLS)
    return result

def generate_random_timestamp(start_date: datetime = datetime(2020, 1, 1), 
                              end_date: datetime = datetime(2025, 12, 31)) -> str:
    """Generate a random timestamp between two dates."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86400)
    result_date = start_date + timedelta(days=random_days, seconds=random_seconds)
    return result_date.strftime("%Y-%m-%d %H:%M:%S")

def generate_virtual_owner() -> str:
    """Generate a random Mexican-sounding virtual owner name."""
    first = random.choice(FIRST_NAMES)
    last1 = random.choice(LAST_NAMES)
    last2 = random.choice(LAST_NAMES)
    return f"{first} {last1} {last2}"

class LicensePlateGenerator:
    """Generator for Mexican license plates with CSV metadata export."""
    
    def __init__(self, font_path: str, template_dir: str):
        """Initialize the license plate generator."""
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
        """Find the template image for a given state."""
        for ext in ['.jpg', '.png', '.jpeg']:
            test_path = os.path.join(self.template_dir, f"{state}{ext}")
            if os.path.exists(test_path):
                return test_path
        raise FileNotFoundError(f"No template image found for state: {state}")
    
    def _generate_plate(self, state: str, ensure_unique: bool = True, max_attempts: int = 100) -> str:
        """Generate a valid license plate for a given state."""
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
        
        # If we can't generate unique after max_attempts, return with a number suffix
        base_plate = result
        suffix = 1
        while f"{base_plate}_{suffix}" in self.generated_plates and suffix < 10:
            suffix += 1
        unique_plate = f"{base_plate}_{suffix}"
        self.generated_plates.add(unique_plate)
        return unique_plate
    
    def _get_font(self, text: str, image_width: int) -> ImageFont.FreeTypeFont:
        """Get appropriately sized font for the given text and image width."""
        target_width = image_width * 0.90
        font_size = self.base_font_size
        
        while True:
            font = ImageFont.truetype(self.font_path, font_size)
            if font.getlength(text) <= target_width or font_size < 20:
                return font
            font_size -= 5
    
    def generate_variants_with_csv(self, num_variants: int = 5, states: Optional[List[str]] = None, 
                                   output_dir: str = "dataset", csv_filename: str = "metadata.csv") -> Dict[str, List[str]]:
        """
        Generate multiple variants with associated CSV metadata.
        
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
                       "Estatus Legal", "Propietario Virtual", "Timestamp Gen", "Filename"]
        
        print(f"Generating {num_variants} variants for {len(states)} states with CSV metadata...")
        
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
                
                # Create filename
                filename = f"{state}_{plate.replace('-', '_')}.jpg"
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
                
                count += 1
                
                # Simple progress indicator
                if count % 20 == 0 or count == total:
                    print(f"  Progress: {count}/{total} images generated")
            
            results[state] = state_plates
        
        # Write CSV file
        csv_path = os.path.join(self.base_dir, output_dir, csv_filename)
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(csv_headers)
            writer.writerows(csv_data)
        
        print(f"\nComplete! Generated {count} images and CSV metadata in {output_dir}/")
        print(f"CSV file: {csv_filename}")
        print(f"Folder structure: {output_dir}/[state]/[state]_[plate].jpg")
        print(f"CSV columns: {', '.join(csv_headers)}")
        
        # Print sample of generated data
        print("\nSample metadata entries:")
        for i, row in enumerate(csv_data[:3]):  # Show first 3 entries
            print(f"  {i+1}. {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]}")
        
        return results


def main():
    """Main execution function."""
    try:
        # Initialize generator
        generator = LicensePlateGenerator(
            font_path="font/NOM-001-SCT-2-2016.ttf",
            template_dir="templates"
        )
        
        # Generate variants with CSV metadata for CNN training
        generator.generate_variants_with_csv(
            num_variants=10,  # 100 images per state
            output_dir="dataset",
            csv_filename="license_plates_metadata.csv"
        )
        
        # Example: Generate for specific states with fewer variants
        # generator.generate_variants_with_csv(
        #     num_variants=50,
        #     states=["ags", "bc", "chih", "df", "jal", "mex", "nl", "ver"],
        #     output_dir="dataset_reduced",
        #     csv_filename="metadata_reduced.csv"
        # )
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())