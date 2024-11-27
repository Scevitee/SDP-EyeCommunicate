

<div align="center">
    <img src="assets/eyecomm.png" alt="EyeCommunicate Logo" width="250" height="250">
</div>

# EyeCommunicate


## <a id="about-the-project"></a> 🚀 About the Project
**EyeCommunicate** is an innovative application that demonstrates the power of **eye tracking** and **facial gestures** as input devices. With EyeCommunicate, users can control their cursor using eye movements and trigger various application hotkeys through facial gestures—making hands-free interaction more accessible.

---

## 📚 Table of Contents
1. [About the Project](#about-the-project)
2. [Available Commands](#available-commands)
3. [Setup Instructions](#setup-instructions)
   - [Windows Users](#windows-users)
   - [Linux/Mac Users](#linuxmac-users-todo)
4. [Features](#features)

## <a id="available-commands"></a> 🎯 Available Commands
- **Look Left** → Change page left  
- **Look Right** → Change page right  
- **Look Up** → Increase window size  
- **Look Down** → Decrease window size  
- **Shake Head** → Change gesture detection sensitivity  
- **Nod Head** → Pin window  
- **Raise Eyebrows** → Enter  
- **Hold Blink** → *TBD*  

---
## <a id="setup-instructions"></a> 🔧 Setup Instructions
EyeCommunicate is designed to work with **Python 3.9**. Follow these steps to set up the application:

1. Create a virtual environment:
   ```bash
   python3.9 -m venv env
   ```
2. Install the required dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

### ⚠️ Operating System Note
Setup instructions may vary depending on your operating system:
### **Windows Users**
   
   #### **1. Install Python 3.9**
   - **Download Python 3.9**
      - Visit the [official Python website](https://www.python.org/downloads/release/python-390/).
      - Download the **Windows Installer** for Python 3.9

   - **Run the Installer**
      - Execute the download installer
      - **Important:** During installation, **check the box** that says **"Add Python to PATH"**.
      - Click **"Install Now"** and follow the on-screen instructions.

   #### **2. Clone the EyeCommunicate Repository**
   - **Install Git (if not already installed):**
      - Download Git from the [official website](https://git-scm.com/download/win).
      - Run the installer and follow the installation prompts.

   - **Clone the Repository:**
      - Open **Command Prompt** or **PowerShell**.
      - Navigate to your desired directory:
         ```bash
         cd path\to\your\desired\directory
         ```
      - Clone the repository:
         ```bash
         git clone https://github.com/yourusername/EyeCommunicate.git
         ```
      - Replace `yourusername` with the actual GitHub username.

   #### **3. Create a Virtual Environment**
   - Refer to the [Setup Instructions](#setup-instructions) section above.

   #### **4. Activate the Virtual Environment**
   - Using Command Prompt:
      ```  
      env\Scripts\activate
      ```
   - Using Powershell:
      ```
      source env/Scripts/activate
      ```
   - **Important:** Once activated, ensure the virtual environment is using python 3.9 by running the following:
      ```
      python --version
      ```

   #### **5. Install the Required Dependencies for Windows:**
   - Ensure `pip` is up-to-date and install dependencies:
      ```
      python -m pip install --upgrade pip
      pip install -r requirements_windows.txt
      ```

   #### **6. Run the Application:**
   - From the root directory of the project, run:
      ```
      python main.py
      ```

   #### **7. Deactivate the Application**
   - When finished, deactive the virtual environment:
      ```
      deactivate
      ```
### **Linux/Mac Users**: TODO.

---

## <a id="features"></a> 🌟 Features
- **Hands-Free Interaction**: Use your eyes and facial gestures for seamless control.
- **Customizable Sensitivity**: Adjust the gesture detection sensitivity to your needs.


---

> _Empower interaction with just a glance!_
