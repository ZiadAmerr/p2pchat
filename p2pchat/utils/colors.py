class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


# Decorator function to apply color to text
def color_text(color):
    def decorator(func):
        def wrapper(*args, **kwargs):
            return f"{color}{func(*args, **kwargs)}{Colors.END}"

        return wrapper

    return decorator


@color_text(Colors.RED)
def red_text(text):
    return text


@color_text(Colors.GREEN)
def green_text(text):
    return text


@color_text(Colors.YELLOW)
def yellow_text(text):
    return text


@color_text(Colors.BLUE)
def blue_text(text):
    return text


@color_text(Colors.MAGENTA)
def magenta_text(text):
    return text


@color_text(Colors.BOLD)
def bold_text(text):
    return text


# usage
if __name__ == "__main__":
    print(bold_text(red_text("hello world")))
    print(magenta_text("hi there"))
