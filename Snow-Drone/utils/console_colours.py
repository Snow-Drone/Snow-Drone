class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
# info print 
def info(str: str) -> None:
    print(f"{bcolors.OKCYAN}[INFO] {str}{bcolors.ENDC}")

# warning formatter
def warn(str: str) -> None:
    print(f"{bcolors.WARNING}[WARNING] {str}{bcolors.ENDC}")

# timing formatter
def timef(str: str) -> None:
    print(f"{bcolors.OKGREEN}[TIME] {str}{bcolors.ENDC}")
    
# queue info formatter
def queuef(str: str, idx: int = None) -> None:
    print(f"{bcolors.OKBLUE}[QUEUE {idx if idx is not None else ''}] {str}{bcolors.ENDC}")

# different info print
def header(str: str) -> None:
    print(f"{bcolors.HEADER}[INFO] {str}{bcolors.ENDC}")

# error formatter
def err(str: str) -> None:
    print(f"{bcolors.FAIL}[ERROR] {str}{bcolors.ENDC}")