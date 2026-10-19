# Card Collection

Six offline Python/Pygame games using the supplied 52-card artwork.

## Setup and launch

Extract the ENTIRE ZIP first. Keep `card_games.py` beside the `cards` folder.
Requires Python 3.10 or later and Pygame 2.

Linux:
```bash
python3 -m pip install pygame
python3 card_games.py
```
If your Linux installation reports an externally managed environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pygame
python card_games.py
```
Your distribution may require its python3-venv package for that option.

Windows:
```bat
py -m pip install pygame
py card_games.py
```

No network connection is needed after installing Pygame. There is no betting or real money.

## Controls

Click a game in the menu. Click Rules for its instructions, New deal to restart,
or Menu to switch games. Escape returns to the menu. N starts a new deal.
The window can be resized; the board scales while keeping its proportions.

## Eleven Out (assumed rules)

This implements the nine-card Elevens solitaire variant. If your Eleven Out
uses different rules, this is the part to adapt.

Nine cards are dealt face up. Select two number cards totaling eleven
(Ace=1), or a Jack, Queen and King of any suits. Click Remove to confirm.
Cards refill from the stock. Clear all 52 cards to win. A deal ends when
no legal combination remains; some deals cannot be won.
Click a selected card again to deselect it, or use Clear selection.
Hint selects an available combination. Undo restores the previous removal,
including the original stock order, and can be used after a blocked deal.

## Blackjack

Click Hit to draw or Stand to let the dealer play. Dealer stands on all 17s,
including soft 17. Aces count as 1 or 11; face cards count as 10. Two-card
blackjack beats a 21 made with more cards. Equal totals push. Each deal uses
a fresh shuffled deck. This is a simplified practice game without splits,
doubling, insurance, betting or persistent statistics.

## Memory

Find 12 pairs using 24 cards (Ace through Queen in clubs and spades).
Matching ranks form pairs. Mismatches remain visible for one second;
matched pairs stay face up. The attempt count increases with each pair tried.

## Higher or Lower

Predict the next rank. Ace is low; King is high. Equal ranks push, preserving
your streak. Wrong guesses reset the streak. Correct guesses add to your score.
Play until all 52 cards have appeared. Best streak applies to the current deal.

## Artwork and moving to another PC

The included `cards` folder contains your original PNG artwork and card backs.
Copy the entire extracted folder to another PC and install Python/Pygame there.
Artwork is located relative to the script rather than the terminal directory.
You can specify a different folder:
```bash
python3 card_games.py --assets "/path/to/cards"
```
Use the existing filenames such as `ace_of_spades.png` and `cardback1.png`.
Missing/unreadable images use generated text cards so games remain playable.
Restart after changing images because artwork is cached during play.

## Code organization and extension

`Card` stores a conventional rank (Ace=1, Jack=11, Queen=12, King=13) and suit.
`Hand` stores a labeled collection. `Deck` creates, shuffles and deals 52 cards.
This rank convention differs from the uploaded prototype's internal face index.
`eleven_valid`, `eleven_moves` and `blackjack_total` are independent rule helpers.
`App` handles the shared menu, artwork cache, drawing, input and game state.
To add a game, add its rules and extend App.start, App.draw and its input actions.
Importing the module does not launch the window or deal cards.

This is a new collection based on your supplied foundation; the original file
is not overwritten. Settings, progress and scores are not saved after exit.

## Pyramid 13

The assumed thirteen game is Pyramid Solitaire. Clear a seven-row pyramid
of 28 cards by removing uncovered pairs totaling 13. King=13 and is removed
alone, Queen=12, Jack=11, Ace=1. A pyramid card is uncovered when both cards
immediately below it have gone. You may pair two uncovered pyramid cards,
or an uncovered card and the top waste card. Click Draw stock to turn over
one card. There is one pass through the stock, with no redeal. Select cards
and click Remove. Undo reverses draws and removals. Clear the pyramid to win;
the stock and waste do not have to be cleared. The program leaves blocked
positions available for undo or a new deal rather than declaring an automatic loss.

## Poker Squares (25-card poker)

Place the next shown card into any empty square in a 5x5 grid. You cannot
swap placed cards, but Undo reverses placement. After 25 placements the
five rows and five columns form ten scored poker hands. Diagonals do not score.
Completed lines score immediately; incomplete lines show zero.

American scoring used here: royal flush 100, straight flush 75, four of a kind
50, full house 25, flush 20, straight 15, three of a kind 10, two pairs 5,
one pair 2, high card 0. Aces may be low in A2345 or high in TJQKA; they cannot
wrap through the middle of a straight. Only the highest category in each
hand scores. Other Poker Squares scoring systems exist; this one is shown
in the built-in Rules screen.
