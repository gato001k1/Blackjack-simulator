# Predefined variables & functions
import random
drawncard = 0
PlayerTurn = True
player_hand = []
AO_hand = []
deck = ["A",2,3,4,5,6,7,8,9,10,"J","Q","K"]
Error1 = "Error: User input does not match given choice. Ending game..."




def Draw():
    drawncard = random.choice(deck)
    if drawncard == "A":
        drawncard = input("Please choose the Ace's value (1 or 11):")
        if drawncard != 1 or drawncard != 11:
            print(Error1)
    if drawncard == "J" or drawncard == "Q" or drawncard == "K":
        drawncard = 10
    return drawncard

def Hit():
    drawncard = Draw()
    if PlayerTurn == True:
        player_hand.append(drawncard)
        print("Your hand: " + str(player_hand))
        if sum(player_hand) > 21:
            print("BUST! You lose.")
    else:
        AO_hand.append(drawncard)
        print("Your hand: " + str(player_hand) + ". \nAO's hand: " + str(AO_hand) + ".")
        if sum(player_hand) > 21:
            print("BUST! AO loses. You Win!")
    return PlayerTurn
        
def Stay():
    if PlayerTurn == True:
        PlayerTurn = False
        print("Your hand: " + player_hand + ". \nAO's hand: " + AO_hand + ".")
    else:
        if sum(AO_hand) > sum(player_hand):
            print("AO Wins!")
        elif sum(AO_hand) < sum(player_hand):
            print("You Win!")
        else:
            print("It's a Tie!")
    return Stay()

Hit = "Hit"
Stay = "Stay"
Draw
Error1 = "Error: User input does not match given choice. Ending game..."
print("Welcome user.\nHit (h) or stay (s)?")
gamechoice = input()
if gamechoice == "Hit":
    (str(Hit()))
elif gamechoice == "Stay":
    print(Stay())
elif gamechoice == "Draw":
    print(Draw())
elif gamechoice != "Hit" and gamechoice != "Stay":
    print(Error1)
print("Welcome user.")
print("\nHit (h) or \nStay (s)?")
# test Draw function
