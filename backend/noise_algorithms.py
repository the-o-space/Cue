"""Noise generation algorithms for procedural art generation."""

import numpy as np
from typing import Tuple, Optional
import math


class NoiseGenerator:
    """Collection of noise generation algorithms."""
    
    @staticmethod
    def gradient_noise(shape: Tuple[int, int], scale: float = 1.0) -> np.ndarray:
        """Simple gradient noise from corner to corner.
        
        Args:
            shape: (height, width) of the output
            scale: Gradient strength
            
        Returns:
            2D array of values 0.0 to 1.0
        """
        height, width = shape
        y, x = np.mgrid[0:height, 0:width]
        
        # Diagonal gradient
        gradient = (x + y) / (width + height)
        
        # Add slight variation
        variation = np.random.randn(height, width) * 0.05
        
        return np.clip(gradient + variation, 0, 1)
    
    @staticmethod
    def perlin_noise(shape: Tuple[int, int], scale: float = 0.1, octaves: int = 1) -> np.ndarray:
        """Perlin-like noise implementation.
        
        Args:
            shape: (height, width) of the output
            scale: Frequency of the noise
            octaves: Number of noise layers
            
        Returns:
            2D array of values 0.0 to 1.0
        """
        height, width = shape
        noise = np.zeros(shape)
        
        for octave in range(octaves):
            freq = 2 ** octave
            amp = 0.5 ** octave
            
            x = np.linspace(0, freq * scale * width, width)
            y = np.linspace(0, freq * scale * height, height)
            X, Y = np.meshgrid(x, y)
            
            # Create smooth noise using sine/cosine
            layer = np.sin(X) * np.cos(Y) + np.sin(X * 1.5) * np.cos(Y * 1.5)
            layer += np.random.randn(height, width) * 0.1
            
            noise += layer * amp
        
        # Normalize
        return (noise - noise.min()) / (noise.max() - noise.min())
    
    @staticmethod
    def fbm_noise(shape: Tuple[int, int], scale: float = 0.02, octaves: int = 6, 
                  persistence: float = 0.5, lacunarity: float = 2.0) -> np.ndarray:
        """Fractal Brownian Motion noise.
        
        Args:
            shape: (height, width) of the output
            scale: Base frequency
            octaves: Number of noise layers
            persistence: Amplitude multiplier per octave
            lacunarity: Frequency multiplier per octave
            
        Returns:
            2D array of values 0.0 to 1.0
        """
        height, width = shape
        noise = np.zeros(shape)
        amplitude = 1.0
        frequency = scale
        
        for _ in range(octaves):
            x = np.linspace(0, frequency * width, width)
            y = np.linspace(0, frequency * height, height)
            X, Y = np.meshgrid(x, y)
            
            # More complex wave pattern
            layer = np.sin(X) * np.cos(Y)
            layer += np.sin(X * 2.1) * np.cos(Y * 1.9)
            layer += np.cos(X * 0.9) * np.sin(Y * 1.1)
            
            # Add randomness
            layer += np.random.randn(height, width) * 0.2
            
            noise += layer * amplitude
            amplitude *= persistence
            frequency *= lacunarity
        
        # Normalize
        return (noise - noise.min()) / (noise.max() - noise.min())
    
    @staticmethod
    def worley_noise(shape: Tuple[int, int], n_points: int = 50, 
                     nth_closest: int = 1) -> np.ndarray:
        """Worley (cellular) noise.
        
        Args:
            shape: (height, width) of the output
            n_points: Number of seed points
            nth_closest: Which closest point to use (1 = closest, 2 = second closest, etc.)
            
        Returns:
            2D array of values 0.0 to 1.0
        """
        height, width = shape
        
        # Generate random points
        points_x = np.random.randint(0, width, n_points)
        points_y = np.random.randint(0, height, n_points)
        
        # Create coordinate grids
        y, x = np.mgrid[0:height, 0:width]
        
        # Calculate distances to all points
        distances = np.zeros((height, width, n_points))
        for i in range(n_points):
            dx = x - points_x[i]
            dy = y - points_y[i]
            distances[:, :, i] = np.sqrt(dx**2 + dy**2)
        
        # Sort distances and take nth closest
        distances.sort(axis=2)
        result = distances[:, :, nth_closest - 1]
        
        # Normalize
        return 1.0 - (result / result.max())
    
    @staticmethod
    def reaction_diffusion(shape: Tuple[int, int], steps: int = 100,
                          feed_rate: float = 0.055, kill_rate: float = 0.062) -> np.ndarray:
        """Reaction-diffusion system (Gray-Scott model).
        
        Args:
            shape: (height, width) of the output
            steps: Number of simulation steps
            feed_rate: Feed rate parameter
            kill_rate: Kill rate parameter
            
        Returns:
            2D array of values 0.0 to 1.0
        """
        height, width = shape
        
        # Initialize concentrations
        A = np.ones(shape)
        B = np.zeros(shape)
        
        # Add random seed areas
        for _ in range(5):
            x = np.random.randint(width // 4, 3 * width // 4)
            y = np.random.randint(height // 4, 3 * height // 4)
            size = np.random.randint(5, 15)
            
            y_grid, x_grid = np.ogrid[:height, :width]
            mask = (x_grid - x)**2 + (y_grid - y)**2 <= size**2
            B[mask] = 1.0
        
        # Diffusion rates
        dA = 1.0
        dB = 0.5
        dt = 1.0
        
        # Laplacian kernel
        kernel = np.array([[0.05, 0.2, 0.05],
                          [0.2, -1, 0.2],
                          [0.05, 0.2, 0.05]])
        
        # Run simulation
        for _ in range(steps):
            # Calculate Laplacians
            A_lap = np.pad(A, 1, mode='edge')
            B_lap = np.pad(B, 1, mode='edge')
            
            A_lap = (
                A_lap[0:-2, 1:-1] + A_lap[2:, 1:-1] +
                A_lap[1:-1, 0:-2] + A_lap[1:-1, 2:] -
                4 * A_lap[1:-1, 1:-1]
            )
            
            B_lap = (
                B_lap[0:-2, 1:-1] + B_lap[2:, 1:-1] +
                B_lap[1:-1, 0:-2] + B_lap[1:-1, 2:] -
                4 * B_lap[1:-1, 1:-1]
            )
            
            # Reaction-diffusion equations
            reaction = A * B * B
            A += dt * (dA * A_lap - reaction + feed_rate * (1 - A))
            B += dt * (dB * B_lap + reaction - (kill_rate + feed_rate) * B)
            
            # Keep values in range
            A = np.clip(A, 0, 1)
            B = np.clip(B, 0, 1)
        
        return B
    
    @staticmethod
    def turbulence_noise(shape: Tuple[int, int], base_scale: float = 0.02, 
                        turbulence_power: float = 5.0) -> np.ndarray:
        """Turbulent noise using distorted coordinates.
        
        Args:
            shape: (height, width) of the output
            base_scale: Base frequency
            turbulence_power: Strength of turbulence
            
        Returns:
            2D array of values 0.0 to 1.0
        """
        height, width = shape
        
        # Create base coordinates
        x = np.linspace(0, base_scale * width, width)
        y = np.linspace(0, base_scale * height, height)
        X, Y = np.meshgrid(x, y)
        
        # Create distortion
        distort_x = NoiseGenerator.perlin_noise(shape, scale=0.05) * turbulence_power
        distort_y = NoiseGenerator.perlin_noise(shape, scale=0.05) * turbulence_power
        
        # Apply distortion
        X_distorted = X + distort_x
        Y_distorted = Y + distort_y
        
        # Generate pattern with distorted coordinates
        pattern = np.sin(X_distorted) * np.cos(Y_distorted)
        pattern += np.sin(X_distorted * 2.3) * np.cos(Y_distorted * 2.1)
        
        # Normalize
        return (pattern - pattern.min()) / (pattern.max() - pattern.min())
    
    @staticmethod
    def terrain_noise(shape: Tuple[int, int], n_hills: int = 15, 
                     min_radius: float = 0.1, max_radius: float = 0.4) -> np.ndarray:
        """Generate smooth terrain-like noise using overlapping gaussian hills.
        
        This creates organic, non-repeating patterns perfect for natural gradients.
        No grid artifacts, just smooth flowing terrain.
        
        Args:
            shape: (height, width) of the output
            n_hills: Number of gaussian hills to place
            min_radius: Minimum hill radius (as fraction of image size)
            max_radius: Maximum hill radius (as fraction of image size)
            
        Returns:
            2D array of values 0.0 to 1.0
        """
        height, width = shape
        terrain = np.zeros(shape)
        
        # Create coordinate grids
        y, x = np.ogrid[:height, :width]
        
        for _ in range(n_hills):
            # Random hill position
            cx = np.random.uniform(0, width)
            cy = np.random.uniform(0, height)
            
            # Random hill parameters
            radius = np.random.uniform(min_radius, max_radius) * min(width, height)
            amplitude = np.random.uniform(0.3, 1.0)
            
            # Calculate gaussian hill
            dist_sq = (x - cx)**2 + (y - cy)**2
            hill = amplitude * np.exp(-dist_sq / (2 * radius**2))
            
            # Add to terrain
            terrain += hill
        
        # Add some very low frequency variation for more organic feel
        x_freq = np.random.uniform(1, 3)
        y_freq = np.random.uniform(1, 3)
        x_phase = np.random.uniform(0, 2 * np.pi)
        y_phase = np.random.uniform(0, 2 * np.pi)
        
        # Create full coordinate grids for low frequency
        x_coords = np.linspace(0, 1, width)
        y_coords = np.linspace(0, 1, height)
        X_coords, Y_coords = np.meshgrid(x_coords, y_coords)
        
        low_freq = 0.3 * (
            np.sin(X_coords * x_freq * np.pi + x_phase) + 
            np.sin(Y_coords * y_freq * np.pi + y_phase)
        )
        terrain += low_freq
        
        # Smooth the terrain slightly to ensure continuity
        from scipy.ndimage import gaussian_filter
        terrain = gaussian_filter(terrain, sigma=2.0)
        
        # Normalize to [0, 1]
        terrain = (terrain - terrain.min()) / (terrain.max() - terrain.min())
        
        return terrain
    
    @staticmethod
    def value_noise(shape: Tuple[int, int], grid_size: int = 8) -> np.ndarray:
        """Generate smooth value noise with bicubic interpolation.
        
        Creates smooth, organic patterns without grid artifacts.
        
        Args:
            shape: (height, width) of the output
            grid_size: Size of the random value grid
            
        Returns:
            2D array of values 0.0 to 1.0
        """
        height, width = shape
        
        # Create random values at grid points
        grid_h = grid_size
        grid_w = int(grid_size * width / height)
        
        # Generate random values with padding for interpolation
        values = np.random.rand(grid_h + 3, grid_w + 3)
        
        # Smooth the values to ensure continuity
        from scipy.ndimage import gaussian_filter
        values = gaussian_filter(values, sigma=1.0)
        
        # Create coordinate arrays for interpolation
        y_grid = np.linspace(0, grid_h - 1, height)
        x_grid = np.linspace(0, grid_w - 1, width)
        
        # Use scipy's 2D interpolation for smooth results
        from scipy.interpolate import RectBivariateSpline
        
        # Create interpolator
        y_points = np.arange(values.shape[0]) - 1
        x_points = np.arange(values.shape[1]) - 1
        interpolator = RectBivariateSpline(y_points, x_points, values, kx=3, ky=3)
        
        # Interpolate to full resolution
        noise = interpolator(y_grid, x_grid)
        
        # Ensure the output has the exact requested shape
        noise = noise[:height, :width]
        
        # Normalize
        noise = (noise - noise.min()) / (noise.max() - noise.min())
        
        return noise 