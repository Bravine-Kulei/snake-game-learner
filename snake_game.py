import os
import time
import random
import keyboard
import threading
import json
from collections import deque
from colorama import init, Fore, Back, Style
# Initialize colorama
init()

# Game constants
WIDTH = 20
HEIGHT = 10
FOOD_CHAR = 'F'
SNAKE_CHAR = 'O'
SNAKE_HEAD_CHAR = 'X'
EMPTY_CHAR = ' '
WALL_CHAR = '#'
REFRESH_RATE = 0.2  # seconds between frames

# Word dictionaries by difficulty
WORD_LISTS = {
    "easy": [
        "cat", "dog", "hat", "pen", "sun", "box", "run", "jump", "fish", "book",
        "tree", "ball", "tent", "frog", "ship", "cup", "coin", "car", "star", "moon"
    ],
    "medium": [
        "apple", "river", "house", "light", "snake", "bread", "chair", "pencil", "horse", "flower",
        "window", "school", "friend", "garden", "orange", "yellow", "planet", "puzzle", "rabbit", "rocket"
    ],
    "hard": [
        "elephant", "dinosaur", "triangle", "computer", "butterfly", "mountain", "language", "umbrella", "vegetable", "beautiful",
        "chocolate", "adventure", "playground", "rectangle", "discovery", "education", "dictionary", "telephone", "wonderful", "happiness"
    ]
}

# Encouraging messages
MESSAGES = [
    "Great job!", "Awesome!", "Keep going!", "You're doing great!", "Fantastic!",
    "Excellent!", "Well done!", "Amazing!", "Super!", "Perfect!", "Brilliant!",
    "You got it!", "Nice work!", "Terrific!", "Wonderful!", "Outstanding!",
    "Way to go!", "Keep it up!", "Good thinking!", "You're a star!"
]

# Stats file
STATS_FILE = "spelling_game_stats.json"

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
    def __init__(self, target_word="snake", difficulty="medium"):
        self.snake = Snake()
        self.food = None
        self.score = 0
        self.game_over = False
        self.target_word = target_word
        self.body_letters = list(self.target_word)
        self.difficulty = difficulty
        self.start_time = time.time()
        self.last_letter_time = self.start_time
        self.letters_collected = 0
        self.show_hint = False
        self.message = ""
        self.message_timer = 0
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
        # Check if snake ate food
        if self.snake.head() == self.food:
            self.snake.grow()
            
            # Calculate time-based score
            current_time = time.time()
            letter_time = current_time - self.last_letter_time
            time_bonus = max(0, int(20 - letter_time))
            difficulty_multiplier = {"easy": 1, "medium": 2, "hard": 3}[self.difficulty]
            points = 10 + (time_bonus * difficulty_multiplier)
            
            self.score += points
            self.letters_collected += 1
            self.last_letter_time = current_time
            
            # Display encouraging message
            self.message = random.choice(MESSAGES)
            self.message_timer = 2  # Display for 2 seconds
            
            # Check if word completed
            if self.letters_collected >= len(self.target_word):
                self.handle_word_completion()
                
            self.generate_food()
            
    def handle_word_completion(self):
        # Calculate completion bonus
        total_time = time.time() - self.start_time
        time_bonus = max(0, int(100 - total_time))
        completion_bonus = time_bonus + (len(self.target_word) * 20)
        self.score += completion_bonus
        
        # Update statistics
        self.update_stats()
    
    def update_stats(self):
        stats = self.load_stats()
        
        # Update stats
        stats["words_completed"] += 1
        stats["total_score"] += self.score
        stats["words_by_difficulty"][self.difficulty] += 1
        
        # Add word to completed list if not already there
        if self.target_word not in stats["completed_words"]:
            stats["completed_words"].append(self.target_word)
        
        # Save stats
        self.save_stats(stats)
    
    def load_stats(self):
        try:
            with open(STATS_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Initialize new stats if file doesn't exist or is corrupt
            return {
                "words_completed": 0,
                "total_score": 0,
                "words_by_difficulty": {"easy": 0, "medium": 0, "hard": 0},
                "completed_words": []
            }
    
    def save_stats(self, stats):
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f)
    
    def draw(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Draw top wall
        print(Fore.CYAN + WALL_CHAR * (WIDTH + 2) + Style.RESET_ALL)
        
        # Show target word and progress
        target_display = f"Target Word: {Fore.GREEN}{self.target_word.upper()}{Style.RESET_ALL}"
        progress = min(self.snake.body_length - 1, len(self.target_word))
        progress_display = f"Progress: {Fore.YELLOW}{progress}/{len(self.target_word)}{Style.RESET_ALL}"
        print(f"{target_display.ljust(WIDTH//2 + 20)}{progress_display.rjust(WIDTH//2)}")
        
        # Show hint if enabled
        if self.show_hint and progress < len(self.target_word):
            next_letter = self.body_letters[progress]
            hint_display = f"Hint: Next letter is {Fore.MAGENTA}{next_letter.upper()}{Style.RESET_ALL}"
            print(hint_display.center(WIDTH + 2))
        
        # Draw game board
        for r in range(HEIGHT):
            print(Fore.CYAN + WALL_CHAR + Style.RESET_ALL, end='')
            for c in range(WIDTH):
                pos = (r, c)
                
                if pos == self.snake.head():
                    print(Fore.GREEN + SNAKE_HEAD_CHAR + Style.RESET_ALL, end='')
                elif pos in self.snake.body:
                    # Find position in the snake body
                    body_index = list(self.snake.body).index(pos)
                    
                    # The first segment after head is index 1, which should be the first letter
                    # Letters should appear in the order of the target word
                    if body_index > 0 and body_index <= len(self.body_letters):
                        letter_index = body_index - 1
                        print(Fore.YELLOW + self.body_letters[letter_index].upper() + Style.RESET_ALL, end='')
                    else:
                        print(Fore.BLUE + SNAKE_CHAR + Style.RESET_ALL, end='')
                elif pos == self.food:
                    next_index = min(self.letters_collected, len(self.target_word) - 1)
                    food_letter = self.body_letters[next_index] if next_index < len(self.body_letters) else FOOD_CHAR
                    print(Fore.MAGENTA + food_letter.upper() + Style.RESET_ALL, end='')
                else:
                    print(EMPTY_CHAR, end='')
            print(Fore.CYAN + WALL_CHAR + Style.RESET_ALL)
            
        # Draw bottom wall
        print(Fore.CYAN + WALL_CHAR * (WIDTH + 2) + Style.RESET_ALL)
        
        # Draw score and multiplier
        multiplier = {"easy": 1, "medium": 2, "hard": 3}[self.difficulty]
        print(f"Score: {Fore.GREEN}{self.score}{Style.RESET_ALL}  Difficulty: {Fore.YELLOW}{self.difficulty.capitalize()}{Style.RESET_ALL}  Multiplier: {Fore.GREEN}x{multiplier}{Style.RESET_ALL}")
        
        # Display encouraging message
        if self.message and self.message_timer > 0:
            self.message_timer -= REFRESH_RATE
            print(Fore.MAGENTA + self.message + Style.RESET_ALL)
        
        # Display controls
        print(f"Controls: {Fore.CYAN}Arrows/WASD{Style.RESET_ALL} to move, {Fore.CYAN}H{Style.RESET_ALL} for hint, {Fore.CYAN}P{Style.RESET_ALL} to pause")
        
        if self.game_over:
            print(f"{Fore.RED}Game Over!{Style.RESET_ALL} Press 'q' to quit or 'r' to restart.")
            
            # Show summary
            if self.letters_collected > 0:
                completion_percent = (self.letters_collected / len(self.target_word)) * 100
                print(f"\nWord: {Fore.GREEN}{self.target_word.upper()}{Style.RESET_ALL}")
                print(f"Letters collected: {Fore.YELLOW}{self.letters_collected}/{len(self.target_word)}{Style.RESET_ALL}")
                print(f"Completion: {Fore.GREEN}{completion_percent:.1f}%{Style.RESET_ALL}")
                print(f"Final score: {Fore.GREEN}{self.score}{Style.RESET_ALL}")
            
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
        elif keyboard.is_pressed('h'):
            game.show_hint = True
        
        time.sleep(0.05)  # Small delay to prevent CPU hogging
def select_difficulty():
    """Allow user to select a difficulty level"""
    print(f"\n{Fore.CYAN}===== SELECT DIFFICULTY ====={Style.RESET_ALL}")
    print(f"{Fore.GREEN}1. Easy{Style.RESET_ALL} - Short words (3-4 letters)")
    print(f"{Fore.YELLOW}2. Medium{Style.RESET_ALL} - Medium words (5-6 letters)")
    print(f"{Fore.RED}3. Hard{Style.RESET_ALL} - Long words (7+ letters)")
    print(f"{Fore.MAGENTA}4. View words in each difficulty{Style.RESET_ALL}")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        if choice == "1":
            return "easy"
        elif choice == "2":
            return "medium"
        elif choice == "3":
            return "hard"
        elif choice == "4":
            view_word_lists()
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")
            
def view_word_lists():
    """Display the word lists for each difficulty level"""
    print(f"\n{Fore.CYAN}===== WORD LISTS BY DIFFICULTY ====={Style.RESET_ALL}")
    
    for difficulty, words in WORD_LISTS.items():
        color = Fore.GREEN if difficulty == "easy" else Fore.YELLOW if difficulty == "medium" else Fore.RED
        print(f"\n{color}{difficulty.capitalize()} Words:{Style.RESET_ALL}")
        
        # Print words in multiple columns
        column_width = 15
        num_columns = 4
        rows = [words[i:i+num_columns] for i in range(0, len(words), num_columns)]
        
        for row in rows:
            print("  " + "".join(word.ljust(column_width) for word in row))
    
    input(f"\n{Fore.CYAN}Press Enter to return to difficulty selection...{Style.RESET_ALL}")

def get_word_for_difficulty(difficulty):
    """Get either a random word from the given difficulty or allow user to input a custom word"""
    print(f"\n{Fore.CYAN}===== WORD SELECTION ====={Style.RESET_ALL}")
    print(f"1. Use a random {difficulty} word")
    print(f"2. Enter your own word")
    
    while True:
        choice = input("\nEnter your choice (1-2): ").strip()
        if choice == "1":
            word = random.choice(WORD_LISTS[difficulty])
            print(f"\nRandom word selected: {Fore.GREEN}{word}{Style.RESET_ALL}")
            return word
        elif choice == "2":
            while True:
                word = input("\nEnter a word for the snake to spell: ").strip().lower()
                if len(word) > 0:
                    return word
                print("Please enter at least one character.")
        else:
            print("Invalid choice. Please enter 1 or 2.")
        print("Please enter at least one character.")
def main():
    print(f"{Fore.CYAN}========================================{Style.RESET_ALL}")
    print(f"{Fore.GREEN}SPELLING SNAKE - EDUCATIONAL EDITION{Style.RESET_ALL}")
    print(f"{Fore.CYAN}========================================{Style.RESET_ALL}")
    print("Move the snake to collect letters in the correct order!")
    print("Press 'q' to quit at any time, 'h' for hints")
    
    # Select difficulty level
    difficulty = select_difficulty()
    
    # Get the target word based on difficulty
    target_word = get_word_for_difficulty(difficulty)
    
    # Show scoring multipliers
    multipliers = {"easy": 1, "medium": 2, "hard": 3}
    print(f"\nDifficulty: {Fore.YELLOW}{difficulty.capitalize()}{Style.RESET_ALL}")
    print(f"Scoring multiplier: {Fore.GREEN}x{multipliers[difficulty]}{Style.RESET_ALL}")
    print(f"Snake will spell: {Fore.MAGENTA}{target_word.upper()}{Style.RESET_ALL}")
    print("\nStarting game in 3 seconds...")
    time.sleep(3)
    time.sleep(2)
    
    while True:
        game = Game(target_word, difficulty)
        
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
                game.draw()  # Keep refreshing the display
                if keyboard.is_pressed('q'):
                    return
                if keyboard.is_pressed('r'):
                    # Reset difficulty and word selection for new game
                    print("\nStarting a new game...")
                    difficulty = select_difficulty()
                    target_word = get_word_for_difficulty(difficulty)
                    print(f"\nNew word: {Fore.MAGENTA}{target_word.upper()}{Style.RESET_ALL}")
                    print("Starting in 2 seconds...")
                    time.sleep(2)
                    break
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            return

if __name__ == "__main__":
    main()

