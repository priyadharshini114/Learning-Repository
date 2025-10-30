#  Git SSH Setup and Push Guide

This guide walks through the steps to connect your **local Git (Windows)** to **GitHub** using **SSH authentication**, and push your project folder to a remote repository.

---

##  1. Check Git Installation

Open **Command Prompt** or **PowerShell** and verify Git installation:
```bash
git --version
```
**Output example:**
```
git version 2.51.2.windows.1
```

---

##  2. Configure Git Username and Email
Set up your global Git identity:
```bash
git config --global user.name "username"
git config --global user.email "priya000000000@gmail.com"
```

To verify:
```bash
git config --list
```

---

##  3. Generate SSH Key

Run this command to generate an SSH key:
```bash
ssh-keygen -t ed000009 -C "priya000000000@gmail.com"
```

When prompted:
```
Enter file in which to save the key (C:\Users\priya/.ssh/id_ed000009):
```
Just press **Enter** to use the default location.  
If it already exists, type **y** to overwrite.

When asked for a **passphrase**, you can leave it **empty** and press Enter twice.

---

##  4. Locate and Copy the Public Key

After generation, your keys are stored here:
```
C:\Users\priya\.ssh\
```

Open the **`id_ed000009.pub`** file in Notepad and copy its entire contents —  
it starts with:
```
ssh-keygen -t ed000009 -C "priya000000000@gmail.com"
```

---

##  5. Add the SSH Key to GitHub

1. Go to your GitHub account → **Settings → SSH and GPG Keys**  
   or visit [https://github.com/settings/ssh/new](https://github.com/settings/ssh/new)

2. Click **New SSH Key**

3. Give it a title (e.g., `Priya114`)

4. Paste your copied key (the one starting with `ssh-ed000009`)

5. Click **Add SSH Key**

You’ll see a confirmation that the key was added successfully.

---

## 6. Test Your SSH Connection

Run this to test:
```bash
ssh -T git@github.com
```

**Expected output:**
```
Hi priyadharshini114! You've successfully authenticated, but GitHub does not provide shell access.
```

That means SSH is working perfectly 🎉

---

## 
 7. Initialize Git in Your Project Folder

Navigate to your local project folder:
```bash
cd D:\python_files\auto_annotation_tool
```

Initialize a new Git repository:
```bash
git init
```

---

## 🌐 8. Connect to the GitHub Repository

Set your remote repository (replace with your actual GitHub repo URL):
```bash
git remote add origin git@github.com:priyadharshini114/Learning-Repository.git
```

If the remote already exists:
```bash
git remote set-url origin git@github.com:priyadharshini114/Learning-Repository.git
```

---

## 📤 9. Add, Commit, and Push Your Code

```bash
git add .
git commit -m "feat(auto_annotation): add auto_annotation_tool project"
git push -u origin main
```

If you see an error saying *“fetch first”*, run:
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

---

## 🗂️ 10. Organize Folder Structure (Optional)

If you want all related files inside a single subfolder (like `auto_annotation_tool/`):
```bash
mkdir auto_annotation_tool
move .gitignore auto_annotation_tool\
move requirements.txt auto_annotation_tool\
move annotation_core.py auto_annotation_tool\
move annotation_gui.py auto_annotation_tool\
git add .
git commit -m "chore(structure): move project files into auto_annotation_tool folder"
git push origin main
```

Your final structure will look like this:
```
Learning-Repository/
 └── auto_annotation_tool/
      ├── .gitignore
      ├── requirements.txt
      ├── annotation_core.py
      ├── annotation_gui.py
```

---

## ✅ Done!

You’ve now:
- Connected your system to GitHub via SSH  
- Verified authentication  
- Pushed your local project to GitHub  
- Organized your files neatly  

---

