import pygame, random, math
from settings import *

class BG(pygame.sprite.Sprite):
    def __init__(self, groups, scale_factor, theme="day"):
        super().__init__(groups)
        self.theme = theme
        
        # Load background - fallback to day if night doesn't exist
        try:
            if theme == "night":
                bg_image = pygame.image.load('./graphics/environment/background_night.png').convert()
            else:
                bg_image = pygame.image.load('./graphics/environment/background.png').convert()
        except:
            # Fallback to day background
            bg_image = pygame.image.load('./graphics/environment/background.png').convert()

        full_height = bg_image.get_height() * scale_factor
        full_width = bg_image.get_width() * scale_factor
        full_sized_image = pygame.transform.scale(bg_image, (full_width, full_height))
        
        self.image = pygame.Surface((full_width * 2, full_height))
        self.image.blit(full_sized_image, (0, 0))
        self.image.blit(full_sized_image, (full_width, 0))

        self.rect = self.image.get_rect(topleft=(0, 0))
        self.pos = pygame.math.Vector2(self.rect.topleft)

    def update(self, dt):
        self.pos.x -= 300 * dt
        if self.rect.centerx <= 0:
            self.pos.x = 0
        self.rect.x = round(self.pos.x)

class Ground(pygame.sprite.Sprite):
    def __init__(self, groups, scale_factor):
        super().__init__(groups)
        self.sprite_type = 'ground'
        
        # image
        ground_surf = pygame.image.load('./graphics/environment/ground.png').convert_alpha()
        self.image = pygame.transform.scale(ground_surf, pygame.math.Vector2(ground_surf.get_size()) * scale_factor)
        
        # position
        self.rect = self.image.get_rect(bottomleft=(0, WINDOW_HEIGHT))
        self.pos = pygame.math.Vector2(self.rect.topleft)

        # mask
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        self.pos.x -= 360 * dt
        if self.rect.centerx <= 0:
            self.pos.x = 0

        self.rect.x = round(self.pos.x)

class Plane(pygame.sprite.Sprite):
    def __init__(self, groups, scale_factor, ui_scale=1):
        super().__init__(groups)

        # image 
        self.import_frames(scale_factor)
        self.frame_index = 0
        self.image = self.frames[self.frame_index]

        # rect
        self.rect = self.image.get_rect(midleft=(WINDOW_WIDTH * ui_scale / 20, WINDOW_HEIGHT * ui_scale / 2))
        self.pos = pygame.math.Vector2(self.rect.topleft)

        # movement
        self.gravity = 500  # Reduced from 600 for easier control
        self.direction = 0

        # mask
        self.mask = pygame.mask.from_surface(self.image)

        # sound
        try:
            self.jump_sound = pygame.mixer.Sound('./sounds/jump.wav')
            self.jump_sound.set_volume(0.3)
        except:
            # Create dummy sound if file doesn't exist
            self.jump_sound = type('DummySound', (), {'play': lambda: None})()

    def import_frames(self, scale_factor):
        self.frames = []
        for i in range(3):
            surf = pygame.image.load(f'./graphics/plane/red{i}.png').convert_alpha()
            scaled_surface = pygame.transform.scale(surf, pygame.math.Vector2(surf.get_size()) * scale_factor)
            self.frames.append(scaled_surface)

    def apply_gravity(self, dt):
        self.direction += self.gravity * dt
        self.pos.y += self.direction * dt
        self.rect.y = round(self.pos.y)

    def jump(self):
        self.jump_sound.play()
        self.direction = -350  # Reduced from -400 for more controlled jumps

    def animate(self, dt):
        self.frame_index += 10 * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]

    def rotate(self):
        rotated_plane = pygame.transform.rotozoom(self.image, -self.direction * 0.06, 1)
        self.image = rotated_plane
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        self.apply_gravity(dt)
        self.animate(dt)
        self.rotate()

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, groups, scale_factor, gap_size=100):
        super().__init__(groups)
        self.sprite_type = 'obstacle'

        # Determine orientation (up or down)
        self.orientation = random.choice(('up', 'down'))
        
        # Load and scale image
        surf = pygame.image.load(f'./graphics/obstacles/{random.choice((0, 1))}.png').convert_alpha()
        self.image = pygame.transform.scale(surf, pygame.math.Vector2(surf.get_size()) * scale_factor)
        
        # Position the obstacle
        x = WINDOW_WIDTH + random.randint(40, 100)
        
        # Use the gap size from difficulty settings
        gap_y = gap_size

        if self.orientation == 'up':
            y = WINDOW_HEIGHT + gap_y
            self.rect = self.image.get_rect(midbottom=(x, y))
        else:
            y = -gap_y
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect = self.image.get_rect(midtop=(x, y))

        self.pos = pygame.math.Vector2(self.rect.topleft)
        
        # Default speed (will be overridden by game)
        self.speed = 400

        # mask
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        # Use the dynamic speed instead of hardcoded value
        self.pos.x -= self.speed * dt
        self.rect.x = round(self.pos.x)
        if self.rect.right <= -100:
            self.kill()

class Coin(pygame.sprite.Sprite):
    def __init__(self, groups, scale_factor, speed, ui_scale=1):
        super().__init__(groups)
        
        # Create coin frames programmatically if coin images don't exist
        try:
            self.frames = []
            for i in range(4):
                surf = pygame.image.load(f'./graphics/coins/coin{i}.png').convert_alpha()
                scaled_surface = pygame.transform.scale(surf, pygame.math.Vector2(surf.get_size()) * scale_factor * 0.6)
                self.frames.append(scaled_surface)
        except:
            # Create simple animated coin if images don't exist
            self.frames = []
            for i in range(4):
                size = int(20 * scale_factor)
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                
                # Create a simple coin with different rotations
                color = (255, 215, 0)  # Gold color
                border_color = (200, 170, 0)
                
                # Draw coin based on frame (rotation effect)
                if i == 0:
                    pygame.draw.circle(surf, color, (size//2, size//2), size//2)
                    pygame.draw.circle(surf, border_color, (size//2, size//2), size//2, 2)
                elif i == 1:
                    pygame.draw.ellipse(surf, color, (size//4, 0, size//2, size))
                    pygame.draw.ellipse(surf, border_color, (size//4, 0, size//2, size), 2)
                elif i == 2:
                    pygame.draw.ellipse(surf, color, (size//3, 0, size//3, size))
                    pygame.draw.ellipse(surf, border_color, (size//3, 0, size//3, size), 2)
                else:
                    pygame.draw.ellipse(surf, color, (size//4, 0, size//2, size))
                    pygame.draw.ellipse(surf, border_color, (size//4, 0, size//2, size), 2)
                
                self.frames.append(surf)
        
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        
        # Position
        x = WINDOW_WIDTH * ui_scale + random.randint(50, 150)
        
        # Ensure coins spawn in safe positions (away from top and bottom)
        safe_margin = int(150 * ui_scale)  # Keep coins away from edges
        y = random.randint(safe_margin, int(WINDOW_HEIGHT * ui_scale - safe_margin))
        
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(self.rect.topleft)
        
        # Add floating animation
        self.float_offset = 0
        self.float_speed = random.uniform(1.0, 3.0)
        self.original_y = self.pos.y
        
        # Movement
        self.speed = speed
        
        # Mask for collision
        self.mask = pygame.mask.from_surface(self.image)
    
    def animate(self, dt):
        self.frame_index += 8 * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]
    
    def update(self, dt):
        # Move coin
        self.pos.x -= self.speed * dt
        
        # Add gentle floating motion
        self.float_offset += self.float_speed * dt
        self.pos.y = self.original_y + math.sin(self.float_offset) * 5
        
        self.rect.x = round(self.pos.x)
        self.rect.y = round(self.pos.y)
        
        # Animate
        self.animate(dt)
        
        # Remove if off screen
        if self.rect.right <= -50:
            self.kill()

class Particle:
    def __init__(self, pos, speed, angle, size, color, lifetime):
        self.pos = pygame.math.Vector2(pos)
        self.velocity = pygame.math.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
        self.size = size
        self.color = color
        self.lifetime = lifetime
        self.original_lifetime = lifetime
    
    def update(self, dt):
        self.pos += self.velocity * dt
        self.velocity.y += 200 * dt  # Gravity
        self.lifetime -= dt
    
    def draw(self, surface, offset_x=0, offset_y=0):
        # Fade out as lifetime decreases
        alpha = int(255 * (self.lifetime / self.original_lifetime))
        
        # Calculate size based on lifetime
        current_size = int(self.size * (self.lifetime / self.original_lifetime))
        if current_size < 1:
            current_size = 1
        
        # Draw particle
        try:
            pygame.draw.circle(
                surface, 
                self.color, 
                (int(self.pos.x + offset_x), int(self.pos.y + offset_y)), 
                current_size
            )
        except:
            # Fallback if drawing fails
            pass
