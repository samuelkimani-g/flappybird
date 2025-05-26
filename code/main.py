import pygame, sys, time, math, random
from settings import *
from sprites import BG, Ground, Plane, Obstacle, Coin, Particle
from database import GameDatabase
from ui import Button, Panel, TextInput, Label

class Game:
    def __init__(self):
        # Core setup
        pygame.init()
        
        # Setup display based on settings
        if FULLSCREEN:
            # Get the current display resolution
            info = pygame.display.Info()
            self.screen_width = info.current_w
            self.screen_height = info.current_h
            self.display_surface = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
            
            # Calculate scaling for fullscreen
            self.scale_x = self.screen_width / WINDOW_WIDTH
            self.scale_y = self.screen_height / WINDOW_HEIGHT
            self.ui_scale = min(self.scale_x, self.scale_y)
        else:
            self.screen_width = WINDOW_WIDTH
            self.screen_height = WINDOW_HEIGHT
            self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.scale_x = 1
            self.scale_y = 1
            self.ui_scale = 1
        
        pygame.display.set_caption('Air Rush')
        self.clock = pygame.time.Clock()
        
        # Game states
        self.state = "main_menu"  # "main_menu", "name_input", "playing", "paused", "game_over", "leaderboard", "help"
        self.active = False
        self.game_over = False
        self.player_name = ""
        self.current_theme = "day"  # "day" or "night"
        
        # Database
        self.db = GameDatabase()
        self.high_score = self.db.get_high_score()
        
        # Visual effects
        self.screen_shake = 0
        self.flash_alpha = 0
        self.transition_alpha = 255  # For smooth transitions
        self.transitioning = False
        self.transition_target = None
        self.level_up_timer = 0  # For level up display
        self.level_up_alpha = 0
        
        # Load assets
        self.load_assets()
        
        # Setup game elements
        self.setup_sprites()
        self.setup_difficulty()
        self.setup_ui()
        self.setup_audio()
        
        # Particles and effects
        self.particles = []
        self.coins = pygame.sprite.Group()
        self.coin_count = 0
        
        # Start with fade-in
        self.start_transition("fade_in")
    
    def load_assets(self):
        """Load all game assets - using existing files only"""
        # Fonts with scaling
        base_large = int(40 * self.ui_scale)
        base_medium = int(30 * self.ui_scale)
        base_small = int(20 * self.ui_scale)
        base_tiny = int(16 * self.ui_scale)
        
        try:
            self.fonts = {
                'large': pygame.font.Font('./graphics/font/BD_Cartoon_Shout.ttf', base_large),
                'medium': pygame.font.Font('./graphics/font/BD_Cartoon_Shout.ttf', base_medium),
                'small': pygame.font.Font('./graphics/font/BD_Cartoon_Shout.ttf', base_small),
                'tiny': pygame.font.Font('./graphics/font/BD_Cartoon_Shout.ttf', base_tiny),
            }
        except:
            # Fallback to default font if custom font not found
            self.fonts = {
                'large': pygame.font.Font(None, base_large),
                'medium': pygame.font.Font(None, base_medium),
                'small': pygame.font.Font(None, base_small),
                'tiny': pygame.font.Font(None, base_tiny),
            }
        
        # Create a dummy sound class
        class DummySound:
            def play(self):
                pass
            
            def set_volume(self, volume):
                pass
        
        # Load sounds if they exist, otherwise create dummy sounds
        self.sounds = {}
        sound_files = ['coin', 'level_up', 'game_over', 'button']
        
        for sound_name in sound_files:
            try:
                sound = pygame.mixer.Sound(f'./sounds/{sound_name}.wav')
                sound.set_volume(0.3)
                self.sounds[sound_name] = sound
            except:
                # Create a dummy sound that does nothing
                self.sounds[sound_name] = DummySound()
    
    def scale_pos(self, x, y):
        """Scale position for fullscreen"""
        if FULLSCREEN:
            # Center the game area
            offset_x = (self.screen_width - WINDOW_WIDTH * self.ui_scale) // 2
            offset_y = (self.screen_height - WINDOW_HEIGHT * self.ui_scale) // 2
            return (int(x * self.ui_scale + offset_x), int(y * self.ui_scale + offset_y))
        return (x, y)
    
    def scale_size(self, width, height):
        """Scale size for fullscreen"""
        if FULLSCREEN:
            return (int(width * self.ui_scale), int(height * self.ui_scale))
        return (width, height)
    
    def create_panel_surface(self, width, height, color=(240, 240, 240), border_color=(100, 100, 100)):
        """Create a panel surface programmatically"""
        scaled_width, scaled_height = self.scale_size(width, height)
        surface = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
        
        # Check if color already has alpha
        if len(color) == 4:
            # Color already has alpha
            base_color = color[:3]
            base_alpha = color[3]
        else:
            # Color doesn't have alpha
            base_color = color
            base_alpha = 255
        
        # Main panel
        pygame.draw.rect(surface, color, (0, 0, scaled_width, scaled_height), border_radius=int(12 * self.ui_scale))
        
        # Border
        pygame.draw.rect(surface, border_color, (0, 0, scaled_width, scaled_height), int(3 * self.ui_scale), border_radius=int(12 * self.ui_scale))
        
        # Subtle gradient effect
        for i in range(scaled_height // 4):
            alpha = 30 - (i * 30 // (scaled_height // 4))
            if alpha > 0:
                gradient_color = (*base_color, alpha)
                pygame.draw.rect(surface, gradient_color, (0, i, scaled_width, 1))
        
        return surface
    
    def setup_sprites(self):
        """Initialize sprite groups and scale factor"""
        self.all_sprites = pygame.sprite.Group()
        self.collision_sprites = pygame.sprite.Group()
        
        bg_height = pygame.image.load('./graphics/environment/background.png').get_height()
        self.scale_factor = (WINDOW_HEIGHT * self.ui_scale) / bg_height
        
        # Create background and ground
        self.bg = BG(self.all_sprites, self.scale_factor, self.current_theme)
        self.ground = Ground([self.all_sprites, self.collision_sprites], self.scale_factor)
    
        # Create the player plane
        self.plane = Plane(self.all_sprites, self.scale_factor / 1.7, self.ui_scale)
    
    def setup_difficulty(self):
        """Initialize difficulty settings - super easy start"""
        self.difficulty_level = 1
        self.last_difficulty_increase = 0
        
        # Get current difficulty settings
        current_diff = DIFFICULTY_LEVELS.get(self.difficulty_level, DIFFICULTY_LEVELS[1])
        self.obstacle_speed = current_diff["speed"]
        self.current_obstacle_interval = current_diff["interval"]
        
        # Coin settings
        self.coin_spawn_chance = 0.4  # 40% chance to spawn a coin
        
        # Timers
        self.obstacle_timer = pygame.USEREVENT + 1
        self.coin_timer = pygame.USEREVENT + 2
        pygame.time.set_timer(self.obstacle_timer, self.current_obstacle_interval)
        pygame.time.set_timer(self.coin_timer, 3000)  # Coin spawn timer
    
    def setup_ui(self):
        """Initialize UI elements"""
        # Main menu buttons
        button_width, button_height = self.scale_size(200, 50)
        center_x, center_y = self.scale_pos(WINDOW_WIDTH // 2, 0)
        
        # Pass the button sound to all buttons
        button_sound = self.sounds['button']
        
        self.main_menu_buttons = [
            Button(*self.scale_pos(WINDOW_WIDTH // 2, 300), *self.scale_size(200, 50), "Play", self.fonts['medium'], 
                   lambda: self.start_transition("name_input"), button_sound),
            Button(*self.scale_pos(WINDOW_WIDTH // 2, 370), *self.scale_size(200, 50), "Leaderboard", self.fonts['medium'], 
                   lambda: self.start_transition("leaderboard"), button_sound),
            Button(*self.scale_pos(WINDOW_WIDTH // 2, 440), *self.scale_size(200, 50), "Help", self.fonts['medium'], 
                   lambda: self.start_transition("help"), button_sound),
            Button(*self.scale_pos(WINDOW_WIDTH // 2, 510), *self.scale_size(200, 50), "Quit", self.fonts['medium'], 
                   lambda: sys.exit(), button_sound)
        ]
        
        # Game UI elements
        self.pause_button = Button(*self.scale_pos(WINDOW_WIDTH - 40, 40), *self.scale_size(60, 60), "⏸️", self.fonts['medium'], 
                                  lambda: self.toggle_pause(), button_sound)
        
        # Name input
        self.name_input = TextInput(*self.scale_pos(WINDOW_WIDTH // 2, 300), *self.scale_size(280, 50), "", self.fonts['medium'], 12)
        
        # Game over buttons
        self.game_over_buttons = [
            Button(*self.scale_pos(WINDOW_WIDTH // 2, 400), *self.scale_size(200, 50), "Play Again", self.fonts['medium'], 
                   lambda: self.reset_game(), button_sound),
            Button(*self.scale_pos(WINDOW_WIDTH // 2, 470), *self.scale_size(200, 50), "Leaderboard", self.fonts['medium'], 
                   lambda: self.start_transition("leaderboard"), button_sound),
            Button(*self.scale_pos(WINDOW_WIDTH // 2, 540), *self.scale_size(200, 50), "Main Menu", self.fonts['medium'], 
                   lambda: self.start_transition("main_menu"), button_sound)
        ]
        
        # Leaderboard and help screen back button
        self.back_button = Button(*self.scale_pos(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 70), *self.scale_size(200, 50), "Back", 
                                 self.fonts['medium'], lambda: self.start_transition("main_menu"), button_sound)
        
        # Pause menu buttons
        self.pause_menu_buttons = [
            Button(*self.scale_pos(WINDOW_WIDTH // 2, 300), *self.scale_size(200, 50), "Resume", self.fonts['medium'], 
                   lambda: self.toggle_pause(), button_sound),
            Button(*self.scale_pos(WINDOW_WIDTH // 2, 370), *self.scale_size(200, 50), "Restart", self.fonts['medium'], 
                   lambda: self.reset_game(), button_sound),
            Button(*self.scale_pos(WINDOW_WIDTH // 2, 440), *self.scale_size(200, 50), "Main Menu", self.fonts['medium'], 
                   lambda: self.start_transition("main_menu"), button_sound)
        ]
        
        # Score and stats
        self.score = 0
        self.start_offset = 0
    
    def setup_audio(self):
        """Initialize audio"""
        try:
            self.music = pygame.mixer.Sound('./sounds/music.wav')
            self.music.set_volume(0.2)
            self.music.play(loops=-1)
        except:
            # No music file found, continue without music
            pass
    
    def reset_game(self):
        """Reset game to initial state"""
        # Clear sprites
        for sprite in self.all_sprites:
            sprite.kill()
        
        self.coins.empty()
        self.particles = []
        
        # Reinitialize
        self.setup_sprites()
        self.plane = Plane(self.all_sprites, self.scale_factor / 1.7, self.ui_scale)
        
        # Reset game state
        self.state = "playing"
        self.active = True
        self.game_over = False
        self.score = 0
        self.coin_count = 0
        self.start_offset = pygame.time.get_ticks()
        
        # Reset difficulty
        self.setup_difficulty()
        
        # Reset effects
        self.screen_shake = 0
        self.flash_alpha = 0
        self.level_up_timer = 0
        self.level_up_alpha = 0
    
    def handle_collision(self):
        """Handle collision with visual effects"""
        if (pygame.sprite.spritecollide(self.plane, self.collision_sprites, False, pygame.sprite.collide_mask) 
            or self.plane.rect.top <= 0):
            
            # Clear obstacles
            for sprite in self.collision_sprites.sprites():
                if sprite.sprite_type == 'obstacle':
                    sprite.kill()
            
            # Game over effects
            self.active = False
            self.game_over = True
            self.state = "game_over"
            self.plane.kill()
            self.screen_shake = 15
            self.flash_alpha = 150
            
            # Create explosion particles
            self.create_explosion(self.plane.rect.center)
            
            # Play sound
            self.sounds['game_over'].play()
            
            # Save score
            if self.score > 0:
                self.db.save_score(self.player_name, self.score, self.coin_count)
            
            # Update high score
            if self.score > self.high_score:
                self.high_score = self.score
    
    def check_coin_collection(self):
        """Check if player collected coins"""
        if hasattr(self, 'plane'):
            collected = pygame.sprite.spritecollide(self.plane, self.coins, True)
            if collected:
                self.coin_count += len(collected)
                self.sounds['coin'].play()
                
                # Create sparkle effect
                for coin in collected:
                    self.create_sparkle(coin.rect.center)
    
    def create_explosion(self, position):
        """Create explosion particles at position"""
        for _ in range(30):
            speed = random.uniform(100, 300)
            angle = random.uniform(0, math.pi * 2)
            size = random.randint(3, 8)
            lifetime = random.uniform(0.5, 1.5)
            color = random.choice([(255, 100, 100), (255, 200, 100), (255, 255, 100)])
            
            self.particles.append(Particle(
                position, speed, angle, size, color, lifetime
            ))
    
    def create_sparkle(self, position):
        """Create sparkle particles at position"""
        for _ in range(15):
            speed = random.uniform(50, 150)
            angle = random.uniform(0, math.pi * 2)
            size = random.randint(2, 5)
            lifetime = random.uniform(0.3, 0.8)
            color = random.choice([(255, 255, 100), (255, 255, 200), (200, 255, 255)])
            
            self.particles.append(Particle(
                position, speed, angle, size, color, lifetime
            ))
    
    def adjust_difficulty(self):
        """Progressive difficulty with clear level system"""
        if self.score > 0 and self.score % 10 == 0 and self.score > self.last_difficulty_increase:
            if self.difficulty_level < MAX_DIFFICULTY:
                self.last_difficulty_increase = self.score
                self.difficulty_level += 1
                
                # Get new difficulty settings
                current_diff = DIFFICULTY_LEVELS.get(self.difficulty_level, DIFFICULTY_LEVELS[MAX_DIFFICULTY])
                self.obstacle_speed = current_diff["speed"]
                self.current_obstacle_interval = current_diff["interval"]
                
                # Update obstacle timer
                pygame.time.set_timer(self.obstacle_timer, self.current_obstacle_interval)
                
                # Visual feedback for level up
                self.screen_shake = 8
                self.level_up_timer = 3.0  # Show level up for 3 seconds
                self.level_up_alpha = 255
                self.create_level_up_effect()
                
                # Play level up sound
                self.sounds['level_up'].play()

    def create_level_up_effect(self):
        """Create level-up particles effect"""
        # Create particles at the top of the screen
        for _ in range(30):
            x = random.randint(0, int(WINDOW_WIDTH * self.ui_scale))
            y = 50 * self.ui_scale
            speed = random.uniform(50, 150)
            angle = random.uniform(math.pi/2 - 0.5, math.pi/2 + 0.5)  # Mostly downward
            size = random.randint(3, 8)
            lifetime = random.uniform(0.8, 2.0)
            
            # Use difficulty level color
            current_diff = DIFFICULTY_LEVELS.get(self.difficulty_level, DIFFICULTY_LEVELS[1])
            color = current_diff["color"]
            
            self.particles.append(Particle(
                (x, y), speed, angle, size, color, lifetime
            ))
    
    def update_effects(self, dt):
        """Update visual effects"""
        # Screen shake
        if self.screen_shake > 0:
            self.screen_shake = max(0, self.screen_shake - 200 * dt)
        
        # Flash effect
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - 300 * dt)
        
        # Level up display timer
        if self.level_up_timer > 0:
            self.level_up_timer -= dt
            self.level_up_alpha = int(255 * (self.level_up_timer / 3.0))
        
        # Transition effect
        if self.transitioning:
            if self.transition_target == "fade_in":
                self.transition_alpha = max(0, self.transition_alpha - 510 * dt)
                if self.transition_alpha <= 0:
                    self.transitioning = False
            else:
                self.transition_alpha = min(255, self.transition_alpha + 510 * dt)
                if self.transition_alpha >= 255:
                    self.transitioning = False
                    self.state = self.transition_target
                    self.transition_alpha = 255
                    self.start_transition("fade_in")
        
        # Update particles
        for particle in self.particles[:]:
            particle.update(dt)
            if particle.lifetime <= 0:
                self.particles.remove(particle)
    
    def get_shake_offset(self):
        """Get screen shake offset"""
        if self.screen_shake <= 0:
            return (0, 0)
        
        shake_x = (pygame.time.get_ticks() * 0.1) % (2 * math.pi)
        shake_y = (pygame.time.get_ticks() * 0.15) % (2 * math.pi)
        
        offset_x = math.sin(shake_x) * self.screen_shake * self.ui_scale
        offset_y = math.sin(shake_y) * self.screen_shake * self.ui_scale
        
        return (int(offset_x), int(offset_y))
    
    def start_transition(self, target):
        """Start transition to new state"""
        if target == "fade_in":
            self.transition_alpha = 255
        else:
            self.transition_alpha = 0
        
        self.transitioning = True
        self.transition_target = target
    
    def toggle_pause(self):
        """Toggle game pause state"""
        if self.state == "playing":
            self.state = "paused"
        elif self.state == "paused":
            self.state = "playing"
    
    def draw_ui(self):
        """Draw all UI elements based on game state"""
        # Clear screen with black for fullscreen
        self.display_surface.fill((0, 0, 0))
        
        if self.state == "main_menu":
            self.draw_main_menu()
        elif self.state == "name_input":
            self.draw_name_input()
        elif self.state == "playing":
            self.draw_game_ui()
        elif self.state == "paused":
            self.draw_pause_menu()
        elif self.state == "game_over":
            self.draw_game_over()
        elif self.state == "leaderboard":
            self.draw_leaderboard()
        elif self.state == "help":
            self.draw_help_screen()
        
        # Draw transition overlay
        if self.transition_alpha > 0:
            overlay = pygame.Surface((self.screen_width, self.screen_height))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(self.transition_alpha)
            self.display_surface.blit(overlay, (0, 0))
    
    def draw_main_menu(self):
        """Draw main menu screen"""
        # Create game area surface
        game_surface = pygame.Surface((int(WINDOW_WIDTH * self.ui_scale), int(WINDOW_HEIGHT * self.ui_scale)))
        
        # Background gradient
        for y in range(int(WINDOW_HEIGHT * self.ui_scale)):
            color_ratio = y / (WINDOW_HEIGHT * self.ui_scale)
            r = int(135 + (50 * color_ratio))
            g = int(206 + (30 * color_ratio))
            b = int(250 + (5 * color_ratio))
            pygame.draw.line(game_surface, (r, g, b), (0, y), (int(WINDOW_WIDTH * self.ui_scale), y))
        
        # Game title with shadow
        title_shadow = self.fonts['large'].render("Air Rush", True, (50, 50, 50))
        title = self.fonts['large'].render("Air Rush", True, (255, 255, 255))
        
        title_rect = title.get_rect(center=(int(WINDOW_WIDTH * self.ui_scale // 2), int(150 * self.ui_scale)))
        shadow_rect = title_shadow.get_rect(center=(int(WINDOW_WIDTH * self.ui_scale // 2 + 3 * self.ui_scale), int(153 * self.ui_scale)))
        
        game_surface.blit(title_shadow, shadow_rect)
        game_surface.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.fonts['small'].render("The Ultimate Flying Experience", True, (100, 100, 100))
        subtitle_rect = subtitle.get_rect(center=(int(WINDOW_WIDTH * self.ui_scale // 2), int(190 * self.ui_scale)))
        game_surface.blit(subtitle, subtitle_rect)
        
        # Blit game surface to center of screen
        game_rect = game_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.display_surface.blit(game_surface, game_rect)
        
        # Buttons
        for button in self.main_menu_buttons:
            button.draw(self.display_surface)
        
        # Version and credits
        version_text = self.fonts['tiny'].render("GAME OF THE YEAR", True, (80, 80, 80))
        credit_text = self.fonts['tiny'].render("Made By Sam", True, (80, 80, 80))
        
        version_pos = self.scale_pos(10, WINDOW_HEIGHT - 40)
        credit_pos = self.scale_pos(10, WINDOW_HEIGHT - 20)
        
        self.display_surface.blit(version_text, version_pos)
        self.display_surface.blit(credit_text, credit_pos)
    
    def draw_name_input(self):
        """Draw name input screen"""
        # Create game area surface
        game_surface = pygame.Surface((int(WINDOW_WIDTH * self.ui_scale), int(WINDOW_HEIGHT * self.ui_scale)))
        
        # Background gradient
        for y in range(int(WINDOW_HEIGHT * self.ui_scale)):
            color_ratio = y / (WINDOW_HEIGHT * self.ui_scale)
            r = int(135 + (50 * color_ratio))
            g = int(206 + (30 * color_ratio))
            b = int(250 + (5 * color_ratio))
            pygame.draw.line(game_surface, (r, g, b), (0, y), (int(WINDOW_WIDTH * self.ui_scale), y))
        
        # Panel
        panel = self.create_panel_surface(400, 300)
        panel_rect = panel.get_rect(center=(int(WINDOW_WIDTH * self.ui_scale // 2), int(WINDOW_HEIGHT * self.ui_scale // 2)))
        game_surface.blit(panel, panel_rect)
        
        # Title with shadow
        title_shadow = self.fonts['medium'].render("ENTER YOUR NAME", True, (100, 100, 100))
        title = self.fonts['medium'].render("ENTER YOUR NAME", True, (50, 50, 50))
        
        title_rect = title.get_rect(center=(int(WINDOW_WIDTH * self.ui_scale // 2), panel_rect.top + int(60 * self.ui_scale)))
        shadow_rect = title_shadow.get_rect(center=(int(WINDOW_WIDTH * self.ui_scale // 2 + 2 * self.ui_scale), panel_rect.top + int(62 * self.ui_scale)))
        
        game_surface.blit(title_shadow, shadow_rect)
        game_surface.blit(title, title_rect)
        
        # Blit game surface to center of screen
        game_rect = game_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.display_surface.blit(game_surface, game_rect)
        
        # Input field
        self.name_input.draw(self.display_surface)
        
        # Instructions with blinking effect
        if pygame.time.get_ticks() % 1000 < 500:
            instr = self.fonts['small'].render("Press ENTER when done", True, (100, 100, 100))
            instr_pos = self.scale_pos(WINDOW_WIDTH // 2 - instr.get_width() // 2, 400)
            self.display_surface.blit(instr, instr_pos)
    
    def draw_game_ui(self):
        """Draw game UI with effects"""
        # Create game area surface
        game_surface = pygame.Surface((int(WINDOW_WIDTH * self.ui_scale), int(WINDOW_HEIGHT * self.ui_scale)))
        game_surface.fill((0, 0, 0))
        
        # Apply screen shake
        shake_x, shake_y = self.get_shake_offset()
        
        # Draw sprites with shake
        for sprite in self.all_sprites:
            pos = (sprite.rect.x + shake_x, sprite.rect.y + shake_y)
            game_surface.blit(sprite.image, pos)
        
        # Draw coins with shake
        for coin in self.coins:
            pos = (coin.rect.x + shake_x, coin.rect.y + shake_y)
            game_surface.blit(coin.image, pos)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(game_surface, shake_x, shake_y)
        
        # Score display
        if self.active:
            self.score = (pygame.time.get_ticks() - self.start_offset) // 1000
            
            # Score panel
            score_panel = self.create_panel_surface(200, 80, (255, 255, 255, 200))
            game_surface.blit(score_panel, (int(10 * self.ui_scale), int(10 * self.ui_scale)))
            
            # Score text with shadow
            score_shadow = self.fonts['medium'].render(f"{self.score}", True, (100, 100, 100))
            score_text = self.fonts['medium'].render(f"{self.score}", True, (50, 50, 50))
            game_surface.blit(score_shadow, (int(32 * self.ui_scale), int(27 * self.ui_scale)))
            game_surface.blit(score_text, (int(30 * self.ui_scale), int(25 * self.ui_scale)))
            
            # Coin counter
            coin_text = self.fonts['small'].render(f"Coins: {self.coin_count}", True, (50, 50, 50))
            game_surface.blit(coin_text, (int(30 * self.ui_scale), int(60 * self.ui_scale)))
            
            # Difficulty level display with color coding
            current_diff = DIFFICULTY_LEVELS.get(self.difficulty_level, DIFFICULTY_LEVELS[1])
            level_panel = self.create_panel_surface(160, 80, (*current_diff["color"], 200))
            game_surface.blit(level_panel, (int((WINDOW_WIDTH - 170) * self.ui_scale), int(10 * self.ui_scale)))
            
            level_name = self.fonts['tiny'].render(current_diff["name"], True, (50, 50, 50))
            level_text = self.fonts['small'].render(f"LVL {self.difficulty_level}", True, (50, 50, 50))
            
            level_name_rect = level_name.get_rect(center=(int((WINDOW_WIDTH - 90) * self.ui_scale), int(30 * self.ui_scale)))
            level_text_rect = level_text.get_rect(center=(int((WINDOW_WIDTH - 90) * self.ui_scale), int(55 * self.ui_scale)))
            
            game_surface.blit(level_name, level_name_rect)
            game_surface.blit(level_text, level_text_rect)
            
            # Speed indicator
            speed_text = self.fonts['tiny'].render(f"Speed: {self.obstacle_speed}", True, (50, 50, 50))
            game_surface.blit(speed_text, (int(30 * self.ui_scale), int(110 * self.ui_scale)))
        
        # Level up notification
        if self.level_up_timer > 0 and self.level_up_alpha > 0:
            current_diff = DIFFICULTY_LEVELS.get(self.difficulty_level, DIFFICULTY_LEVELS[1])
            
            # Create level up surface
            level_up_surface = pygame.Surface((int(400 * self.ui_scale), int(100 * self.ui_scale)), pygame.SRCALPHA)
            level_up_surface.fill((*current_diff["color"], min(self.level_up_alpha, 200)))
            
            # Level up text
            level_up_text = self.fonts['medium'].render(f"LEVEL UP! {current_diff['name']}", True, (255, 255, 255))
            level_up_rect = level_up_text.get_rect(center=(int(200 * self.ui_scale), int(30 * self.ui_scale)))
            level_up_surface.blit(level_up_text, level_up_rect)
            
            # Stats text
            stats_text = self.fonts['small'].render(f"Speed: {current_diff['speed']} | Gap: {current_diff['gap']}", True, (255, 255, 255))
            stats_rect = stats_text.get_rect(center=(int(200 * self.ui_scale), int(60 * self.ui_scale)))
            level_up_surface.blit(stats_text, stats_rect)
            
            # Position at center of screen
            level_up_pos = (int((WINDOW_WIDTH - 400) * self.ui_scale // 2), int((WINDOW_HEIGHT - 100) * self.ui_scale // 2))
            game_surface.blit(level_up_surface, level_up_pos)
        
        # Blit game surface to center of screen
        game_rect = game_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.display_surface.blit(game_surface, game_rect)
        
        # Pause button
        self.pause_button.draw(self.display_surface)
        
        # Flash effect
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((self.screen_width, self.screen_height))
            flash_surf.set_alpha(self.flash_alpha)
            flash_surf.fill((255, 100, 100))
            self.display_surface.blit(flash_surf, (0, 0))
    
    def draw_pause_menu(self):
        """Draw pause menu overlay"""
        # Draw game underneath
        self.draw_game_ui()
        
        # Darken screen
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.display_surface.blit(overlay, (0, 0))
        
        # Panel
        panel = self.create_panel_surface(300, 300)
        panel_pos = self.scale_pos(WINDOW_WIDTH // 2 - 150, WINDOW_HEIGHT // 2 - 150)
        self.display_surface.blit(panel, panel_pos)
        
        # Title
        title = self.fonts['medium'].render("PAUSED", True, (50, 50, 50))
        title_pos = self.scale_pos(WINDOW_WIDTH // 2 - title.get_width() // 2, WINDOW_HEIGHT // 2 - 100)
        self.display_surface.blit(title, title_pos)
        
        # Buttons
        for button in self.pause_menu_buttons:
            button.draw(self.display_surface)
    
    def draw_game_over(self):
        """Draw game over screen"""
        # Draw game underneath
        self.draw_game_ui()
        
        # Panel
        panel = self.create_panel_surface(350, 400)
        panel_pos = self.scale_pos(WINDOW_WIDTH // 2 - 175, WINDOW_HEIGHT // 2 - 200)
        self.display_surface.blit(panel, panel_pos)
        
        # Title with shadow
        title_shadow = self.fonts['large'].render("GAME OVER", True, (100, 100, 100))
        title = self.fonts['large'].render("GAME OVER", True, (200, 50, 50))
        
        title_pos = self.scale_pos(WINDOW_WIDTH // 2 - title.get_width() // 2, WINDOW_HEIGHT // 2 - 150)
        shadow_pos = self.scale_pos(WINDOW_WIDTH // 2 - title.get_width() // 2 + 2, WINDOW_HEIGHT // 2 - 148)
        
        self.display_surface.blit(title_shadow, shadow_pos)
        self.display_surface.blit(title, title_pos)
        
        # Score
        score_text = self.fonts['medium'].render(f"Score: {self.score}", True, (50, 50, 50))
        score_pos = self.scale_pos(WINDOW_WIDTH // 2 - score_text.get_width() // 2, WINDOW_HEIGHT // 2 - 90)
        self.display_surface.blit(score_text, score_pos)
        
        # Level reached
        current_diff = DIFFICULTY_LEVELS.get(self.difficulty_level, DIFFICULTY_LEVELS[1])
        level_text = self.fonts['medium'].render(f"Level: {current_diff['name']}", True, current_diff["color"])
        level_pos = self.scale_pos(WINDOW_WIDTH // 2 - level_text.get_width() // 2, WINDOW_HEIGHT // 2 - 50)
        self.display_surface.blit(level_text, level_pos)
        
        # Coins
        coin_text = self.fonts['medium'].render(f"Coins: {self.coin_count}", True, (50, 50, 50))
        coin_pos = self.scale_pos(WINDOW_WIDTH // 2 - coin_text.get_width() // 2, WINDOW_HEIGHT // 2 - 10)
        self.display_surface.blit(coin_text, coin_pos)
        
        # High score
        if self.score >= self.high_score and self.score > 0:
            high_text = self.fonts['small'].render("NEW HIGH SCORE!", True, (255, 215, 0))
            high_pos = self.scale_pos(WINDOW_WIDTH // 2 - high_text.get_width() // 2, WINDOW_HEIGHT // 2 + 30)
            self.display_surface.blit(high_text, high_pos)
        else:
            high_text = self.fonts['small'].render(f"Best: {self.high_score}", True, (50, 50, 50))
            high_pos = self.scale_pos(WINDOW_WIDTH // 2 - high_text.get_width() // 2, WINDOW_HEIGHT // 2 + 30)
            self.display_surface.blit(high_text, high_pos)
        
        # Player name
        name_text = self.fonts['small'].render(f"Player: {self.player_name}", True, (50, 50, 50))
        name_pos = self.scale_pos(WINDOW_WIDTH // 2 - name_text.get_width() // 2, WINDOW_HEIGHT // 2 + 70)
        self.display_surface.blit(name_text, name_pos)
        
        # Buttons
        for button in self.game_over_buttons:
            button.draw(self.display_surface)
    
    def draw_leaderboard(self):
        """Draw leaderboard screen"""
        # Create game area surface
        game_surface = pygame.Surface((int(WINDOW_WIDTH * self.ui_scale), int(WINDOW_HEIGHT * self.ui_scale)))
        
        # Background
        for y in range(int(WINDOW_HEIGHT * self.ui_scale)):
            color_ratio = y / (WINDOW_HEIGHT * self.ui_scale)
            r = int(20 + (30 * color_ratio))
            g = int(30 + (40 * color_ratio))
            b = int(50 + (60 * color_ratio))
            pygame.draw.line(game_surface, (r, g, b), (0, y), (int(WINDOW_WIDTH * self.ui_scale), y))
        
        # Panel
        panel = self.create_panel_surface(400, 600)
        panel_rect = panel.get_rect(center=(int(WINDOW_WIDTH * self.ui_scale // 2), int(WINDOW_HEIGHT * self.ui_scale // 2)))
        game_surface.blit(panel, panel_rect)
        
        # Title
        title = self.fonts['medium'].render("LEADERBOARD", True, (50, 50, 50))
        title_rect = title.get_rect(center=(int(WINDOW_WIDTH * self.ui_scale // 2), panel_rect.top + int(40 * self.ui_scale)))
        game_surface.blit(title, title_rect)
        
        # Scores
        leaderboard = self.db.get_leaderboard()
        y_pos = panel_rect.top + int(100 * self.ui_scale)
        
        for i, (name, score, coins) in enumerate(leaderboard):
            # Background for top 3
            if i < 3:
                colors = [(255, 215, 0, 50), (192, 192, 192, 50), (205, 127, 50, 50)]
                entry_bg = pygame.Surface((int(350 * self.ui_scale), int(40 * self.ui_scale)), pygame.SRCALPHA)
                entry_bg.fill(colors[i])
                game_surface.blit(entry_bg, (panel_rect.left + int(25 * self.ui_scale), y_pos - int(5 * self.ui_scale)))
            
            # Medal and rank
            medals = ["🥇", "🥈", "🥉"]
            rank_text = medals[i] if i < 3 else f"{i+1}."
            rank = self.fonts['small'].render(rank_text, True, (50, 50, 50))
            game_surface.blit(rank, (panel_rect.left + int(40 * self.ui_scale), y_pos))
            
            # Name and score
            name_text = self.fonts['small'].render(f"{name}", True, (50, 50, 50))
            game_surface.blit(name_text, (panel_rect.left + int(80 * self.ui_scale), y_pos))
            
            score_text = self.fonts['small'].render(f"{score}", True, (50, 50, 50))
            game_surface.blit(score_text, (panel_rect.right - int(100 * self.ui_scale), y_pos))
            
            coin_text = self.fonts['small'].render(f"C:{coins}", True, (50, 50, 50))
            game_surface.blit(coin_text, (panel_rect.right - int(60 * self.ui_scale), y_pos))
            
            y_pos += int(45 * self.ui_scale)
            
            # Only show top 10
            if i >= 9:
                break
        
        # Blit game surface to center of screen
        game_rect = game_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.display_surface.blit(game_surface, game_rect)
        
        # Back button
        self.back_button.draw(self.display_surface)
    
    def draw_help_screen(self):
        """Draw help/tutorial screen"""
        # Create game area surface
        game_surface = pygame.Surface((int(WINDOW_WIDTH * self.ui_scale), int(WINDOW_HEIGHT * self.ui_scale)))
        
        # Background gradient
        for y in range(int(WINDOW_HEIGHT * self.ui_scale)):
            color_ratio = y / (WINDOW_HEIGHT * self.ui_scale)
            r = int(135 + (50 * color_ratio))
            g = int(206 + (30 * color_ratio))
            b = int(250 + (5 * color_ratio))
            pygame.draw.line(game_surface, (r, g, b), (0, y), (int(WINDOW_WIDTH * self.ui_scale), y))
        
        # Panel
        panel = self.create_panel_surface(400, 600)
        panel_rect = panel.get_rect(center=(int(WINDOW_WIDTH * self.ui_scale // 2), int(WINDOW_HEIGHT * self.ui_scale // 2)))
        game_surface.blit(panel, panel_rect)
        
        # Title
        title = self.fonts['medium'].render("HOW TO PLAY", True, (50, 50, 50))
        title_rect = title.get_rect(center=(int(WINDOW_WIDTH * self.ui_scale // 2), panel_rect.top + int(40 * self.ui_scale)))
        game_surface.blit(title, title_rect)
        
        # Instructions
        instructions = [
            "• Click or tap to make the bird fly",
            "• Avoid hitting pipes and the ground",
            "• Collect coins for bonus points",
            "• The game gets harder as you progress",
            "• Press the pause button to pause",
            "",
            "DIFFICULTY LEVELS:",
            "• Tutorial → Easy → Normal → Hard",
            "• Each level increases speed and reduces gaps",
            "",
            "CONTROLS:",
            "• Mouse click: Jump/Select",
            "• ESC: Pause game",
            "• F11: Toggle fullscreen (if supported)",
            "",
            "TIPS:",
            "• Stay in the middle when possible",
            "• Time your jumps carefully",
            "• Watch the difficulty indicator!"
        ]
        
        y_pos = panel_rect.top + int(100 * self.ui_scale)
        for line in instructions:
            if line.startswith("DIFFICULTY") or line.startswith("CONTROLS:") or line.startswith("TIPS:"):
                text = self.fonts['small'].render(line, True, (50, 50, 50))
                y_pos += int(10 * self.ui_scale)
            else:
                text = self.fonts['tiny'].render(line, True, (50, 50, 50))
            
            game_surface.blit(text, (panel_rect.left + int(40 * self.ui_scale), y_pos))
            y_pos += int(25 * self.ui_scale)
        
        # Blit game surface to center of screen
        game_rect = game_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.display_surface.blit(game_surface, game_rect)
        
        # Back button
        self.back_button.draw(self.display_surface)
    
    def handle_input(self, event):
        """Handle all input events based on game state"""
        # Global events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == "playing":
                    self.toggle_pause()
                elif self.state == "paused":
                    self.toggle_pause()
            elif event.key == pygame.K_F11:
                # Toggle fullscreen (basic implementation)
                pass
        
        # State-specific events
        if self.state == "main_menu":
            for button in self.main_menu_buttons:
                button.handle_event(event)
        
        elif self.state == "name_input":
            self.name_input.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and self.name_input.text:
                self.player_name = self.name_input.text
                self.reset_game()
                self.sounds['button'].play()
        
        elif self.state == "playing":
            if event.type == pygame.MOUSEBUTTONDOWN and self.active:
                self.plane.jump()
            
            if event.type == self.obstacle_timer and self.active:
                current_diff = DIFFICULTY_LEVELS.get(self.difficulty_level, DIFFICULTY_LEVELS[1])
                obstacle = Obstacle([self.all_sprites, self.collision_sprites], self.scale_factor * 1.1, current_diff["gap"])
                obstacle.speed = self.obstacle_speed
            
            if event.type == self.coin_timer and self.active:
                if random.random() < self.coin_spawn_chance:
                    Coin(self.coins, self.scale_factor, self.obstacle_speed, self.ui_scale)
            
            self.pause_button.handle_event(event)
        
        elif self.state == "paused":
            for button in self.pause_menu_buttons:
                button.handle_event(event)
        
        elif self.state == "game_over":
            for button in self.game_over_buttons:
                button.handle_event(event)
        
        elif self.state == "leaderboard" or self.state == "help":
            self.back_button.handle_event(event)
    
    def run(self):
        """Main game loop"""
        last_time = time.time()
        
        while True:
            dt = time.time() - last_time
            last_time = time.time()
            
            # Cap delta time to prevent large jumps
            dt = min(dt, 0.05)
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                self.handle_input(event)
            
            # Update
            self.update_effects(dt)
            
            if self.state == "playing" and self.active:
                self.all_sprites.update(dt)
                self.coins.update(dt)
                self.handle_collision()
                self.check_coin_collection()
                self.adjust_difficulty()
            
            # Draw
            self.draw_ui()
            
            pygame.display.update()
            self.clock.tick(FRAMERATE)

if __name__ == '__main__':
    game = Game()
    game.run()
