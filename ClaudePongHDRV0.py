import pygame
import random
import math
import sys

# Initialize pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

# Constants
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 15, 100
BALL_SIZE = 15
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
SCORE_FONT = pygame.font.Font(None, 74)
MENU_FONT = pygame.font.Font(None, 64)
TEXT_FONT = pygame.font.Font(None, 36)
WINNING_SCORE = 5

# NES-style sound generation
def generate_nes_sound(frequency, duration, volume=0.5, duty_cycle=0.5):
    """Generate an NES-style square wave sound"""
    sample_rate = 44100
    num_samples = int(duration * sample_rate)
    buf = bytearray(num_samples)
    
    # Generate a square wave with the given duty cycle
    for i in range(num_samples):
        t = i / sample_rate
        if (t * frequency) % 1 < duty_cycle:
            buf[i] = 127 + int(127 * volume)
        else:
            buf[i] = 127 - int(127 * volume)
    
    return pygame.mixer.Sound(buffer=bytes(buf))

# Generate sound effects
hit_paddle_sound = generate_nes_sound(440, 0.1, 0.7)  # A4 note
hit_wall_sound = generate_nes_sound(330, 0.1, 0.5)    # E4 note
score_sound = generate_nes_sound(220, 0.3, 0.8)       # A3 note
menu_select_sound = generate_nes_sound(660, 0.1, 0.6)  # E5 note
game_over_sound = generate_nes_sound(165, 0.5, 0.9)    # E3 note

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")
clock = pygame.time.Clock()

# Game objects
class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.velocity = 0
        self.speed = 10
    
    def move(self, direction):
        self.velocity = direction * self.speed
    
    def update(self):
        self.rect.y += self.velocity
        # Keep paddle on screen
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
    
    def draw(self):
        pygame.draw.rect(screen, WHITE, self.rect)

class Ball:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.rect = pygame.Rect(WIDTH // 2 - BALL_SIZE // 2, 
                               HEIGHT // 2 - BALL_SIZE // 2, 
                               BALL_SIZE, BALL_SIZE)
        # Random angle between -45 and 45 degrees or 135 and 225 degrees
        angle = random.choice([-1, 1]) * random.uniform(math.pi/6, math.pi/3)
        self.dx = math.cos(angle) * 7
        self.dy = math.sin(angle) * 7
    
    def update(self, left_paddle, right_paddle):
        self.rect.x += self.dx
        self.rect.y += self.dy
        
        # Wall collision (top and bottom)
        if self.rect.top <= 0 or self.rect.bottom >= HEIGHT:
            self.dy *= -1
            hit_wall_sound.play()
        
        # Paddle collision
        if self.rect.colliderect(left_paddle.rect) and self.dx < 0:
            # Calculate bounce angle based on where the ball hit the paddle
            relative_intersect_y = (left_paddle.rect.y + PADDLE_HEIGHT/2) - self.rect.centery
            normalized_relative_intersect_y = relative_intersect_y / (PADDLE_HEIGHT/2)
            bounce_angle = normalized_relative_intersect_y * (math.pi/3)  # Max 60 degrees
            
            self.dx = abs(self.dx) * 1.05  # Speed up slightly
            self.dy = -math.sin(bounce_angle) * math.sqrt(self.dx**2 + self.dy**2)
            hit_paddle_sound.play()
            
        elif self.rect.colliderect(right_paddle.rect) and self.dx > 0:
            # Calculate bounce angle based on where the ball hit the paddle
            relative_intersect_y = (right_paddle.rect.y + PADDLE_HEIGHT/2) - self.rect.centery
            normalized_relative_intersect_y = relative_intersect_y / (PADDLE_HEIGHT/2)
            bounce_angle = normalized_relative_intersect_y * (math.pi/3)  # Max 60 degrees
            
            self.dx = -abs(self.dx) * 1.05  # Speed up slightly
            self.dy = -math.sin(bounce_angle) * math.sqrt(self.dx**2 + self.dy**2)
            hit_paddle_sound.play()
        
        # Cap ball speed
        speed = math.sqrt(self.dx**2 + self.dy**2)
        if speed > 15:
            self.dx = (self.dx / speed) * 15
            self.dy = (self.dy / speed) * 15
        
        # Check for scoring
        if self.rect.left <= 0:
            score_sound.play()
            return 2  # Player 2 scores
        elif self.rect.right >= WIDTH:
            score_sound.play()
            return 1  # Player 1 scores
        return 0  # No scoring
    
    def draw(self):
        pygame.draw.rect(screen, WHITE, self.rect)

class Button:
    def __init__(self, x, y, width, height, text, font, color=WHITE, hover_color=GRAY):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        
    def draw(self):
        color = self.hover_color if self.is_hovered else self.color
        text_surf = self.font.render(self.text, True, color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
        # Draw button outline
        pygame.draw.rect(screen, color, self.rect, 2)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def is_clicked(self, pos, click):
        return self.rect.collidepoint(pos) and click

# Simple AI for player 2
def update_ai(paddle, ball):
    # Move towards the ball with some delay
    if ball.rect.centery < paddle.rect.centery - 10:
        paddle.move(-1)
    elif ball.rect.centery > paddle.rect.centery + 10:
        paddle.move(1)
    else:
        paddle.move(0)

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2

def main_menu():
    title_text = MENU_FONT.render("PONG", True, WHITE)
    title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//4))
    
    single_player_button = Button(WIDTH//2 - 150, HEIGHT//2 - 30, 300, 60, 
                                 "Single Player", TEXT_FONT)
    two_player_button = Button(WIDTH//2 - 150, HEIGHT//2 + 50, 300, 60, 
                              "Two Players", TEXT_FONT)
    quit_button = Button(WIDTH//2 - 150, HEIGHT//2 + 130, 300, 60, 
                        "Quit", TEXT_FONT)
    
    menu_running = True
    ai_enabled = True
    
    while menu_running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_clicked = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        
        # Check button interactions
        single_player_button.check_hover(mouse_pos)
        two_player_button.check_hover(mouse_pos)
        quit_button.check_hover(mouse_pos)
        
        if single_player_button.is_clicked(mouse_pos, mouse_clicked):
            menu_select_sound.play()
            ai_enabled = True
            menu_running = False
        elif two_player_button.is_clicked(mouse_pos, mouse_clicked):
            menu_select_sound.play()
            ai_enabled = False
            menu_running = False
        elif quit_button.is_clicked(mouse_pos, mouse_clicked):
            menu_select_sound.play()
            pygame.quit()
            sys.exit()
        
        # Draw menu
        screen.fill(BLACK)
        screen.blit(title_text, title_rect)
        single_player_button.draw()
        two_player_button.draw()
        quit_button.draw()
        
        # Draw pong animation in background
        pygame.display.flip()
        clock.tick(FPS)
    
    return ai_enabled

def game_over_screen(winner):
    game_over_sound.play()
    
    if winner == 1:
        title_text = MENU_FONT.render("PLAYER 1 WINS!", True, WHITE)
    else:
        title_text = MENU_FONT.render("PLAYER 2 WINS!", True, WHITE)
    
    title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//3))
    
    restart_button = Button(WIDTH//2 - 150, HEIGHT//2, 300, 60, 
                           "Play Again", TEXT_FONT)
    menu_button = Button(WIDTH//2 - 150, HEIGHT//2 + 80, 300, 60, 
                        "Main Menu", TEXT_FONT)
    
    game_over_running = True
    restart_game = False
    return_to_menu = False
    
    while game_over_running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_clicked = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    restart_game = True
                    game_over_running = False
                elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:
                    return_to_menu = True
                    game_over_running = False
        
        # Check button interactions
        restart_button.check_hover(mouse_pos)
        menu_button.check_hover(mouse_pos)
        
        if restart_button.is_clicked(mouse_pos, mouse_clicked):
            menu_select_sound.play()
            restart_game = True
            game_over_running = False
        elif menu_button.is_clicked(mouse_pos, mouse_clicked):
            menu_select_sound.play()
            return_to_menu = True
            game_over_running = False
        
        # Draw game over screen
        screen.fill(BLACK)
        screen.blit(title_text, title_rect)
        
        prompt_text = TEXT_FONT.render("Press Y to restart or N to return to menu", True, WHITE)
        prompt_rect = prompt_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        screen.blit(prompt_text, prompt_rect)
        
        restart_button.draw()
        menu_button.draw()
        
        pygame.display.flip()
        clock.tick(FPS)
    
    return restart_game, return_to_menu

def main():
    game_state = MENU
    ai_enabled = True
    
    while True:
        if game_state == MENU:
            ai_enabled = main_menu()
            game_state = PLAYING
            
            # Create game objects
            player1 = Paddle(20, HEIGHT // 2 - PADDLE_HEIGHT // 2)
            player2 = Paddle(WIDTH - 20 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2)
            ball = Ball()
            
            # Reset scores
            score1 = 0
            score2 = 0
            
        elif game_state == PLAYING:
            # Game loop
            running = True
            while running:
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_w:
                            player1.move(-1)
                        elif event.key == pygame.K_s:
                            player1.move(1)
                        elif event.key == pygame.K_UP and not ai_enabled:
                            player2.move(-1)
                        elif event.key == pygame.K_DOWN and not ai_enabled:
                            player2.move(1)
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                            game_state = MENU
                    elif event.type == pygame.KEYUP:
                        if event.key in (pygame.K_w, pygame.K_s):
                            player1.move(0)
                        elif event.key in (pygame.K_UP, pygame.K_DOWN) and not ai_enabled:
                            player2.move(0)
                
                # Update game state
                player1.update()
                
                if ai_enabled:
                    update_ai(player2, ball)
                player2.update()
                
                # Update ball and check for scoring
                result = ball.update(player1, player2)
                if result == 1:
                    score1 += 1
                    ball.reset()
                    if score1 >= WINNING_SCORE:
                        running = False
                        game_state = GAME_OVER
                        winner = 1
                elif result == 2:
                    score2 += 1
                    ball.reset()
                    if score2 >= WINNING_SCORE:
                        running = False
                        game_state = GAME_OVER
                        winner = 2
                
                # Draw everything
                screen.fill(BLACK)
                
                # Draw center line
                for y in range(0, HEIGHT, 30):
                    pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 5, y, 10, 15))
                
                # Draw paddles and ball
                player1.draw()
                player2.draw()
                ball.draw()
                
                # Draw scores
                score1_text = SCORE_FONT.render(str(score1), True, WHITE)
                score2_text = SCORE_FONT.render(str(score2), True, WHITE)
                screen.blit(score1_text, (WIDTH // 4, 20))
                screen.blit(score2_text, (3 * WIDTH // 4 - score2_text.get_width(), 20))
                
                # Draw game mode
                mode_text = TEXT_FONT.render("Single Player" if ai_enabled else "Two Players", True, GRAY)
                screen.blit(mode_text, (WIDTH // 2 - mode_text.get_width() // 2, HEIGHT - 30))
                
                # Update the display
                pygame.display.flip()
                
                # Cap the frame rate
                clock.tick(FPS)
                
        elif game_state == GAME_OVER:
            restart_game, return_to_menu = game_over_screen(winner)
            
            if restart_game:
                game_state = PLAYING
                # Create game objects
                player1 = Paddle(20, HEIGHT // 2 - PADDLE_HEIGHT // 2)
                player2 = Paddle(WIDTH - 20 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2)
                ball = Ball()
                
                # Reset scores
                score1 = 0
                score2 = 0
            elif return_to_menu:
                game_state = MENU

if __name__ == "__main__":
    main()
