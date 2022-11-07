from os import name, system, get_terminal_size
from abc import ABC, abstractmethod
from pynput import keyboard


class AbstractInterfaceElement(ABC):
    def __init__(self, x : int, y : int, w : int, h : int):
        super().__init__()
        self.w = w
        self.h = h
        self.x = x
        self.y = y
        self.surface = [[i]*self.w for i in [' ']*self.h]

    @abstractmethod
    def _render(self) -> list[list]:
        pass

    @abstractmethod
    def click(self, x, y):
        pass



class Scoreboard(AbstractInterfaceElement):
    def __init__(self, x : int, y : int):
        super().__init__(x, y, 50, 3)
        self.surface[1] = [s for s in '| Текущий ход:   |']
        self.w = len(self.surface[1])
        self.surface[2] = ['=']*len(self.surface[1])
        self.surface[0] = ['=']*len(self.surface[1])
        self.current_symbol = 'X'
        self.game_ended = False
        
    def _render(self) -> list[list]:
        if self.game_ended:
            self.surface[1] = [s for s in '| Игра окончена! |']
        else:
            self.surface[1][15] = self.current_symbol
        return self.surface
    
    def click(self, x, y):
        pass

    def change_symbol(self, symbol):
        self.current_symbol = symbol

    def set_end_message(self):
        self.game_ended = True



class GameField(AbstractInterfaceElement):
    def __init__(self, x : int, y : int):
        super().__init__(x, y, 11, 5)
        self.cells = [[i]*3 for i in [' ']*3]
        self.m = (0, 2, 4)
        self.n = (1, 5, 9)
        self.surface[0][3] = self.surface[0][7] = '|'
        self.surface[1] = ['-']*11
        self.surface[2][3] = self.surface[2][7] = '|'
        self.surface[3] = ['-']*11
        self.surface[4][3] = self.surface[4][7] = '|'
        self.current_symbol = 'X'
        self.__scoreboards = set()
        self.winner = None

    def edit_cell(self, string : int, column : int, value):
        self.cells[string][column] = value

    def connect_scoreboard(self, sboard : AbstractInterfaceElement):
        self.__scoreboards.add(sboard)

    #Возвращает сетку с актуальным состоянием игрового поля
    def _render(self) -> list[list]:
        if self.winner != None:
            self.surface = [[i]*self.w for i in [' ']*self.h]
            self.surface[2][5] = self.winner
            self.surface[3][4:7] = ['w', 'i', 'n']
        else:
            for i in range(3):
                for j in range(3):
                    self.surface[self.m[i]][self.n[j]] = self.cells[i][j]
        return self.surface

    def check_win(self):
        for symbol in ('X', '0'):
            for string in self.cells:
                if string == [symbol, symbol, symbol]:
                    self.winner = symbol
            for i in range(3):
                if [self.cells[s][i] for s in range(3)] == [symbol, symbol, symbol]:
                    self.winner = symbol
            if [self.cells[i][i] for i in range(3)] == [symbol, symbol, symbol]:
                self.winner = symbol
            if [self.cells[i][2-i] for i in range(3)] == [symbol, symbol, symbol]:
                self.winner = symbol
        if self.winner != None:
            for sboard in self.__scoreboards:
                sboard.set_end_message()

    #Обрабатывает клик в указанное место игрового поля
    #Ставит соответствующий символ
    #Уведомляет табло об изменении символа
    def click(self, x, y):
        if self.winner != None:
            return
        if ({x, x-1, x+1}.intersection({self.n}) != None) and (y in self.m):
            for i in (x-1, x, x+1):
                for n in self.n:
                    if i == n:
                        self.edit_cell(self.m.index(y), self.n.index(n), self.current_symbol)
        if self.current_symbol == 'X':
            self.current_symbol = '0'
        else:
            self.current_symbol = 'X'
        for sboard in self.__scoreboards:
            sboard.change_symbol(self.current_symbol)
        self.check_win()



class ConsoleInterface:
    def __init__(self, width : int, height : int):
        self.width = width
        self.height = height
        self.surface = list()
        self.cursor = [1,1] #x, y
        self.__elements : AbstractInterfaceElement = set()
        self.__working = False

    def add_element(self, element : AbstractInterfaceElement):
        self.__elements.add(element)
    
    #Заполняет сетку символов актуальным видом всех элементов интерфейса
    def __render(self):
        self.surface = [[i]*self.width for i in [' ']*self.height]
        for element in self.__elements:
            element_render = element._render()
            for in_x in range(element.w):
                for in_y in range(element.h):
                    self.surface[element.y + in_y][element.x + in_x] = element_render[in_y][in_x]
        self.surface[self.cursor[1]][self.cursor[0]] = '█'

    #Очищает консоль
    def _clear(self):  
        #Для windowc 
        if name == 'nt':  
            _ = system('cls')  
        #Для mac и linux  
        else:  
            _ = system('clear') 

    @staticmethod
    def _is_rectangle(arr : list):
        """
        Checks whether a two-dimensional array is square
        """
        for i in range(1, len(arr)):
            if not (len(arr[i]) == len(arr[i-1])):
                return False
        return True

    #Выводит в консоль актуальный вид интерфейса
    def _print(self):
        print('\n'.join([''.join(string) for string in self.surface]), end='')

    def __on_press(self, key):
        try:
            if hasattr(key, 'char'):
                if (key.char == 's') and (self.cursor[1] < (self.height - 1)):
                    self.cursor[1] += 1
                if (key.char == 'w') and (self.cursor[1] > 0):
                    self.cursor[1] -= 1
                if (key.char == 'd') and (self.cursor[0] < (self.width - 1)):
                    self.cursor[0] += 1
                if (key.char == 'a') and (self.cursor[0] > 0):
                    self.cursor[0] -= 1
        except:
            print('errlol')
        return False
    
    def __on_release(self, key):
        if (hasattr(key, 'char')) and (key.char == 'q'):
            self.__working = False
        if key == keyboard.Key.enter:
            for element in self.__elements:
                if (self.cursor[1]>=element.y)and(self.cursor[1]<=element.y+element.h-1)and(self.cursor[0]>=element.x)and(self.cursor[0]<=element.x+element.w-1):
                    element.click(self.cursor[0]-element.x, self.cursor[1]-element.y)
        return False
    
    def run(self):
        self.__working = True
        while self.__working:
            self.__render()
            self._clear()
            self._print()
            with keyboard.Listener(on_press=self.__on_press, on_release=self.__on_release) as listener:
                listener.join()
            


interface = ConsoleInterface(*get_terminal_size())
f = GameField(10, 5)
s = Scoreboard(6, 0)
f.connect_scoreboard(s)
interface.add_element(f)
interface.add_element(s)
interface.run()


