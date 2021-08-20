# Robot Game
Robot Game Repo for CS 5440

# Meeting Room
Team meeting room is **202-C**.

# (Orange) Team Members
 - Imbleau, Spencer
 - Sterckx, Matt
 - Issa, Abdel
 - Villemagne, Jacob
 - Patterson, Luke
 - Pobrica, Andrew

# Tools, IDEs, Environments
 - Python 3.7+
 - Anaconda 3 - [Install](https://docs.anaconda.com/anaconda/install/)
 - PyCharm Community Edition - [Install](https://www.jetbrains.com/pycharm/download/)

# Getting Started (Tips we've learned)
 - The Robot class is in p01.py 
   - p01.py must be called p01.py per Dr. Parry's test files.

 - Install Python 3.7+
 - Install Anaconda 3
 - Install Pycharm Community or Pro (Free for students)
 - open pycharm and click git in the toolbar and select clone
 - clone the repo https://github.com/simbleau/robotgame.git
 - install the conda enviroment in the git repo
   - in windows open conda prompt in linux any old terminal
   - run conda env create -f cs5440.yml in git directory
 - in pycharm click the gear in the upper right hand corner of the window 
 - click settings
 - click the gear next to python interpreter and click add
 - click existing enviorment and select the class one from the dropdown
 - click ok
 - in the terminal type exit and then reopen it
 - run  python3 (or python instead of python3) rgkit/run.py p01.py p01.py

# Submitting
Submit via WebCat at [https://asulearn.appstate.edu/mod/page/view.php?id=1858390](https://asulearn.appstate.edu/mod/page/view.php?id=1858390).
- How to easily compile the submission? 
  - `cd` to the parent directiory of the repo.
  - `rm -i submission.zip || true && zip -r submission.zip robotgame/` - This will zip the repo up and attempt to ask you if you'd like to erase a previous submission if it exists. (If asking is annoying - remove the `-i` flag)
