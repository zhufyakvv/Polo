import os
import sys

import pygame

import varibles
from Modules.controls import Controls
from Modules.program import Program

FPS = varibles.FPS
window_title = varibles.window_title
screen_resolution = varibles.screen_resolution
screen_mode = varibles.screen_mode


class Engine:
    def __init__(self):
        pygame.init()
        self.running = True
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 30)
        pygame.display.set_caption(window_title)
        self.display = pygame.display.set_mode(screen_resolution)
        self.controls = Controls()
        self.program = Program()

    def level(self, level_name=""):
        # self.level_creator("first")
        print("LEVEL LOAD")

    def blit(self):
        self.display.blit(self.controls, self.controls.position)
        self.display.blit(self.program, self.program.position)

    def event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if pygame.mouse.get_pressed()[0]:
                self.controls.event(pygame.mouse)
                self.program.event(pygame.mouse)

                if self.controls.get_command() != "":
                    self.program.add(self.controls.get_command())
                if self.program.get_deleted() != "":
                    self.controls.add(self.program.get_deleted())

                self.blit()

    def run(self):
        self.blit()
        while self.running:
            self.event()

            pygame.display.flip()
            pygame.display.update()
            # TODO FPS LOCK
            # TODO GIT IT
