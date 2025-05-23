import pygame

class Button:
    def __init__(self, x, y, width, height, text, font, action=None, sound=None):
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = (x, y)
        self.text = text
        self.font = font
        self.action = action
        self.hovered = False
        self.sound = sound  # Sound is now passed in, not loaded directly
        
        # Button states - IMPROVED COLORS FOR BETTER VISIBILITY
        self.normal_color = (230, 230, 230)
        self.hover_color = (180, 210, 255)  # Lighter blue for better contrast
        self.text_color = (50, 50, 50)
        self.hover_text_color = (20, 20, 100)  # Dark blue instead of black for better visibility
    
    def draw(self, surface):
        # Draw button background
        color = self.hover_color if self.hovered else self.normal_color
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 2, border_radius=12)
        
        # Draw text
        text_color = self.hover_text_color if self.hovered else self.text_color
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
        # Draw shadow when hovered
        if self.hovered:
            shadow = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 30))
            surface.blit(shadow, (self.rect.x + 3, self.rect.y + 3), special_flags=pygame.BLEND_RGBA_MULT)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) and event.button == 1:
                if self.sound:
                    self.sound.play()
                if self.action:
                    self.action()
                return True
        return False

class Panel:
    def __init__(self, x, y, width, height, color=(230, 230, 230), alpha=255):
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = (x, y)
        self.color = color
        self.alpha = alpha
    
    def draw(self, surface):
        panel = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel.fill((*self.color, self.alpha))
        pygame.draw.rect(panel, (100, 100, 100, self.alpha), (0, 0, self.rect.width, self.rect.height), 2, border_radius=12)
        surface.blit(panel, self.rect)

class TextInput:
    def __init__(self, x, y, width, height, text="", font=None, max_length=20):
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = (x, y)
        self.text = text
        self.font = font
        self.max_length = max_length
        self.active = True
        self.cursor_visible = True
        self.cursor_timer = 0
        
        # Colors
        self.inactive_color = (230, 230, 230)
        self.active_color = (255, 255, 255)
        self.text_color = (50, 50, 50)
        self.cursor_color = (0, 0, 0)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return True
            elif len(self.text) < self.max_length and event.unicode.isalnum():
                self.text += event.unicode
        
        return False
    
    def update(self, dt):
        # Blink cursor
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self, surface):
        # Draw input box
        color = self.active_color if self.active else self.inactive_color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (100, 100, 100), self.rect, 2, border_radius=8)
        
        # Draw text
        if self.text:
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)
        
        # Draw cursor
        if self.active and self.cursor_visible:
            if self.text:
                text_surf = self.font.render(self.text, True, self.text_color)
                cursor_x = self.rect.centerx + text_surf.get_width() // 2 + 5
            else:
                cursor_x = self.rect.centerx
            
            cursor_height = self.font.get_height() * 0.8
            cursor_y = self.rect.centery - cursor_height // 2
            pygame.draw.line(surface, self.cursor_color, (cursor_x, cursor_y), 
                            (cursor_x, cursor_y + cursor_height), 2)

class Label:
    def __init__(self, x, y, text, font, color=(50, 50, 50), centered=True):
        self.pos = (x, y)
        self.text = text
        self.font = font
        self.color = color
        self.centered = centered
        self.shadow = False
        self.shadow_color = (0, 0, 0)
        self.shadow_offset = (2, 2)
    
    def draw(self, surface):
        text_surf = self.font.render(self.text, True, self.color)
        
        if self.centered:
            text_rect = text_surf.get_rect(center=self.pos)
        else:
            text_rect = text_surf.get_rect(topleft=self.pos)
        
        if self.shadow:
            shadow_surf = self.font.render(self.text, True, self.shadow_color)
            shadow_rect = shadow_surf.get_rect(topleft=(text_rect.x + self.shadow_offset[0], 
                                                      text_rect.y + self.shadow_offset[1]))
            surface.blit(shadow_surf, shadow_rect)
        
        surface.blit(text_surf, text_rect)
