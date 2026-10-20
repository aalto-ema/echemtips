"""PyInstaller script entry; all application policy lives in the package."""
from multiprocessing import freeze_support
from echemtips.desktop_launcher import main

if __name__ == '__main__':
    freeze_support()
    main()
