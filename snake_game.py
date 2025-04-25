import os
import time
import random
import keyboard
import threading
from collections import deque

# Game constants
WIDTH = 20
HEIGHT = 10
FOOD_CHAR = 'F'
SNAKE_CHAR = 'O'
SNAKE_HEAD_CHAR = 'X'
EMPTY_CHAR = ' '
WALL_CHAR = '#'
REFRESH_RATE = 0.2  # seconds between frames

# Direction vectors (row, col)
UP = (-1, 0)
DOWN = (1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)

class Snake:
    def __init__(self, start_pos=(HEIGHT // 2, WIDTH // 2)):
        self.body = deque([start_pos])
        self.direction = RIGHT
        self.grow_next = False
        self.body_length = 1  # Head only
        
    def head(self):
        return self.body[0]
        
    def move(self):
        head_row, head_col = self.head()
        dir_row, dir_col = self.direction
        new_head = (head_row + dir_row, head_col + dir_col)
        
        self.body.appendleft(new_head)
        if not self.grow_next:
            self.body.pop()
        else:
            self.grow_next = False
            
    def grow(self):
        self.grow_next = True
        self.body_length += 1
        
    def change_direction(self, new_dir):
        # Prevent 180-degree turns
        head_row, head_col = self.head()
        dir_row, dir_col = self.direction
        new_dir_row, new_dir_col = new_dir
        
        if (dir_row, dir_col) != (-new_dir_row, -new_dir_col):
            self.direction = new_dir
            
    def check_collision_with_self(self):
        return self.head() in list(self.body)[1:]
        
    def check_wall_collision(self):
        row, col = self.head()
        return row < 0 or row >= HEIGHT or col < 0 or col >= WIDTH

class Game:
    def __init__(self, target_word="Bravin"):
        self.snake = Snake()
        self.food = None
        self.score = 0
        self.game_over = False
        self.target_word = target_word
        self.body_letters = list(self.target_word)
        self.generate_food()
        
    def generate_food(self):
        # Find all empty positions
        snake_positions = list(self.snake.body)
        empty_positions = [(r, c) for r in range(HEIGHT) for c in range(WIDTH) 
                           if (r, c) not in snake_positions]
        
        if empty_positions:
            self.food = random.choice(empty_positions)
        else:
            # No empty positions, you've won!
            self.food = None
            
    def update(self):
        if self.game_over:
            return
            
        self.snake.move()
        
        # Check for collisions
        if self.snake.check_wall_collision() or self.snake.check_collision_with_self():
            self.game_over = True
            return
            
        # Check if snake ate food
        if self.snake.head() == self.food:
            self.snake.grow()
            self.score += 10
            self.generate_food()
            
    def draw(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Draw top wall
        print(WALL_CHAR * (WIDTH + 2))
        
        # Show target word and progress
        target_display = f"Target Word: {self.target_word}"
        progress = min(self.snake.body_length - 1, len(self.target_word))
        progress_display = f"Progress: {progress}/{len(self.target_word)}"
        print(f"{target_display.ljust(WIDTH//2)}{progress_display.rjust(WIDTH//2)}")
        
        # Draw game board
        for r in range(HEIGHT):
            print(WALL_CHAR, end='')
            for c in range(WIDTH):
                pos = (r, c)
                
                if pos == self.snake.head():
                    print(SNAKE_HEAD_CHAR, end='')
                elif pos in self.snake.body:
                    # Find position in the snake body
                    body_index = list(self.snake.body).index(pos)
                    
                    # The first segment after head is index 1, which should be the first letter
                    # Letters should appear in the order of the target word
                    if body_index > 0 and body_index <= len(self.body_letters):
                        letter_index = body_index - 1
                        print(self.body_letters[letter_index], end='')
                    else:
                        print(SNAKE_CHAR, end='')
                elif pos == self.food:
                    print(FOOD_CHAR, end='')
                else:
                    print(EMPTY_CHAR, end='')
            print(WALL_CHAR)
            
        # Draw bottom wall
        print(WALL_CHAR * (WIDTH + 2))
        
        # Draw score
        print(f"Score: {self.score}")
        
        if self.game_over:
            print("Game Over! Press 'q' to quit or 'r' to restart.")
            
def key_listener(game):
    while not game.game_over:
        if keyboard.is_pressed('up') or keyboard.is_pressed('w'):
            game.snake.change_direction(UP)
        elif keyboard.is_pressed('down') or keyboard.is_pressed('s'):
            game.snake.change_direction(DOWN)
        elif keyboard.is_pressed('left') or keyboard.is_pressed('a'):
            game.snake.change_direction(LEFT)
        elif keyboard.is_pressed('right') or keyboard.is_pressed('d'):
            game.snake.change_direction(RIGHT)
        
        time.sleep(0.05)  # Small delay to prevent CPU hogging

def get_valid_word():
    while True:
        word = input("Enter a word for the snake to spell (default is 'Bravin'): ").strip()
        if not word:
            return "Bravin"  # Default
        if len(word) > 0:
            return word
        print("Please enter at least one character.")

def main():
    print("Snake Game - Press any arrow key or WASD to start")
    print("Press 'q' to quit at any time")
    
    # Get the target word from user
    target_word = get_valid_word()
    print(f"Snake will spell: {target_word}")
    print("Starting game in 2 seconds...")
    time.sleep(2)
    
    while True:
        game = Game(target_word)
        
        # Start key listener thread
        listener_thread = threading.Thread(target=key_listener, args=(game,))
        listener_thread.daemon = True
        listener_thread.start()
        
        # Main game loop
        try:
            while not game.game_over:
                game.update()
                game.draw()
                time.sleep(REFRESH_RATE)
                
                # Check for quit
                if keyboard.is_pressed('q'):
                    return
                    
            # Game over, wait for restart or quit
            while game.game_over:
                if keyboard.is_pressed('q'):
                    return
                if keyboard.is_pressed('r'):
                    break
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            return

if __name__ == "__main__":
    main()

