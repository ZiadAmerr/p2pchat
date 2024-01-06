STYLES = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "bold": "\033[1m",
    "underline": "\033[4m",
    "end": "\033[0m",
}


def colorize(text, style: str=None):
    if style is not None:
        if style in STYLES.keys():
            start = STYLES[style]
            end = STYLES["end"]

            return f"{start}{text}{end}"
        
        raise ValueError(
            f"Invalid style: {style}, choose from {STYLES.keys()}")
    
    return text
         


# Usage
if __name__ == "__main__":
    text1 = "hello world"
    text2 = "hi there"

    print(colorize(text1, "red"))
    print(colorize(text2, "underline"))
