import math
import pygame
from config import *


class Player(pygame.sprite.Sprite):
    def __init__(self, game, pos):
        self.game = game
        self.groups = self.game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.groups.change_layer(self, PLAYER_LAYER)

        self.x = WIN_WIDTH / 2
        self.y = WIN_HEIGHT / 2

        self.image = pygame.Surface([32, 32])
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.pos = pos

        self.move_str = ''

    def update(self):
        self.movement()

    def movement(self):
        keys = pygame.key.get_pressed()

        if self.pos[0] > 640:
            if keys[pygame.K_a]:
                for sprite in self.game.all_sprites:
                    sprite.rect.x += PLAYER_SPEED
                for sprite in self.game.other_players:
                    sprite.rect.x += PLAYER_SPEED
                for sprite in self.game.other_shots:
                    sprite.rect.x += PLAYER_SPEED
                self.rect.x -= PLAYER_SPEED
                self.pos[0] -= PLAYER_SPEED
                self.move_str += 'l '

        if self.pos[0] < 5760:
            if keys[pygame.K_d]:
                for sprite in self.game.all_sprites:
                    sprite.rect.x -= PLAYER_SPEED
                for sprite in self.game.other_players:
                    sprite.rect.x -= PLAYER_SPEED
                for sprite in self.game.other_shots:
                    sprite.rect.x -= PLAYER_SPEED
                self.rect.x += PLAYER_SPEED
                self.pos[0] += PLAYER_SPEED
                self.move_str += 'r '

        if self.pos[1] > 480:
            if keys[pygame.K_w]:
                for sprite in self.game.all_sprites:
                    sprite.rect.y += PLAYER_SPEED
                for sprite in self.game.other_players:
                    sprite.rect.y += PLAYER_SPEED
                for sprite in self.game.other_shots:
                    sprite.rect.y += PLAYER_SPEED
                self.rect.y -= PLAYER_SPEED
                self.pos[1] -= PLAYER_SPEED
                self.move_str += 'u '

        if self.pos[1] < 4320:
            if keys[pygame.K_s]:
                for sprite in self.game.all_sprites:
                    sprite.rect.y -= PLAYER_SPEED
                for sprite in self.game.other_players:
                    sprite.rect.y -= PLAYER_SPEED
                for sprite in self.game.other_shots:
                    sprite.rect.y -= PLAYER_SPEED
                self.rect.y += PLAYER_SPEED
                self.pos[1] += PLAYER_SPEED
                self.move_str += 'd '

    def get_pos(self):
        moves = self.move_str
        self.move_str = ''
        return moves

    def collide(self):
        hits = pygame.sprite.spritecollide(self, self.game.other_shots, False)
        if hits:
            return True
        return False


class Shot(pygame.sprite.Sprite):
    def __init__(self, game, player_pos, mouse_pos):
        self.game = game
        self.serial = self.game.serial

        self.groups = self.game.all_sprites, self.game.all_shots
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.groups[0].change_layer(self, SHOT_LAYER)
        self.groups[1].change_layer(self, SHOT_LAYER)

        # player center position
        self.x = player_pos[0] + 8
        self.y = player_pos[1] + 8

        self.image = pygame.image.load('img/circle.png').convert()

        # Distance and angel
        angel = math.atan2(mouse_pos[1] - self.y, mouse_pos[0] - self.x)

        self.image.set_colorkey(GREEN)

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.dx = math.cos(angel) * SHOT_SPEED
        self.dy = math.sin(angel) * SHOT_SPEED

    def update(self):
        self.movement()

    def movement(self):
        self.x += self.dx
        self.y += self.dy
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def get_pos(self):
        if -32 < self.rect.x < 640 and -32 < self.rect.y < 480:
            return [self.serial, self.rect.x, self.rect.y]
        self.kill()
        return [self.serial, -1, -1]


class Other_Shot(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self.groups = self.game.other_shots
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.groups.change_layer(self, SHOT_LAYER)

        self.x = x
        self.y = y

        self.image = pygame.image.load('img/circle.png').convert()
        self.image.set_colorkey(GREEN)

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y


class Other_Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y, pos):
        self.game = game
        self.groups = self.game.other_players
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.groups.change_layer(self, PLAYER_LAYER)

        self.x = pos[0]
        self.y = pos[1]

        self.image = pygame.Surface([x, y])
        self.image.fill(GREEN)

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y




class Ground(pygame.sprite.Sprite):
    def __init__(self, game, x, y, color):
        self.game = game
        self.groups = self.game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.groups.change_layer(self, GROUND_LAYER)

        self.x = x
        self.y = y

        self.image = pygame.Surface([TILESIZE, TILESIZE])
        self.image.fill(color)

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y


class Button:
    def __init__(self, x, y, width, height, fg, bg, content, fontsize):
        self.font = pygame.font.Font('arial.ttf', fontsize)
        self.content = content

        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.fg = fg
        self.bg = bg

        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(self.bg)
        self.rect = self.image.get_rect()

        self.rect.x = self.x
        self.rect.y = self.y

        self.text = self.font.render(self.content, True, self.fg)
        self.text_rect = self.text.get_rect(center=(self.width / 2, self.height / 2))
        self.image.blit(self.text, self.text_rect)

    def is_pressed(self, pos, pressed):
        if self.rect.collidepoint(pos):
            if pressed[0]:
                return True
            return False
        return False
