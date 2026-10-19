"""Four offline card games sharing a reusable card model and artwork cache."""
from dataclasses import dataclass
from pathlib import Path
from itertools import combinations
import random
import argparse
from collections import Counter

SUITS = ('clubs', 'spades', 'hearts', 'diamonds')
NAMES = {1: 'ace', 11: 'jack', 12: 'queen', 13: 'king'}

@dataclass(frozen=True)
class Card:
    rank: int
    suit: str

    def __str__(self):
        return f'{NAMES.get(self.rank, str(self.rank))}_of_{self.suit}'

class Hand:
    def __init__(self, label=''):
        self.label, self.cards = label, []

    def __len__(self):
        return len(self.cards)

    def __getitem__(self, index):
        return self.cards[index]

    def add_card(self, card):
        self.cards.append(card)

class Deck(Hand):
    def __init__(self):
        super().__init__('Deck')
        self.cards = [Card(r, s) for s in SUITS for r in range(1, 14)]
        random.shuffle(self.cards)

    def pop_card(self):
        return self.cards.pop() if self.cards else None

    def deal_cards(self, hand, count):
        for _ in range(min(count, len(self))):
            hand.add_card(self.pop_card())

def eleven_valid(cards):
    return (len(cards) == 2 and all(c.rank <= 10 for c in cards)
            and sum(c.rank for c in cards) == 11) or (
            len(cards) == 3 and sorted(c.rank for c in cards) == [11, 12, 13])

def eleven_moves(board):
    available = [i for i, c in enumerate(board) if c]
    return [group for n in (2, 3) for group in combinations(available, n)
            if eleven_valid([board[i] for i in group])]

def blackjack_total(cards):
    total = sum(11 if c.rank == 1 else min(c.rank, 10) for c in cards)
    aces = sum(c.rank == 1 for c in cards)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def poker_score(cards):
    if len(cards) != 5 or any(c is None for c in cards): return ('Incomplete', 0)
    ranks = sorted(14 if c.rank == 1 else c.rank for c in cards)
    groups = sorted(Counter(ranks).values(), reverse=True)
    flush = len({c.suit for c in cards}) == 1
    straight = len(set(ranks)) == 5 and (ranks[-1]-ranks[0] == 4 or ranks == [2,3,4,5,14])
    if straight and flush: return ('Royal flush', 100) if ranks == [10,11,12,13,14] else ('Straight flush', 75)
    if groups == [4,1]: return ('Four of a kind', 50)
    if groups == [3,2]: return ('Full house', 25)
    if flush: return ('Flush', 20)
    if straight: return ('Straight', 15)
    if groups == [3,1,1]: return ('Three of a kind', 10)
    if groups == [2,2,1]: return ('Two pairs', 5)
    if groups == [2,1,1,1]: return ('One pair', 2)
    return ('High card', 0)


RULES = {
    'Eleven Out': ['Remove all 52 cards to win. Select cards, then click Remove.',
                   'Select two number cards totaling 11. Ace = 1.',
                   'Or select one Jack, one Queen and one King (any suits).',
                   'Empty spaces refill automatically. No available move ends the deal.',
                   'Hint highlights a move. Undo reverses your last removal.'],
    'Blackjack': ['Get closer to 21 than the dealer without going over.',
                  'Ace = 1 or 11; picture cards = 10. Hit draws; Stand ends your turn.',
                  'Dealer stands on all 17s. A two-card 21 beats other 21s.',
                  'Ties push. Practice only: no money, splits, doubling or insurance.'],
    'Memory': ['Find 12 pairs among 24 face-down cards.',
               'A pair has the same rank, regardless of suit.',
               'Click two cards. Mismatches turn back after a short pause.',
               'Matched pairs remain visible. Fewer attempts is better.'],
    'Higher or Lower': ['Guess whether the next card has a higher or lower rank.',
                        'Ace is low (1); Jack = 11, Queen = 12, King = 13.',
                        'Equal ranks are a push: keep your streak.',
                        'A wrong guess resets the streak. Play through all 52 cards.']}

RULES['Pyramid 13'] = [
    'Clear the 28-card pyramid. Only uncovered pyramid cards are playable.',
    'Select a pair totaling 13, then Remove. A King (13) goes alone.',
    'Ace=1, Jack=11, Queen=12. Use the waste top with pyramid cards.',
    'Draw flips one stock card. One pass only; no redeals.',
    'Undo reverses a removal or draw. New deal restarts when blocked.']
RULES['Poker Squares'] = [
    'Place 25 cards into a 5 x 5 grid. Click an empty space for the next card.',
    'Cards cannot move after placement, except through Undo.',
    'All five rows and five columns score; diagonals do not.',
    'American scoring: royal flush 100; straight flush 75; four of a kind 50;',
    'full house 25; flush 20; straight 15; three of a kind 10;',
    'two pairs 5; pair 2; high card 0. Ace can be high or low in straights.']

class App:
    def __init__(self, assets=None):
        import pygame
        self.pg = pygame
        pygame.init()
        self.screen = pygame.display.set_mode((1100, 800), pygame.RESIZABLE)
        pygame.display.set_caption('Card Collection')
        self.canvas = pygame.Surface((1100, 800))
        self.font = pygame.font.Font(None, 26)
        self.big = pygame.font.Font(None, 42)
        self.small = pygame.font.Font(None, 22)
        self.clock = pygame.time.Clock()
        self.assets = Path(assets) if assets else Path(__file__).resolve().parent / 'cards'
        self.images = {}
        self.game = None
        self.help = False
        self.buttons, self.hits = [], []
        self.running = True

    def text(self, message, x, y, big=False, color=(240, 243, 232)):
        self.canvas.blit((self.big if big else self.font).render(str(message), True, color), (x, y))

    def button(self, label, x, y, action, width=145):
        rect = self.pg.Rect(x, y, width, 40)
        self.pg.draw.rect(self.canvas, (40, 67, 78), rect, border_radius=8)
        self.text(label, x+12, y+9)
        self.buttons.append((rect, action))

    def card(self, card, x, y, index=None, hidden=False, selected=False, height=120):
        key = 'cardback1' if hidden else str(card)
        if key not in self.images:
            try:
                img = self.pg.image.load(str(self.assets / (key+'.png'))).convert_alpha()
                self.images[key] = self.pg.transform.smoothscale(img, (84, 120))
            except (OSError, self.pg.error):
                img = self.pg.Surface((84, 120))
                img.fill((50, 77, 130) if hidden else (250, 246, 233))
                if not hidden:
                    ink = (170, 32, 44) if card.suit in ('hearts', 'diamonds') else (25, 30, 40)
                    img.blit(self.font.render(NAMES.get(card.rank, str(card.rank)).upper(), True, ink), (5, 12))
                    img.blit(self.small.render(card.suit, True, ink), (5, 62))
                self.images[key] = img
        rect = self.pg.Rect(x, y, 84, height)
        self.canvas.blit(self.pg.transform.smoothscale(self.images[key], (84, height)), rect)
        if selected:
            self.pg.draw.rect(self.canvas, (255, 210, 80), rect.inflate(6, 6), 4, border_radius=5)
        if index is not None:
            self.hits.append((rect, index))

    def start(self, name):
        self.game, self.help, self.done = name, False, False
        self.deck = Deck()
        self.selected, self.history = [], []
        self.message = ''
        self.score = self.streak = self.best = self.attempts = 0
        if name == 'Eleven Out':
            self.board = [self.deck.pop_card() for _ in range(9)]
            self.check_eleven()
        elif name == 'Pyramid 13':
            self.board = [self.deck.pop_card() for _ in range(28)]
            self.waste = []
        elif name == 'Poker Squares':
            self.board = [None]*25
            self.current = self.deck.pop_card()
        elif name == 'Memory':
            self.board = [Card(r, s) for r in range(1, 13) for s in SUITS[:2]]
            random.shuffle(self.board)
            self.matched, self.revealed, self.hide_at = set(), [], 0
        elif name == 'Blackjack':
            self.player = [self.deck.pop_card(), self.deck.pop_card()]
            self.dealer = [self.deck.pop_card(), self.deck.pop_card()]
            if blackjack_total(self.player) == 21 or blackjack_total(self.dealer) == 21:
                self.settle()
        else:
            self.current = self.deck.pop_card()
            self.previous = None

    def check_eleven(self):
        self.done = not eleven_moves(self.board)
        self.message = ('You cleared the deck!' if all(c is None for c in self.board)
                        else 'No moves remain. Try a new deal or Undo.') if self.done else 'Select a pair totaling 11, or a Jack, Queen and King.'

    def exposed(self, i):
        if i == 28: return bool(self.waste)
        if not self.board[i]: return False
        row = next(r for r in range(7) if i < (r+1)*(r+2)//2)
        if row == 6: return True
        col = i - row*(row+1)//2
        child = (row+1)*(row+2)//2 + col
        return self.board[child] is None and self.board[child+1] is None

    def pyramid_card(self, i):
        return self.waste[-1] if i == 28 else self.board[i]

    def snapshot_pyramid(self):
        self.history.append((self.board[:], self.deck.cards[:], self.waste[:]))

    def draw_stock(self):
        if not self.done and len(self.deck):
            self.snapshot_pyramid()
            self.waste.append(self.deck.pop_card())
            self.selected = []

    def pyramid_remove(self):
        cards = [self.pyramid_card(i) for i in self.selected]
        if not (len(cards) == 1 and cards[0].rank == 13 or
                len(cards) == 2 and sum(c.rank for c in cards) == 13):
            self.message = 'Select an exposed King, or two exposed cards totaling 13.'
            return
        self.snapshot_pyramid()
        for i in self.selected:
            if i == 28: self.waste.pop()
            else: self.board[i] = None
        self.selected = []
        if not any(self.board): self.done, self.message = True, 'Pyramid cleared! You win.'
        else: self.message = 'Select uncovered cards. Draw from stock when needed.'

    def extra_undo(self):
        if not self.history: return
        if self.game == 'Pyramid 13':
            self.board, self.deck.cards, self.waste = self.history.pop()
            self.selected = []
        else:
            self.board, self.deck.cards, self.current = self.history.pop()
        self.done, self.message = False, ''

    def poker_lines(self):
        return ([self.board[r*5:r*5+5] for r in range(5)] +
                [[self.board[r*5+c] for r in range(5)] for c in range(5)])

    def remove(self):
        if not eleven_valid([self.board[i] for i in self.selected]):
            self.message = 'That selection is not a pair totaling 11 or a J/Q/K trio.'
            return
        self.history.append((self.board[:], self.deck.cards[:], self.score))
        for i in self.selected:
            self.board[i] = self.deck.pop_card()
            self.score += 1
        self.selected = []
        self.check_eleven()

    def undo(self):
        if self.history:
            self.board, self.deck.cards, self.score = self.history.pop()
            self.selected = []
            self.check_eleven()

    def hint(self):
        moves = eleven_moves(self.board)
        if moves:
            self.selected = list(moves[0])

    def settle(self):
        p, d = blackjack_total(self.player), blackjack_total(self.dealer)
        pn, dn = p == 21 and len(self.player) == 2, d == 21 and len(self.dealer) == 2
        if p > 21: result = 'Bust! Dealer wins.'
        elif d > 21: result = 'Dealer busts! You win.'
        elif pn != dn: result = 'Blackjack! You win.' if pn else 'Dealer blackjack.'
        elif p == d: result = 'Push: a tie.'
        else: result = 'You win!' if p > d else 'Dealer wins.'
        self.message, self.done = result, True

    def hit(self):
        if not self.done:
            self.player.append(self.deck.pop_card())
            if blackjack_total(self.player) >= 21:
                self.stand()

    def stand(self):
        if self.done: return
        if blackjack_total(self.player) <= 21:
            while blackjack_total(self.dealer) < 17:
                self.dealer.append(self.deck.pop_card())
        self.settle()

    def guess(self, higher):
        if self.done: return
        next_card = self.deck.pop_card()
        self.previous, self.current = self.current, next_card
        delta = next_card.rank - self.previous.rank
        if delta == 0: self.message = 'Same rank: push.'
        elif (delta > 0) == higher:
            self.streak += 1
            self.score += 1
            self.message = 'Correct!'
        else:
            self.streak = 0
            self.message = 'Wrong guess. Start a new streak!'
        self.best = max(self.best, self.streak)
        if not len(self.deck):
            self.done = True
            self.message += ' Deck complete!'

    def select(self, i):
        if self.done: return
        if self.game == 'Pyramid 13':
            if not self.exposed(i): return
            if i in self.selected: self.selected.remove(i)
            elif len(self.selected) < 2: self.selected.append(i)
        elif self.game == 'Poker Squares':
            if self.board[i] is not None: return
            self.history.append((self.board[:], self.deck.cards[:], self.current))
            self.board[i] = self.current
            if all(self.board):
                self.current = None
                self.done = True
                total = sum(poker_score(line)[1] for line in self.poker_lines())
                self.message = f'Grid complete! Total score: {total}. Click Rules for the scoring table.'
            else: self.current = self.deck.pop_card()
        elif self.game == 'Eleven Out':
            if i in self.selected: self.selected.remove(i)
            elif len(self.selected) < 3: self.selected.append(i)
        elif self.game == 'Memory':
            if i in self.matched or i in self.revealed or len(self.revealed) == 2: return
            self.revealed.append(i)
            if len(self.revealed) == 2:
                self.attempts += 1
                a, b = self.revealed
                if self.board[a].rank == self.board[b].rank:
                    self.matched.update(self.revealed)
                    self.revealed = []
                    if len(self.matched) == 24:
                        self.done, self.message = True, f'All pairs found in {self.attempts} attempts!'
                else: self.hide_at = self.pg.time.get_ticks() + 1000

    def draw(self):
        self.canvas.fill((16, 78, 65))
        self.buttons, self.hits = [], []
        self.text('CARD COLLECTION', 35, 25, True)
        if not self.game:
            self.text('Choose a game', 70, 115, True)
            for n, name in enumerate(RULES):
                self.button(name, 70, 175+n*85, lambda name=name: self.start(name), 260)
                self.text(RULES[name][0], 355, 185+n*85)
            self.text('Your card artwork included. Fully offline. Resize the window to fit.', 70, 715)
            return
        self.text(self.game, 35, 85, True)
        self.button('Menu', 600, 25, lambda: setattr(self, 'game', None), 110)
        self.button('New deal', 725, 25, lambda: self.start(self.game))
        self.button('Rules', 885, 25, lambda: setattr(self, 'help', not self.help))
        if self.help:
            for n, line in enumerate(RULES[self.game]): self.text(line, 40, 175+n*50)
            self.text('Click Rules to return. Esc returns to the menu. N starts a new deal.', 40, 650)
            return
        if self.game == 'Pyramid 13':
            for row in range(7):
                for col in range(row+1):
                    i = row*(row+1)//2+col
                    c = self.board[i]
                    if c:
                        self.card(c, 385-row*47+col*94, 155+row*63, i,
                                  selected=i in self.selected)
            self.text(f'Stock: {len(self.deck)}', 840, 160)
            if self.waste: self.card(self.waste[-1], 850, 210, 28, selected=28 in self.selected)
            self.button('Draw stock', 820, 365, self.draw_stock)
            self.button('Remove', 820, 425, self.pyramid_remove)
            self.button('Undo', 820, 485, self.extra_undo)
            self.text('One pass / no redeal', 790, 560)
        elif self.game == 'Poker Squares':
            lines = self.poker_lines()
            self.text('Score: '+str(sum(poker_score(line)[1] for line in lines)), 790, 165)
            for i, c in enumerate(self.board):
                x, y = 110+(i%5)*110, 150+(i//5)*109
                if c: self.card(c, x, y, height=95)
                else:
                    rect = self.pg.Rect(x, y, 84, 95)
                    self.pg.draw.rect(self.canvas, (95, 155, 132), rect, 2, border_radius=6)
                    self.hits.append((rect, i))
            for r in range(5):
                name, points = poker_score(lines[r])
                self.text(f'{points}', 680, 190+r*109)
            for c in range(5): self.text(str(poker_score(lines[5+c])[1]), 140+c*110, 695)
            if self.current:
                self.text('Next card', 810, 225)
                self.card(self.current, 825, 270)
            self.button('Undo', 800, 450, self.extra_undo)
            self.text('Rows + columns', 785, 520)
        elif self.game == 'Eleven Out':
            self.text(f'Removed: {self.score}/52     Stock: {len(self.deck)}', 340, 95)
            for i, c in enumerate(self.board):
                if c: self.card(c, 310+(i%3)*145, 160+(i//3)*158, i, selected=i in self.selected)
            self.button('Remove', 820, 200, self.remove)
            self.button('Hint', 820, 260, self.hint)
            self.button('Undo', 820, 320, self.undo)
            self.button('Clear selection', 795, 380, lambda: self.selected.clear(), 200)
        elif self.game == 'Memory':
            self.text(f'Pairs: {len(self.matched)//2}/12      Attempts: {self.attempts}', 340, 95)
            for i, c in enumerate(self.board):
                self.card(c, 160+(i%6)*130, 160+(i//6)*137, i,
                          hidden=i not in self.matched and i not in self.revealed,
                          selected=i in self.matched)
        elif self.game == 'Blackjack':
            self.text('Dealer: '+(str(blackjack_total(self.dealer)) if self.done else '?'), 50, 145)
            for i, c in enumerate(self.dealer): self.card(c, 50+i*89, 185, hidden=i==1 and not self.done)
            self.text(f'You: {blackjack_total(self.player)}', 50, 370)
            for i, c in enumerate(self.player): self.card(c, 50+i*89, 410)
            if not self.done:
                self.button('Hit', 80, 585, self.hit)
                self.button('Stand', 250, 585, self.stand)
        else:
            self.text(f'Correct: {self.score}    Streak: {self.streak}    Best: {self.best}    Left: {len(self.deck)}', 70, 160)
            if self.previous:
                self.text('Previous', 330, 230)
                self.card(self.previous, 330, 275)
            self.text('Current', 530, 230)
            self.card(self.current, 530, 275)
            if not self.done:
                self.button('Higher', 330, 465, lambda: self.guess(True))
                self.button('Lower', 510, 465, lambda: self.guess(False))
        self.text(self.message, 35, 735)

    def run(self):
        while self.running:
            if self.game == 'Memory' and len(self.revealed) == 2 and self.pg.time.get_ticks() >= self.hide_at:
                self.revealed = []
            self.draw()
            size = self.screen.get_size()
            scale = min(size[0]/1100, size[1]/800)
            w, h = int(1100*scale), int(800*scale)
            ox, oy = (size[0]-w)//2, (size[1]-h)//2
            self.screen.fill((10, 25, 27))
            self.screen.blit(self.pg.transform.smoothscale(self.canvas, (w, h)), (ox, oy))
            self.pg.display.flip()
            for event in self.pg.event.get():
                if event.type == self.pg.QUIT: self.running = False
                elif event.type == self.pg.KEYDOWN:
                    if event.key == self.pg.K_ESCAPE: self.game = None
                    elif event.key == self.pg.K_n and self.game: self.start(self.game)
                elif event.type == self.pg.MOUSEBUTTONDOWN and event.button == 1:
                    pos = ((event.pos[0]-ox)/scale, (event.pos[1]-oy)/scale)
                    for rect, action in self.buttons:
                        if rect.collidepoint(pos):
                            action()
                            break
                    else:
                        for rect, index in reversed(self.hits):
                            if rect.collidepoint(pos):
                                self.select(index)
                                break
            self.clock.tick(60)
        self.pg.quit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', help='Folder containing the card PNG files')
    args = parser.parse_args()
    try:
        App(args.assets).run()
    except ModuleNotFoundError as error:
        if error.name != 'pygame': raise
        raise SystemExit('Install pygame first: python -m pip install pygame')
