from rich.console import Console
console = Console()
def print(text,color= "green"):
    console.print(text, style=color)


if __name__ == "__main__":
    print("hello")