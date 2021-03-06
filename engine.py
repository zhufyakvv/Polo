import os
import sys

import pygame

import Libraries.load as load
import variables
from Modules.controls import Controls
from Modules.menu import Menu
from Modules.message import Message
from Modules.program import Program
from Modules.scene import Scene
from level import Level, Voice, save_current, load_current

FPS = variables.FPS
window_title = variables.window_title
screen_resolution = variables.screen_resolution
screen_mode = variables.screen_mode

language = variables.language


class Engine:
    def __init__(self):
        pygame.init()
        # Engine pause
        self.pause = False
        # Talk
        self.talk = False
        # Set up of window
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 30)
        # Window title
        pygame.display.set_caption(window_title)
        # Set up window resolution
        self.display = pygame.display.set_mode(screen_resolution)  # pygame.FULLSCREEN
        # Icon
        icon = load.image("Source/Prop/polo.png")
        if icon is not None:
            pygame.display.set_icon(icon[0])
        self.levels = load.get_levels()
        self.languages = load.get_languages()
        # Language
        self.language = 0
        self.max_lang = len(self.languages) - 1
        # Sets level
        self.level_index = 0
        self.max_level = len(self.levels) - 1
        # Clock init for ticks
        self.clock = pygame.time.Clock()
        # Level load
        self.level = Level(self.levels[self.level_index])
        # Sound
        self.sound = True
        self.controls = Controls()
        self.program = Program()
        self.scene = Scene()
        self.menu = Menu()
        self.message = Message()
        self.voice = Voice()

    def update_all(self):
        """
        Updating all screen.
        :return:
        """
        self.display.blit(self.controls, self.controls.rect)
        self.display.blit(self.program, self.program.rect)
        self.display.blit(self.scene, self.scene.rect)

        if self.talk:
            self.display.blit(self.message, self.message.rect)
        elif self.pause:
            self.display.blit(self.menu, self.menu.rect)
        pygame.display.flip()

    def update(self):
        """
        Updating parts of scene
        :return:
        """
        mouse = pygame.mouse.get_pos()
        if self.talk:
            self.display.blit(self.message, self.message.rect)
            pygame.display.update(self.message.rect)
        elif self.pause:
            self.display.blit(self.menu, self.menu.rect)
            pygame.display.update(self.menu.rect)
        else:
            if self.program.is_in(mouse) or self.controls.is_in(mouse):
                self.display.blit(self.controls, self.controls.rect)
                self.display.blit(self.program, self.program.rect)
                pygame.display.update(self.program.rect)
                pygame.display.update(self.controls.rect)
            if self.scene.is_in(mouse) or self.scene.launch:
                self.display.blit(self.scene, self.scene.rect)
                pygame.display.update(self.scene.rect)

    def get_level(self):
        """
        Returns current level
        :return:
        """
        return self.level_index

    def level_up(self):
        """
        Ups level
        :return: 
        """
        self.level_index += 1 if self.level_index < self.max_level else -self.level_index

    def level_down(self):
        """
        Ups level
        :return: 
        """
        self.level_index -= 1 if self.level_index > 0 else -self.max_level

    def set_up(self, new_lvl=None, lang=None):
        """
        Set level
        :param lang: int index of language
        :param new_lvl: int index of level in list
        :return:
        """
        if new_lvl is None:
            new_lvl = self.level_index
        else:
            self.level_index = (new_lvl + len(self.levels)) % len(self.levels)
        if lang is not None:
            self.language = (lang + len(self.languages)) % len(self.languages)
        self.load(self.levels[new_lvl])
        self.update_all()

    def get_lang(self):
        return self.languages[self.language]

    def lang_up(self):
        self.language += 1 if self.language < self.max_lang else -self.max_lang

    def lang_down(self):
        self.language -= 1 if self.language > 0 else -self.max_lang

    def load(self, level_name):
        """
        Load level to all modules
        :param level_name:
        :return:
        """
        self.level = Level(level_name)
        self.level.load()
        # Pass level to other modules
        self.program = Program()
        self.controls.level(self.level)
        self.scene.level(self.level)
        # For direct moves
        self.program.direction = int(self.scene.robot.direction)

        self.load_voice(level_name)

    def load_voice(self, level_name=None):
        """
        Load voice
        :param level_name: name of level
        :return: 
        """
        if level_name is None:
            level_name = self.levels[self.level_index]
        self.voice = Voice(level_name, self.get_lang())
        self.voice.load()

    # TODO Add sound handler. All sounds plays here.
    def check_sound(self):
        # TODO Mute sound in all modules
        if self.sound:
            pygame.mixer.unpause()
        else:
            pygame.mixer.pause()

    def reload(self):
        """
        Reloads level(scene)
        :return:
        """
        self.scene.level(self.level)
        self.update_all()

    def event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.pause = not self.pause
                    self.update_all()
                if event.key == pygame.K_SPACE:
                    if self.talk:
                        self.message.page += 1
                        if self.message.page >= len(self.message.text):
                            self.talk = False
                            self.message.page = 0
                            self.update_all()
                    elif self.pause:
                        self.pause = False
                    elif not self.scene.launch:
                        self.setup_scene()
                    elif self.scene.launch:
                        self.scene.speed_up = True

            if self.talk:
                self.message.event(pygame.mouse, event)
            elif self.pause:
                self.menu.event(pygame.mouse, event)
            else:
                if not self.scene.launch:
                    self.controls.event(pygame.mouse, event)
                    self.program.event(pygame.mouse, event)
                    self.scene.event(pygame.mouse, event)

                # I can just change time in scene to speed up
                if self.scene.launch and pygame.mouse.get_pressed()[0]:
                    # Speed up scene
                    self.scene.speed_up = True
            self.invoker()

    def invoker(self):
        """
        Invokes module calls
        :return:
        """
        """Message Echo"""
        if self.message.get_echo() is not None:
            self.message_handler()
            self.message.echo_out()

        """Controls Echos"""
        if self.controls.get_echo() is not None:
            self.program.add(self.controls.get_echo())
            # Direct turn
            self.controls.set_delta_direct(self.program.get_delta_direction())
            self.controls.echo_out()

        """Program Echos"""
        if self.program.get_echo() is not None:
            self.controls.add(self.program.get_echo())
            # Direct turn
            self.controls.set_delta_direct(self.program.get_delta_direction())
            self.program.echo_out()

        """Scene Echos"""
        if self.scene.get_echo() is not None:
            self.scene_handler()
            self.scene.echo_out()

        """Menu Echos"""
        if self.menu.get_echo() is not None:
            self.menu_handler()
            self.menu.echo_out()

        """Level Changing"""
        if self.menu.level != self.level_index:
            self.menu.set_level(self.level_index)
            self.menu.update()
        """Language Changing"""
        if self.menu.language != self.language:
            self.menu.set_language(self.language)
            self.menu.update()

    def play(self):
        self.pause = False
        """VOICE"""
        self.set_message(self.voice.start)
        self.talk = len(self.voice.start) > 0

    def menu_handler(self):
        for i in self.menu.get_echo():
            if str(i) == "play":
                self.play()
            elif str(i) == "exit":
                self.exit()
            elif str(i) == "level_choose":
                self.load(i.caption)
                self.update_all()
            elif str(i) == "level_prev":
                self.level_down()
                self.update()
            elif str(i) == "level_next":
                self.level_up()
                self.update()
            elif str(i) == "lang_choose":
                self.load_voice()
                self.update_all()
            elif str(i) == "lang_prev":
                self.lang_down()
                self.update()
            elif str(i) == "lang_next":
                self.lang_up()
                self.update()
            elif str(i) == "sound":
                self.sound = i.switch_index == 1
                self.check_sound()
            elif str(i) == "about":
                variables.about()

    def set_message(self, text):
        self.message.set_text(text)
        self.message.update()
        self.update_all()

    def message_handler(self):
        self.talk = self.message.echo != "end"
        if self.message.echo == "end":
            self.update_all()
            self.message.flush()

    def scene_handler(self):
        for i in self.scene.echo:
            if i.name == "finish":
                self.pause = True
            elif i.name == "polo":
                self.setup_scene()

    def setup_scene(self):
        """
        setups
        :return:
        """
        self.scene.set_program(self.program.get_program())
        self.scene.start()
        self.clock.tick()

    def intro(self, logo_path="Source/logo.png", bg_color=(0, 0, 0)):
        """
        Game intro. Shows logo of my "studio" :D
        :param logo_path: path to image
        :param bg_color: background color
        :return: 
        """
        size = (self.display.get_size()[0], self.display.get_size()[1])
        surface_intro = pygame.Surface(size)
        surface_intro.fill(bg_color)
        logo_image = load.image(logo_path)
        surface_intro.blit(logo_image[0], ((size[0] - logo_image[1].w) / 2, (size[1] - logo_image[1].h) / 2))
        surface_intro.set_alpha(0)
        x = -225
        clock = pygame.time.Clock()
        while x < 225:
            surface_intro.set_alpha(225 - abs(x))
            self.display.fill(bg_color)
            self.display.blit(surface_intro, (0, 0))
            pygame.display.flip()
            clock.tick(FPS)
            x += 3

    def run(self):
        self.pause = True
        self.clock.tick()

        """Intro"""
        self.intro()
        self.update_all()
        while True:
            """Scene"""
            if self.scene.launch:
                self.scene.step(self.clock.tick(FPS))
                self.scene.update()
            """Scene result"""
            if self.scene.done and not self.scene.success:
                self.reload()
            elif self.scene.done and self.scene.success:
                self.set_message(self.voice.end)
                self.talk = True
                self.scene.done = False  # to get into next elif
            elif not self.scene.done and self.scene.success and not self.talk:
                self.level_up()
                self.set_up(self.level_index)
                self.play()
                # self.pause = True

            """Events"""
            self.event()
            """Update"""
            self.update()

    def exit(self):
        self.pause = True
        save_current(self.level_index, self.language)
        pygame.quit()
        sys.exit()


# If not imported -> called like main
if __name__ == "__main__":
    e = Engine()
    try:
        state = load_current()
        e.set_up(state[0], state[1])
    except FileNotFoundError:
        e.set_up(e.level_index)
    e.run()
