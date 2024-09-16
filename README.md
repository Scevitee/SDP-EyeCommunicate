# SDP-EyeCommunicate
Application Suite Utilizing Eye-Tracking and Facial Gestures

---


For development, create a virtual environment using `venv` or `conda`, I use venv

```python3.11 -m venv env```

(Package I used for a test is incompatible with latest Python version, hence the Python3.11)

Access your virtual environment.  

```source env/bin/activate```  

If on Windows, run the following
```source env/Scripts/activate```  

Install the current requirements

```pip install -r requirements.txt```

Update requirements.txt if you install any additional packages

```pip freeze > requirements.txt```

Good practice is to NOT commit your environment files, so I've added env/ to our .gitignore file

---

Please work on your own branch. To cover our bases, I've added some basic stuff about version control just so we're all on the same page. 

Create branch / change branches

```git checkout -b <branch-name>```

Sync with remote regularly 

```git push origin <branch-name>```

Pull and rebase regularly
```
git fetch origin
git checkout main
git pull origin main
```

After pulling, rebase your branch
```
git checkout <branch-name>
git rebase main
```

Merge your branch
```
git checkout main
git pull origin main
git merge <branch-name>
git push origin main
```

OPTIONAL: Delete branch
```
git branch -d <branch-name>
git push origin --delete <branch-name>
```

Example workflow

1. You pull the latest changes from the main branch, create a new branch (feature/user-authentication), and start working.

2. You commit and push your changes regularly. You also pull updates from the main branch, rebase your branch, and resolve any conflicts.

3. You open a pull request for your feature branch. After review and testing, the pull request is approved and merged.

4. You delete the feature branch and start a new branch for the next task