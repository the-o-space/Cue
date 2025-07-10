"""Art generation module for creating grainy, noise-based generative art."""

import numpy as np
from PIL import Image, ImageFilter
from typing import Dict, Tuple, List
from noise_algorithms import NoiseGenerator
from config import DEFAULT_IMAGE_SIZE, COLOR_TEMPERATURES, NOISE_COMPLEXITY_RANGES


class ArtGenerator:
    """Generates abstract art based on sentiment parameters using height maps."""
    
    def __init__(self, size: Tuple[int, int] = DEFAULT_IMAGE_SIZE):
        """Initialize the art generator.
        
        Args:
            size: Image size as (width, height) tuple
        """
        self.width, self.height = size
        self.size = (self.height, self.width)  # numpy uses (height, width)
        self.noise_gen = NoiseGenerator()
    
    def generate_height_map(self, energy: float, noise_type: str = "terrain") -> np.ndarray:
        """Generate height map using a specific noise algorithm.
        
        Args:
            energy: Determines turbulence/chaos level and algorithm parameters (0.0 to 1.0)
            noise_type: Which noise algorithm to use ("terrain", "value", "worley", "gradient")
            
        Returns:
            2D height map with values 0.0 to 1.0
        """
        # Generate specific noise type with energy-based parameters
        if noise_type == "gradient":
            # Improved gradient with more organic flow
            base_map = self.noise_gen.gradient_noise(self.size)
            # Add some terrain noise for organic variation
            terrain = self.noise_gen.terrain_noise(self.size, n_hills=5, min_radius=0.2, max_radius=0.5)
            base_map = base_map * 0.6 + terrain * 0.4
            
        elif noise_type == "terrain":
            # Our new organic terrain algorithm
            n_hills = int(10 + energy * 20)  # More hills with higher energy
            min_radius = 0.05 + (1 - energy) * 0.1  # Smaller hills with high energy
            max_radius = 0.2 + (1 - energy) * 0.3   # Larger hills with low energy
            base_map = self.noise_gen.terrain_noise(
                self.size, 
                n_hills=n_hills,
                min_radius=min_radius,
                max_radius=max_radius
            )
            
        elif noise_type == "value":
            # Smooth value noise with energy-based grid size
            grid_size = int(4 + energy * 12)  # Higher energy = more detail
            base_map = self.noise_gen.value_noise(self.size, grid_size=grid_size)
            
        elif noise_type == "worley":
            # Worley stays the same - it's already quite organic
            worley_points = int(20 + energy * 80)
            base_map = self.noise_gen.worley_noise(self.size, n_points=worley_points)
            
        else:
            raise ValueError(f"Unknown noise type: {noise_type}")
        
        # Add very subtle turbulence only for high energy and appropriate types
        if energy > 0.6 and noise_type in ["terrain", "value"]:
            # Use terrain noise for turbulence instead of the grid-like perlin
            turbulence = self.noise_gen.terrain_noise(
                self.size, 
                n_hills=int(5 + energy * 10),
                min_radius=0.05,
                max_radius=0.15
            )
            turbulence_strength = (energy - 0.6) * 0.2  # Very subtle
            base_map = base_map * (1 - turbulence_strength) + turbulence * turbulence_strength
        
        # Ensure values are in [0, 1] range
        base_map = (base_map - base_map.min()) / (base_map.max() - base_map.min())
        
        return base_map

    def generate_all_noise_variations(self, sentiment_scores: Dict[str, float]) -> Dict[str, Image.Image]:
        """Generate art using all noise algorithms separately.
        
        Args:
            sentiment_scores: Dictionary with positiveness, energy, complexity, conflictness
            
        Returns:
            Dictionary mapping noise type to PIL Image
        """
        # Extract parameters
        positiveness = sentiment_scores.get("positiveness", 0.5)
        energy = sentiment_scores.get("energy", 0.5)
        conflictness = sentiment_scores.get("conflictness", 0.5)
        
        # Generate color palette (same for all)
        color_palette = self.generate_color_palette(positiveness, conflictness)
        
        # Generate one image per noise algorithm (using our new organic ones)
        noise_types = ["terrain", "value", "worley", "gradient"]
        variations = {}
        
        for noise_type in noise_types:
            # Generate height map with specific noise
            height_map = self.generate_height_map(energy, noise_type)
            
            # Apply colors to height map
            rgb_image = self.apply_height_to_color(height_map, color_palette)
            
            # Add grain based on energy level
            grain_intensity = 0.05 + energy * 0.15
            rgb_image = self.add_grain(rgb_image, grain_intensity)
            
            # Convert to PIL Image
            image = Image.fromarray(rgb_image, mode='RGB')
            
            # Apply slight blur for smoother appearance (less blur for high energy)
            if energy < 0.7:
                blur_radius = 1.0 - energy * 0.5
                image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            
            variations[noise_type] = image
        
        return variations

    def generate_color_palette(self, positiveness: float, conflictness: float) -> List[Tuple[int, int, int]]:
        """Generate a smooth gradient palette between 2-3 colors sampled from temperature range.
        
        Args:
            positiveness: Influences color warmth (0.0 = cold, 1.0 = warm)
            conflictness: Influences color diversity (0.0 = harmonious, 1.0 = contrasting)
            
        Returns:
            List of RGB color tuples forming a smooth gradient
        """
        # Define full color ranges for each temperature
        if positiveness < 0.33:
            # Cold palette - full range from deep purple to cyan
            hue_min = 180  # Cyan
            hue_max = 280  # Purple
            saturation_base = 0.6
            brightness_base = 0.7
            temp_name = "cold"
        elif positiveness < 0.66:
            # Neutral palette - greens, teals, earth tones
            hue_min = 60   # Yellow-green
            hue_max = 180  # Cyan
            saturation_base = 0.4
            brightness_base = 0.6
            temp_name = "neutral"
        else:
            # Warm palette - full range from red through orange to yellow
            hue_min = 0    # Red
            hue_max = 60   # Yellow
            saturation_base = 0.7
            brightness_base = 0.8
            temp_name = "warm"
        
        # Number of key colors - always use at least 3 for diversity
        n_colors = 3 if conflictness > 0.3 else 2
        
        # Generate key colors sampled across the full temperature range
        key_colors = []
        for i in range(n_colors):
            # Distribute colors across the full range
            if n_colors == 2:
                # Two colors at 25% and 75% of range
                t = 0.25 if i == 0 else 0.75
            else:
                # Three colors at 0%, 50%, and 100% of range
                t = i / (n_colors - 1)
            
            # Sample hue from full range
            hue = hue_min + t * (hue_max - hue_min)
            
            # Add controlled randomness for organic feel
            hue += np.random.uniform(-15, 15)
            hue = hue % 360
            
            # Vary saturation and brightness for more interest
            saturation = saturation_base + np.random.uniform(-0.15, 0.15)
            brightness = brightness_base + np.random.uniform(-0.15, 0.15)
            
            # Ensure values are in valid range
            saturation = np.clip(saturation, 0.2, 0.9)
            brightness = np.clip(brightness, 0.3, 0.95)
            
            # Convert HSV to RGB
            import colorsys
            r, g, b = colorsys.hsv_to_rgb(hue / 360, saturation, brightness)
            key_colors.append((int(r * 255), int(g * 255), int(b * 255)))
        
        # For high conflictness, add more color variation
        if conflictness > 0.6 and n_colors == 3:
            # Make middle color more distinct
            mid_idx = len(key_colors) // 2
            h, s, v = colorsys.rgb_to_hsv(
                key_colors[mid_idx][0] / 255,
                key_colors[mid_idx][1] / 255,
                key_colors[mid_idx][2] / 255
            )
            # Shift hue significantly
            h = (h + 0.15) % 1.0
            # Boost saturation
            s = min(s * 1.3, 0.9)
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            key_colors[mid_idx] = (int(r * 255), int(g * 255), int(b * 255))
        
        # Create smooth gradient between key colors
        gradient_steps = 10  # More steps for smoother gradients
        palette = []
        
        for i in range(len(key_colors) - 1):
            start_color = key_colors[i]
            end_color = key_colors[i + 1]
            
            for step in range(gradient_steps):
                t = step / gradient_steps
                # Use smooth interpolation curve
                t = t * t * (3.0 - 2.0 * t)  # Smoothstep function
                
                r = int(start_color[0] * (1 - t) + end_color[0] * t)
                g = int(start_color[1] * (1 - t) + end_color[1] * t)
                b = int(start_color[2] * (1 - t) + end_color[2] * t)
                palette.append((r, g, b))
        
        # Add the last color
        palette.append(key_colors[-1])
        
        return palette
    
    def apply_height_to_color(self, height_map: np.ndarray, color_palette: List[Tuple[int, int, int]]) -> np.ndarray:
        """Map height values to colors from palette.
        
        Args:
            height_map: 2D array of height values (0.0 to 1.0)
            color_palette: List of RGB colors
            
        Returns:
            RGB image array
        """
        height, width = height_map.shape
        rgb_image = np.zeros((height, width, 3), dtype=np.uint8)
        
        n_colors = len(color_palette)
        
        for i in range(n_colors):
            # Define the range for this color
            if i == 0:
                mask = height_map < (1.0 / n_colors)
            elif i == n_colors - 1:
                mask = height_map >= (i / n_colors)
            else:
                mask = (height_map >= (i / n_colors)) & (height_map < ((i + 1) / n_colors))
            
            # Interpolate with next color
            if i < n_colors - 1:
                # Calculate interpolation factor
                t = (height_map - (i / n_colors)) * n_colors
                t = np.clip(t, 0, 1)
                
                # Interpolate between current and next color
                for c in range(3):
                    rgb_image[:, :, c] = np.where(
                        mask,
                        color_palette[i][c] * (1 - t) + color_palette[i + 1][c] * t,
                        rgb_image[:, :, c]
                    )
            else:
                # Last color
                for c in range(3):
                    rgb_image[:, :, c] = np.where(mask, color_palette[i][c], rgb_image[:, :, c])
        
        return rgb_image
    
    def add_grain(self, image: np.ndarray, intensity: float = 0.1) -> np.ndarray:
        """Add larger, film-like grain to the image.
        
        Args:
            image: RGB image array
            intensity: Grain strength (0.0 to 1.0)
            
        Returns:
            Image with grain applied
        """
        height, width = image.shape[:2]
        
        # Create larger grain by using a smaller resolution and upscaling
        grain_scale = 3  # Make grain 3x larger
        small_height = height // grain_scale
        small_width = width // grain_scale
        
        # Generate grain at smaller resolution
        small_grain = np.random.randn(small_height, small_width) * intensity * 40
        
        # Upscale grain using nearest neighbor for blocky appearance
        grain = np.repeat(np.repeat(small_grain, grain_scale, axis=0), grain_scale, axis=1)
        
        # Crop to exact size if needed
        grain = grain[:height, :width]
        
        # Apply grain to each channel
        for c in range(3):
            image[:, :, c] = np.clip(image[:, :, c].astype(float) + grain, 0, 255).astype(np.uint8)
        
        # Add some additional fine grain for texture
        fine_grain = np.random.randn(height, width) * intensity * 15
        for c in range(3):
            image[:, :, c] = np.clip(image[:, :, c].astype(float) + fine_grain, 0, 255).astype(np.uint8)
        
        return image
    
    def generate(self, sentiment_scores: Dict[str, float]) -> Image.Image:
        """Generate art based on sentiment scores (defaults to terrain noise).
        
        Args:
            sentiment_scores: Dictionary with positiveness, energy, complexity, conflictness
            
        Returns:
            PIL Image object
        """
        # Extract parameters
        positiveness = sentiment_scores.get("positiveness", 0.5)
        energy = sentiment_scores.get("energy", 0.5)
        conflictness = sentiment_scores.get("conflictness", 0.5)
        
        # Generate height map using terrain noise (best default for organic gradients)
        height_map = self.generate_height_map(energy, "terrain")
        
        # Generate color palette
        color_palette = self.generate_color_palette(positiveness, conflictness)
        
        # Apply colors to height map
        rgb_image = self.apply_height_to_color(height_map, color_palette)
        
        # Add grain based on energy level
        grain_intensity = 0.05 + energy * 0.15
        rgb_image = self.add_grain(rgb_image, grain_intensity)
        
        # Convert to PIL Image
        image = Image.fromarray(rgb_image, mode='RGB')
        
        # Apply slight blur for smoother appearance (less blur for high energy)
        if energy < 0.7:
            blur_radius = 1.0 - energy * 0.5
            image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        return image
    
    def generate_variations(self, sentiment_scores: Dict[str, float], count: int = 4) -> List[Image.Image]:
        """Generate multiple variations of art for the same sentiment.
        
        Args:
            sentiment_scores: Dictionary of sentiment scores
            count: Number of variations to generate
            
        Returns:
            List of PIL Images
        """
        variations = []
        original_state = np.random.get_state()
        
        for i in range(count):
            np.random.seed(i * 1000 + 42)  # Different seed for each variation
            image = self.generate(sentiment_scores)
            variations.append(image)
        
        np.random.set_state(original_state)
        return variations


if __name__ == "__main__":
    # Test the generator
    generator = ArtGenerator(size=(800, 600))
    
    test_profiles = [
        {
            "name": "Warm_Simple_Unified",
            "scores": {"positiveness": 0.9, "energy": 0.3, "complexity": 0.2, "conflictness": 0.1}
        },
        {
            "name": "Cold_Chaotic_Complex",
            "scores": {"positiveness": 0.1, "energy": 0.9, "complexity": 0.8, "conflictness": 0.7}
        },
        {
            "name": "Neutral_Moderate_Conflicted",
            "scores": {"positiveness": 0.5, "energy": 0.5, "complexity": 0.5, "conflictness": 0.9}
        },
    ]
    
    for profile in test_profiles:
        print(f"Generating: {profile['name']}")
        image = generator.generate(profile['scores'])
        image.save(f"test_{profile['name'].lower()}.png")
        print(f"  Saved as test_{profile['name'].lower()}.png") 