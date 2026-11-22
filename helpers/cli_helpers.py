import colorama
colorama.init()

COLORS = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "purple": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",

    "gray": "\033[90m",               # "preto claro"
    "light_red": "\033[91m",
    "light_green": "\033[92m",
    "light_yellow": "\033[93m",
    "light_blue": "\033[94m",
    "light_purple": "\033[95m",
    "light_cyan": "\033[96m",
    "light_white": "\033[97m",
}

BACKGROUND_COLORS = {
    "black": "\033[40m",
    "red": "\033[41m",
    "green": "\033[42m",
    "yellow": "\033[43m",
    "blue": "\033[44m",
    "purple": "\033[45m",
    "cyan": "\033[46m",
    "white": "\033[47m",

    "light_gray": "\033[100m",
    "light_red": "\033[91m",
    "light_green": "\033[102m",
    "light_yellow": "\033[103m",
    "light_blue": "\033[104m",
    "light_purple": "\033[105m",
    "light_cyan": "\033[106m",
    "light_white": "\033[107m",
}

CLEAR = "\033[0m"

def _colorful_text_for_print(text, color=None, background_color=None):
    return f"""{
            COLORS[color] if color in COLORS else ''
        }{
            BACKGROUND_COLORS[background_color] if background_color in BACKGROUND_COLORS else ''
        }{
            text
        }{
            CLEAR
        }"""

def info(text):
    return _colorful_text_for_print(text, color="blue")

def warning(text):
    return _colorful_text_for_print(text, color="yellow")

def error(text):
    return _colorful_text_for_print(text, color="red")

def success(text):
    return _colorful_text_for_print(text, color="green")