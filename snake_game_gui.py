import tkinter as tk
from tkinter import ttk, font, messagebox
import random
import json
import time
from collections import deque

# Game constants
GRID_SIZE = 25  # Size of each cell in pixels
GRID_WIDTH = 20  # Number of cells horizontally
GRID_HEIGHT = 15  # Number of cells vertically
GAME_SPEED = 200  # Milliseconds between frames (lower = faster)

# Colors (modern theme)
COLORS = {
    "bg_dark": "#1e1e2e",
    "bg_light": "#292a37",
    "accent": "#94e2d5",
    "text_light": "#f5e0dc",
    "text_dark": "#6c7086",
    "snake_head": "#f5c2e7",
    "snake_body": "#cba6f7",
    "food": "#f38ba8",
    "wall": "#7f849c",
    "button": "#313244",
    "button_hover": "#45475a",
    "easy": "#a6e3a1",
    "medium": "#f9e2af",
    "hard": "#f38ba8",
    "progress_bg": "#313244",
    "progress_fg": "#94e2d5",
    "hint": "#fab387"
}

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

class Particle:
    """Simple particle for visual effects"""
    def __init__(self, canvas, x, y, color, size=5, life=20, speed=3):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.speed = speed
        self.angle = random.uniform(0, 2 * 3.14159)
        self.dx = self.speed * random.uniform(-1, 1)
        self.dy = self.speed * random.uniform(-1, 1)
        self.id = canvas.create_oval(
            x - size, y - size, 
            x + size, y + size, 
            fill=color, outline=""
        )
        
    def update(self):
        """Update particle position and appearance"""
        self.life -= 1
        if self.life <= 0:
            self.canvas.delete(self.id)
            return False
            
        # Update position
        self.x += self.dx
        self.y += self.dy
        
        # Fade out as life decreases
        opacity = int(255 * (self.life / self.max_life))
        hex_opacity = format(opacity, '02x')
        color = f"{self.color}{hex_opacity}"
        
        # Shrink as life decreases
        current_size = self.size * (self.life / self.max_life)
        
        # Update on canvas
        self.canvas.coords(
            self.id,
            self.x - current_size,
            self.y - current_size,
            self.x + current_size,
            self.y + current_size
        )
        
        try:
            self.canvas.itemconfig(self.id, fill=color)
        except:
            # If color format is not supported, just use original color
            pass
            
        return True
        
class SnakeGame:
    """Main game class for the Snake Spelling Game"""
    def __init__(self, master):
        self.master = master
        self.master.title("Spelling Snake - Learn While You Play!")
        self.master.geometry(f"{GRID_WIDTH * GRID_SIZE + 300}x{GRID_HEIGHT * GRID_SIZE + 150}")
        self.master.minsize(800, 600)
        self.master.configure(bg=COLORS["bg_dark"])
        
        # Create custom fonts
        self.title_font = font.Font(family="Arial", size=24, weight="bold")
        self.header_font = font.Font(family="Arial", size=18, weight="bold")
        self.normal_font = font.Font(family="Arial", size=12)
        self.small_font = font.Font(family="Arial", size=10)
        self.game_font = font.Font(family="Courier New", size=14, weight="bold")
        
        # Set up ttk style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use clam theme as a base
        
        # Configure styles
        self.style.configure("TFrame", background=COLORS["bg_dark"])
        self.style.configure("TLabel", background=COLORS["bg_dark"], foreground=COLORS["text_light"])
        self.style.configure("TButton", 
                             background=COLORS["button"], 
                             foreground=COLORS["text_light"],
                             borderwidth=0,
                             focusthickness=0,
                             font=self.normal_font)
        self.style.map("TButton",
                      background=[('active', COLORS["button_hover"])],
                      foreground=[('active', COLORS["accent"])])
                      
        # Configure progress bar
        self.style.configure("TProgressbar", 
                            background=COLORS["progress_fg"],
                            troughcolor=COLORS["progress_bg"],
                            borderwidth=0,
                            thickness=15)
        
        # Game state variables
        self.is_running = False
        self.game_over = False
        self.paused = False
        self.current_frame = None
        self.difficulty = "medium"
        self.target_word = ""
        self.show_hint = False
        self.particles = []
        
        # Initialize game data
        self.snake = None
        self.food_pos = None
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.score = 0
        self.letters_collected = 0
        self.body_letters = []
        self.last_letter_time = 0
        self.message = ""
        self.message_timer = 0
        
        # Create the main container
        self.main_container = ttk.Frame(self.master)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Show the main menu initially
        self.show_main_menu()
        
    def load_stats(self):
        """Load the player statistics from the stats file"""
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
        """Save the player statistics to the stats file"""
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f)
    
    def update_stats(self):
        """Update player statistics at the end of a game"""
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
    
    def clear_frame(self):
        """Clear the current frame to switch views"""
        if self.current_frame:
            self.current_frame.destroy()
            self.current_frame = None
    
    def show_main_menu(self):
        """Display the main menu screen"""
        self.clear_frame()
        self.is_running = False
        
        # Create menu frame
        self.current_frame = ttk.Frame(self.main_container)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            self.current_frame, 
            text="Spelling Snake", 
            font=self.title_font, 
            foreground=COLORS["accent"]
        )
        title_label.pack(pady=(50, 10))
        
        # Subtitle
        subtitle_label = ttk.Label(
            self.current_frame, 
            text="Learn to spell while having fun!", 
            font=self.header_font
        )
        subtitle_label.pack(pady=(0, 50))
        
        # Buttons
        button_frame = ttk.Frame(self.current_frame)
        button_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create button style with larger size
        button_width = 20
        button_padding = 10
        
        play_button = ttk.Button(
            button_frame, 
            text="Play Game", 
            command=self.show_difficulty_selection,
            width=button_width,
            padding=button_padding
        )
        play_button.pack(pady=10)
        
        stats_button = ttk.Button(
            button_frame, 
            text="Statistics", 
            command=self.show_statistics,
            width=button_width,
            padding=button_padding
        )
        stats_button.pack(pady=10)
        
        help_button = ttk.Button(
            button_frame, 
            text="How to Play", 
            command=self.show_help,
            width=button_width,
            padding=button_padding
        )
        help_button.pack(pady=10)
        
        quit_button = ttk.Button(
            button_frame, 
            text="Quit", 
            command=self.master.destroy,
            width=button_width,
            padding=button_padding
        )
        quit_button.pack(pady=10)
    
    def show_difficulty_selection(self):
        """Display the difficulty selection screen"""
        self.clear_frame()
        
        # Create difficulty selection frame
        self.current_frame = ttk.Frame(self.main_container)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            self.current_frame, 
            text="Select Difficulty", 
            font=self.header_font, 
            foreground=COLORS["accent"]
        )
        title_label.pack(pady=(30, 20))
        
        # Difficulty buttons
        button_frame = ttk.Frame(self.current_frame)
        button_frame.pack(fill=tk.BOTH, expand=True, padx=50)
        
        # Custom styles for difficulty buttons
        self.style.configure("Easy.TButton", background=COLORS["easy"])
        self.style.configure("Medium.TButton", background=COLORS["medium"])
        self.style.configure("Hard.TButton", background=COLORS["hard"])
        
        easy_button = ttk.Button(
            button_frame, 
            text="Easy (3-4 letter words)", 
            command=lambda: self.set_difficulty("easy"),
            style="Easy.TButton",
            padding=15
        )
        easy_button.pack(fill=tk.X, pady=10)
        
        medium_button = ttk.Button(
            button_frame, 
            text="Medium (5-6 letter words)", 
            command=lambda: self.set_difficulty("medium"),
            style="Medium.TButton",
            padding=15
        )
        medium_button.pack(fill=tk.X, pady=10)
        
        hard_button = ttk.Button(
            button_frame, 
            text="Hard (7+ letter words)", 
            command=lambda: self.set_difficulty("hard"),
            style="Hard.TButton",
            padding=15
        )
        hard_button.pack(fill=tk.X, pady=10)
        
        # Show word list button
        word_list_button = ttk.Button(
            button_frame, 
            text="View Word Lists", 
            command=self.show_word_lists,
            padding=10
        )
        word_list_button.pack(fill=tk.X, pady=(30, 10))
        
        # Back button
        back_button = ttk.Button(
            self.current_frame, 
            text="Back to Main Menu", 
            command=self.show_main_menu,
            padding=10
        )
        back_button.pack(pady=(0, 20))
    
    def set_difficulty(self, difficulty):
        """Set the game difficulty and move to word selection"""
        self.difficulty = difficulty
        self.show_word_selection()
    
    def show_word_lists(self):
        """Display the word lists for each difficulty level"""
        self.clear_frame()
        
        # Create word list frame with scrollbar
        self.current_frame = ttk.Frame(self.main_container)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            self.current_frame, 
            text="Word Lists", 
            font=self.header_font, 
            foreground=COLORS["accent"]
        )
        title_label.pack(pady=(20, 10))
        
        # Create scrollable frame for each difficulty
        main_frame = ttk.Frame(self.current_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Add back button
        back_button = ttk.Button(
            self.current_frame,
            text="Back",
            command=self.show_difficulty_selection,
            padding=10
        )
        back_button.pack(pady=10)
        
        # Create frames for each difficulty
        for difficulty, words in WORD_LISTS.items():
            # Create section for this difficulty
            diff_frame = ttk.Frame(main_frame)
            diff_frame.pack(fill=tk.X, pady=10)
            
            # Header for the difficulty
            color = COLORS["easy"] if difficulty == "easy" else COLORS["medium"] if difficulty == "medium" else COLORS["hard"]
            header = ttk.Label(
                diff_frame,
                text=f"{difficulty.capitalize()} Words",
                font=self.header_font,
                foreground=color
            )
            header.pack(anchor=tk.W)
            
            # Word list
            word_text = ", ".join(words)
            word_label = ttk.Label(
                diff_frame,
                text=word_text,
                font=self.normal_font,
                wraplength=600
            )
            word_label.pack(fill=tk.X, pady=5)
    
    def show_word_selection(self):
        """Display the word selection screen"""
        self.clear_frame()
        
        # Create word selection frame
        self.current_frame = ttk.Frame(self.main_container)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            self.current_frame, 
            text="Select a Word", 
            font=self.header_font, 
            foreground=COLORS["accent"]
        )
        title_label.pack(pady=(30, 20))
        
        # Word selection options
        options_frame = ttk.Frame(self.current_frame)
        options_frame.pack(fill=tk.BOTH, expand=True, padx=50)
        
        # Random word option
        random_button = ttk.Button(
            options_frame,
            text=f"Use a Random {self.difficulty.capitalize()} Word",
            command=self.use_random_word,
            padding=15
        )
        random_button.pack(fill=tk.X, pady=10)
        
        # Custom word option
        custom_frame = ttk.Frame(options_frame)
        custom_frame.pack(fill=tk.X, pady=10)
        
        custom_label = ttk.Label(
            custom_frame,
            text="Or enter your own word:",
            font=self.normal_font
        )
        custom_label.pack(anchor=tk.W)
        
        # Entry field with submit button
        entry_frame = ttk.Frame(custom_frame)
        entry_frame.pack(fill=tk.X, pady=5)
        
        self.word_entry = ttk.Entry(entry_frame, font=self.normal_font)
        self.word_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        submit_button = ttk.Button(
            entry_frame,
            text="Submit",
            command=self.use_custom_word,
            padding=5
        )
        submit_button.pack(side=tk.RIGHT)
        
        # Back button
        back_button = ttk.Button(
            self.current_frame,
            text="Back to Difficulty Selection",
            command=self.show_difficulty_selection,
            padding=10
        )
        back_button.pack(pady=(20, 10))
    
    def use_random_word(self):
        """Select a random word from the current difficulty"""
        self.target_word = random.choice(WORD_LISTS[self.difficulty])
        self.start_game()
    
    def use_custom_word(self):
        """Use a custom word entered by the user"""
        word = self.word_entry.get().strip().lower()
        if word:
            self.target_word = word
            self.start_game()
        else:
            messagebox.showwarning("Empty Word", "Please enter a word.")
    
    def show_statistics(self):
        """Display player statistics"""
        self.clear_frame()
        
        # Create statistics frame
        self.current_frame = ttk.Frame(self.main_container)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            self.current_frame, 
            text="Your Statistics", 
            font=self.header_font, 
            foreground=COLORS["accent"]
        )
        title_label.pack(pady=(30, 20))
        
        # Load statistics
        stats = self.load_stats()
        
        # Create stats display
        stats_frame = ttk.Frame(self.current_frame)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=50)
        
        # Words completed
        words_label = ttk.Label(
            stats_frame,
            text=f"Words Completed: {stats['words_completed']}",
            font=self.normal_font
        )
        words_label.pack(anchor=tk.W, pady=5)
        
        # Total score
        score_label = ttk.Label(
            stats_frame,
            text=f"Total Score: {stats['total_score']}",
            font=self.normal_font
        )
        score_label.pack(anchor=tk.W, pady=5)
        
        # Words by difficulty
        diff_frame = ttk.Frame(stats_frame)
        diff_frame.pack(fill=tk.X, pady=10)
        
        diff_label = ttk.Label(
            diff_frame,
            text="Words by Difficulty:",
            font=self.normal_font
        )
        diff_label.pack(anchor=tk.W)
        
        easy_label = ttk.Label(
            diff_frame,
            text=f"Easy: {stats['words_by_difficulty']['easy']}",
            foreground=COLORS["easy"]
        )
        easy_label.pack(anchor=tk.W, padx=20)
        
        medium_label = ttk.Label(
            diff_frame,
            text=f"Medium: {stats['words_by_difficulty']['medium']}",
            foreground=COLORS["medium"]
        )
        medium_label.pack(anchor=tk.W, padx=20)
        
        hard_label = ttk.Label(
            diff_frame,
            text=f"Hard: {stats['words_by_difficulty']['hard']}",
            foreground=COLORS["hard"]
        )
        hard_label.pack(anchor=tk.W, padx=20)
        
        # Back button
        back_button = ttk.Button(
            self.current_frame,
            text="Back to Main Menu",
            command=self.show_main_menu,
            padding=10
        )
        back_button.pack(pady=(20, 10))
    
    def show_help(self):
        """Display help information"""
        self.clear_frame()
        
        # Create help frame
        self.current_frame = ttk.Frame(self.main_container)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            self.current_frame, 
            text="How to Play", 
            font=self.header_font, 
            foreground=COLORS["accent"]
        )
        title_label.pack(pady=(30, 20))
        
        # Help text
        help_frame = ttk.Frame(self.current_frame)
        help_frame.pack(fill=tk.BOTH, expand=True, padx=50)
        
        # Game objective
        objective_label = ttk.Label(
            help_frame,
            text="Game Objective:",
            font=self.normal_font,
            foreground=COLORS["accent"]
        )
        objective_label.pack(anchor=tk.W, pady=5)
        
        objective_text = ttk.Label(
            help_frame,
            text="Control the snake to collect letters in the correct order to spell out the target word.",
            wraplength=600,
            justify=tk.LEFT
        )
        objective_text.pack(anchor=tk.W, padx=20, pady=5)
        
        # Controls
        controls_label = ttk.Label(
            help_frame,
            text="Controls:",
            font=self.normal_font,
            foreground=COLORS["accent"]
        )
        controls_label.pack(anchor=tk.W, pady=5)
        
        controls_text = ttk.Label(
            help_frame,
            text="• Arrow Keys: Move the snake up, down, left, or right\n"
                 "• H Key: Show hint (highlights the next letter)\n"
                 "• P Key: Pause game\n"
                 "• Q Key: Quit current game",
            wraplength=600,
            justify=tk.LEFT
        )
        controls_text.pack(anchor=tk.W, padx=20, pady=5)
        
        # Scoring
        scoring_label = ttk.Label(
            help_frame,
            text="Scoring:",
            font=self.normal_font,
            foreground=COLORS["accent"]
        )
        scoring_label.pack(anchor=tk.W, pady=5)
        
        scoring_text = ttk.Label(
            help_frame,
            text="• Each letter collected: 10 points base\n"
                 "• Speed bonus: Up to 20 extra points for quick collection\n"
                 "• Difficulty multipliers: Easy (x1), Medium (x2), Hard (x3)\n"
                 "• Word completion bonus: Based on word length and time",
            wraplength=600,
            justify=tk.LEFT
        )
        scoring_text.pack(anchor=tk.W, padx=20, pady=5)
        
        # Back button
        back_button = ttk.Button(
            self.current_frame,
            text="Back to Main Menu",
            command=self.show_main_menu,
            padding=10
        )
        back_button.pack(pady=(20, 10))
    
    def start_game(self):
        """Initialize and start the snake game"""
        self.clear_frame()
        
        # Set up game variables
        self.body_letters = list(self.target_word)
        self.score = 0
        self.letters_collected = 0
        self.is_running = True
        self.game_over = False
        self.paused = False
        self.show_hint = False
        self.snake = deque([(GRID_HEIGHT // 2, GRID_WIDTH // 2)])
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.food_pos = None
        self.last_letter_time = time.time()
        self.message = ""
        self.message_timer = 0
        self.particles = []
        
        # Create game frame
        self.current_frame = ttk.Frame(self.main_container)
        self.current_frame.pack(fill=tk.BOTH, expand=True)
        
        # Info panel (top)
        info_panel = ttk.Frame(self.current_frame)
        info_panel.pack(fill=tk.X, pady=10)
        
        # Word display
        word_frame = ttk.Frame(info_panel)
        word_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        word_label = ttk.Label(
            word_frame,
            text="Target Word:",
            font=self.normal_font
        )
        word_label.pack(side=tk.LEFT)
        
        self.word_display = ttk.Label(
            word_frame,
            text=self.target_word.upper(),
            font=self.header_font,
            foreground=COLORS["accent"]
        )
        self.word_display.pack(side=tk.LEFT, padx=10)
        
        # Difficulty display
        diff_label = ttk.Label(
            info_panel,
            text=f"Difficulty: {self.difficulty.capitalize()}",
            font=self.normal_font,
            foreground=COLORS["medium"] if self.difficulty == "medium" else 
                       COLORS["easy"] if self.difficulty == "easy" else COLORS["hard"]
        )
        diff_label.pack(side=tk.RIGHT)
        
        # Progress bar and stats
        progress_frame = ttk.Frame(self.current_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        progress_label = ttk.Label(
            progress_frame,
            text="Progress:",
            font=self.small_font
        )
        progress_label.pack(side=tk.LEFT)
        
        # Progress display
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            length=200,
            maximum=len(self.target_word),
            mode='determinate',
            style="TProgressbar"
        )
        self.progress_bar.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Progress text
        self.progress_text = ttk.Label(
            progress_frame,
            text=f"0/{len(self.target_word)}",
            font=self.small_font
        )
        self.progress_text.pack(side=tk.LEFT, padx=5)
        
        # Score display
        self.score_label = ttk.Label(
            progress_frame,
            text="Score: 0",
            font=self.normal_font
        )
        self.score_label.pack(side=tk.RIGHT, padx=10)
        
        # Game canvas
        canvas_frame = ttk.Frame(self.current_frame, borderwidth=2, relief="sunken")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(
            canvas_frame,
            width=GRID_WIDTH * GRID_SIZE,
            height=GRID_HEIGHT * GRID_SIZE,
            bg=COLORS["bg_light"],
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create grid pattern for better visibility
        for i in range(GRID_WIDTH):
            for j in range(GRID_HEIGHT):
                if (i + j) % 2 == 0:
                    self.canvas.create_rectangle(
                        i * GRID_SIZE, j * GRID_SIZE,
                        (i + 1) * GRID_SIZE, (j + 1) * GRID_SIZE,
                        fill=COLORS["bg_light"],
                        outline=""
                    )
                else:
                    self.canvas.create_rectangle(
                        i * GRID_SIZE, j * GRID_SIZE,
                        (i + 1) * GRID_SIZE, (j + 1) * GRID_SIZE,
                        fill=COLORS["bg_dark"],
                        outline=""
                    )
        
        # Message display
        self.message_label = ttk.Label(
            self.current_frame,
            text="",
            font=self.normal_font,
            foreground=COLORS["accent"]
        )
        self.message_label.pack(pady=5)
        
        # Controls reminder
        controls_label = ttk.Label(
            self.current_frame,
            text="Arrow Keys: Move | H: Hint | P: Pause | Q: Quit",
            font=self.small_font,
            foreground=COLORS["text_dark"]
        )
        controls_label.pack(pady=5)
        
        # Set up keyboard bindings
        self.master.bind("<Left>", lambda e: self.set_direction(LEFT))
        self.master.bind("<Right>", lambda e: self.set_direction(RIGHT))
        self.master.bind("<Up>", lambda e: self.set_direction(UP))
        self.master.bind("<Down>", lambda e: self.set_direction(DOWN))
        self.master.bind("h", lambda e: self.toggle_hint())
        self.master.bind("H", lambda e: self.toggle_hint())
        self.master.bind("p", lambda e: self.toggle_pause())
        self.master.bind("P", lambda e: self.toggle_pause())
        self.master.bind("q", lambda e: self.quit_game())
        self.master.bind("Q", lambda e: self.quit_game())
        
        # Generate first food
        self.generate_food()
        
        # Start the game loop
        self.game_loop()
    
    def set_direction(self, new_dir):
        """Change the snake's direction if valid"""
        if not self.is_running or self.paused or self.game_over:
            return
            
        # Prevent 180-degree turns
        if (self.direction[0] != -new_dir[0] or self.direction[1] != -new_dir[1]):
            self.next_direction = new_dir
    
    def toggle_hint(self):
        """Toggle hint display"""
        if self.is_running and not self.game_over:
            self.show_hint = not self.show_hint
            self.draw_game()
    
    def toggle_pause(self):
        """Pause or resume the game"""
        if self.is_running and not self.game_over:
            self.paused = not self.paused
            if self.paused:
                self.message_label.config(text="Game Paused - Press P to resume")
            else:
                self.message_label.config(text="")
    
    def quit_game(self):
        """Quit the current game and return to main menu"""
        if self.is_running:
            self.is_running = False
            self.show_main_menu()
    
    def generate_food(self):
        """Generate food at a random empty position"""
        if not self.is_running:
            return
            
        # Find all empty positions
        occupied = set(self.snake)
        empty_positions = [(r, c) for r in range(GRID_HEIGHT) for c in range(GRID_WIDTH) 
                           if (r, c) not in occupied]
        
        if empty_positions:
            self.food_pos = random.choice(empty_positions)
        else:
            # No empty positions, game won!
            self.food_pos = None
            self.handle_game_won()
    
    def handle_letter_collection(self):
        """Handle the collection of a letter"""
        # Add particle effects at food position
        self.create_particles(
            self.food_pos[1] * GRID_SIZE + GRID_SIZE // 2,
            self.food_pos[0] * GRID_SIZE + GRID_SIZE // 2,
            COLORS["food"],
            10,  # Number of particles
            8,  # Size
            30  # Life
        )
        
        # Calculate time-based score
        current_time = time.time()
        letter_time = current_time - self.last_letter_time
        time_bonus = max(0, int(20 - letter_time))
        difficulty_multiplier = {"easy": 1, "medium": 2, "hard": 3}[self.difficulty]
        points = 10 + (time_bonus * difficulty_multiplier)
        
        self.score += points
        self.letters_collected += 1
        self.score_label.config(text=f"Score: {self.score}")
        self.last_letter_time = current_time
        
        # Update progress
        self.progress_var.set(self.letters_collected)
        self.progress_text.config(text=f"{self.letters_collected}/{len(self.target_word)}")
        
        # Show encouraging message
        self.message = random.choice(MESSAGES)
        self.message_label.config(text=self.message)
        self.master.after(2000, lambda: self.message_label.config(text=""))
        
        # Check if word is completed
        if self.letters_collected >= len(self.target_word):
            self.handle_word_completion()
    
    def handle_word_completion(self):
        """Handle completion of the target word"""
        # Calculate completion bonus
        total_time = time.time() - self.last_letter_time
        time_bonus = max(0, int(100 - total_time))
        completion_bonus = time_bonus + (len(self.target_word) * 20)
        self.score += completion_bonus
        self.score_label.config(text=f"Score: {self.score}")
        
        # Special particle effects for completion
        for snake_segment in self.snake:
            self.create_particles(
                snake_segment[1] * GRID_SIZE + GRID_SIZE // 2,
                snake_segment[0] * GRID_SIZE + GRID_SIZE // 2,
                COLORS["accent"],
                5,
                6,
                20
            )
        
        # Update statistics
        self.update_stats()
        
        # Special message
        self.message_label.config(
            text=f"Congratulations! You spelled {self.target_word.upper()} correctly!",
            foreground=COLORS["accent"]
        )
    
    def handle_game_won(self):
        """Handle winning the game (filling the entire grid)"""
        self.game_over = True
        self.message_label.config(
            text="Amazing! You filled the entire grid!",
            foreground=COLORS["accent"]
        )
        self.update_stats()
        self.show_game_over()
    
    def handle_game_over(self):
        """Handle game over state"""
        self.game_over = True
        self.message_label.config(
            text="Game Over!",
            foreground=COLORS["hard"]
        )
        self.show_game_over()
    
    def show_game_over(self):
        """Show game over screen with stats"""
        # Create game over frame (overlaid on game)
        game_over_frame = ttk.Frame(
            self.current_frame,
            padding=20
        )
        game_over_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Title
        title_label = ttk.Label(
            game_over_frame,
            text="Game Over",
            font=self.header_font,
            foreground=COLORS["hard"]
        )
        title_label.pack(pady=(0, 20))
        
        # Game stats
        stats_frame = ttk.Frame(game_over_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Word
        word_label = ttk.Label(
            stats_frame,
            text=f"Word: {self.target_word.upper()}",
            font=self.normal_font
        )
        word_label.pack(anchor=tk.W, pady=5)
        
        # Letters collected
        letters_label = ttk.Label(
            stats_frame,
            text=f"Letters Collected: {self.letters_collected}/{len(self.target_word)}",
            font=self.normal_font
        )
        letters_label.pack(anchor=tk.W, pady=5)
        
        # Completion percentage
        completion_percent = min(100, (self.letters_collected / len(self.target_word) * 100))
        completion_label = ttk.Label(
            stats_frame,
            text=f"Completion: {completion_percent:.1f}%",
            font=self.normal_font
        )
        completion_label.pack(anchor=tk.W, pady=5)
        
        # Final score
        score_label = ttk.Label(
            stats_frame,
            text=f"Final Score: {self.score}",
            font=self.normal_font
        )
        score_label.pack(anchor=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(game_over_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        retry_button = ttk.Button(
            button_frame,
            text="Play Again",
            command=self.show_difficulty_selection,
            padding=10
        )
        retry_button.pack(side=tk.LEFT, padx=10)
        
        menu_button = ttk.Button(
            button_frame,
            text="Main Menu",
            command=self.show_main_menu,
            padding=10
        )
        menu_button.pack(side=tk.RIGHT, padx=10)
    
    def create_particles(self, x, y, color, count=10, size=5, life=20):
        """Create particle effects at given position"""
        for _ in range(count):
            particle = Particle(self.canvas, x, y, color, size, life)
            self.particles.append(particle)
    
    def update_particles(self):
        """Update all active particles"""
        if not self.particles:
            return
            
        # Update each particle and filter out dead ones
        self.particles = [p for p in self.particles if p.update()]
    
    def move_snake(self):
        """Move the snake based on current direction"""
        if not self.is_running or self.paused or self.game_over:
            return
            
        # Update direction
        self.direction = self.next_direction
        
        # Calculate new head position
        head_row, head_col = self.snake[0]
        dir_row, dir_col = self.direction
        new_head = (head_row + dir_row, head_col + dir_col)
        
        # Check for collisions
        if (new_head[0] < 0 or new_head[0] >= GRID_HEIGHT or 
            new_head[1] < 0 or new_head[1] >= GRID_WIDTH or
            new_head in self.snake):
            # Collision with wall or self
            self.handle_game_over()
            return
            
        # Add new head
        self.snake.appendleft(new_head)
        
        # Check if food was collected
        if new_head == self.food_pos:
            # Food collected, grow snake (don't remove tail)
            self.handle_letter_collection()
            self.generate_food()
        else:
            # No food collected, remove tail to maintain length
            self.snake.pop()
    
    def draw_game(self):
        """Draw the current game state on the canvas"""
        if not self.is_running:
            return
            
        # Clear previous drawings
        self.canvas.delete("snake", "food", "hint")
        
        # Draw food with letter
        if self.food_pos:
            food_row, food_col = self.food_pos
            food_x, food_y = food_col * GRID_SIZE, food_row * GRID_SIZE
            
            # Draw food background
            self.canvas.create_oval(
                food_x + 2, food_y + 2, 
                food_x + GRID_SIZE - 2, food_y + GRID_SIZE - 2,
                fill=COLORS["food"],
                outline="",
                tags="food"
            )
            
            # Draw letter on food
            if self.letters_collected < len(self.target_word):
                next_letter = self.target_word[self.letters_collected].upper()
                self.canvas.create_text(
                    food_x + GRID_SIZE // 2, 
                    food_y + GRID_SIZE // 2,
                    text=next_letter,
                    font=self.game_font,
                    fill=COLORS["text_light"],
                    tags="food"
                )
        
        # Draw snake
        for i, segment in enumerate(self.snake):
            row, col = segment
            x, y = col * GRID_SIZE, row * GRID_SIZE
            
            if i == 0:
                # Head
                self.canvas.create_rectangle(
                    x + 1, y + 1, 
                    x + GRID_SIZE - 1, y + GRID_SIZE - 1,
                    fill=COLORS["snake_head"],
                    outline="",
                    tags="snake"
                )
                
                # Draw direction indicator
                dir_x, dir_y = self.direction
                eye_x, eye_y = x + GRID_SIZE // 2, y + GRID_SIZE // 2
                self.canvas.create_oval(
                    eye_x + dir_x * 5 - 2, 
                    eye_y + dir_y * 5 - 2,
                    eye_x + dir_x * 5 + 2, 
                    eye_y + dir_y * 5 + 2,
                    fill=COLORS["bg_dark"],
                    outline="",
                    tags="snake"
                )
            elif i <= len(self.target_word) and i <= self.letters_collected:
                # Body segment with letter
                self.canvas.create_rectangle(
                    x + 2, y + 2, 
                    x + GRID_SIZE - 2, y + GRID_SIZE - 2,
                    fill=COLORS["snake_body"],
                    outline="",
                    tags="snake"
                )
                
                # Draw letter on body segment
                letter_idx = i - 1
                if letter_idx < len(self.target_word):
                    letter = self.target_word[letter_idx].upper()
                    self.canvas.create_text(
                        x + GRID_SIZE // 2, 
                        y + GRID_SIZE // 2,
                        text=letter,
                        font=self.game_font,
                        fill=COLORS["text_light"],
                        tags="snake"
                    )
            else:
                # Regular body segment
                self.canvas.create_rectangle(
                    x + 3, y + 3, 
                    x + GRID_SIZE - 3, y + GRID_SIZE - 3,
                    fill=COLORS["snake_body"],
                    outline="",
                    tags="snake"
                )
        
        # Draw hint if enabled
        if self.show_hint and self.food_pos:
            food_row, food_col = self.food_pos
            food_x, food_y = food_col * GRID_SIZE, food_row * GRID_SIZE
            
            # Highlight path to food
            self.canvas.create_rectangle(
                food_x, food_y,
                food_x + GRID_SIZE, food_y + GRID_SIZE,
                outline=COLORS["hint"],
                width=3,
                tags="hint"
            )
    
    def game_loop(self):
        """Main game loop"""
        if not self.is_running:
            return
        
        if not self.paused and not self.game_over:
            # Move snake
            self.move_snake()
            
            # Update particles
            self.update_particles()
            
            # Draw game state
            self.draw_game()
        
        # Schedule next update
        if self.is_running:
            self.master.after(GAME_SPEED, self.game_loop)

def main():
    """Initialize and run the game"""
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()
