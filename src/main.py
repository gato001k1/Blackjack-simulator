import tkinter as tk
from tkinter import Canvas
import random
import os
from PIL import Image, ImageTk
import time

# --- Constants & Configuration ---
SUITS = ["clubs", "diamonds", "hearts", "spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace"]
CARD_FILES = [f"{rank}_of_{suit}.png" for suit in SUITS for rank in RANKS]

class BlackjackApp(tk.Tk):
    """
    Main Application Class for Blackjack Simulator
    Organized into:
    1. Initialization (Window, Resources, State)
    2. UI Setup (Draw Table, Buttons)
    3. Game Actions (New Game, Hit, Stand)
    4. Card Management (Deal, Reveal)
    5. Animation (Flip)
    """

    # -------------------------------------------------------------------------
    # 1. Initialization
    # -------------------------------------------------------------------------
    def __init__(self):
        super().__init__()
        self.setup_window()
        self.load_resources()
        self.init_game_state()
        self.setup_ui()

    def setup_window(self):
        self.title("Blackjack Simulator")
        self.geometry("1000x800")
        self.resizable(False, False)

    def load_resources(self):
        self.base_path = os.path.dirname(__file__)
        self.sprites_path = os.path.join(self.base_path, "individual_sprites")
        
        # Load Back Image
        self.card_back_path = os.path.join(self.sprites_path, "back.png")
        if not os.path.exists(self.card_back_path):
             print(f"Error: back.png not found at {self.card_back_path}")
             self.card_back_image_pil = Image.new('RGB', (100, 145), color = 'red')
        else:
             self.card_back_image_pil = Image.open(self.card_back_path)
             
        # Calculate Dimensions
        self.card_original_size = self.card_back_image_pil.size
        # Aim for width=100
        original_w, original_h = self.card_original_size
        if original_w > 0:
            scale_factor = 100 / original_w
        else:
            scale_factor = 1
            
        self.card_size = (int(original_w * scale_factor), int(original_h * scale_factor))
        if self.card_size[0] == 0: self.card_size = (100, 145)

        # Prepare Resized Back Image for Display
        self.card_back_image_pil = self.card_back_image_pil.resize(self.card_size, Image.Resampling.LANCZOS)
        self.card_back_photo = ImageTk.PhotoImage(self.card_back_image_pil)

    def init_game_state(self):
        self.card_items = []            # References to canvas create_image items
        self.card_images_ref = []       # Keep python references to avoid GC
        self.current_player_slot = 0    
        self.current_dealer_slot = 0    
        self.game_active = False
        self.dealer_hole_card_item = None
        self.dealer_hole_card_front = None
        self.player_hand = []
        self.dealer_hand = []
        self.player_score_text = None
        self.dealer_score_text = None
        
        # Temporary holding for animation frames to prevent GC during loop
        self.temp_animation_ref = None 

    def setup_ui(self):
        # Canvas
        self.canvas = Canvas(self, width=1000, height=800, bg="#004d00", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Draw Static Table Elements
        self.draw_table_vectors()

        # Buttons
        btn_font = ("Arial", 14, "bold")
        self.new_game_button = tk.Button(self, text="New Game", command=self.start_new_game, font=btn_font, bg="gold")
        self.new_game_button.place(x=350, y=700)
        
        self.hit_button = tk.Button(self, text="Hit", command=self.hit, font=btn_font, bg="lightgreen")
        self.hit_button.place(x=500, y=700)
        
        self.stand_button = tk.Button(self, text="Stand", command=self.stand, font=btn_font, bg="salmon")
        self.stand_button.place(x=600, y=700)
        
        # Initial State: Disabled Actions
        self.hit_button.config(state="disabled")
        self.stand_button.config(state="disabled")

    # -------------------------------------------------------------------------
    # 2. UI Drawing Methods
    # -------------------------------------------------------------------------
    def draw_table_vectors(self):
        # Table border (wood trim)
        self.canvas.create_rectangle(50, 50, 950, 750, outline="#3e2723", width=20, tags="table")
        
        # Draw the "line" where chips go or text is. 
        self.canvas.create_arc(100, 350, 900, 750, start=0, extent=180, style="arc", outline="yellow", width=2, tags="table")
        
        # Text Info
        self.canvas.create_text(500, 420, text="BLACKJACK PAYS 3 TO 2", fill="yellow", font=("Times New Roman", 24, "bold"))
        self.canvas.create_text(500, 460, text="Dealer must stand on 17 and must draw to 16", fill="white", font=("Arial", 12))
        
        # Area Labels
        self.canvas.create_text(500, 100, text="DEALER", fill="lightgrey", font=("Arial", 16, "bold"))
        self.dealer_score_text = self.canvas.create_text(500, 70, text="0", fill="white", font=("Arial", 14, "bold"))
        
        self.canvas.create_text(500, 530, text="PLAYER", fill="lightgrey", font=("Arial", 16, "bold"))
        self.player_score_text = self.canvas.create_text(500, 560, text="0", fill="white", font=("Arial", 14, "bold"))

        # Dealer Slots
        dealer_y = 130
        for i in range(5):
            x = 200 + (i * 150)
            self.canvas.create_rectangle(x - 5, dealer_y - 5, x + 100 + 5, dealer_y + 145 + 5, outline="#006400", width=2)
            
        # Player Slots
        player_y = 550
        for i in range(5):
            x = 200 + (i * 150)
            self.canvas.create_rectangle(x - 5, player_y - 5, x + 100 + 5, player_y + 145 + 5, outline="#006400", width=2)

    # -------------------------------------------------------------------------
    # 3. Game Actions
    # -------------------------------------------------------------------------
    def get_card_value(self, rank):
        if rank in ["jack", "queen", "king"]:
            return 10
        elif rank == "ace":
            return 11
        else:
            try:
                return int(rank)
            except ValueError:
                return 0

    def calculate_hand_value(self, hand):
        value = 0
        aces = 0
        for card_rank in hand:
            val = self.get_card_value(card_rank)
            value += val
            if card_rank == 'ace':
                aces += 1
        
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        return value

    def update_scores(self):
        p_val = self.calculate_hand_value(self.player_hand)
        
        # Dealer score: if hole card hidden, only show visible cards
        if self.dealer_hole_card_item is not None and len(self.dealer_hand) >= 2:
             # Just the up card (index 0)
             visible_hand = [self.dealer_hand[0]]
             d_val = self.calculate_hand_value(visible_hand)
        else:
             d_val = self.calculate_hand_value(self.dealer_hand)
             
        if self.player_score_text:
            self.canvas.itemconfig(self.player_score_text, text=str(p_val))
        if self.dealer_score_text:
            self.canvas.itemconfig(self.dealer_score_text, text=str(d_val))

    def start_new_game(self):
        # Cleanup Previous Game
        for item in self.card_items:
            self.canvas.delete(item)
        self.card_items.clear()
        self.card_images_ref.clear()
        
        self.player_hand.clear()
        self.dealer_hand.clear()
        if self.player_score_text: self.canvas.itemconfig(self.player_score_text, text="0")
        if self.dealer_score_text: self.canvas.itemconfig(self.dealer_score_text, text="0")
        
        # Reset State
        self.current_player_slot = 0
        self.current_dealer_slot = 0
        self.game_active = True
        self.dealer_hole_card_item = None
        self.dealer_hole_card_front = None
        
        # Disable buttons during dealing
        self.hit_button.config(state="disabled")
        self.stand_button.config(state="disabled")
        
        # Schedule Deal Sequence with increased delays to allow animations to complete
        # Animation takes: (10 steps down + 10 steps up) * 0.02s sleep + overhead ~= 0.4s - 0.5s
        # 0ms: Player 1
        # 600ms: Dealer 1
        # 1200ms: Player 2
        # 1800ms: Dealer 2 (Face Down - Instant)
        # 2000ms: Enable Buttons
        self.deal_card("player")
        self.after(600, lambda: self.deal_card("dealer"))
        self.after(1200, lambda: self.deal_card("player"))
        self.after(1800, lambda: self.deal_card("dealer", face_down=True))
        self.after(2000, self.enable_game_buttons)

    def enable_game_buttons(self):
        self.hit_button.config(state="normal")
        self.stand_button.config(state="normal")

    def hit(self):
        if self.game_active:
            # Prevent re-entrancy during animation
            self.hit_button.config(state="disabled")
            self.stand_button.config(state="disabled")
            
            self.deal_card("player")
            
            # Re-enable if game still active (and not busted)
            if self.game_active:
                self.enable_game_buttons()

    def stand(self):
        if self.game_active:
            print("Stand - Player ends turn")
            self.game_active = False
            self.hit_button.config(state="disabled")
            self.stand_button.config(state="disabled")
            
            self.reveal_dealer_hole_card()
            # Start Dealer Logic
            self.after(800, self.perform_dealer_turn)

    def perform_dealer_turn(self):
        """
        Dealer hits until score is 17 or higher.
        Uses recursion with timer to allow animation between cards.
        """
        dealer_val = self.calculate_hand_value(self.dealer_hand)
        
        if dealer_val < 17:
            self.deal_card("dealer")
            # Continue turn after animation delay
            self.after(1000, self.perform_dealer_turn)
        else:
            self.finalize_game_outcome()

    def finalize_game_outcome(self):
        player_val = self.calculate_hand_value(self.player_hand)
        dealer_val = self.calculate_hand_value(self.dealer_hand)
        
        print(f"Game Over. Player: {player_val}, Dealer: {dealer_val}")
        # Logic for win/loss text can be added here later
            
    def reveal_dealer_hole_card(self):
        if self.dealer_hole_card_item and self.dealer_hole_card_front:
            # We need coordinates from canvas
            coords = self.canvas.coords(self.dealer_hole_card_item)
            if coords:
                x, y = coords[0], coords[1]
                # Coordinates are currently NW. Pass them directly.
                self.animate_flip(self.dealer_hole_card_item, self.card_back_image_pil, self.dealer_hole_card_front, x, y)
            self.dealer_hole_card_item = None # Prevent re-reveal
            self.update_scores()

    # -------------------------------------------------------------------------
    # 4. Card Management
    # -------------------------------------------------------------------------
    def get_random_card_file(self):
        return random.choice(CARD_FILES)

    def deal_card(self, recipient="player", face_down=False):
        # Determine Position
        if recipient == "player":
            if self.current_player_slot >= 5: return
            target_x = 200 + (self.current_player_slot * 150)
            target_y = 550
            self.current_player_slot += 1
        else: # dealer
            if self.current_dealer_slot >= 5: return
            target_x = 200 + (self.current_dealer_slot * 150)
            target_y = 130 
            self.current_dealer_slot += 1

        # Load random card image
        card_filename = self.get_random_card_file()
        
        # Parse Rank and Add to Hand
        rank = card_filename.split("_of_")[0]
        if recipient == "player":
            self.player_hand.append(rank)
        else:
            self.dealer_hand.append(rank)
            
        full_path = os.path.join(self.sprites_path, card_filename)
        
        if not os.path.exists(full_path):
            print(f"Error: Card image not found: {full_path}")
            return

        front_pil = Image.open(full_path)
        front_pil = front_pil.resize(self.card_size, Image.Resampling.LANCZOS)
        
        # Place "Back" of card on table initially (Anchor NW)
        card_item = self.canvas.create_image(target_x, target_y, anchor="nw", image=self.card_back_photo)
        self.card_items.append(card_item)
        
        if face_down:
            # Save for later, do not flip yet
            self.dealer_hole_card_item = card_item
            self.dealer_hole_card_front = front_pil
        else:
            self.animate_flip(card_item, self.card_back_image_pil, front_pil, target_x, target_y)
            
        self.update_scores()

    # -------------------------------------------------------------------------
    # 5. Animation
    # -------------------------------------------------------------------------
    def animate_flip(self, canvas_item, back_pil, front_pil, nw_x, nw_y):
        """
        Simulate a 3D flip.
        To ensure stability, we temporarily switch the anchor to CENTER.
        """
        steps = 10
        sleep_time = 0.02
        current_width, height = self.card_size
        
        # Calculate Center Coordinates
        center_x = nw_x + (current_width // 2)
        center_y = nw_y + (height // 2)
        
        # Switch Anchor to Center for Animation
        self.canvas.itemconfig(canvas_item, anchor="center")
        self.canvas.coords(canvas_item, center_x, center_y)
        
        # Phase 1: Shrink width (showing back)
        for i in range(steps, 0, -1):
            new_width = int(current_width * (i / steps))
            if new_width <= 0: new_width = 1
            
            resized_back = back_pil.resize((new_width, height), Image.Resampling.NEAREST)
            new_photo = ImageTk.PhotoImage(resized_back)
            
            # Just swap image, anchor center handles the alignment
            self.canvas.itemconfig(canvas_item, image=new_photo)
            
            self.canvas.update()
            self.temp_animation_ref = new_photo 
            time.sleep(sleep_time)

        # Phase 2: Grow width (showing front)
        for i in range(1, steps + 1):
            new_width = int(current_width * (i / steps))
            if new_width <= 0: new_width = 1
            
            resized_front = front_pil.resize((new_width, height), Image.Resampling.NEAREST)
            new_photo = ImageTk.PhotoImage(resized_front)
            
            self.canvas.itemconfig(canvas_item, image=new_photo)
            
            self.canvas.update()
            self.temp_animation_ref = new_photo
            time.sleep(sleep_time)

        # Finalize: Restore to NW anchor
        final_photo = ImageTk.PhotoImage(front_pil)
        self.canvas.itemconfig(canvas_item, image=final_photo, anchor="nw")
        self.canvas.coords(canvas_item, nw_x, nw_y)
        
        self.card_images_ref.append(final_photo)
        self.temp_animation_ref = None

if __name__ == "__main__":
    app = BlackjackApp()
    app.mainloop()



    